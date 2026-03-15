import argparse
import glob
import os
import numpy as np
import pandas as pd


REQUIRED_COLS = ["time", "btc_price", "price_up", "price_down"]


def _time_bucket(remain_time: float) -> str:
    if remain_time <= 180:
        return "0-3m"
    if remain_time <= 360:
        return "3-6m"
    if remain_time <= 540:
        return "6-9m"
    if remain_time <= 720:
        return "9-12m"
    return "12-15m"


def _clean_and_transform_one(path: str, min_rows: int, max_nan_ratio: float) -> pd.DataFrame | None:
    try:
        df = pd.read_csv(path)
    except Exception:
        return None
    if not all(c in df.columns for c in REQUIRED_COLS):
        return None
    if len(df) < min_rows:
        return None

    core = df[REQUIRED_COLS].copy()
    core["time"] = pd.to_datetime(core["time"], errors="coerce", utc=True)
    for c in ["btc_price", "price_up", "price_down"]:
        core[c] = pd.to_numeric(core[c], errors="coerce")
    core = core.dropna(subset=["time"]).sort_values("time")
    if core.empty:
        return None

    nan_ratio = core[["btc_price", "price_up", "price_down"]].isna().mean().max()
    if nan_ratio > max_nan_ratio:
        return None

    # Resample to 1s for stable remain_time and matrix feature engineering
    sec = core.set_index("time").resample("1s").last()
    sec[["btc_price", "price_up", "price_down"]] = sec[["btc_price", "price_up", "price_down"]].ffill().bfill()
    sec = sec.dropna(subset=["btc_price", "price_up", "price_down"]).reset_index()
    if len(sec) < 600:  # at least 10 minutes effective data
        return None

    start = float(sec["btc_price"].iloc[0])
    end = float(sec["btc_price"].iloc[-1])
    outcome = "UP" if end > start else "DOWN"

    sec["btc_start_price"] = start
    sec["btc_price_diff"] = sec["btc_price"] - start
    sec["remain_time"] = np.arange(len(sec) - 1, -1, -1)
    sec["outcome"] = outcome
    sec["time_bucket"] = sec["remain_time"].map(_time_bucket)
    return sec


def build_training_table(snapshots_dir: str, min_rows: int, max_nan_ratio: float) -> tuple[pd.DataFrame, int, int]:
    files = sorted(glob.glob(os.path.join(snapshots_dir, "*_snapshots.csv")))
    good = []
    ok = 0
    bad = 0
    for fp in files:
        one = _clean_and_transform_one(fp, min_rows=min_rows, max_nan_ratio=max_nan_ratio)
        if one is None:
            bad += 1
            continue
        ok += 1
        one["source_file"] = os.path.basename(fp)
        good.append(one)
    if not good:
        raise RuntimeError("No qualified snapshot files after cleaning")
    return pd.concat(good, ignore_index=True), ok, bad


def load_legacy_data(legacy_data_dir: str) -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(legacy_data_dir, "btc-updown-15m-*_1s.csv")))
    chunks = []
    for fp in files:
        try:
            df = pd.read_csv(fp, usecols=["btc_price_diff", "remain_time", "outcome"])
        except Exception:
            continue
        if df.empty:
            continue
        df["outcome"] = df["outcome"].astype(str).str.upper()
        df = df[df["outcome"].isin(["UP", "DOWN"])].copy()
        if df.empty:
            continue
        df["btc_price_diff"] = pd.to_numeric(df["btc_price_diff"], errors="coerce")
        df["remain_time"] = pd.to_numeric(df["remain_time"], errors="coerce")
        df = df.dropna(subset=["btc_price_diff", "remain_time"])
        if df.empty:
            continue
        df["time_bucket"] = df["remain_time"].map(_time_bucket)
        chunks.append(df[["btc_price_diff", "remain_time", "outcome", "time_bucket"]])
    if not chunks:
        return pd.DataFrame(columns=["btc_price_diff", "remain_time", "outcome", "time_bucket"])
    return pd.concat(chunks, ignore_index=True)


def build_fv_matrix(df: pd.DataFrame, diff_bin: int, min_samples: int) -> pd.DataFrame:
    mn = float(df["btc_price_diff"].min())
    mx = float(df["btc_price_diff"].max())
    bins = np.arange(int(mn / diff_bin) * diff_bin - diff_bin, int(mx / diff_bin) * diff_bin + 2 * diff_bin, diff_bin)
    df = df.copy()
    df["diff_bucket"] = pd.cut(df["btc_price_diff"], bins=bins)
    df["outcome_up"] = (df["outcome"] == "UP").astype(int)

    rows = []
    for (tb, db), g in df.groupby(["time_bucket", "diff_bucket"], observed=False):
        n = len(g)
        if n < min_samples:
            continue
        y = g["outcome_up"].astype(float).values
        X = np.column_stack([np.ones(n), g["btc_price_diff"].values, g["remain_time"].values])
        b0, b1, b2 = np.linalg.lstsq(X, y, rcond=None)[0]
        rows.append(
            {
                "time_bucket": tb,
                "diff_bucket": str(db),
                "sample_size": n,
                "up_win_rate": float(y.mean()),
                "down_win_rate": 1.0 - float(y.mean()),
                "up_intercept": float(b0),
                "up_slope_price": float(b1),
                "up_slope_time": float(b2),
                "down_intercept": float(1.0 - b0),
                "down_slope_price": float(-b1),
                "down_slope_time": float(-b2),
            }
        )
    out = pd.DataFrame(rows).sort_values(["time_bucket", "sample_size"], ascending=[True, False])
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Clean snapshots and build fair-value matrix directly")
    p.add_argument("--snapshots-dir", default="snapshots_50")
    p.add_argument("--legacy-data-dir", default=None, help="Optional: include all historical rows from data/*.csv")
    p.add_argument("--cleaned-out", default="cleaned_training_table.csv")
    p.add_argument("--matrix-out", default="fair_values_matrix_from_snapshots.csv")
    p.add_argument("--min-rows", type=int, default=2000)
    p.add_argument("--max-nan-ratio", type=float, default=0.05)
    p.add_argument("--diff-bin", type=int, default=20)
    p.add_argument("--min-samples", type=int, default=500)
    args = p.parse_args()

    train_snap, ok_cnt, bad_cnt = build_training_table(args.snapshots_dir, args.min_rows, args.max_nan_ratio)
    train_base = train_snap[["btc_price_diff", "remain_time", "outcome", "time_bucket"]].copy()

    legacy_rows = 0
    if args.legacy_data_dir:
        legacy = load_legacy_data(args.legacy_data_dir)
        legacy_rows = len(legacy)
        if legacy_rows > 0:
            train_base = pd.concat([train_base, legacy], ignore_index=True)

    train_base.to_csv(args.cleaned_out, index=False)
    matrix = build_fv_matrix(train_base, diff_bin=args.diff_bin, min_samples=args.min_samples)
    matrix.to_csv(args.matrix_out, index=False)

    print(f"qualified_files={ok_cnt} rejected_files={bad_cnt}")
    print(f"snapshot_rows={len(train_snap)} legacy_rows={legacy_rows} total_training_rows={len(train_base)} -> {args.cleaned_out}")
    print(f"matrix_rules={len(matrix)} -> {args.matrix_out}")
