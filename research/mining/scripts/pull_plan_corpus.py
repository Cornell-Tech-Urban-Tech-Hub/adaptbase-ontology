"""Pull plan corpus from local PDFs using Kreuzberg parser.

Parses resilience plan PDFs from the local directory, extracts text + metadata,
and samples a representative set across regions for property extraction.

Outputs:
- corpus/plans/plans.parquet (city, region, pdf_path, text_content, metadata, file_size_kb)
- corpus/plans/parse_stats.txt (success/failure counts, avg length, regions covered)

Usage:
    uv run packages/ontology/mining/scripts/pull_plan_corpus.py [--sample 50] [--refresh]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
from kreuzberg import extract_file_sync, ExtractionConfig

MINING_ROOT = Path(__file__).resolve().parents[1]
CORPUS_PLANS = MINING_ROOT / "corpus" / "plans"
PLANS_DIR = Path("/Users/anthonytownsend/code/_dev/resilience-scanner-plan-PDFs")


def find_all_pdfs(base_dir: Path) -> list[dict]:
    """Walk directory tree and collect all PDFs with region/city metadata."""
    pdfs = []
    for region_dir in base_dir.iterdir():
        if not region_dir.is_dir() or region_dir.name.startswith("."):
            continue
        region = region_dir.name
        for city_dir in region_dir.iterdir():
            if not city_dir.is_dir() or city_dir.name.startswith("."):
                continue
            city = city_dir.name
            for pdf_path in city_dir.glob("*.pdf"):
                pdfs.append({
                    "city": city,
                    "region": region,
                    "pdf_path": str(pdf_path),
                    "filename": pdf_path.name,
                    "file_size_kb": pdf_path.stat().st_size / 1024,
                })
    return pdfs


def parse_pdf(pdf_path: str) -> dict | None:
    """Extract text and metadata from PDF using Kreuzberg."""
    try:
        config = ExtractionConfig()
        result = extract_file_sync(pdf_path, config=config)
        return {
            "text_content": result.content,
            "metadata": result.metadata if hasattr(result, "metadata") else {},
            "text_length": len(result.content),
            "parse_success": True,
            "parse_error": None,
        }
    except Exception as e:
        return {
            "text_content": None,
            "metadata": {},
            "text_length": 0,
            "parse_success": False,
            "parse_error": str(e),
        }


def sample_plans(pdfs: list[dict], n: int) -> list[dict]:
    """Sample n plans, stratified by region if possible."""
    df = pd.DataFrame(pdfs)
    # Try to sample proportionally by region
    sampled = df.groupby("region", group_keys=False).apply(
        lambda x: x.sample(n=min(len(x), max(1, int(n * len(x) / len(df)))), random_state=42)
    )
    # If we got fewer than n, add more from largest regions
    if len(sampled) < n:
        remaining = df[~df.index.isin(sampled.index)]
        additional = remaining.sample(n=min(n - len(sampled), len(remaining)), random_state=42)
        sampled = pd.concat([sampled, additional])
    return sampled.to_dict("records")


def write_stats(df: pd.DataFrame, out_path: Path) -> None:
    """Write parsing statistics."""
    lines = [
        "# Plan Corpus Parsing Statistics\n",
        f"Generated: {datetime.now().isoformat()}\n\n",
        f"Total PDFs found: {len(df)}\n",
        f"Successfully parsed: {df['parse_success'].sum()}\n",
        f"Parse failures: {(~df['parse_success']).sum()}\n\n",
        f"## Text statistics (successful parses only)\n",
        f"Average text length: {df[df['parse_success']]['text_length'].mean():.0f} chars\n",
        f"Median text length: {df[df['parse_success']]['text_length'].median():.0f} chars\n",
        f"Min text length: {df[df['parse_success']]['text_length'].min():.0f} chars\n",
        f"Max text length: {df[df['parse_success']]['text_length'].max():.0f} chars\n\n",
        "## Coverage by region\n",
    ]
    region_counts = df.groupby("region").agg(
        total=("city", "count"),
        parsed=("parse_success", "sum"),
        avg_length=("text_length", "mean"),
    )
    for region, row in region_counts.iterrows():
        lines.append(f"- {region}: {int(row['parsed'])}/{int(row['total'])} parsed, avg {row['avg_length']:.0f} chars\n")

    if (~df["parse_success"]).sum() > 0:
        lines.append("\n## Parse errors\n")
        for _, row in df[~df["parse_success"]].iterrows():
            lines.append(f"- {row['city']} / {row['filename']}: {row['parse_error']}\n")

    out_path.write_text("".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=50, help="Number of plans to sample")
    ap.add_argument("--refresh", action="store_true", help="Re-parse even if cache exists")
    ap.add_argument("--stats", action="store_true", help="Print stats and exit")
    args = ap.parse_args()

    CORPUS_PLANS.mkdir(parents=True, exist_ok=True)
    out_path = CORPUS_PLANS / "plans.parquet"

    # Check cache
    if out_path.exists() and not args.refresh:
        df = pd.read_parquet(out_path)
        if args.stats:
            print(f"Cached corpus: {len(df)} plans")
            print(f"  Parsed: {df['parse_success'].sum()}")
            print(f"  Avg length: {df[df['parse_success']]['text_length'].mean():.0f} chars")
            print(f"  Regions: {df['region'].nunique()}")
            return 0
        print(f"Using cached corpus ({len(df)} plans). Use --refresh to re-parse.")
        return 0

    # Find all PDFs
    if not PLANS_DIR.exists():
        sys.exit(f"Plans directory not found: {PLANS_DIR}")

    print(f"Scanning {PLANS_DIR} for PDFs...")
    all_pdfs = find_all_pdfs(PLANS_DIR)
    print(f"  Found {len(all_pdfs)} PDFs across {len(set(p['region'] for p in all_pdfs))} regions")

    # Sample
    if args.sample and args.sample < len(all_pdfs):
        print(f"Sampling {args.sample} plans (stratified by region)...")
        selected = sample_plans(all_pdfs, args.sample)
    else:
        selected = all_pdfs

    print(f"Parsing {len(selected)} PDFs with Kreuzberg...")
    for i, pdf in enumerate(selected, 1):
        if i % 10 == 0 or i == len(selected):
            print(f"  {i}/{len(selected)}: {pdf['city']} / {pdf['filename']}")
        parse_result = parse_pdf(pdf["pdf_path"])
        pdf.update(parse_result)

    # Save
    df = pd.DataFrame(selected)
    df.to_parquet(out_path, index=False)
    print(f"\nWrote {out_path}")
    print(f"  {df['parse_success'].sum()} successful parses")
    print(f"  {(~df['parse_success']).sum()} failures")

    # Write stats
    stats_path = CORPUS_PLANS / "parse_stats.txt"
    write_stats(df, stats_path)
    print(f"Wrote {stats_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
