# Relationship Types Extraction Summary

**Generated:** 2026-04-14  
**Source:** extraction-schema-v1.json (v1.1, v1.2) + student ontology  
**Method:** Cross-dimension reference analysis + governance vocabulary import  
**Output:** ontology/relationships.json (17 relationship types)

---

## Extraction Logic

Relationships inferred by analyzing **how dimensions reference each other** in the extraction schema:

- `hazards` dimension → Solution addresses Hazards → **MITIGATES** relationship
- `urban_systems` dimension → Solution operates on UrbanSystems → **OPERATES_ON** relationship
- `implementation.cities[]` → Solution deployed in Cities → **IMPLEMENTED_IN** relationship
- `context.governance_relationships` → Policy-Solution links → **MANDATES, FACILITATES, HINDERS, IMPLEMENTS**

---

## Extracted Relationships (17 Total)

### Core Solution Relationships (8)

1. **MITIGATES** - Solution → Hazard (addresses climate threat)
2. **OPERATES_ON** - Solution → UrbanSystem (deployed on infrastructure)
3. **USES_MECHANISM** - Solution → Mechanism (how it works)
4. **IMPLEMENTED_IN** - Solution → City (where deployed)
5. **IMPLEMENTED_BY** - Solution → Actor (who implements)
6. **CONTRIBUTES_TO** - Solution → ResilienceGoal (CRF goals achieved)
7. **PRODUCES** - Solution → Outcome (effectiveness/co-benefits/failures)
8. **MEASURED_BY** - Outcome → Indicator (quantified metrics)

### Governance Relationships (4)

9. **MANDATES** - Policy → Solution (legal requirement)
10. **FACILITATES** - Policy → Solution (enables without mandating)
11. **HINDERS** - Policy → Solution (creates obstacles)
12. **IMPLEMENTS** - Solution → Policy (operationalizes policy)

### Prerequisite Relationships (2)

13. **REQUIRES** - Solution → EnablingCondition (prerequisites)
14. **FACES** - Solution → Barrier (obstacles encountered)

### Financing Relationships (3)

15. **FUNDED_BY** - Solution → FinancingSource (capital provider)
16. **USES_INSTRUMENT** - Solution → FinancialInstrument (financing mechanism)
17. **SUPPLIED_BY** - Solution → Supplier (technology/component provider)

---

## Cardinality Patterns

**Many-to-Many (most relationships):**
- Solution ←→ Hazard (one solution can address multiple hazards)
- Solution ←→ City (replication across jurisdictions)
- Solution ←→ Actor (multi-stakeholder implementations)

**One-to-Many:**
- Solution → Outcome (one solution produces multiple outcomes)
- Outcome → Indicator (one outcome measured by multiple indicators)

---

## Properties on Relationships

Key properties extracted from schema relationship objects:

| Relationship | Properties | Purpose |
|---|---|---|
| MITIGATES | is_primary, claim_ids | Distinguish primary vs. co-addressed hazards |
| IMPLEMENTED_IN | deployment_context, claim_ids | Capture local adaptations |
| IMPLEMENTED_BY | role, is_lead, claim_ids | Distinguish lead vs. supporting actors |
| FUNDED_BY | amount_usd, claim_ids | Enable cost aggregation queries |
| USES_INSTRUMENT | amount_usd, description, claim_ids | Detail financing mechanisms |
| PRODUCES | outcome_type, evidence_level, claim_ids | Differentiate effectiveness/co-benefits/failures |

All relationships carry **claim_ids** for provenance tracking.

---

## Governance Vocabulary from Student Ontology

Imported 4 governance relationship types:

- **MANDATES** - Strongest policy support (legal requirement)
- **FACILITATES** - Policy enables without mandating
- **HINDERS** - Policy creates obstacles
- **IMPLEMENTS** - Solution operationalizes policy

Source: `context.governance_relationships.policies_enabling[]` and `policies_hindering[]` with `relationship_type` enum.

---

## Design Decisions

### 1. Financing: Source vs. Instrument

**Decision:** Separate relationships for FUNDED_BY (who provides money) and USES_INSTRUMENT (how money is structured).

**Rationale:** Schema distinguishes `funding_sources[].source` from `financial_instruments[].instrument_type`. Enables queries like "Which green bonds fund coastal protection?"

### 2. Outcome Properties on Relationship

**Decision:** outcome_type and evidence_level are properties of PRODUCES relationship, not Outcome node.

**Rationale:** Same outcome can have different evidence levels depending on context. Relationship property preserves this nuance.

### 3. Mechanism Technical Components

**Decision:** Technical components stored as property on USES_MECHANISM relationship, not as separate nodes.

**Rationale:** Schema has `mechanisms.technical_components[]` as array property. Components are descriptive details, not first-class entities requiring separate queries.

### 4. Supplier-Component Link

**Decision:** component_refs property on SUPPLIED_BY relationship links suppliers to specific components.

**Rationale:** Schema's `suppliers[].component_refs` references `technical_components[].component` values. Preserves this linkage without creating Component nodes.

---

## What This Enables

**Query patterns now possible:**

1. **Hazard-centric**: "Show all solutions that mitigate coastal flooding"
   - `MATCH (s:Solution)-[:MITIGATES]->(h:Hazard {hazard_id: 'coastal_flood'})`

2. **Urban system interdependency**: "Which solutions protect energy substations during floods?"
   - `MATCH (s:Solution)-[:MITIGATES]->(:Hazard {category: 'flood'})-[:OPERATES_ON]->(:UrbanSystem {system_id: 'substations'})`

3. **Replication tracking**: "Where has this solution been implemented?"
   - `MATCH (s:Solution {id: '...'})-[:IMPLEMENTED_IN]->(c:City)`

4. **Financing flows**: "Total funding from Green Climate Fund for nature-based solutions"
   - `MATCH (s:Solution {category: 'nature'})-[r:FUNDED_BY]->(:FinancingSource {name: 'Green Climate Fund'}) RETURN sum(r.amount_usd)`

5. **Policy-solution chains**: "Solutions mandated by climate adaptation plans"
   - `MATCH (p:Policy)-[:MANDATES]->(s:Solution)`

6. **Evidence-based filtering**: "Rigorously evaluated solutions for heat mitigation"
   - `MATCH (s:Solution)-[:MITIGATES]->(:Hazard {category: 'extreme_temperature_hot'})-[r:PRODUCES {evidence_level: 'rigorously_evaluated'}]->(o:Outcome)`

---

## Validation Against Schema

All 17 relationship types validated:

- ✅ Every relationship maps to schema field paths
- ✅ Properties map to relationship object fields in schema
- ✅ Cardinality matches schema structure (array fields = many-to-many)
- ✅ Governance relationships match student ontology vocabulary

**No invented relationships.** All grounded in schema structure or imported vocabularies.

---

## Next Steps

1. **Create alignment files** - Map to IPCC AR6, UNDRR, CRF 2024 canonical terms
2. **Validate against data** - Query Supabase to confirm relationships exist in populated extraction schemas
3. **Stress test** - Validate against held-out cases
4. **Document decisions** - Log design choices in ontology/decisions-log.md

---

## Files Generated

- `ontology/relationships.json` - Machine-readable relationship types
- `ontology/draft-v0.json` - Viewer-compatible ontology (16 types + 17 relationships + 5 vocabularies)
- `ontology/RELATIONSHIPS-EXTRACTION-SUMMARY.md` - This document

**Status:** Phase 2 (Relationship Extraction) complete ✅  
**Next:** Phase 3 (Vocabulary Alignment)
