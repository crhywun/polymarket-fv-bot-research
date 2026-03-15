import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


BASE = Path(__file__).parent
TS_JSON = BASE / "backtest_timesplit_full_validation.json"
WF_JSON = BASE / "backtest_walkforward_full_validation.json"


def _load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def plot_timesplit(ts: dict):
    rows = ts.get("results", [])
    thr = [r["threshold"] for r in rows if "mean_pnl_per_signal" in r]
    mean = [r["mean_pnl_per_signal"] for r in rows if "mean_pnl_per_signal" in r]
    pval = [max(r["p_value_one_sided_t"], 1e-300) for r in rows if "mean_pnl_per_signal" in r]
    neglogp = [-np.log10(p) for p in pval]

    fig, ax1 = plt.subplots(figsize=(9, 5))
    x = np.arange(len(thr))
    b = ax1.bar(x - 0.18, mean, width=0.36, label="mean pnl/signal")
    ax1.axhline(0, color="black", linewidth=1)
    ax1.set_ylabel("Mean PnL per Signal")
    ax1.set_xticks(x, [f"{t:.2f}" for t in thr])
    ax1.set_xlabel("Threshold")
    ax1.set_title("Full Data Time-Split Validation")

    ax2 = ax1.twinx()
    l = ax2.plot(x + 0.18, neglogp, marker="o", linewidth=2, label="-log10(p)")
    ax2.set_ylabel("-log10(p-value)")

    ax1.legend([b, l[0]], ["mean pnl/signal", "-log10(p)"], loc="upper right")
    fig.tight_layout()
    fig.savefig(BASE / "chart_timesplit_full.png", dpi=150)
    plt.close(fig)


def plot_walkforward_aggregate(wf: dict):
    rows = wf.get("aggregate", [])
    thr = [r["threshold"] for r in rows]
    mean = [r["weighted_mean_pnl"] for r in rows]
    medp = [r["median_p_value"] for r in rows]

    fig, ax1 = plt.subplots(figsize=(9, 5))
    x = np.arange(len(thr))
    b = ax1.bar(x - 0.18, mean, width=0.36, label="weighted mean pnl")
    ax1.axhline(0, color="black", linewidth=1)
    ax1.set_ylabel("Weighted Mean PnL")
    ax1.set_xticks(x, [f"{t:.2f}" for t in thr])
    ax1.set_xlabel("Threshold")
    ax1.set_title("Full Data Walk-Forward Aggregate")

    ax2 = ax1.twinx()
    l = ax2.plot(x + 0.18, medp, marker="o", linewidth=2, color="orange", label="median p-value")
    ax2.set_ylabel("Median p-value")
    ax2.set_ylim(0, 1.05)

    ax1.legend([b, l[0]], ["weighted mean pnl", "median p-value"], loc="upper right")
    fig.tight_layout()
    fig.savefig(BASE / "chart_walkforward_full.png", dpi=150)
    plt.close(fig)


def plot_walkforward_folds(wf: dict):
    folds = wf.get("folds", [])
    x = []
    y08 = []
    y10 = []
    for f in folds:
        fid = f.get("fold")
        if not fid:
            continue
        m = {r.get("threshold"): r for r in f.get("results", []) if "mean_pnl_per_signal" in r}
        if 0.08 in m and 0.10 in m:
            x.append(fid)
            y08.append(m[0.08]["mean_pnl_per_signal"])
            y10.append(m[0.10]["mean_pnl_per_signal"])

    if not x:
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, y08, marker="o", label="th=0.08")
    ax.plot(x, y10, marker="o", label="th=0.10")
    ax.axhline(0, color="black", linewidth=1)
    ax.set_xlabel("Fold")
    ax.set_ylabel("Mean PnL per Signal")
    ax.set_title("Walk-Forward Fold-by-Fold Stability (Full Data)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(BASE / "chart_walkforward_folds_full.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    ts = _load(TS_JSON)
    wf = _load(WF_JSON)
    plot_timesplit(ts)
    plot_walkforward_aggregate(wf)
    plot_walkforward_folds(wf)
    print("saved:", BASE / "chart_timesplit_full.png")
    print("saved:", BASE / "chart_walkforward_full.png")
    print("saved:", BASE / "chart_walkforward_folds_full.png")
