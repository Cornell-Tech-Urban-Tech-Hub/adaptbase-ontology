"""Pull the 'depth corpus' from Supabase into a local parquet cache.

The depth corpus is the set of published deep-research solution narratives:
- research_versions where published=true (~220)
- solutions for those solution_ids (taxonomy, loc_id, extraction_schema)
- claims joined by solution_id (run_id is an import-batch marker here, not a
  per-research-session key — solution_id is the correct semantic join)
- documents joined by claims.document_id

Written to packages/ontology/mining/corpus/depth/*.parquet. Idempotent: a
refresh older than --freshness-days (default 7) is required to re-pull.

Usage:
    uv run packages/ontology/mining/scripts/pull_depth_corpus.py --stats
    uv run packages/ontology/mining/scripts/pull_depth_corpus.py --refresh
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client

REPO_ROOT = Path(__file__).resolve().parents[4]
MINING_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = MINING_ROOT / "corpus" / "depth"

PAGE_SIZE = 1000
IN_BATCH_SIZE = 200  # supabase/postgrest URL length cap when filtering by IN(...)


def get_client() -> Client:
    load_dotenv(REPO_ROOT / ".env")
    url = os.environ.get("PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        sys.exit("ERROR: PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(url, key)


def _paginate(client: Client, table: str, columns: str, filters: dict | None = None):
    """Yield rows from table in PAGE_SIZE pages.

    filters: {column: ("eq"|"in", value)} for simple equality or IN filters.
    """
    offset = 0
    while True:
        q = client.table(table).select(columns)
        for col, (op, val) in (filters or {}).items():
            if op == "eq":
                q = q.eq(col, val)
            elif op == "in":
                q = q.in_(col, val)
            else:
                raise ValueError(f"unsupported op: {op}")
        res = q.range(offset, offset + PAGE_SIZE - 1).execute()
        if not res.data:
            break
        yield from res.data
        if len(res.data) < PAGE_SIZE:
            break
        offset += PAGE_SIZE


def _paginate_in(client: Client, table: str, columns: str, in_col: str, ids: list):
    """Paginate a table with an IN(...) filter, chunking IDs to avoid URL limits."""
    seen = set()
    for start in range(0, len(ids), IN_BATCH_SIZE):
        batch = ids[start : start + IN_BATCH_SIZE]
        offset = 0
        while True:
            res = (
                client.table(table)
                .select(columns)
                .in_(in_col, batch)
                .range(offset, offset + PAGE_SIZE - 1)
                .execute()
            )
            if not res.data:
                break
            for row in res.data:
                # Dedup by id when available (documents may repeat across batches)
                rid = row.get("id")
                if rid is not None:
                    if rid in seen:
                        continue
                    seen.add(rid)
                yield row
            if len(res.data) < PAGE_SIZE:
                break
            offset += PAGE_SIZE


def _stringify_jsonb(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Serialize JSONB-typed columns to JSON strings so parquet can store them.

    Mixed dict/list/null columns break pyarrow; storing as strings is lossless
    and downstream scripts can `json.loads` on demand.
    """
    for c in cols:
        if c in df.columns:
            df[c] = df[c].map(lambda v: json.dumps(v) if v is not None else None)
    return df


def pull_research_versions(client: Client) -> pd.DataFrame:
    cols = (
        "id, solution_id, run_id, version, published, hazards, "
        "markdown, metadata, created_at, generated_at"
    )
    rows = list(_paginate(client, "research_versions", cols, {"published": ("eq", True)}))
    df = pd.DataFrame(rows)
    return _stringify_jsonb(df, ["hazards", "metadata"])


def pull_solutions(client: Client, solution_ids: list[str]) -> pd.DataFrame:
    if not solution_ids:
        return pd.DataFrame()
    cols = "id, loc_id, taxonomy, publication, research, extraction_schema, created_at, updated_at"
    rows = list(_paginate_in(client, "solutions", cols, "id", solution_ids))
    df = pd.DataFrame(rows)
    return _stringify_jsonb(df, ["taxonomy", "publication", "research", "extraction_schema"])


def pull_claims(client: Client, solution_ids: list[str]) -> pd.DataFrame:
    cols = (
        "id, claim_id, solution_id, run_id, document_id, chunk_id, "
        "claim_text, claim_type, source_snippet, source_url, source_title, "
        "source_type, source_domain, confidence, validation_status, "
        "validation_score, metadata, extraction_model, extraction_stage, "
        "report_section, relevance_scope, created_at"
    )
    rows = list(_paginate_in(client, "claims", cols, "solution_id", solution_ids))
    df = pd.DataFrame(rows)
    return _stringify_jsonb(df, ["metadata"])


def pull_documents(client: Client, document_ids: list[str]) -> pd.DataFrame:
    if not document_ids:
        return pd.DataFrame()
    cols = (
        "id, document_id, url, title, domain, source_type, scope, language, "
        "city_name, loc_id, text_summary, word_count, processing_status, "
        "classifications, tags, provenance, created_at"
    )
    rows = list(_paginate_in(client, "documents", cols, "id", document_ids))
    df = pd.DataFrame(rows)
    return _stringify_jsonb(df, ["classifications", "tags", "provenance"])


def _null_rate(df: pd.DataFrame, col: str) -> str:
    if col not in df.columns or len(df) == 0:
        return "n/a"
    nulls = df[col].isna().sum() + (df[col] == "").sum() if df[col].dtype == object else df[col].isna().sum()
    return f"{100.0 * nulls / len(df):.1f}%"


def print_stats(rv: pd.DataFrame, sol: pd.DataFrame, cl: pd.DataFrame, dc: pd.DataFrame) -> None:
    print("=" * 60)
    print("DEPTH CORPUS STATS")
    print("=" * 60)
    print(f"research_versions: {len(rv):>7,} rows")
    if len(rv):
        total_md_bytes = rv["markdown"].fillna("").str.len().sum()
        print(f"  unique solution_ids: {rv['solution_id'].nunique()}")
        print(f"  markdown total: {total_md_bytes / 1e6:.1f} MB  (median {rv['markdown'].fillna('').str.len().median():.0f} chars)")
        print(f"  null rate markdown: {_null_rate(rv, 'markdown')}")
        print(f"  null rate hazards:  {_null_rate(rv, 'hazards')}")
    print(f"solutions:         {len(sol):>7,} rows")
    if len(sol):
        print(f"  null rate taxonomy:          {_null_rate(sol, 'taxonomy')}")
        print(f"  null rate extraction_schema: {_null_rate(sol, 'extraction_schema')}")
        print(f"  null rate loc_id:            {_null_rate(sol, 'loc_id')}")
    print(f"claims:            {len(cl):>7,} rows")
    if len(cl):
        print(f"  null rate source_url:     {_null_rate(cl, 'source_url')}")
        print(f"  null rate source_snippet: {_null_rate(cl, 'source_snippet')}")
        print(f"  null rate document_id:    {_null_rate(cl, 'document_id')}")
        top_types = cl["claim_type"].value_counts().head(10) if "claim_type" in cl.columns else pd.Series()
        if not top_types.empty:
            print("  top claim_types:")
            for t, n in top_types.items():
                print(f"    {n:>6,}  {t}")
    print(f"documents:         {len(dc):>7,} rows")
    if len(dc):
        print(f"  null rate text_summary: {_null_rate(dc, 'text_summary')}")
        top_dom = dc["domain"].value_counts().head(5) if "domain" in dc.columns else pd.Series()
        if not top_dom.empty:
            print("  top domains:")
            for d, n in top_dom.items():
                print(f"    {n:>4,}  {d}")


def cache_fresh(paths: list[Path], max_age_days: float) -> bool:
    if not all(p.exists() for p in paths):
        return False
    now = time.time()
    age_days = min((now - p.stat().st_mtime) / 86400 for p in paths)
    return age_days < max_age_days


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="Force re-pull even if cache is fresh")
    ap.add_argument("--stats", action="store_true", help="Print stats after pull (or on cached files)")
    ap.add_argument("--freshness-days", type=float, default=7.0)
    args = ap.parse_args()

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    rv_path = CORPUS_DIR / "research_versions.parquet"
    sol_path = CORPUS_DIR / "solutions.parquet"
    cl_path = CORPUS_DIR / "claims.parquet"
    dc_path = CORPUS_DIR / "documents.parquet"
    paths = [rv_path, sol_path, cl_path, dc_path]

    # Stale research_runs file from an earlier draft of this script; remove so
    # downstream scripts don't pick up zero-row data.
    stale = CORPUS_DIR / "research_runs.parquet"
    if stale.exists():
        stale.unlink()

    if not args.refresh and cache_fresh(paths, args.freshness_days):
        print(f"Cache is fresh (< {args.freshness_days} days). Use --refresh to force.")
        if args.stats:
            rv = pd.read_parquet(rv_path)
            sol = pd.read_parquet(sol_path)
            cl = pd.read_parquet(cl_path)
            dc = pd.read_parquet(dc_path)
            print_stats(rv, sol, cl, dc)
        return 0

    client = get_client()

    print("[1/4] pulling research_versions (published=true) ...")
    rv = pull_research_versions(client)
    print(f"      {len(rv):,} rows ({rv['solution_id'].nunique()} unique solution_ids)")
    rv.to_parquet(rv_path, index=False)

    solution_ids = [s for s in rv["solution_id"].dropna().unique().tolist() if s]
    print(f"[2/4] pulling solutions for {len(solution_ids):,} solution_ids ...")
    sol = pull_solutions(client, solution_ids)
    print(f"      {len(sol):,} rows")
    sol.to_parquet(sol_path, index=False)

    print(f"[3/4] pulling claims for {len(solution_ids):,} solution_ids ...")
    cl = pull_claims(client, solution_ids)
    print(f"      {len(cl):,} rows")
    cl.to_parquet(cl_path, index=False)

    doc_ids = []
    if len(cl) and "document_id" in cl.columns:
        doc_ids = [d for d in cl["document_id"].dropna().unique().tolist() if d]
    print(f"[4/4] pulling documents for {len(doc_ids):,} document_ids ...")
    dc = pull_documents(client, doc_ids)
    print(f"      {len(dc):,} rows")
    dc.to_parquet(dc_path, index=False)

    if args.stats:
        print()
        print_stats(rv, sol, cl, dc)

    total_bytes = sum(p.stat().st_size for p in paths)
    print()
    print(f"Wrote {len(paths)} parquet files totaling {total_bytes / 1e6:.1f} MB to {CORPUS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
