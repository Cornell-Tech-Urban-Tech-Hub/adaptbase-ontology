"""Phase A — Mechanism clustering via embeddings.

Embeds all mechanism candidates and clusters them using hierarchical
agglomerative clustering with cosine distance. The distance threshold is
tunable; default 0.25 gives semantically coherent clusters.

Outputs:
- corpus/depth/mechanism_candidates_clustered.parquet (adds cluster_id column)
- reports/mechanism-clustering-stats.txt

Usage:
    uv run packages/ontology/mining/scripts/phase_a_cluster_mechanisms.py [--threshold 0.25]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from sklearn.cluster import AgglomerativeClustering

MINING_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DEPTH = MINING_ROOT / "corpus" / "depth"
REPORTS = MINING_ROOT / "reports"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from research.mining.scripts._llm import embed_texts  # noqa: E402


def cluster_mechanisms(
    candidates: pd.DataFrame, threshold: float
) -> tuple[pd.DataFrame, dict]:
    """Embed and cluster mechanism descriptions."""
    descriptions = candidates["description"].fillna("").tolist()
    print(f"embedding {len(descriptions)} mechanism descriptions ...")
    embeddings = embed_texts(descriptions, batch_size=100)
    print(f"  got {len(embeddings)} embeddings, dim={len(embeddings[0])}")

    print(f"clustering with threshold={threshold} ...")
    clusterer = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=threshold,
        metric="cosine",
        linkage="average",
    )
    labels = clusterer.fit_predict(embeddings)
    n_clusters = len(set(labels))
    print(f"  found {n_clusters} clusters")

    candidates["cluster_id"] = labels

    # Compute cluster stats
    cluster_sizes = candidates.groupby("cluster_id").size().to_dict()
    cluster_verbs = (
        candidates.groupby("cluster_id")["canonical_verb"]
        .apply(lambda x: x.mode()[0] if len(x.mode()) > 0 else "unknown")
        .to_dict()
    )

    stats = {
        "n_clusters": n_clusters,
        "cluster_sizes": cluster_sizes,
        "cluster_verbs": cluster_verbs,
    }
    return candidates, stats


def write_stats(stats: dict, out_path: Path) -> None:
    lines = [
        "# Mechanism Clustering Statistics\n",
        f"Total clusters: {stats['n_clusters']}\n",
        "\n## Cluster sizes\n",
    ]
    for cid in sorted(stats["cluster_sizes"], key=lambda x: stats["cluster_sizes"][x], reverse=True):
        size = stats["cluster_sizes"][cid]
        verb = stats["cluster_verbs"].get(cid, "unknown")
        lines.append(f"- Cluster {cid}: {size} candidates (modal verb: {verb})\n")
    out_path.write_text("".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.25, help="Cosine distance threshold")
    args = ap.parse_args()

    candidates_path = CORPUS_DEPTH / "mechanism_candidates.parquet"
    if not candidates_path.exists():
        sys.exit(
            f"mechanism_candidates.parquet not found. "
            f"Run phase_a_extract_mechanisms.py first."
        )

    candidates = pd.read_parquet(candidates_path)
    print(f"loaded {len(candidates)} mechanism candidates")

    clustered, stats = cluster_mechanisms(candidates, args.threshold)

    out_path = CORPUS_DEPTH / "mechanism_candidates_clustered.parquet"
    clustered.to_parquet(out_path, index=False)
    print(f"\nwrote {out_path}")

    REPORTS.mkdir(parents=True, exist_ok=True)
    stats_path = REPORTS / "mechanism-clustering-stats.txt"
    write_stats(stats, stats_path)
    print(f"wrote {stats_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
