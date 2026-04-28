"""Pull the 'breadth corpus' (CDP city adaptation actions) from Supabase.

CDP data lives in catalog_cdp_adaptation (migration 072). ~11,842 records
across 'action' / 'goal' / 'project' record_types, spanning ~762 cities.

Written to packages/ontology/mining/corpus/breadth/cdp_actions.parquet.

Usage:
    uv run packages/ontology/mining/scripts/pull_breadth_corpus.py --stats
    uv run packages/ontology/mining/scripts/pull_breadth_corpus.py --refresh
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client

REPO_ROOT = Path(__file__).resolve().parents[4]
MINING_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = MINING_ROOT / "corpus" / "breadth"

PAGE_SIZE = 1000


def get_client() -> Client:
    load_dotenv(REPO_ROOT / ".env")
    url = os.environ.get("PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        sys.exit("ERROR: PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(url, key)


def pull_cdp(client: Client) -> pd.DataFrame:
    rows: list[dict] = []
    offset = 0
    while True:
        res = (
            client.table("catalog_cdp_adaptation")
            .select("*")
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
        )
        if not res.data:
            break
        rows.extend(res.data)
        if len(res.data) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return pd.DataFrame(rows)


def cache_fresh(path: Path, max_age_days: float) -> bool:
    if not path.exists():
        return False
    return (time.time() - path.stat().st_mtime) / 86400 < max_age_days


def print_stats(df: pd.DataFrame) -> None:
    print("=" * 60)
    print("BREADTH CORPUS STATS (CDP)")
    print("=" * 60)
    print(f"total rows: {len(df):,}")
    if not len(df):
        return
    print(f"unique cities:    {df['city_name'].nunique():,}")
    print(f"unique countries: {df['country'].nunique():,}")
    print("\nrecord_type distribution:")
    for rt, n in df["record_type"].value_counts().items():
        print(f"  {n:>6,}  {rt}")
    print("\ntop regions:")
    for r, n in df["region"].value_counts().head(8).items():
        print(f"  {n:>6,}  {r}")
    actions = df[df["record_type"] == "action"]
    if len(actions):
        print(f"\nactions: {len(actions):,}")
        print(f"  null rate action_name:        {100 * actions['action_name'].isna().mean():.1f}%")
        print(f"  null rate action_description: {100 * actions['action_description'].isna().mean():.1f}%")
        print(f"  null rate action_hazards:     {100 * actions['action_hazards'].isna().mean():.1f}%")
        print(f"  null rate action_sectors:     {100 * actions['action_sectors'].isna().mean():.1f}%")
        print(f"  null rate action_status:      {100 * actions['action_status'].isna().mean():.1f}%")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--freshness-days", type=float, default=7.0)
    args = ap.parse_args()

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    out = CORPUS_DIR / "cdp_actions.parquet"

    if not args.refresh and cache_fresh(out, args.freshness_days):
        print(f"Cache is fresh (< {args.freshness_days} days). Use --refresh to force.")
        if args.stats:
            print_stats(pd.read_parquet(out))
        return 0

    client = get_client()
    print("pulling catalog_cdp_adaptation ...")
    df = pull_cdp(client)
    print(f"  {len(df):,} rows")
    df.to_parquet(out, index=False)

    if args.stats:
        print()
        print_stats(df)

    print()
    print(f"Wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
