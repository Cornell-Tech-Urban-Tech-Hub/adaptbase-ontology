"""Phase A — Mechanism extraction from depth corpus.

Extracts mechanism descriptions from research_versions.markdown and claims for
clustering and taxonomy generation. Uses Haiku for cheap extraction at scale.

The 8 seed mechanism verbs (absorb, redirect, harden, monitor, govern,
adapt_behavior, restore_regenerate, plus some contamination) are used as
anchors for LLM extraction.

Outputs:
- corpus/depth/mechanism_candidates.parquet

Usage:
    uv run packages/ontology/mining/scripts/phase_a_extract_mechanisms.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

MINING_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DEPTH = MINING_ROOT / "corpus" / "depth"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from research.mining.scripts._llm import HAIKU_MODEL, chat_json  # noqa: E402

SEED_VERBS = [
    "absorb",
    "redirect",
    "harden",
    "monitor",
    "govern",
    "adapt_behavior",
    "restore_regenerate",
]

EXTRACT_SYSTEM = """\
You are a climate adaptation expert. Extract mechanism descriptions from the \
research narrative. A mechanism is HOW a solution works — the physical, social, \
or institutional process that creates adaptive capacity or reduces vulnerability. \
Focus on verbs like absorb, redirect, harden, monitor, govern, adapt_behavior, \
restore/regenerate. Return a JSON array of mechanism objects.\
"""


def extract_prompt(markdown: str, solution_id: str) -> str:
    # Clip to ~4K chars to stay under Haiku context
    clip = markdown[:4000] if len(markdown) > 4000 else markdown
    return f"""SOLUTION ID: {solution_id}

RESEARCH NARRATIVE:
{clip}

Extract 1-5 mechanisms described in this narrative. For each mechanism:
- description: one sentence — HOW it works (the causal process)
- supporting_quote: verbatim excerpt from the narrative (max 200 chars)
- canonical_verb: which seed verb best fits (absorb/redirect/harden/monitor/govern/adapt_behavior/restore_regenerate)

Return JSON array:
[
  {{
    "description": "...",
    "supporting_quote": "...",
    "canonical_verb": "..."
  }},
  ...
]

If no clear mechanisms, return []."""


def extract_from_markdown(rv: pd.DataFrame, model: str) -> list[dict]:
    """Extract mechanism candidates from research_versions.markdown."""
    results = []
    for i, (_, row) in enumerate(rv.iterrows()):
        md = row.get("markdown")
        sol_id = row.get("solution_id")
        if not md or not sol_id:
            continue
        try:
            out = chat_json(
                extract_prompt(md, str(sol_id)),
                system=EXTRACT_SYSTEM,
                model=model,
                max_tokens=800,
            )
            if isinstance(out, list):
                for item in out:
                    results.append(
                        {
                            "solution_id": sol_id,
                            "source_type": "research_markdown",
                            "description": item.get("description") or "",
                            "supporting_quote": item.get("supporting_quote") or "",
                            "canonical_verb": item.get("canonical_verb") or "unknown",
                        }
                    )
        except Exception as e:
            print(f"  ! solution {sol_id}: {e}")

        if (i + 1) % 20 == 0:
            print(f"    ... {i + 1}/{len(rv)}")

    return results


def extract_from_claims(claims: pd.DataFrame) -> list[dict]:
    """Extract mechanism-related claims based on claim_type patterns."""
    # First, discover claim_type values that mention mechanism
    claim_types = claims["claim_type"].dropna().unique()
    mech_types = [
        ct for ct in claim_types if ct and ("mechanism" in ct.lower() or "how" in ct.lower())
    ]
    print(f"  found {len(mech_types)} mechanism-related claim_type values:")
    for ct in sorted(mech_types)[:10]:
        print(f"    - {ct}")

    # Extract claims matching those types
    mech_claims = claims[claims["claim_type"].isin(mech_types)]
    results = []
    for _, row in mech_claims.iterrows():
        text = row.get("claim_text") or ""
        if len(text) < 20:
            continue
        results.append(
            {
                "solution_id": row.get("solution_id"),
                "source_type": "claim",
                "description": text[:300],
                "supporting_quote": row.get("source_snippet") or "",
                "canonical_verb": "unknown",
                "claim_type": row.get("claim_type"),
            }
        )
    return results


def main() -> int:
    print("loading depth corpus ...")
    rv = pd.read_parquet(CORPUS_DEPTH / "research_versions.parquet")
    claims = pd.read_parquet(CORPUS_DEPTH / "claims.parquet")
    print(f"  {len(rv)} research_versions, {len(claims)} claims")

    print(f"extracting from markdown ({len(rv)} docs, model={HAIKU_MODEL}) ...")
    md_candidates = extract_from_markdown(rv, HAIKU_MODEL)
    print(f"  extracted {len(md_candidates)} mechanism candidates from markdown")

    print("extracting from claims ...")
    claim_candidates = extract_from_claims(claims)
    print(f"  extracted {len(claim_candidates)} mechanism candidates from claims")

    all_candidates = md_candidates + claim_candidates
    df = pd.DataFrame(all_candidates)
    out_path = CORPUS_DEPTH / "mechanism_candidates.parquet"
    df.to_parquet(out_path, index=False)
    print(f"\nwrote {len(df)} candidates to {out_path}")
    print(f"  by source_type: {df['source_type'].value_counts().to_dict()}")
    print(f"  by canonical_verb: {df['canonical_verb'].value_counts().to_dict()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
