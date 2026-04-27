"""Phase P — Extract property patterns from plan documents.

Simplified two-step approach:
1. Extract key metadata fields from each plan (this script)
2. Cluster patterns and propose schema (separate script)

This script focuses on extracting specific, structured fields that appear
across resilience plans, similar to how we extracted mechanism patterns.

Outputs:
- corpus/plans/property_candidates.parquet

Usage:
    uv run packages/ontology/mining/scripts/phase_p_extract_properties.py [--limit 10]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

MINING_ROOT = Path(__file__).resolve().parents[1]
CORPUS_PLANS = MINING_ROOT / "corpus" / "plans"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _llm import chat_json, SONNET_MODEL  # noqa: E402

EXTRACTION_PROMPT = """Analyze this resilience plan and extract the following specific fields.
Return ONLY valid JSON with no markdown formatting or explanation.

Extract these fields (use null if not found):
1. plan_title: Official title of the plan
2. plan_type: Type of plan (e.g., "Resilience Strategy", "Climate Action Plan", "Adaptation Plan")
3. adoption_year: Year the plan was adopted or published (integer)
4. planning_horizon_years: How many years into the future this plan covers (integer)
5. authoring_organizations: Array of organizations that authored/commissioned the plan
6. implementing_agencies: Array of key implementing agencies or departments
7. total_actions: Total number of actions/initiatives/solutions in the plan (integer)
8. total_budget_mentioned: Any budget or cost estimates mentioned (string with currency)
9. external_frameworks: Array of external frameworks referenced (e.g., ["CRF", "Sendai", "SDGs"])
10. monitoring_approach: How the plan describes monitoring/evaluation (brief string or null)

Return as:
{{"fields": {{"plan_title": "...", "plan_type": "...", ...}}}}

Plan text (first 30,000 chars):
{plan_text}"""


def extract_properties_from_plan(
    city: str, region: str, text_content: str
) -> dict | None:
    """Use LLM to extract structured fields from a plan document."""
    # Truncate to manageable size
    text_sample = text_content[:30000]

    prompt = EXTRACTION_PROMPT.format(plan_text=text_sample)

    try:
        result = chat_json(
            prompt=prompt,
            model=SONNET_MODEL,  # Use Sonnet for better structured output
            temperature=0,
            max_tokens=2000,
        )
        fields = result.get("fields", {})
        # Add source metadata
        fields["source_city"] = city
        fields["source_region"] = region
        fields["text_length"] = len(text_content)
        return fields
    except Exception as e:
        print(f"  Error extracting from {city}: {e}")
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="Limit to first N plans for testing")
    args = ap.parse_args()

    plans_path = CORPUS_PLANS / "plans.parquet"
    if not plans_path.exists():
        sys.exit(
            f"Plan corpus not found at {plans_path}. "
            f"Run pull_plan_corpus.py first."
        )

    plans = pd.read_parquet(plans_path)
    plans = plans[plans["parse_success"]]  # Only successfully parsed
    if args.limit:
        plans = plans.head(args.limit)

    print(f"Extracting properties from {len(plans)} plans...")

    all_candidates = []
    for i, row in plans.iterrows():
        print(f"  {i+1}/{len(plans)}: {row['city']}")
        fields = extract_properties_from_plan(
            row["city"], row["region"], row["text_content"]
        )
        if fields:
            all_candidates.append(fields)

    print(f"\nExtracted {len(all_candidates)} plan records")

    # Save
    out_path = CORPUS_PLANS / "property_candidates.parquet"
    df = pd.DataFrame(all_candidates)
    df.to_parquet(out_path, index=False)
    print(f"Wrote {out_path}")

    # Quick stats
    print(f"\nExtraction completeness:")
    non_null_counts = df.notna().sum()
    print(non_null_counts[non_null_counts > 0].sort_values(ascending=False).to_string())

    return 0


if __name__ == "__main__":
    sys.exit(main())
