import argparse
import os
import time
import pandas as pd
import requests
import config


BASE_URL = "https://api.polybacktest.com/v2"


def _headers() -> dict:
    api_key = os.environ.get("POLYBACKTEST_API_KEY", config.API_KEY).strip()
    if not api_key:
        raise RuntimeError("Missing POLYBACKTEST_API_KEY in environment")
    return {"X-API-Key": api_key, "Accept": "application/json"}


def _get_json(path: str, params: dict, timeout: int = 20, retries: int = 3):
    url = f"{BASE_URL}{path}"
    last_err = None
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=_headers(), timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            if i < retries - 1:
                time.sleep(1.2 * (i + 1))
    raise RuntimeError(f"API request failed: {last_err}")


def fetch_market_list(limit: int = 200, slug_prefix: str = config.SLUG_PREFIX) -> pd.DataFrame:
    all_rows = []
    seen_ids = set()
    offset = 0
    batch_size = 100
    no_new_rounds = 0
    while len(all_rows) < limit:
        need = min(batch_size, max(1, limit - len(all_rows)))
        data = _get_json(
            "/markets",
            params={"limit": need, "offset": offset, "coin": "BTC", "resolution": "15m"},
        )
        markets = data.get("markets", data.get("data", [])) if isinstance(data, dict) else data
        if not markets:
            break
        before = len(all_rows)
        for m in markets:
            slug = str(m.get("slug", ""))
            if not slug.startswith(slug_prefix):
                continue
            market_id = m.get("market_id", m.get("id"))
            if market_id in seen_ids:
                continue
            seen_ids.add(market_id)
            all_rows.append(
                {
                    "market_id": market_id,
                    "slug": slug,
                    "coin": m.get("coin", "BTC"),
                    "resolution": m.get("resolution", "15m"),
                    "start_time": m.get("start_time"),
                    "end_time": m.get("end_time"),
                    "final_price_up": m.get("final_price_up"),
                    "final_price_down": m.get("final_price_down"),
                }
            )
            if len(all_rows) >= limit:
                break
        if len(markets) < need:
            break
        if len(all_rows) == before:
            no_new_rounds += 1
        else:
            no_new_rounds = 0
        if no_new_rounds >= 3:
            break
        offset += len(markets)
        time.sleep(0.2)
    return pd.DataFrame(all_rows)


def fetch_snapshots_for_market(market_id: str, out_csv: str) -> int:
    snaps = []
    offset = 0
    while True:
        data = _get_json(
            f"/markets/{market_id}/snapshots",
            params={"limit": 1000, "offset": offset, "coin": "BTC"},
        )
        batch = data.get("snapshots", []) if isinstance(data, dict) else []
        if not batch:
            break
        snaps.extend(batch)
        total = int(data.get("total", len(snaps))) if isinstance(data, dict) else len(snaps)
        offset += len(batch)
        if offset >= total:
            break
        time.sleep(0.1)
    if not snaps:
        return 0
    df = pd.DataFrame(snaps)
    df.to_csv(out_csv, index=False)
    return len(df)


def fetch_snapshots_batch(markets_csv: str, out_dir: str, max_markets: int | None = None) -> tuple[int, int]:
    os.makedirs(out_dir, exist_ok=True)
    src = pd.read_csv(markets_csv)
    if "market_id" not in src.columns:
        raise RuntimeError("markets_csv missing 'market_id' column")
    rows = src.dropna(subset=["market_id"]).copy()
    rows["market_id"] = rows["market_id"].astype(str)
    total = 0
    done = 0
    for _, r in rows.iterrows():
        if max_markets is not None and done >= max_markets:
            break
        mid = r["market_id"]
        slug = str(r.get("slug", mid))
        out_csv = os.path.join(out_dir, f"{slug}_snapshots.csv")
        if os.path.exists(out_csv) and os.path.getsize(out_csv) > 0:
            done += 1
            continue
        try:
            n = fetch_snapshots_for_market(mid, out_csv)
            total += n
            done += 1
            print(f"[{done}] {slug}: {n} snapshots")
        except Exception as e:
            print(f"[{done+1}] {slug}: FAILED ({e})")
        time.sleep(0.2)
    return done, total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch history via PolyBacktest API")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--slug-prefix", default=config.SLUG_PREFIX)
    parser.add_argument("--out", default="history_markets.csv")
    parser.add_argument("--market-id", default=None, help="Optional: fetch snapshots for one market_id")
    parser.add_argument("--snapshots-out", default="history_snapshots.csv")
    parser.add_argument("--batch-csv", default=None, help="CSV with market_id column for batch snapshots")
    parser.add_argument("--snapshots-dir", default="snapshots", help="Output directory for batch snapshots")
    parser.add_argument("--max-markets", type=int, default=None)
    args = parser.parse_args()

    if not args.market_id and not args.batch_csv:
        df = fetch_market_list(limit=args.limit, slug_prefix=args.slug_prefix)
        df.to_csv(args.out, index=False)
        print(f"saved {len(df)} rows -> {args.out}")
    if args.market_id:
        n = fetch_snapshots_for_market(args.market_id, args.snapshots_out)
        print(f"saved {n} snapshots -> {args.snapshots_out}")
    if args.batch_csv:
        done, total = fetch_snapshots_batch(args.batch_csv, args.snapshots_dir, args.max_markets)
        print(f"batch done markets={done} snapshots={total} dir={args.snapshots_dir}")
