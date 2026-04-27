# Phase P: Plan Entity Properties — Summary

## What We Built

Extended the corpus mining pipeline to extract and propose Plan entity properties from actual resilience plan documents.

### Pipeline Components

1. **PDF Parsing** (`pull_plan_corpus.py`)
   - Parsed 158 local PDFs using Kreuzberg parser
   - Sampled 50 plans stratified by region
   - 100% success rate (50/50 parsed)
   - Average plan length: ~181K chars

2. **Property Extraction** (`phase_p_extract_properties.py`)
   - Extracted 10 structured fields from each plan using Sonnet
   - Fields: title, type, adoption_year, planning_horizon, authoring_organizations, implementing_agencies, total_actions, budget, external_frameworks, monitoring_approach
   - Coverage ranges from 14% (budget) to 100% (plan_type, authoring_orgs)

3. **Schema Proposal** (`phase_p_propose_schema.py`)
   - Analyzed extraction patterns across 50 plans
   - Generated 11 property definitions
   - Generated 11 relationship types
   - Identified 3 required properties (plan_title, plan_type, adoption_year)

4. **Review UI** (extended `review_server.py` + `review.html`)
   - Added "plans" phase to review dropdown
   - Properties and relationships reviewable as separate items
   - Shows data types, examples, coverage stats

5. **Decision Application** (extended `apply_decisions.py`)
   - Applies approved properties to Plan entity in ontology-v0.1.json
   - Applies approved relationships to ontology relationships array
   - Logs rejections to decisions-log.md

### Generated Proposals

**Properties (11 total):**
- Required: plan_title, plan_type, adoption_year
- Optional: planning_horizon_years, total_actions, total_budget_mentioned, monitoring_approach, plan_uri, document_url, geographic_scope, plan_status

**Relationships (11 total):**
- AUTHORED_BY → Organization
- IMPLEMENTED_BY → Organization
- ALIGNS_WITH → Framework
- SUPERSEDES → Plan
- SUPERSEDED_BY → Plan
- COVERS_LOCATION → Location
- CONTAINS_ACTION → Action
- ADDRESSES_HAZARD → Hazard
- TARGETS_SECTOR → Sector
- REFERENCES → Plan
- FUNDED_BY → Organization

### Data Quality

**Extraction Coverage (50 plans):**
- plan_title: 98%
- plan_type: 100%
- adoption_year: 90%
- planning_horizon_years: 74%
- authoring_organizations: 100%
- implementing_agencies: 96%
- total_actions: 42%
- total_budget_mentioned: 14%
- external_frameworks: 96%
- monitoring_approach: 78%

### Next Steps

1. User reviews proposals via http://127.0.0.1:8769 (plans phase)
2. Approve/reject/edit each property and relationship
3. Run `uv run packages/ontology/mining/scripts/apply_decisions.py --phase plans`
4. Validated Plan entity replaces placeholder in ontology-v0.1.json
5. Can repeat with larger corpus or different plan types as needed

## Cost Estimate

- PDF parsing: Free (Kreuzberg is open source)
- Property extraction (50 plans × Sonnet): ~$10
- Schema proposal (1 Sonnet call): ~$0.20
- Total: ~$10.20

## Files Created

```
packages/ontology/mining/
├── corpus/plans/
│   ├── plans.parquet (50 plans, ~10MB)
│   ├── property_candidates.parquet (50 records)
│   └── parse_stats.txt
├── proposals/
│   └── plan-properties-v0.json (11 props + 11 rels)
└── scripts/
    ├── pull_plan_corpus.py
    ├── phase_p_extract_properties.py
    └── phase_p_propose_schema.py
```

## Integration with V3 Pipeline

The expanded Plan entity will enable:
- Graph queries like "Find all plans addressing coastal flooding in Asia"
- Temporal analysis of plan evolution (SUPERSEDES relationships)
- Framework alignment tracking (ALIGNS_WITH → Framework)
- Stakeholder accountability mapping (AUTHORED_BY, IMPLEMENTED_BY)
- Cross-plan references and influence networks (REFERENCES)

This grounds the Plan entity in real data rather than leaving it as placeholders.
