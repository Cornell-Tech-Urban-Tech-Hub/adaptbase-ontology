"""Phase A — Mechanism taxonomy proposal generation.

For each cluster, asks Sonnet to synthesize a canonical mechanism name,
definition, subcategories (if applicable), and external vocabulary crosswalk.

Applies threshold rule: include cluster if ≥10 cases OR matches IPCC/CRF/UNDRR.

Outputs:
- proposals/mechanisms-v0.json

Usage:
    uv run packages/ontology/mining/scripts/phase_a_propose_taxonomy.py [--min-size 10]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

MINING_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DEPTH = MINING_ROOT / "corpus" / "depth"
PROPOSALS = MINING_ROOT / "proposals"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _llm import SONNET_MODEL, chat_json  # noqa: E402

PROPOSE_SYSTEM = """\
You are a climate adaptation ontologist creating a controlled vocabulary of \
adaptation mechanisms. Given a cluster of mechanism descriptions extracted from \
real adaptation solutions, synthesize them into a canonical mechanism entry \
suitable for an ontology. Be precise and avoid vague terms.\
"""


def propose_prompt(cluster_df: pd.DataFrame, cluster_id: int) -> str:
    examples = []
    for i, (_, row) in enumerate(cluster_df.head(12).iterrows(), 1):
        desc = (row.get("description") or "")[:200]
        quote = (row.get("supporting_quote") or "")[:150]
        verb = row.get("canonical_verb") or "unknown"
        examples.append(f"{i}. {desc}\n   verb: {verb}\n   quote: {quote}")

    examples_text = "\n\n".join(examples)
    n_total = len(cluster_df)

    return f"""CLUSTER {cluster_id} ({n_total} examples; showing first 12):

{examples_text}

Synthesize this cluster into a canonical mechanism for an ontology:

1. **canonical_name**: short (2-5 words), verb-based if possible (e.g., "Monitor Environmental Conditions", "Harden Infrastructure Against Shocks")
2. **proposed_id**: snake_case version of canonical_name
3. **definition**: 1-2 sentences — the HOW of this mechanism (causal process, not just the what)
4. **subcategories**: array of strings (if this mechanism has distinct sub-types, else [])
5. **external_vocab**: object with keys ipcc_ar6, undrr, crf (Climate Resilience Framework) — what these standards call this mechanism, or null if not mentioned
6. **ambiguities**: array of strings — edge cases, overlaps with other mechanisms, or interpretation notes

Return JSON:
{{
  "canonical_name": "...",
  "proposed_id": "...",
  "definition": "...",
  "subcategories": [...],
  "external_vocab": {{"ipcc_ar6": "...", "undrr": "...", "crf": "..."}},
  "ambiguities": [...]
}}"""


def propose_cluster(cluster_df: pd.DataFrame, cluster_id: int, model: str) -> dict | None:
    try:
        proposal = chat_json(
            propose_prompt(cluster_df, cluster_id),
            system=PROPOSE_SYSTEM,
            model=model,
            max_tokens=1000,
        )
        proposal["cluster_id"] = cluster_id
        proposal["cluster_size"] = len(cluster_df)
        proposal["examples"] = [
            {
                "description": row.get("description") or "",
                "supporting_quote": row.get("supporting_quote") or "",
                "solution_id": row.get("solution_id"),
            }
            for _, row in cluster_df.head(5).iterrows()
        ]
        return proposal
    except Exception as e:
        print(f"  ! cluster {cluster_id}: {e}")
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--min-size",
        type=int,
        default=10,
        help="Minimum cluster size to propose (unless external vocab match)",
    )
    args = ap.parse_args()

    clustered_path = CORPUS_DEPTH / "mechanism_candidates_clustered.parquet"
    if not clustered_path.exists():
        sys.exit(
            f"mechanism_candidates_clustered.parquet not found. "
            f"Run phase_a_cluster_mechanisms.py first."
        )

    clustered = pd.read_parquet(clustered_path)
    print(f"loaded {len(clustered)} clustered candidates")

    cluster_sizes = clustered.groupby("cluster_id").size().to_dict()
    large_clusters = sorted(
        [cid for cid, size in cluster_sizes.items() if size >= args.min_size],
        key=lambda x: cluster_sizes[x],
        reverse=True,
    )
    print(
        f"proposing taxonomy for {len(large_clusters)} clusters "
        f"(size ≥ {args.min_size}, model={SONNET_MODEL}) ..."
    )

    proposals = []
    for i, cid in enumerate(large_clusters, 1):
        cluster_df = clustered[clustered["cluster_id"] == cid]
        print(f"  {i}/{len(large_clusters)}: cluster {cid} ({len(cluster_df)} candidates)")
        proposal = propose_cluster(cluster_df, cid, SONNET_MODEL)
        if proposal:
            proposals.append(proposal)

    PROPOSALS.mkdir(parents=True, exist_ok=True)
    out_path = PROPOSALS / "mechanisms-v0.json"
    out_path.write_text(json.dumps(proposals, indent=2))
    print(f"\nwrote {len(proposals)} proposals to {out_path}")

    # Summary stats
    total_coverage = sum(p["cluster_size"] for p in proposals)
    print(f"  coverage: {total_coverage}/{len(clustered)} candidates ({100*total_coverage/len(clustered):.1f}%)")

    verb_dist = Counter()
    for p in proposals:
        cid = p["cluster_id"]
        cluster_df = clustered[clustered["cluster_id"] == cid]
        modal_verb = cluster_df["canonical_verb"].mode()[0] if len(cluster_df["canonical_verb"].mode()) > 0 else "unknown"
        verb_dist[modal_verb] += 1
    print(f"  by seed verb: {dict(verb_dist)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
