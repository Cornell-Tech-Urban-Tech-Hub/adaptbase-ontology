# Document Analysis: [TITLE]

**Date:** [YYYY-MM-DD]  
**Analyst:** [Name]

---

## Document Metadata

- **Title:** [Full title]
- **Type:** [document_type from Supabase]
- **Source:** [source_organization]
- **City/Country:** [city, country]
- **URL:** [pdf_url]
- **Supabase ID:** [id]

---

## Node Type Coverage

For each node type, indicate: count found, examples (1-2), notes

### Solutions Domain

| Node Type | Count | Examples | Notes |
|-----------|-------|----------|-------|
| Solution | | | |
| Hazard | | | |
| UrbanSystem | | | |
| Mechanism | | | |
| Infrastructure | | | **NEW - Phase 2c** |
| City | | | |
| ResilienceGoal | | | |
| Outcome | | | |
| Indicator | | | |
| Supplier | | | |

### Planning Domain

| Node Type | Count | Examples | Notes |
|-----------|-------|----------|-------|
| Actor | | | |
| Policy | | | |
| EnablingCondition | | | |
| Barrier | | | |
| FinancingSource | | | |
| FinancialInstrument | | | |
| Vulnerability | | | **NEW - Phase 2a** |
| TimePoint | | | **NEW - Phase 2b** |
| ExposureUnit | | | **NEW - Phase 2c** |

---

## Relationship Coverage

### Core Solution Relationships

- [ ] **MITIGATES** (Solution → Hazard) - Count: ___ | Example: ___
- [ ] **OPERATES_ON** (Solution → UrbanSystem) - Count: ___ | Example: ___
- [ ] **USES_MECHANISM** (Solution → Mechanism) - Count: ___ | Example: ___
- [ ] **IMPLEMENTED_IN** (Solution → City) - Count: ___ | Spatial properties? ___
- [ ] **IMPLEMENTED_BY** (Solution → Actor) - Count: ___ | Example: ___
- [ ] **CONTRIBUTES_TO** (Solution → ResilienceGoal) - Count: ___ | Example: ___
- [ ] **PRODUCES** (Solution → Outcome) - Count: ___ | Example: ___
- [ ] **MEASURED_BY** (Outcome → Indicator) - Count: ___ | Example: ___

### Planning Relationships

- [ ] **REQUIRES** (Solution → EnablingCondition) - Count: ___ | Example: ___
- [ ] **FACES** (Solution → Barrier) - Count: ___ | Example: ___
- [ ] **MANDATES** (Policy → Solution) - Count: ___ | Example: ___
- [ ] **FACILITATES** (Policy → Solution) - Count: ___ | Example: ___
- [ ] **HINDERS** (Policy → Solution) - Count: ___ | Example: ___
- [ ] **IMPLEMENTS** (Solution → Policy) - Count: ___ | Example: ___
- [ ] **FUNDED_BY** (Solution → FinancingSource) - Count: ___ | Example: ___
- [ ] **USES_INSTRUMENT** (Solution → FinancialInstrument) - Count: ___ | Example: ___
- [ ] **SUPPLIED_BY** (Solution → Supplier) - Count: ___ | Example: ___

### Phase 2 Additions (FOCUS HERE!)

- [ ] **REDUCES** (Solution → Vulnerability) - Count: ___ | Example: ___ | **Explicitly stated?**
- [ ] **IMPROVES** (Solution → Infrastructure) - Count: ___ | Example: ___ | **Clear vs. OPERATES_ON?**
- [ ] **COORDINATES_WITH** (Actor → Actor) - Count: ___ | Example: ___
- [ ] **REPORTS_TO** (Actor → Actor) - Count: ___ | Example: ___
- [ ] **PARTICIPATES_IN** (Actor → Solution) - Count: ___ | Example: ___
- [ ] **MONITORS** (Actor → Indicator) - Count: ___ | Example: ___
- [ ] **MANAGES** (Actor → Mechanism) - Count: ___ | Example: ___
- [ ] **STARTED_AT** (Solution → TimePoint) - Count: ___ | Example: ___
- [ ] **ISSUED_AT** (Policy → TimePoint) - Count: ___ | Example: ___
- [ ] **RECORDED_AT** (Indicator → TimePoint) - Count: ___ | Example: ___
- [ ] **EXPOSES** (Hazard → ExposureUnit) - Count: ___ | Example: ___
- [ ] **SERVES** (Infrastructure → ExposureUnit) - Count: ___ | Example: ___
- [ ] **EXPERIENCES_VULN** (ExposureUnit → Vulnerability) - Count: ___ | Example: ___

---

## Coverage Summary

**Percentage of document content expressible in ontology:** ~___% (rough estimate)

**Most common nodes/relationships in this doc:**
1. [Node/Relationship]: [count] instances
2. [Node/Relationship]: [count] instances
3. [Node/Relationship]: [count] instances

**Absent but expected:**
- [Node/Relationship]: Why expected? Why absent?

---

## Gaps Identified

### Critical Gaps (can't express at all)
1. **Concept:** [What concept from doc]
   - **Why critical:** [Why we need to express this]
   - **Current limitation:** [Why ontology can't handle it]
   - **Example:** [Specific text from doc]

### Awkward Fits (can express but feels forced)
1. **Concept:** [What concept]
   - **How we'd model it:** [Which nodes/relationships]
   - **Why awkward:** [What feels forced]
   - **Better approach:** [What would work better]

### Over-designed (added but never appears)
1. **Node/Relationship:** [Which one]
   - **Why we thought we needed it:** [Original rationale]
   - **Why it's not appearing:** [Document doesn't have it, or we can't identify it]

---

## Property Issues

### Missing Properties
1. **Node:** [Which node type]
   - **Property needed:** [What we need to capture]
   - **Example value from doc:** [Specific value]
   - **Why missing:** [Why didn't we include it]

### Type Mismatches
1. **Property:** [Which property]
   - **Current type:** [e.g., string, number, enum]
   - **Actual data:** [What we found in doc]
   - **Issue:** [Why current type doesn't work]

### Controlled Vocabulary Issues
1. **Field:** [Which field]
   - **Current vocab:** [Allowed values]
   - **Needed value:** [Value from doc that doesn't fit]
   - **Recommendation:** [Add to vocab / make free-text / other]

---

## Positive Findings

### Relationships That Worked Well
1. **Relationship:** [Which one]
   - **Example:** [Specific instance from doc]
   - **Why it worked:** [Clear semantics, good fit, etc.]

### Properties That Captured Exactly What We Needed
1. **Property:** [Which one]
   - **Example value:** [From doc]
   - **Why successful:** [Good granularity, right type, etc.]

### Phase 2 Additions That Validated
1. **Addition:** [Node/relationship from Phase 2]
   - **Example:** [Instance from doc]
   - **Validation:** [Why this confirms we needed it]

---

## Observations

### Infrastructure vs. UrbanSystem Distinction
**Did the split work?**
- OPERATES_ON examples: [List 1-2]
- IMPROVES examples: [List 1-2]
- **Clear separation?** Yes/No - [Why/why not]

### Temporal Relationships
**Were planning cycles expressible?**
- TimePoint instances: [Examples]
- Temporal relationships: [Which ones appeared]
- **Adequate?** Yes/No - [Missing anything?]

### Actor Coordination
**Was multi-stakeholder governance captured?**
- Actor-to-actor relationships: [Which ones, how many]
- **Pattern observed:** [Describe coordination structure]

### UNDRR Risk Chain
**Hazard → ExposureUnit → Vulnerability pathway:**
- Complete chain found? Yes/No
- Which links present? [EXPOSES, EXPERIENCES_VULN, etc.]
- **Assessment:** [Does risk chain model work for this doc?]

---

## Recommendations for This Document Type

**For [document_type] documents specifically:**
1. [Recommendation based on patterns in this type]
2. [Recommendation]
3. [Recommendation]

---

## Quick Wins

**Changes we could make immediately to better support this doc:**
1. [Small fix - property, vocab value, etc.]
2. [Small fix]
3. [Small fix]

---

## Overall Assessment

**Strengths:** [What worked well]

**Weaknesses:** [What struggled]

**Confidence in ontology for this doc type:** Low / Medium / High

**Next steps for this document type:** [What to investigate or change]
