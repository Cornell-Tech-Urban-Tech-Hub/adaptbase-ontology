# Node Types Extraction Summary

**Generated:** 2026-04-14  
**Source:** extraction-schema-v1.json (v1.1, v1.2)  
**Method:** Structural analysis of 7 dimensions + controlled vocabularies  
**Output:** ontology/types.json (16 node types)

---

## Extraction Logic

Node types were extracted by analyzing the **structure** of the extraction schema, not by mining populated data. Each dimension in the schema implies entity types and their relationships:

### Dimension → Node Type Mapping

| Schema Dimension | Implied Node Types | Rationale |
|---|---|---|
| **identity** | Solution, Actor | Root entity (Solution) + implementing actors |
| **hazards** | Hazard | Climate threats addressed by solutions |
| **urban_systems** | UrbanSystem | City infrastructure/systems that solutions operate on |
| **mechanisms** | Mechanism | Functional processes (how solutions work) |
| **implementation** | City, FinancingSource, FinancialInstrument, Supplier | Deployment context: where, who funds, how funded, who supplies |
| **outcomes** | Outcome, Indicator, ResilienceGoal | Results: effectiveness, co-benefits, failure modes, CRF goals |
| **context** | Policy, EnablingCondition, Barrier | Governance layer: policies, prerequisites, obstacles |

---

## Extracted Node Types (16 Total)

### Solutions Domain (9 Types)

1. **Solution** - Core entity. Climate adaptation intervention/project/technology.
2. **Hazard** - Climate threats addressed (C40/Arup taxonomy, 31 hazards).
3. **UrbanSystem** - City subsystems operated on (7 sectors, 50+ systems).
4. **Mechanism** - How solution works (free-text now, to be formalized in corpus mining).
5. **City** - Municipal jurisdictions where solutions are deployed.
6. **ResilienceGoal** - CRF 2024 goals (22 goals across 4 dimensions).
7. **Outcome** - Measured/observed results (effectiveness, co-benefits, failures).
8. **Indicator** - Quantified metrics (baseline, target, measured value).
9. **Supplier** - Vendors/manufacturers providing technology/components.

### Planning Domain (7 Types)

10. **Actor** - Organizations/stakeholders implementing or governing solutions.
11. **Policy** - Regulatory frameworks enabling/hindering solutions.
12. **EnablingCondition** - Prerequisites for successful deployment (5 types).
13. **Barrier** - Obstacles impeding adoption (6 types).
14. **FinancingSource** - Entities providing capital (Green Climate Fund, World Bank, etc.).
15. **FinancialInstrument** - Funding mechanisms (green bonds, climate bonds, etc.).

---

## Properties Mapped from Schema Fields

Each node type's properties map directly to extraction schema JSONB fields:

**Example: Solution node**
```json
{
  "id": "Solution",
  "properties": [
    {"id": "name", "schema_field": "identity.solution_name"},
    {"id": "category_id", "schema_field": "identity.solution_category.category_id"},
    {"id": "ipcc_action_types", "schema_field": "identity.ipcc_action_type.values"}
  ]
}
```

This 1:1 mapping ensures the ontology accurately reflects the populated data structure.

---

## Vocabulary Bindings

Node types bind to controlled vocabularies where applicable:

| Node Type | Vocabulary | Field(s) Bound |
|---|---|---|
| Solution | solution-categories | category_id, subcategory_id |
| Hazard | hazards | hazard_id, hazard_name, hazard_category |
| UrbanSystem | urban-systems | system_id, sector, subsector |
| ResilienceGoal | crf-goals | goal_id, dimension |
| Mechanism | enums | mechanism_type (seed vocabulary only) |
| Actor | enums | actor_type |
| EnablingCondition | enums | condition_type |
| Barrier | enums | barrier_type |
| FinancialInstrument | enums | instrument_type |

**Total vocabularies referenced:** 4 files (solution-categories, hazards, urban-systems, crf-goals) + enums.json for controlled value lists.

---

## Design Decisions

### 1. Solution as Core Node

**Decision:** Solution is the primary entity; all other solution-domain nodes connect to it.

**Rationale:** Matches extraction schema structure (Solution is root JSONB object). Enables star-schema queries radiating from Solution.

### 2. Mechanism as Free-Text Node (For Now)

**Decision:** Mechanism type is free-text with seed vocabulary guidance, not strict controlled vocabulary.

**Rationale:** Schema v1.2 uses free text in `mechanisms.primary_mechanism.value`. Formalization deferred to corpus mining phase (Weeks 7-8) where mechanism descriptions will be clustered into canonical types.

### 3. Outcome as Umbrella Type

**Decision:** Single Outcome node type covers effectiveness indicators, co-benefits, and failure modes.

**Rationale:** Schema groups these under `outcomes` dimension. `outcome_type` property differentiates. Avoids ontology bloat (3 separate types → 1 type with enum property).

### 4. Indicator as Child of Outcome

**Decision:** Indicator is separate node type, not property of Outcome.

**Rationale:** Indicators have rich structure (baseline, target, measured_value, unit, data_source). Separate node enables queries like "Show solutions with measured indicators > 30% improvement over baseline."

### 5. Financing: Source vs. Instrument

**Decision:** FinancingSource (who) and FinancialInstrument (how) are separate node types.

**Rationale:** Schema distinguishes `funding_sources[].source` from `financial_instruments[].instrument_type`. Ontology preserves this distinction to support queries like "Which green bonds fund coastal protection?"

### 6. Policy Bridges Planning and Solutions

**Decision:** Policy is planning-domain node but connects to solution-domain.

**Rationale:** Schema's `context.governance_relationships` links policies to solutions. Policy is the bridge: planning domain generates policies, solutions domain implements under policy constraints.

### 7. Actor in Planning Domain (Not Solutions)

**Decision:** Actor classified as planning-domain entity.

**Rationale:** Actors govern and implement solutions but are not solutions themselves. Actor relationships (IMPLEMENTS, MANAGES) bridge planning → solutions.

### 8. Many-to-Many City-Solution

**Decision:** City is separate node type, not property of Solution.

**Rationale:** Schema's `implementation.cities[]` array enables many-to-many. A solution can be deployed in multiple cities (replication tracking). Separate node enables city-centric queries: "Show all solutions deployed in Singapore."

---

## What This Extraction Does NOT Include

**Excluded from this extraction (to be added later):**

1. **Relationship types** - Deferred to next step (ontology/relationships.json).
2. **Evidence case counts** - Empty `evidence_cases: []` arrays. To be populated after validation against held-out cases.
3. **Emergent entity types** - Types discovered via corpus mining (Weeks 7-8), e.g., named technologies, standards, certifications.
4. **Formalized mechanism taxonomy** - Deferred to corpus clustering phase.

---

## Validation Against Schema

All 16 node types validated against extraction schema v1.2:

- ✅ Every node type maps to a dimension or controlled vocabulary
- ✅ Every property maps to a schema field path
- ✅ Vocabulary bindings reference actual vocabulary files in `schemas/vocabularies/`
- ✅ Enum values match schema constraints

**No invented types.** All types grounded in schema structure or vocabularies.

---

## Next Steps

1. **Extract relationships** - Analyze cross-dimension references to infer edge types (MITIGATES, OPERATES_ON, etc.)
2. **Draft v0.1 ontology** - Combine types.json + relationships.json into viewer-compatible `draft-v0.json`
3. **Validate against data** - Query Supabase to confirm all types have instances in populated extraction_schema fields
4. **Align with external vocabularies** - Map to IPCC AR6, UNDRR, CRF 2024 canonical terms
5. **Stress test** - Validate against held-out cases not used in schema analysis

---

## Files Generated

- `ontology/types.json` - Machine-readable node types with properties and vocabulary bindings
- `ontology/TYPES-EXTRACTION-SUMMARY.md` - This document (human-readable explanation)

**Status:** Phase 1 (Type Extraction) complete ✅  
**Next:** Phase 2 (Relationship Extraction)
