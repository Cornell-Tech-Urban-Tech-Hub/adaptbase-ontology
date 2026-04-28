# Competency Questions — KG Scope Definition

*Draft v0.1 — 2026-04-23*

## Purpose

Competency questions (CQs) define what the Resilience Scanner knowledge graph must be able to answer. They serve three roles:

1. **Scope guardrail** — anything outside these question shapes is out-of-scope for v1
2. **Ontology validation** — each CQ should be expressible as a Cypher / SPARQL traversal over the existing types and relationships
3. **GraphRAG test harness** — these become the seed query set for the NL→Cypher→synthesis pipeline

## Scope assumptions

- **Two linked domains**: adaptation-solutions (the interventions) and adaptation-planning (the governance, plans, and documents that surround them). Bridged by the upper-ontology `ResilienceGoal` and by Plan↔Solution relationships.
- **Two main document classes**: (a) ~150 city adaptation plans; (b) implementation-stage reports, blog posts, and news on individual solutions.
- **Initial solution focus**: technology-enabled solutions (sensors, distributed energy, water tech, cooling tech, monitoring/early-warning, digital governance), but ontology must accommodate ecosystem-based, social, and institutional types.
- **Provenance is non-negotiable** — every fact in an answer must be traceable to a `claim` and through it to a source chunk.

## User personas

| Persona | Primary use case | What they need from the graph |
|---|---|---|
| **Planner** (city / regional adaptation officer) | Discovery during plan development | Peer-city precedent, mechanism options per hazard, enabling conditions, replication context |
| **Analyst / evaluator** (researcher, funder M&E, NGO) | Assessment of benefits, outcomes, equity | Evidence quality, indicator coverage, gap analysis, distributional impacts |
| **Investor** (climate fund, private capital, infra developer) | Project benchmarking, due diligence | Capital structure precedent, supplier landscape, barrier patterns, comparable performance |

---

## Competency questions

Each CQ is annotated with the ontology elements it exercises, in the form `Source -[REL]-> Target`. CQs marked **(planning-extraction-dependent)** require the Plan node and its relationships, which are scheduled but not yet populated.

### A. Planner — Solution discovery & peer learning

**CQ-1.** *What solutions have been deployed in cities comparable to ours (similar climate, size, governance type) that address [hazard X]?*
- `Solution -[MITIGATES]-> Hazard`, `Solution -[IMPLEMENTED_IN]-> City`, City attributes for comparability filter

**CQ-2.** *For [hazard X] in [urban system Y], which mechanisms are used, and which have produced measured (vs. anecdotal) outcomes?*
- `Solution -[MITIGATES]-> Hazard`, `Solution -[OPERATES_ON]-> UrbanSystem`, `Solution -[USES_MECHANISM]-> Mechanism`, `Solution -[PRODUCES]-> Outcome` filtered by `evidence_level`

**CQ-3.** *Which solutions have been replicated across the most cities, and what deployment-context variations are documented?*
- `Solution -[IMPLEMENTED_IN]-> City` (count), `IMPLEMENTED_IN.deployment_context` aggregation

**CQ-4.** *What enabling conditions are most frequently cited for [solution category], and which condition types (regulatory / financial / technical / social / institutional) recur?*
- `Solution -[REQUIRES]-> EnablingCondition` grouped by `condition_type`

**CQ-5.** *For an exposure profile of [low-income coastal residents], which solutions have evidence of reducing vulnerability for that group?*
- `Hazard -[EXPOSES]-> ExposureUnit -[EXPERIENCES_VULN]-> Vulnerability <-[REDUCES]- Solution`, filtered by `ExposureUnit.affected_group` / `Vulnerability.affected_group`

**CQ-6.** *Which suppliers / vendors have provided technology for [solution category] across the most cities, and which categories do they cover?*
- `Solution -[SUPPLIED_BY]-> Supplier`, `Solution -[IMPLEMENTED_IN]-> City`, aggregated by `Supplier.supplier_name` and `Solution.category_id`

**CQ-7.** *For a candidate solution we're considering, what barriers should we expect, and which are flagged as structural vs. addressable?*
- `Solution -[FACES]-> Barrier` filtered by `Barrier.is_structural`, `Barrier.severity_score`, `Barrier.affected_stakeholder`

### B. Planner / Analyst — Plan-to-action gap analysis  *(planning-extraction-dependent)*

**CQ-8.** *Which CRF resilience goals are set in [city]'s adaptation plan but lack any prescribed solution?*
- `Plan -[SETS_GOAL]-> ResilienceGoal` MINUS `Plan -[PRESCRIBES]-> Solution -[CONTRIBUTES_TO]-> ResilienceGoal`

**CQ-9.** *Across our corpus of plans, which resilience goals are most and least frequently targeted?*
- `Plan -[SETS_GOAL]-> ResilienceGoal` aggregated by `ResilienceGoal.goal_id`

**CQ-10.** *For [city], how do the hazards prioritized in the adaptation plan compare to those addressed by deployed solutions in that city?*
- `Plan -[ISSUED_BY]-> Actor` (city), `Plan -[PRESCRIBES]-> Solution -[MITIGATES]-> Hazard` vs. `Solution -[IMPLEMENTED_IN]-> City -[MITIGATES via deployed solutions]-> Hazard`

**CQ-11.** *Which solutions prescribed by plans have a documented funding source and lead implementing actor (i.e., are actually shovel-ready)?*
- `Plan -[PRESCRIBES]-> Solution`, with both `Solution -[FUNDED_BY]-> FinancingSource` AND `Solution -[IMPLEMENTED_BY]-> Actor` (`is_lead=true`)

**CQ-12.** *Which policies established by plans have actually been implemented by deployed solutions?*
- `Plan -[ESTABLISHES]-> Policy <-[IMPLEMENTS]- Solution`

**CQ-13.** *Which actors are most frequently named as plan issuers, and what types of solutions do their plans prescribe?*
- `Plan -[ISSUED_BY]-> Actor`, `Plan -[PRESCRIBES]-> Solution`, grouped by `Actor.actor_type` and `Solution.category_id`

### C. Analyst / evaluator — Outcomes & evidence

**CQ-14.** *For [solution type], what indicators are most commonly used to measure effectiveness, and what baseline-to-measured ranges are reported?*
- `Solution -[PRODUCES]-> Outcome -[MEASURED_BY]-> Indicator`, aggregated by `Indicator.indicator_name`

**CQ-15.** *Which solutions have rigorously evaluated outcomes (vs. anecdotal), and how does evidence quality distribute by hazard category?*
- `Solution -[PRODUCES { evidence_level }]-> Outcome`, `Solution -[MITIGATES]-> Hazard`

**CQ-16.** *What documented failure modes recur for [solution type], and under what enabling-condition gaps did they occur?*
- `Solution -[PRODUCES { outcome_type='failure_mode' }]-> Outcome`, joined to `Solution -[REQUIRES]-> EnablingCondition`

**CQ-17.** *Which solutions deliver co-benefits beyond their primary hazard target, and what categories of co-benefits recur?*
- `Solution -[PRODUCES { outcome_type='co_benefit' }]-> Outcome`

**CQ-18.** *For [resilience goal], which deployed solutions have outcomes demonstrating measured progress (vs. only claimed contribution)?*
- `Solution -[CONTRIBUTES_TO]-> ResilienceGoal` ∩ `Solution -[PRODUCES]-> Outcome -[DEMONSTRATES_PROGRESS_ON]-> ResilienceGoal`

**CQ-19.** *How does evidence quality vary across IPCC AR6 action types (structural / social / institutional / ecosystem-based)?*
- `Solution.ipcc_action_types` × `Solution -[PRODUCES]-> Outcome.evidence_level`

**CQ-20.** *Show the time-series of measured indicator values for [solution] across reporting periods.*
- `Solution -[PRODUCES]-> Outcome -[MEASURED_BY]-> Indicator -[RECORDED_AT]-> TimePoint`

### D. Investor — Project benchmarking & due diligence

**CQ-21.** *For [solution type] in [region], what financing structures (instrument × source) have been used, and what capital amounts?*
- `Solution -[FUNDED_BY { amount_usd }]-> FinancingSource`, `Solution -[USES_INSTRUMENT { amount_usd }]-> FinancialInstrument`, filtered by `Solution -[IMPLEMENTED_IN]-> City`

**CQ-22.** *Which financial instruments (green bond, blended finance, resilience bond, etc.) are associated with the highest-evidence outcomes?*
- `Solution -[USES_INSTRUMENT]-> FinancialInstrument`, `Solution -[PRODUCES { evidence_level }]-> Outcome`

**CQ-23.** *Which solutions are blended-financed (multiple sources or multiple instruments), and what does the source-type mix look like?*
- `Solution -[FUNDED_BY]-> FinancingSource` (count > 1), grouped by `FinancingSource.source_type`

**CQ-24.** *For a candidate investment in [solution] in [city profile], what barriers and enabling conditions should I expect, based on comparable past deployments?*
- `Solution -[FACES]-> Barrier`, `Solution -[REQUIRES]-> EnablingCondition`, joined to `Solution -[IMPLEMENTED_IN]-> City` matching profile

**CQ-25.** *Which suppliers serve the most cities for [hazard / urban-system] segment, and what's their reach by region?*
- `Supplier <-[SUPPLIED_BY]- Solution -[MITIGATES | OPERATES_ON]-> Hazard | UrbanSystem`, `Solution -[IMPLEMENTED_IN]-> City`

**CQ-26.** *Which actors coordinate or co-finance with whom in deployed solutions, and what coordination patterns recur?*
- `Actor -[COORDINATES_WITH]-> Actor`, `Solution -[FUNDED_BY]-> FinancingSource`, `Solution -[IMPLEMENTED_BY]-> Actor`

### E. Cross-cutting / structural

**CQ-27.** *Show infrastructure improvements delivered by solutions targeting [hazard], grouped by infra color (green / grey / blue / hybrid).*
- `Solution -[MITIGATES]-> Hazard`, `Solution -[IMPROVES]-> Infrastructure` grouped by `Infrastructure.infra_color`

**CQ-28.** *Trace the full evidence chain from a claim about [outcome] back to its source document and character span.*
- `Outcome.claim_ids -> claims table -> documents -> document_chunks` (provenance traversal)

**CQ-29.** *Across the corpus, which mechanisms are most associated with measured vulnerability reduction?*
- `Solution -[USES_MECHANISM]-> Mechanism`, `Solution -[REDUCES { mechanism_of_reduction }]-> Vulnerability`

**CQ-30.** *Which cities have adaptation plans that prescribe solutions covering all four CRF dimensions (health & wellbeing, economy & society, infrastructure & environment, leadership & planning) vs. only some?*  *(planning-extraction-dependent)*
- `Plan -[ISSUED_BY]-> Actor`, `Plan -[PRESCRIBES]-> Solution -[CONTRIBUTES_TO]-> ResilienceGoal.dimension`, completeness check across the 4 dimensions

### F. Technology stack & maturity  *(Sprint 4 — cross-persona)*

Added to exercise the `DEPENDS_ON` relationship and `Solution.maturity_level` property. These are not tech-exclusive — `DEPENDS_ON` also applies to non-tech solutions that build on each other (e.g., a cooling-center program depending on a heat early-warning system). Extraction should surface dependency statements whenever solutions reference prerequisite systems or integrations.

**CQ-31 (Planner).** *If we deploy [predictive maintenance / digital twin / DERMS / early-warning system], what foundational systems must already exist in our city for it to work?*
- `Solution -[DEPENDS_ON]-> Solution` traversed backward from target solution through the dependency chain

**CQ-32 (Planner / Investor).** *For [candidate solution], which cities in the corpus already have the prerequisite stack deployed vs. which would be starting from scratch?*
- Dependency chain from target solution ∩ `Solution -[IMPLEMENTED_IN]-> City` — identifies "ready" cities by intersecting prerequisite coverage

**CQ-33 (Investor).** *Which solutions in the corpus function as "platforms" — depended on by many other solutions — vs. "endpoints"?*
- Aggregate inbound `DEPENDS_ON` edges per Solution; high in-degree indicates platform role (opportunity or lock-in risk)

**CQ-34 (Analyst).** *What's the typical sequencing pattern — which solution categories are usually deployed before which others?*
- `DEPENDS_ON` filtered by `dependency_type`, grouped by `Solution.category_id` on source and target

**CQ-35 (Investor).** *For [solution category] in [region], what's the maturity distribution — mostly established, or mostly emerging pilots?*
- `Solution.maturity_level` × `Solution.category_id` × `Solution -[IMPLEMENTED_IN]-> City.region`

**CQ-36 (Analyst — validation).** *Does evidence quality actually correlate with maturity level in our corpus, or do emerging solutions sometimes have strong outcome evidence while "established" solutions coast on reputation?*
- `Solution.maturity_level` × `Outcome.evidence_level` crosstab
- **Note:** This CQ is a *falsifiability test* for the `maturity_level` property. If the crosstab shows near-perfect correlation, `maturity_level` is redundant with `evidence_level` and should be removed. Target: run this query once ≥20 tech-enabled solutions are extracted.

**CQ-37 (Planner).** *What emerging solutions are extending [established solution category] — what's on the horizon that we should track?*
- Filter `Solution.maturity_level = emerging` within a category; optionally joined via `DEPENDS_ON` to identify which emerging solutions extend established ones

### G. Equity & justice  *(Sprint 5 — cross-persona, EDF/Cornell study)*

Added to exercise `Solution.equity_focus`, `Solution.target_populations`, `Outcome.justice_dimension`, `Vulnerability.affected_group`, and `ExposureUnit.affected_group`. These CQs form the analytic backbone for the EDF/Cornell AI equity impact assessment.

**CQ-38 (Analyst — equity baseline).** *For [solution type], what fraction of deployments have explicit equity intent (primary_target vs. co_benefit vs. none), and which vulnerable populations are most and least targeted?*
- `Solution.equity_focus` distribution × `Solution.category_id`; `Solution.target_populations` frequency aggregation

**CQ-39 (Analyst — justice gap).** *Across the corpus, what justice dimensions are documented in outcomes, and which are underrepresented — suggesting systematic equity evidence gaps?*
- `Outcome.justice_dimension` frequency distribution; absence signals underdocumented justice types (especially `epistemic`, expected to be rarest)

**CQ-40 (Planner — equity discovery).** *Which solutions have documented distributive benefits for [specific population group] in cities comparable to ours?*
- `Solution.target_populations` contains group, `Solution -[PRODUCES]-> Outcome` filtered by `justice_dimension = distributive`, `Solution -[IMPLEMENTED_IN]-> City` for comparability filter

**CQ-41 (Analyst — procedural equity).** *Which solution types have evidence of meaningful community participation in design, governance, or evaluation?*
- `Solution -[PRODUCES]-> Outcome` filtered by `justice_dimension = procedural`; aggregated by `Solution.category_id`

**CQ-42 (Analyst — equity gap).** *For [hazard X], which exposure units with high vulnerable-population concentration are NOT covered by any solution that targets their group?*
- `Hazard -[EXPOSES]-> ExposureUnit` where `vulnerable_ratio > threshold` MINUS path to `Solution.target_populations` intersecting `ExposureUnit.affected_group`

**CQ-43 (Analyst — AI equity, EDF study).** *What are the documented equity impacts — across all four justice dimensions — of AI-enabled and technology-native solutions, and how do they compare to non-tech solutions?*
- Filter `Solution.category_id` for tech-native categories (or `Solution.maturity_level` as proxy); `Solution -[PRODUCES]-> Outcome.justice_dimension` crosstab across four dimensions
- Note: Primary CQ for EDF/Cornell AI-for-climate-adaptation equity study

**CQ-44 (Analyst — financing equity).** *Do equity-primary solutions systematically differ in financing model from solutions with no equity framing?*
- `Solution.equity_focus` × `Solution -[FUNDED_BY]-> FinancingSource.source_type` × `Solution -[USES_INSTRUMENT]-> FinancialInstrument.instrument_type`

---

## Coverage matrix

| Ontology element | CQs that exercise it |
|---|---|
| `Solution` | all 30 |
| `Hazard` / `MITIGATES` | 1, 2, 10, 15, 25, 27 |
| `UrbanSystem` / `OPERATES_ON` | 2, 25 |
| `Mechanism` / `USES_MECHANISM` | 2, 29 |
| `City` / `IMPLEMENTED_IN` | 1, 3, 6, 10, 21, 24, 25 |
| `Actor` / `IMPLEMENTED_BY` / `ISSUED_BY` / `COORDINATES_WITH` | 11, 13, 26 |
| `Outcome` / `PRODUCES` / `DEMONSTRATES_PROGRESS_ON` | 2, 14–20, 22 |
| `Indicator` / `MEASURED_BY` / `RECORDED_AT` | 14, 20 |
| `EnablingCondition` / `REQUIRES` | 4, 16, 24 |
| `Barrier` / `FACES` | 7, 24 |
| `FinancingSource` / `FUNDED_BY` | 11, 21, 23, 26 |
| `FinancialInstrument` / `USES_INSTRUMENT` | 21, 22, 23 |
| `Supplier` / `SUPPLIED_BY` | 6, 25 |
| `Infrastructure` / `IMPROVES` | 27 |
| `Vulnerability` / `REDUCES` | 5, 29 |
| `ExposureUnit` / `EXPOSES` / `EXPERIENCES_VULN` | 5 |
| `ResilienceGoal` / `CONTRIBUTES_TO` / `SETS_GOAL` | 8, 9, 18, 30 |
| `Plan` / `PRESCRIBES` / `ESTABLISHES` / `PUBLISHED_AT` | 8–13, 30 |
| `Policy` / `IMPLEMENTS` / `FACILITATES` / `HINDERS` | 12 |
| `TimePoint` / `STARTED_AT` / `ISSUED_AT` / `PUBLISHED_AT` / `RECORDED_AT` | 20 |
| `DEPENDS_ON` (Solution → Solution) | 31, 32, 33, 34, 37 |
| `Solution.maturity_level` | 35, 36, 37 |
| `Solution.equity_focus` | 38, 44 |
| `Solution.target_populations` / `vulnerable-populations` vocab | 5, 38, 40, 42 |
| `Outcome.justice_dimension` | 39, 40, 41, 43, 44 |
| `Vulnerability.affected_group` (vocab-bound) | 5, 42 |
| `ExposureUnit.affected_group` (vocab-bound) | 5, 42 |
| Provenance chain (claims → documents → chunks) | 28 (and implicitly all) |

## Resolutions and open questions

1. **Comparability** (CQ-1, CQ-24): **Resolved** — "comparable city" is a query-time filter spanning all available city characteristics, with particular weight on (a) hazards identified in the city's own adaptation plan and (b) attributes from our `cities` reference data (climate, population, country / region, income, coastal status, etc.). No single "similarity" graph property; leave comparability logic in the query layer.
2. **Equity dimension** (CQ-5): **Resolved — Sprint 5.** `vulnerable-populations` vocabulary created (18 population groups, IPCC AR6 / UNDRR aligned). `Vulnerability.affected_group` and `ExposureUnit.affected_group` are now vocabulary-bound arrays. `Solution.target_populations` added for explicit population targeting. `Outcome.justice_dimension` added for equity outcome characterization. CQ-5 is now fully expressible; see also CQ-38 through CQ-44.
3. **Cost normalization** (CQ-21, CQ-22): **Partially resolved** — add a `reference_year` (or equivalent) property alongside `amount_usd` on `FUNDED_BY` and `USES_INSTRUMENT` so values are at least dated. Inflation adjustment is out of scope for v1.
4. **Plan extraction scope** (CQ-8 through CQ-13, CQ-30): **TBD** — Plan node properties and PRESCRIBES / SETS_GOAL / ESTABLISHES / ISSUED_BY / PUBLISHED_AT extraction are still to be specified. CQ-8–13 and CQ-30 remain the scoping targets for that work.
5. **Investor benchmarking** (CQ-22, CQ-25): **Deferred — take what we can get.** No single performance metric is mandated; capture whatever quantitative indicators appear in sources (CapEx/OpEx, returns, risk-adjusted outcome scores, avoided-loss estimates) as `Indicator` nodes and let consumers compose the measure they need.
6. **Tech-enabled filter**: **Resolved** — derivable from `solution-categories`. No dedicated `is_tech_enabled` flag.
7. **Technology stack & maturity** (CQ-31 to CQ-37): **Resolved — minimal additions, pending validation.** Added `DEPENDS_ON` (Solution → Solution) and `Solution.maturity_level` (emerging / demonstrated / established) in Sprint 4. Rejected a dedicated `Technology` node, TRL scale, `deployment_model`, and separate `POWERED_BY` / `MONITORS_VIA` / `INTEGRATES_WITH` relationships — all either redundant with `solution-categories` / `Supplier` / `EnablingCondition` or wrong granularity for document-level extraction. `maturity_level` is provisional: CQ-36 is a falsifiability test to determine whether it is redundant with `Outcome.evidence_level`.

8. **Equity CQs (CQ-38 through CQ-44)**: **Added — Sprint 5.** Designed for EDF/Cornell AI equity impact study. These CQs exercise `equity_focus`, `target_populations`, `justice_dimension`, and vocabulary-bound `affected_group` fields. CQ-43 is the primary EDF study CQ — crosstab of justice dimensions against tech-enabled vs. non-tech solutions. Extraction completeness for equity fields will be lower than for hazard/outcome fields; treat equity-tagged data as signal, not census.

## Next steps

- Review CQ list with team; cut, merge, or add as needed
- Validate each CQ against ~5 published cases in `research_versions` to confirm answerability
- Draft Cypher templates for 5–10 CQs as the GraphRAG test harness seed
- Use unanswerable-but-desired CQs to drive Plan-extraction prioritization
