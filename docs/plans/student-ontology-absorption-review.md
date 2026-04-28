# Student Ontology Absorption Review

**Date:** 2026-04-14  
**Context:** Solutions originate from climate adaptation plans; planners are end users  
**Source:** `resources/ruowen-climate-adaptation.py`

## Strategic Insight

Our ontology was initially framed as "solutions-focused" vs "planning-focused", but this is a false dichotomy. **Solutions exist within the planning context.** Adaptation planners are our end users, and they need to:

- Contextualize solutions within vulnerability reduction frameworks
- Understand spatial targeting within cities
- Track actor coordination and governance
- Model infrastructure improvements
- Navigate implementation constraints
- Align with planning/policy cycles

## What We've Absorbed (Phase 1)

### Governance Layer
- ✅ **Policy** node (with properties)
- ✅ **Actor** node (implementing actors)
- ✅ **MANDATES** (Policy → Solution)
- ✅ **FACILITATES** (Policy → Solution)
- ✅ **HINDERS** (Policy → Solution)
- ✅ **IMPLEMENTS** (Solution → Policy, reversed)

### Evaluation Layer
- ✅ **Outcome** node
- ✅ **Indicator** node
- ✅ **MEASURED_BY** (Outcome → Indicator)

## Critical Gaps for Planning Context

### 1. Vulnerability Modeling
**Her model:**
```python
"Vulnerability": {
    "properties": [
        "vuln_type",
        "exposure_score",
        "sensitivity_score",
        "adaptive_capacity_score",
        "affected_group"
    ]
}
```

**Relationships:**
- `WORSENS` (Hazard → Vulnerability)
- `EXPERIENCES_VULN` (ExposureUnit → Vulnerability)
- `REDUCES` (AdaptationAction → Vulnerability) ← **KEY PLANNING OUTCOME**

**Why we need this:** Planners think in terms of reducing vulnerability, not just mitigating hazards. IPCC AR6 and UNDRR frameworks center on vulnerability reduction.

**Recommendation:** Add Vulnerability node and REDUCES relationship. Map to IPCC vulnerability components.

---

### 2. Spatial Targeting
**Her model:**
```python
"UrbanZone": {
    "description": "Functional spatial units within a city",
    "properties": [
        "zone_type",
        "area_km2",
        "population_density",
        "land_use_type"
    ]
}
```

**Relationships:**
- `HAS_ZONE` (City → UrbanZone)
- `TARGETS_ZONE` (AdaptationAction → UrbanZone) ← **KEY PLANNING DETAIL**
- `AFFECTS_ZONE` (ClimateHazard → UrbanZone)

**Why we need this:** Plans specify WHERE within a city solutions are deployed (neighborhoods, districts, zones). Our current City node is too coarse.

**Recommendation:** Add UrbanZone node OR extend our UrbanSystem to include spatial zones.

---

### 3. Infrastructure Improvement
**Her model:**
```python
"Infrastructure": {
    "description": "Socio-technical infrastructure (green/grey/blue)",
    "properties": [
        "infra_type",
        "infra_color",  # green/grey/blue classification
        "capacity",
        "condition",
        "service_coverage"
    ]
}
```

**Relationships:**
- `IMPROVES` (AdaptationAction → Infrastructure) ← **KEY PLANNING OUTCOME**
- `SERVES` (Infrastructure → ExposureUnit)

**Why we need this:** Our UrbanSystem is about what systems solutions operate ON. Infrastructure is about what gets IMPROVED. These are different concepts.

**Recommendation:** Add Infrastructure node distinct from UrbanSystem, add IMPROVES relationship.

---

### 4. Actor Coordination
**Relationships we're missing:**
- `COORDINATES_WITH` (Actor → Actor)
- `REPORTS_TO` (Actor → Actor)
- `MANAGES` (Actor → Mechanism)
- `PARTICIPATES_IN` (Actor → AdaptationAction)
- `MONITORS` (Actor → Indicator)

**Why we need this:** Multi-stakeholder governance is central to adaptation planning. Plans specify who coordinates with whom, reporting structures, monitoring responsibilities.

**Recommendation:** Add actor-to-actor coordination relationships.

---

### 5. Implementation Constraints
**Her model:**
```python
"Constraint": {
    "properties": [
        "constraint_type",
        "severity_score",
        "affected_stakeholder",
        "is_structural"
    ]
}
```

**Relationships:**
- `FACES` (Actor → Constraint)
- `HINDERED_BY` (AdaptationAction → Constraint)

**We have:** Barrier node and `FACES` (Solution → Barrier), but less detailed.

**Recommendation:** Enhance Barrier node with constraint properties, or adopt Constraint terminology.

---

### 6. Temporal Modeling
**Her model:**
```python
"TimePoint": {
    "properties": [
        "year",
        "period",
        "policy_cycle"
    ]
}
```

**Relationships:**
- `STARTED_AT` (AdaptationAction → TimePoint)
- `ISSUED_AT` (Policy → TimePoint)
- `RECORDED_AT` (Indicator → TimePoint)

**Why we need this:** Planning cycles, policy windows, timeline tracking. Currently we have year_of_deployment property but no temporal node.

**Recommendation:** Add TimePoint node for temporal relationships, especially policy_cycle tracking.

---

### 7. Exposure Units
**Her model:**
```python
"ExposureUnit": {
    "description": "Population or asset exposed to hazards",
    "properties": [
        "population_count",
        "asset_value",
        "vulnerable_ratio",
        "social_capital_index"
    ]
}
```

**Relationships:**
- `EXPOSES` (ClimateHazard → ExposureUnit)
- `EXPERIENCES_VULN` (ExposureUnit → Vulnerability)
- `SERVES` (Infrastructure → ExposureUnit)

**Why we need this:** Plans quantify exposed populations and assets. This is UNDRR/Sendai Framework language.

**Recommendation:** Consider for Phase 2 absorption. May overlap with our demographic/socioeconomic modeling.

---

## What We Don't Need (Justifications)

### ClimateHazard properties
She has: `frequency`, `severity`, `trend`, `return_period`, `spatial_extent`

**Our approach:** We reference C40/Arup hazard taxonomy but don't model hazard characteristics. This is climate science modeling, not solution documentation.

**Decision:** Keep our simpler Hazard node. Hazard characteristics live in external climate models.

---

## Absorption Plan

### Immediate (Phase 2a - before May 15)
1. **Add Vulnerability node** with REDUCES relationship
2. **Add IMPROVES relationship** (Solution → UrbanSystem for now, revisit Infrastructure)
3. **Add TARGETS_ZONE or spatial properties** to IMPLEMENTED_IN relationship
4. **Enhance Actor relationships** - add COORDINATES_WITH, REPORTS_TO

### Soon (Phase 2b - before May 15 if time)
5. **Add TimePoint node** with temporal relationships
6. **Review Constraint vs Barrier** - enhance or rename

### Later (Post-deadline)
7. **Infrastructure as separate node** - distinguish from UrbanSystem
8. **ExposureUnit consideration** - align with UNDRR frameworks

---

## Integration Notes

**Terminology reconciliation:**
- Her "AdaptationAction" = Our "Solution"
- Her "Mechanism" (governance) ≠ Our "Mechanism" (physical/technical)
- Her "Infrastructure" ⊂ Our "UrbanSystem" (currently), should split

**Domain alignment:**
- Her ontology = planning-focused, vulnerability-reduction framing
- Our ontology = solutions-focused, but embedded in planning context
- **Synthesis:** Solutions AS planning interventions, not just technical objects

---

## Next Steps

1. Review this document with user
2. Update types.json and relationships.json with Phase 2a additions
3. Update TYPES-EXTRACTION-SUMMARY.md and RELATIONSHIPS-EXTRACTION-SUMMARY.md
4. Regenerate draft-v0.json
5. Update viewer to visualize planning-domain relationships
6. Document absorption decisions in ontology/decisions-log.md

---

## References

- Student ontology: `resources/ruowen-climate-adaptation.py`
- IPCC AR6 WGII Chapter 17 (Decision-Making Options for Managing Risk)
- UNDRR Sendai Framework (vulnerability, exposure, capacity)
- Our extraction schema: `schemas/extraction-schema-v1.json`
