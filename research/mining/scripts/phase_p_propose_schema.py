"""Phase P — Generate Plan entity property schema from extracted patterns.

Analyzes the property candidates extracted from plan documents and generates
a proposed schema for the Plan entity in the ontology. Uses LLM to synthesize
common patterns, determine data types, and identify which properties should be
required vs optional.

Outputs:
- proposals/plan-properties-v0.json

Usage:
    uv run packages/ontology/mining/scripts/phase_p_propose_schema.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

MINING_ROOT = Path(__file__).resolve().parents[1]
CORPUS_PLANS = MINING_ROOT / "corpus" / "plans"
PROPOSALS = MINING_ROOT / "proposals"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from research.mining.scripts._llm import chat_json, SONNET_MODEL  # noqa: E402

PROPOSAL_PROMPT = """You are designing a knowledge graph schema for resilience plans based on real-world data.

I've extracted structured fields from {n_plans} resilience plans. Here's the analysis:

**Coverage statistics** (how many plans have each field):
{coverage_stats}

**Sample values** for each field:
{sample_values}

Based on this data, propose a comprehensive property schema for the Plan entity.

For each property, specify:
1. property_id: Snake_case identifier
2. property_name: Human-readable label
3. data_type: One of: string, integer, date, array_of_strings, array_of_objects, boolean, currency
4. required: Whether this should be required (true/false) - base this on coverage % and importance
5. definition: 1-2 sentence description of what this property represents
6. examples: Array of 2-3 example values from the data
7. notes: Any implementation notes, edge cases, or relationships to external vocabularies

Additionally propose:
8. **Relationship types** that Plans should have to other entities (e.g., Plan-[:AUTHORED_BY]->Organization, Plan-[:ALIGNS_WITH]->Framework)

Focus on properties that would enable meaningful graph queries. Prioritize properties
with good coverage (>50%) unless they're critically important for context.

IMPORTANT: Return ONLY valid JSON in the exact format below, no markdown formatting:

{{
  "properties": [
    {{
      "property_id": "plan_title",
      "property_name": "Plan Title",
      "data_type": "string",
      "required": true,
      "definition": "Official title of the resilience plan document",
      "examples": ["Lagos Resilience Strategy", "Pittsburgh Climate Action Plan 3.0"],
      "notes": "Primary identifier for the plan"
    }}
  ],
  "relationships": [
    {{
      "relationship_type": "AUTHORED_BY",
      "target_entity": "Organization",
      "definition": "Organization that authored or commissioned the plan",
      "cardinality": "many"
    }}
  ]
}}
"""


def analyze_coverage(df: pd.DataFrame) -> str:
    """Generate coverage statistics for each field."""
    total = len(df)
    lines = []
    for col in df.columns:
        if col.startswith("source_") or col == "text_length":
            continue
        non_null = df[col].notna().sum()
        pct = (non_null / total) * 100
        lines.append(f"- {col}: {non_null}/{total} ({pct:.0f}%)")
    return "\n".join(lines)


def sample_values(df: pd.DataFrame, n=3) -> str:
    """Generate sample values for each field."""
    lines = []
    for col in df.columns:
        if col.startswith("source_") or col == "text_length":
            continue
        samples = df[col].dropna().head(n).tolist()
        if samples:
            # Format samples nicely
            formatted = []
            for s in samples:
                if isinstance(s, list):
                    formatted.append(f"{s[:2]}..." if len(s) > 2 else str(s))
                else:
                    formatted.append(str(s)[:80])
            lines.append(f"\n{col}:")
            for f in formatted:
                lines.append(f"  - {f}")
    return "\n".join(lines)


def main() -> int:
    candidates_path = CORPUS_PLANS / "property_candidates.parquet"
    if not candidates_path.exists():
        sys.exit(
            f"Property candidates not found at {candidates_path}. "
            f"Run phase_p_extract_properties.py first."
        )

    df = pd.read_parquet(candidates_path)
    print(f"Loaded {len(df)} plan records")

    # Generate analysis
    coverage = analyze_coverage(df)
    samples = sample_values(df, n=3)

    prompt = PROPOSAL_PROMPT.format(
        n_plans=len(df),
        coverage_stats=coverage,
        sample_values=samples,
    )

    print("Generating property schema proposal...")
    try:
        result = chat_json(
            prompt=prompt,
            model=SONNET_MODEL,
            temperature=0,
            max_tokens=4000,
        )
    except Exception as e:
        sys.exit(f"Failed to generate proposals: {e}")

    # Handle cases where LLM returns list instead of dict
    if isinstance(result, list):
        result = {"properties": result, "relationships": []}

    # Save proposal
    PROPOSALS.mkdir(parents=True, exist_ok=True)
    out_path = PROPOSALS / "plan-properties-v0.json"

    import json
    out_path.write_text(json.dumps(result, indent=2))
    print(f"\nWrote {out_path}")

    # Print summary
    n_props = len(result.get("properties", []))
    n_rels = len(result.get("relationships", []))
    print(f"\nProposed:")
    print(f"  {n_props} properties")
    print(f"  {n_rels} relationship types")

    # Show required properties
    required = [p for p in result.get("properties", []) if p.get("required")]
    print(f"\n  Required properties ({len(required)}):")
    for p in required:
        print(f"    - {p['property_id']}: {p['property_name']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
