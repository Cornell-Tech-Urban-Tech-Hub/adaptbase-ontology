# Structural QA Review — ontology-v0.1.3

Date: 2026-04-27  
Scope: `ontology/ontology-v0.1.3.json`, `ontology/decisions-log.md`  
Reviewer focus: structural and formal ontology quality for KG/extraction readiness.

## Executive summary

- Current artifact contains **18 types**, **36 relationships**, and **6 vocabularies**.
- This does **not** match stated target of 17/35/7; reconcile before external review.
- Naming conventions are largely consistent and machine-lintable.
- Main structural risks are inverse asymmetry, mixed vocabulary binding strategy, and hub concentration around `Solution`.

## 1) Naming consistency

### Checks
- Type IDs should be PascalCase.
- Relationship IDs should be SCREAMING_SNAKE.
- Property IDs should be snake_case.

### Findings
- No casing violations detected in IDs.
- Minor consistency drift in labels/definitions:
  - Relationship labels are mostly verb phrases but not fully normalized.
  - Definitions vary in grammatical template.

### Fixes
1. Add CI lint rules:
   - `type.id`: `^[A-Z][A-Za-z0-9]*$`
   - `relationship.id`: `^[A-Z][A-Z0-9_]*$`
   - `property.id`: `^[a-z][a-z0-9_]*$`
2. Normalize definitions:
   - Type: “A/An [class] that …”
   - Relationship: “Indicates that [source] [verb phrase] [target] …”

## 2) Relationship analysis

### Findings
- Relationships include explicit cardinality strings (good), but these are not operationally constraining.
- Inverse coverage is incomplete (many directional-only edges).
- Several domain traversals require reverse logic at query time.

### Implied cardinality profile
- Most domain links are modeled as many-to-many and likely correct for city-scale corpora.
- A subset likely has practical max constraints (e.g., one primary hazard, one owning plan role in context), but schema cannot encode this today.

### Fixes
1. Add machine-checkable constraints per relationship:
   - `source_min`, `source_max`, `target_min`, `target_max`.
2. Add inverse strategy:
   - Either explicit inverse relationships (e.g., `MITIGATED_BY`) or
   - metadata (`inverse_of`) with inference policy in implementation docs.
3. Add release-time relationship completeness check for expected inverse pairs.

## 3) Property type consistency

### Findings
- Mixed patterns observed:
  - `enum`, `array<enum>`, vocab-bound strings, open strings.
- `required` appears broadly used but not guaranteed universal.
- Some conceptually controlled fields are not vocabulary-bound.

### Fixes
1. Establish one policy:
   - Externally managed taxonomy => `string` + `vocabulary`.
   - Small local closed list => `enum` + `values`.
   - Multi-valued controlled list => `array<string>` + `vocabulary`.
2. Require explicit `required: true|false` on every property.
3. Add optional `binding_policy` and `binding_rationale` fields.

## 4) Redundancy and overlap

### Findings
- Potential overlap in governance/functional semantics around `Mechanism` (already noted in decision log).
- `Barrier` and `EnablingCondition` are polarity complements that may benefit from shared abstraction.
- Repeated descriptive properties across types indicate reusable patterns.

### Fixes
1. Add abstract pattern `ContextFactor` for `Barrier` + `EnablingCondition`.
2. Split `Mechanism` into `FunctionalMechanism` and `GovernanceMechanism`, or add required discriminator.
3. Define reusable property bundles (`Identifiable`, `Describable`, `TemporalScoped`).

## 5) Graph topology

### Findings
- `Solution` is intentionally central and likely high-degree.
- Hubness is acceptable for extraction-centric workflows but can limit direct non-solution analysis.
- Dead-end/underconnected type risk should be tracked release to release.

### Fixes
1. Add selected non-`Solution` direct links where domain-valid:
   - `Hazard` ↔ `Vulnerability`
   - `Plan` ↔ `Outcome`
   - `Stakeholder` ↔ `FinancialInstrument`
   - `Location` ↔ `ExposureUnit`
2. Add topology QA gates:
   - single connected component
   - max-degree threshold warning
   - dead-end count warning
   - diameter trend monitoring

## 6) Vocabulary binding gaps

### Findings
- Ontology currently exposes 6 vocabularies, not 7 as expected.
- Binding approach is mixed and not always justified in-schema.

### Fixes
1. Reconcile vocabulary inventory before publication.
2. Convert classification/status-like open strings to vocabulary-bound fields where stable taxonomies exist.
3. Add explicit rationale when leaving a field open.

## 7) Query supportability

Five likely expert queries and support assessment:

1. Heat solutions reducing high vulnerabilities with measured outcomes.
2. Stakeholder-implemented solutions financed via grants in coastal locations.
3. Barriers associated with unsuccessful outcomes.
4. Mechanisms used by established flood solutions.
5. Exposure units served under high-intensity hazards.

Assessment: mostly supportable, but inverse asymmetry and inconsistent controlled terms create avoidable query workarounds.

## 8) Evolution readiness

### Findings
- Good documentation of decisions and iterative modeling.
- Risks from hardcoded enums and missing per-field lifecycle metadata.

### Fixes
1. Add lifecycle metadata to types/relationships/properties:
   - `introduced_in`, `deprecated_in`, `status`, `replacement`.
2. Prefer vocabulary-driven extensibility over static enums for evolving classes.
3. Add compositional abstraction support (`extends`, reusable property groups).

## Publication blockers / priority actions

1. Reconcile stated counts vs artifact counts (17/35/7 vs 18/36/6).
2. Implement and document inverse relationship policy.
3. Add automated structural lint/QA in CI.
4. Publish adjacency matrix + degree summary in release notes.

---

## Appendix A — Suggested Cypher query set

```cypher
MATCH (s:Solution)-[:MITIGATES]->(h:Hazard),
      (s)-[:IMPLEMENTED_IN]->(l:Location),
      (s)-[:REDUCES]->(v:Vulnerability),
      (s)-[:PRODUCES]->(o:Outcome)
WHERE h.name = "Extreme Heat" AND v.severity IN ["high","very_high"]
RETURN s, l, o
```

```cypher
MATCH (st:Stakeholder)-[:IMPLEMENTS]->(s:Solution)-[:IMPLEMENTED_IN]->(l:Location),
      (s)-[:FINANCED_BY]->(fi:FinancialInstrument)
WHERE fi.instrument_type = "grant" AND l.coastal = true
RETURN st, s, l
```

```cypher
MATCH (s:Solution)-[:FACES_BARRIER]->(b:Barrier),
      (s)-[:PRODUCES]->(o:Outcome)
WHERE o.result = "not_achieved"
RETURN s, b, o
```

```cypher
MATCH (s:Solution)-[:MITIGATES]->(h:Hazard),
      (s)-[:USES]->(m:Mechanism)
WHERE s.maturity_level = "established" AND h.name = "Flooding"
RETURN DISTINCT m
```

```cypher
MATCH (h:Hazard)-[:EXPOSES]->(e:ExposureUnit),
      (u:UrbanSystem)-[:SERVES]->(e),
      (u)-[:LOCATED_IN]->(l:Location)
WHERE h.intensity_class = "high"
RETURN e, u, l
```
