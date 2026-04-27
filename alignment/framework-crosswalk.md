# Framework Crosswalk: Adaptation Planning Domain
**Version:** 0.1  
**Date:** 2026-04-23  
**Sprint:** Sprint 3 (Taxonomy Integration)  
**Status:** Draft — pending team review

---

## Executive Summary

This document maps our Adaptation Planning domain node types and relationships against three external frameworks (C40 Impacts Taxonomy, ICLEI 5-Milestones, GCoM CRF) and documents the integration decision for the RCC Shocks + Stresses taxonomy.

**Key findings:**
1. The ontology provides strong coverage of the ICLEI planning lifecycle and GCoM reporting structure. No new node types are needed to achieve alignment with either framework, but two relationship properties should be added.
2. The C40 Impacts Taxonomy confirms our hazard and solution vocabularies; the main gap is formalizing the `impacts_on_urban_systems` linkage to align with C40's intervention logic.
3. RCC Shocks map partially to existing Hazard vocabulary. RCC Stresses are chronic conditions that do **not** warrant a new node type — they distribute across Vulnerability, Barrier, Hazard (slow-onset), and Infrastructure nodes with a controlled crosswalk.

**Recommended ontology changes (minor):**
- Add `implementation_stage` property to `PRESCRIBES` relationship (aligns with ICLEI + GCoM action status)
- Add `reporting_period` property to `PUBLISHED_AT` / `RECORDED_AT` relationships (aligns with GCoM disclosure cycle)
- Add `rcc_shock_category` as optional vocabulary binding on Hazard node (non-climate shocks)
- Formalize two RCC stress sub-categories as Vulnerability vocabulary: `socioeconomic_stress` and `governance_stress`

---

## 1. C40 Impacts Taxonomy Crosswalk

### Framework overview
C40's adaptation framework categorizes cities' climate challenges as hazard-driven impacts on urban systems, and classifies adaptation responses by intervention type. Key public elements:

- **Climate hazard categories**: aligned with C40/Arup typology (already our primary Hazard vocabulary — 13 categories, 31 hazards)
- **Intervention categories**: organized by primary hazard + urban system affected
- **Co-benefits framework**: standardized categories of ancillary benefits from adaptation actions
- **Impact pathways**: Hazard → exposed urban system → impact type → adaptation response

### Crosswalk: C40 domains → Ontology nodes

| C40 Concept | Our Node / Relationship | Alignment | Notes |
|---|---|---|---|
| Climate hazard categories (13) | `Hazard.hazard_category` | **Full** | C40/Arup vocabulary already bound |
| Climate hazard specifics (31) | `Hazard.hazard_id` | **Full** | C40/Arup vocabulary already bound |
| Adaptation intervention category | `Solution.category_id` | **Partial** | Our vocabulary is internally derived; Sprint 3 should map categories to C40 intervention types |
| Exposed urban system | `UrbanSystem.sector` | **Full** | Our 7 sectors cover C40's urban system types |
| Impact type | `Outcome.description` + `Outcome.outcome_type` | **Partial** | C40 formalizes impact types (flooding of roads, heat-related mortality, etc.) we capture free-text |
| Co-benefits | `Outcome` (outcome_type=`co_benefit`) | **Full** | Node type and relationship already exist |
| Adaptation strategy goals | `ResilienceGoal` | **Partial** | CRF goals cover C40 resilience goals; direct mapping exists for most |
| Funding mechanism | `FinancialInstrument` | **Partial** | C40 categories slightly narrower than our vocabulary |
| Implementation stage | `PRESCRIBES.implementation_stage` | **Gap** | C40 tracks action stage (committed/in planning/under implementation/completed) — not yet in ontology |

### Gap: Implementation stage
C40's reporting schema requires cities to specify whether an adaptation action is:
- Committed (planned, no timeline)
- In planning (timeline exists)
- Under implementation (started)
- Completed

This maps to the `PRESCRIBES` relationship (Plan → Solution). Recommend adding `implementation_stage: enum[committed, in_planning, under_implementation, completed]` to `PRESCRIBES`.

### Confirmed alignment
The C40 hazard typology is already our primary Hazard vocabulary. The main opportunity is adding a backwards crosswalk from our `Solution.category_id` values to C40 intervention types — this is a vocabulary metadata task, not an ontology change.

---

## 2. ICLEI 5-Milestones Crosswalk

### Framework overview
ICLEI's adaptation planning framework describes five milestones in the local climate adaptation cycle:

| Milestone | Description |
|---|---|
| **A. Initiate** | Establish governance, mandate, and team for adaptation planning |
| **B. Investigate** | Conduct climate risk and vulnerability assessment |
| **C. Plan** | Develop and adopt a local adaptation strategy / plan |
| **D. Implement** | Prioritize, fund, and execute adaptation actions |
| **E. Monitor** | Track progress, evaluate outcomes, report, iterate |

### Crosswalk: ICLEI Milestones → Ontology

| ICLEI Milestone | Key Activities | Our Nodes / Relationships | Coverage |
|---|---|---|---|
| **A. Initiate** | Mandate, team formation, stakeholder engagement | `Actor`, `COORDINATES_WITH`, `REPORTS_TO` | **Good** — actor governance covered |
| **A. Initiate** | Securing resources and commitment | `FinancingSource`, `EnablingCondition` (institutional type) | **Good** |
| **B. Investigate** | Hazard and climate risk assessment | `Hazard`, `ExposureUnit` (EXPOSES) | **Good** |
| **B. Investigate** | Vulnerability assessment (exposure, sensitivity, adaptive capacity) | `Vulnerability`, `EXPERIENCES_VULN`, `ExposureUnit` | **Good** — IPCC AR6 model |
| **B. Investigate** | Stakeholder vulnerability mapping | `Vulnerability.affected_group`, `ExposureUnit.vulnerable_ratio` | **Partial** — free text today |
| **C. Plan** | Develop adaptation strategy document | `Plan`, `PUBLISHED_AT`, `ISSUED_BY` | **Good** |
| **C. Plan** | Set adaptation goals and targets | `Plan -[SETS_GOAL]-> ResilienceGoal` | **Good** |
| **C. Plan** | Prescribe adaptation actions | `Plan -[PRESCRIBES]-> Solution` | **Good** |
| **C. Plan** | Policy and regulatory framework | `Plan -[ESTABLISHES]-> Policy` | **Good** |
| **D. Implement** | Execute adaptation actions | `Solution -[IMPLEMENTED_IN]-> City`, `IMPLEMENTED_BY` | **Good** |
| **D. Implement** | Secure financing | `FUNDED_BY`, `USES_INSTRUMENT` | **Good** |
| **D. Implement** | Address barriers | `Solution -[FACES]-> Barrier` | **Good** |
| **D. Implement** | Build enabling conditions | `Solution -[REQUIRES]-> EnablingCondition` | **Good** |
| **D. Implement** | **Action stage tracking** | `PRESCRIBES.implementation_stage` | **Gap** — not yet in ontology |
| **E. Monitor** | Track outcome indicators | `Outcome -[MEASURED_BY]-> Indicator` | **Good** |
| **E. Monitor** | Measure progress on goals | `Outcome -[DEMONSTRATES_PROGRESS_ON]-> ResilienceGoal` | **Good** |
| **E. Monitor** | Time-series reporting | `Indicator -[RECORDED_AT]-> TimePoint` | **Good** |
| **E. Monitor** | **Reporting period tracking** | `RECORDED_AT.reporting_period` | **Gap** — want to distinguish monitoring cycle from single year |

### Assessment
The ICLEI 5-Milestones maps cleanly onto the ontology — our planning domain design implicitly followed this lifecycle. The two gaps are both minor relationship properties (action stage and reporting period). No new node types needed.

**Standardization opportunity**: `Plan.plan_type` vocabulary could be aligned with ICLEI plan types:
- `adaptation_strategy` (city-wide resilience / adaptation strategy)
- `sectoral_adaptation_plan` (e.g., coastal adaptation plan)
- `climate_action_plan` (combined mitigation + adaptation)
- `disaster_risk_reduction_plan` (UNDRR/Sendai aligned)
- `nature_based_solutions_plan`

Currently `Plan.plan_type` is free text. Formalizing this vocabulary aligns with ICLEI documentation categories and enables CQ-13 queries by plan type.

---

## 3. GCoM Common Reporting Framework (CRF) Crosswalk

### Framework overview
The Global Covenant of Mayors CRF for Adaptation defines standardized data fields for city-level climate adaptation disclosure. Cities submit through CDP's platform. Key data domains:

1. **Hazards and risk** — hazard types, risk levels, current/future horizon
2. **Adaptation actions** — category, description, lead agency, status, timeline
3. **Co-benefits** — social, economic, environmental
4. **Urban context** — sector/system affected
5. **Stakeholder engagement** — who is involved
6. **Financing** — amount, source, instrument
7. **Monitoring and progress** — indicators, measured outcomes

### Crosswalk: GCoM CRF fields → Ontology

| GCoM CRF Field | Our Node / Relationship | Coverage | Notes |
|---|---|---|---|
| Hazard type | `Hazard` (C40/Arup vocabulary) | **Full** | Direct C40 alignment |
| Hazard risk level (current, 2050) | `ExposureUnit.vulnerable_ratio`, `Vulnerability` scores | **Partial** | CRF uses low/medium/high/very high risk scale; our scores are unscaled |
| Adaptation action category | `Solution.category_id` | **Partial** | GCoM has ~20 action categories; map needed |
| Adaptation action status | `PRESCRIBES.implementation_stage` | **Gap** | CRF: planned/in progress/completed |
| Adaptation action timeframe | `STARTED_AT`, `PUBLISHED_AT` | **Partial** | CRF wants projected completion too |
| Lead organization | `Actor` (ISSUED_BY, IMPLEMENTED_BY) | **Good** |  |
| Co-benefits | `Outcome` (outcome_type=co_benefit) | **Good** |  |
| Urban sector affected | `UrbanSystem.sector` | **Full** |  |
| Funding amount | `FUNDED_BY.amount_usd` | **Good** |  |
| Funding source type | `FinancingSource.source_type` | **Full** | Types align with GCoM vocabulary |
| Financial instrument | `FinancialInstrument.instrument_type` | **Good** | Minor vocabulary differences |
| Progress indicator | `Indicator` | **Good** |  |
| Baseline / measured value | `Indicator.baseline`, `Indicator.measured_value` | **Good** |  |
| Reporting year | `TimePoint.year` | **Good** |  |

### Assessment
GCoM CRF is the strongest alignment case. Our planning + solutions nodes were implicitly designed against GCoM's disclosure categories (since our source data includes CDP submissions). The main gap remains `implementation_stage` on PRESCRIBES.

**Standardization opportunity**: GCoM uses a specific action category vocabulary (~20 categories). We should create a crosswalk from our `Solution.category_id` values to GCoM categories and document it in `vocabularies/`. This is metadata work, not a schema change.

---

## 4. RCC Shocks + Stresses Integration Decision

### Background
The Resilient Cities Network (RCC / 100 Resilient Cities) taxonomy, extracted from `resources/Shocks and Stresses.xlsx`, defines 25 **shocks** (acute events) and 45 **stresses** (chronic conditions).

Current state: The Hazard node's notes say "Non-climate shocks/stresses use separate `resilience_hazards` field (free text)." This was a placeholder. This section formalizes the integration decision.

---

### 4.1 RCC Shocks Analysis

Full RCC shock list (25 items):

| RCC Shock | Climate-driven? | C40/Arup equivalent | Action |
|---|---|---|---|
| Blizzard | Yes | extreme_temperature_cold / precipitation | Already covered |
| Drought | Yes | water_scarcity | Already covered |
| Dust / Sand Storm | Yes | mass_movement / wind | Already covered (dust storm in C40) |
| Extreme Cold | Yes | extreme_temperature_cold | Already covered |
| Extreme Heat | Yes | extreme_temperature_hot | Already covered |
| Fire | Yes | wild_fire | Already covered |
| Hurricane / Typhoon / Cyclone | Yes | wind / wave_action | Already covered |
| Landslide | Yes | mass_movement | Already covered |
| Rainfall Flooding | Yes | flood | Already covered |
| Severe Storms | Yes | wind / precipitation | Already covered |
| Storm Surge | Yes | wave_action / flood | Already covered |
| Tornado | Yes | wind | Already covered |
| Tsunami | Yes | wave_action | Already covered |
| **Cyber Attack** | **No** | — | Add to RCC shocks vocabulary |
| **Disease Outbreak** | **No** | — | Add to RCC shocks vocabulary |
| **Earthquake** | **No** | mass_movement (partial) | Add to RCC shocks vocabulary (seismic) |
| **Financial / Economic Crisis** | **No** | — | Add to RCC shocks vocabulary |
| **Hazardous Materials Accident** | **No** | chemical_change (partial) | Add to RCC shocks vocabulary |
| **Infrastructure Failure** | **No** | — | Add to RCC shocks vocabulary |
| **Liquefaction** | **No** | mass_movement (seismic-induced) | Add to RCC shocks vocabulary |
| **Nuclear Incident** | **No** | — | Add to RCC shocks vocabulary |
| **Power Outage** | **No** | — | Add to RCC shocks vocabulary |
| **Riot / Civil Unrest** | **No** | — | Add to RCC shocks vocabulary |
| **Terrorist Attack** | **No** | — | Add to RCC shocks vocabulary |
| **Volcanic Activity** | **No** | — | Add to RCC shocks vocabulary |

**Decision: Add `hazard_source` and a secondary RCC shock vocabulary to Hazard node.**

The 13 climate-driven RCC shocks are already covered by C40/Arup bindings. The 12 non-climate shocks should be added as an optional secondary vocabulary binding with a `hazard_source` property to disambiguate.

**Proposed change to Hazard node:**
```json
{
  "id": "hazard_source",
  "type": "enum",
  "values": ["c40_arup", "rcc"],
  "note": "Vocabulary source. c40_arup = climate hazards only; rcc = non-climate acute shocks from RCC taxonomy"
}
```
And add RCC non-climate shocks to `vocabularies/hazards.json` under a new `rcc_shocks` category.

---

### 4.2 RCC Stresses Analysis

Full RCC stress list (45 items), categorized and mapped to existing nodes:

#### Category A: Environmental stresses → Map to Hazard (slow-onset)

These are gradual-onset environmental processes that function as climate hazards in planning contexts:

| RCC Stress | Maps to | Notes |
|---|---|---|
| Climate Change | `Hazard` (meta-hazard, often context) | Usually a framing context, not an individual hazard node |
| Coastal / Tidal Flooding | `Hazard` (flood) | Already in C40 |
| Environmental Degradation | `Hazard` (new slow-onset category) | Add to RCC slow-onset stresses vocabulary |
| Invasive Species | `Hazard` (insects_and_microorganisms — partial) | Add to slow-onset vocabulary |
| Loss of Biodiversity | `Hazard` (new) or `UrbanSystem` context | Add to slow-onset vocabulary |
| Poor Air Quality | `Hazard` (chemical_change — partial) | Add to slow-onset vocabulary |
| Sea Level Rise / Coastal Erosion | `Hazard` (wave_action / flood — partial) | Already in CRF as distinct hazard; add explicitly |
| Subsidence | `Hazard` (mass_movement — partial) | Add explicitly |

**Proposed**: Create `rcc_stresses_environmental` vocabulary category under Hazard, covering slow-onset environmental stresses not fully captured by C40 acute hazard typology.

#### Category B: Socioeconomic stresses → Map to Vulnerability

These describe population characteristics that increase climate vulnerability — they are drivers of the Vulnerability node's properties:

| RCC Stress | Maps to | Notes |
|---|---|---|
| Aging Population | `Vulnerability.affected_group` = "elderly" | Population characteristic |
| Crime / Violence | `Vulnerability.vuln_type` or Barrier | Context-dependent |
| Declining Population / Human Capital Flight | `Vulnerability.adaptive_capacity_score` context | Weakens adaptive capacity |
| Displaced Populations / Migrants | `ExposureUnit` (vulnerable_ratio) + `Vulnerability.affected_group` | High vulnerability group |
| Drug / Alcohol Abuse | `Vulnerability` (sensitivity) | Social determinant of vulnerability |
| Economic Inequality | `Vulnerability.vuln_type` = "economic_inequality" | Core vulnerability driver |
| Ethnic Inequality | `Vulnerability.vuln_type` = "ethnic_inequality" | Social vulnerability |
| Food Insecurity | `Vulnerability.vuln_type` = "food_insecurity" | Compound vulnerability |
| Gender Inequality | `Vulnerability.vuln_type` = "gender_inequality" | Social vulnerability |
| Homelessness | `Vulnerability` (exposure high, adaptive_capacity low) | Exposed group |
| Informal Housing / Settlements | `Infrastructure.condition` = poor + `Vulnerability` | Physical + social vulnerability compound |
| Lack of Social Cohesion | `Vulnerability.adaptive_capacity_score` context | Weakens collective adaptive capacity |
| Poverty | `Vulnerability.vuln_type` = "poverty" | Foundational vulnerability driver |
| Structural Racism | `Vulnerability.vuln_type` = "structural_racism" | Systemic vulnerability driver |
| Unemployment | `Vulnerability.vuln_type` = "unemployment" | Economic vulnerability |
| Urban Blight | `Infrastructure.condition` + `Vulnerability` | Physical-social compound |
| Youth Disenfranchisement | `Vulnerability.affected_group` | Specific vulnerable group |

**Proposed**: Formalize `Vulnerability.vuln_type` vocabulary with key socioeconomic stress categories. Currently free text — controlled vocabulary enables CQ-5 ("Which solutions reduce vulnerability for [low-income coastal residents]?").

#### Category C: Governance + institutional stresses → Map to Barrier

These chronic conditions function as structural barriers to adaptation:

| RCC Stress | Maps to Barrier.barrier_type | Notes |
|---|---|---|
| Corruption | `political` | Institutional barrier |
| Inadequate Educational Systems | `social` + `institutional` | System-level social barrier |
| Inadequate Health Systems | `social` + `institutional` | System-level social barrier |
| Inadequate Public Transportation Systems | `institutional` | System deficiency barrier |
| Inadequate Sanitation Systems | `institutional` | System deficiency barrier |
| Insecure Municipal Finances | `financial` | Direct financial barrier to adaptation |
| Lack of Investment | `financial` | Investment barrier |
| Political Instability | `political` | Governance barrier |
| Poor Governance / Regulatory Climate | `regulatory` + `political` | Barrier to adaptation policy |

**No change needed** — these map well to existing `Barrier.barrier_type` vocabulary. The crosswalk documents the mapping.

#### Category D: Urban development stresses → Map to City / UrbanSystem context

These are urban growth and spatial planning challenges — they provide context for solution deployment rather than driving individual nodes:

| RCC Stress | Maps to | Notes |
|---|---|---|
| Aging Infrastructure | `Infrastructure.condition` (poor/critical) | Infrastructure state property |
| Energy Insecurity | `UrbanSystem` (energy_telecom) + `Vulnerability` | System vulnerability |
| Inadequate Infrastructure | `Infrastructure.condition` (poor/critical) | Infrastructure state property |
| Lack of Affordable Housing | `Vulnerability` + urban context | Social vulnerability driver |
| Lack of Green Space | `Infrastructure` (green, service_coverage low) | Green infrastructure gap |
| Population Growth / Overpopulation | City / UrbanSystem context | Deployment context property |
| Shifting Macroeconomic Trends | `FinancingSource` context / `Barrier` (financial) | Macro-financial barrier |
| Traffic Congestion | `UrbanSystem` (mobility_transport) | System stress |
| Traffic Injuries | `Outcome` (failure_mode) / `Vulnerability` | Safety vulnerability |
| Uncontrolled Urban Development | Deployment context / `Barrier` | Regulatory barrier |
| Undiversified Economy | `Vulnerability.adaptive_capacity_score` context | Reduces economic adaptive capacity |
| Water Insecurity | `UrbanSystem` (hydrological_water) + `Vulnerability` | System + vulnerability compound |

**No change needed** — these distribute across existing node properties.

---

### 4.3 RCC Integration Decision Summary

| Component | Decision | Ontology Change |
|---|---|---|
| Climate-aligned shocks (13) | Already covered by C40/Arup | None |
| Non-climate shocks (12) | Add to Hazard vocabulary with `hazard_source: "rcc"` | Add `hazard_source` property to Hazard + extend `hazards.json` |
| Environmental stresses (8) | Add slow-onset vocabulary to Hazard | Extend `hazards.json` with `rcc_stresses_environmental` category |
| Socioeconomic stresses (17) | Map to `Vulnerability.vuln_type` | Formalize `vuln_type` vocabulary (currently free text) |
| Governance stresses (9) | Map to `Barrier.barrier_type` | Document crosswalk; no type change needed |
| Urban development stresses (12) | Map to Infrastructure, UrbanSystem, Barrier | Document crosswalk; no type change needed |
| **New Stress node?** | **No** | No new node type — stresses distribute across existing nodes |

**Rationale for no Stress node**: A dedicated `Stress` node would either duplicate Vulnerability (for socioeconomic stresses) or Barrier (for governance stresses) or Hazard (for environmental stresses). The RCC taxonomy's "shock vs. stress" distinction is meaningful for city risk assessment framing but does not justify separate node types in a solutions-focused KG. The distinction can be captured via vocabulary tags (`hazard_source`, `vuln_type` categories) on existing nodes.

---

## 5. Gap Analysis and Recommendations

### Ontology changes recommended (minor, Sprint 3)

| Change | Affected Element | Alignment Driver | Priority |
|---|---|---|---|
| Add `implementation_stage` to PRESCRIBES | Relationship | C40, ICLEI-D, GCoM | **High** — needed for plan-to-action gap analysis |
| Add `hazard_source` to Hazard | Node property | RCC integration | **High** — disambiguates climate vs. non-climate hazards |
| Extend `hazards.json` with RCC non-climate shocks | Vocabulary | RCC shocks integration | **High** |
| Extend `hazards.json` with RCC slow-onset stresses | Vocabulary | RCC environmental stresses | **Medium** |
| Formalize `Vulnerability.vuln_type` vocabulary | Node property vocabulary | RCC socioeconomic stresses | **Medium** — enables CQ-5 |
| Add `plan_type` vocabulary binding to Plan node | Node property vocabulary | ICLEI standardization | **Low** — currently free text |

### Vocabulary metadata tasks (no schema change, Sprint 3–4)

| Task | Description |
|---|---|
| Solution categories → C40 intervention crosswalk | Add `c40_intervention_type` field to solution-categories.json |
| Solution categories → GCoM action categories crosswalk | Add `gcom_category` field to solution-categories.json |
| Barrier types → RCC stresses crosswalk | Add `rcc_stress_ids` field to Barrier type definitions |
| Vulnerability types → RCC stresses crosswalk | Document RCC stress → vuln_type mapping in vocabulary |

### No changes recommended

| Thing | Why not |
|---|---|
| New `Stress` node type | Stresses distribute across Vulnerability, Barrier, Hazard; no new node needed |
| New `Action` or `Process` node type | ICLEI's action concept = our Solution; Plan covers the document artifact |
| Separate `ClimateRisk` node | Our ExposureUnit + Vulnerability combination covers this |
| GCoM risk level vocabulary on Vulnerability | Scores are too context-specific; leave as free-form numbers with scale TBD |

---

## 6. Appendix: RCC Full Crosswalk Reference

### A. Shocks → Hazard mapping

| RCC Shock | Existing C40 Hazard ID | RCC Integration |
|---|---|---|
| Blizzard | extreme_temperature_cold.blizzard (or precipitation.blizzard) | Use C40 |
| Cyber Attack | — | Add: `rcc.cyber_attack` |
| Disease Outbreak | insects_and_microorganisms (partial) | Add: `rcc.disease_outbreak` |
| Drought | water_scarcity.* | Use C40 |
| Dust / Sand Storm | mass_movement.dust_sand_storm | Use C40 |
| Earthquake | — | Add: `rcc.earthquake` |
| Extreme Cold | extreme_temperature_cold.* | Use C40 |
| Extreme Heat | extreme_temperature_hot.* | Use C40 |
| Financial / Economic Crisis | — | Add: `rcc.financial_economic_crisis` |
| Fire | wild_fire.* | Use C40 |
| Hazardous Materials Accident | chemical_change (partial) | Add: `rcc.hazmat_accident` |
| Hurricane / Typhoon / Cyclone | wind.* + wave_action.* | Use C40 |
| Infrastructure Failure | — | Add: `rcc.infrastructure_failure` |
| Landslide | mass_movement.landslide | Use C40 |
| Liquefaction | — | Add: `rcc.liquefaction` |
| Nuclear Incident | — | Add: `rcc.nuclear_incident` |
| Power Outage | — | Add: `rcc.power_outage` |
| Rainfall Flooding | flood.* | Use C40 |
| Riot / Civil Unrest | — | Add: `rcc.riot_civil_unrest` |
| Severe Storms | wind.* + precipitation.* | Use C40 |
| Storm Surge | wave_action.storm_surge | Use C40 |
| Terrorist Attack | — | Add: `rcc.terrorist_attack` |
| Tornado | wind.tornado | Use C40 |
| Tsunami | wave_action.tsunami | Use C40 |
| Volcanic Activity | — | Add: `rcc.volcanic_activity` |

### B. Stresses → Ontology node mapping

| RCC Stress | Primary Node | Secondary Node | Mapping Notes |
|---|---|---|---|
| Aging Infrastructure | Infrastructure.condition | Barrier (financial) | Condition property; financial barrier for replacement |
| Aging Population | Vulnerability.affected_group | ExposureUnit.vulnerable_ratio | Specific vulnerable group |
| Climate Change | Hazard (meta context) | — | Usually framing, not individual hazard |
| Coastal / Tidal Flooding | Hazard (flood) | — | Use C40 flood vocabulary |
| Corruption | Barrier (political) | — | Institutional governance barrier |
| Crime / Violence | Barrier (social) | Vulnerability | Context-dependent |
| Declining Population / Human Capital Flight | Vulnerability (adaptive_capacity) | Barrier (institutional) | Reduces community adaptive capacity |
| Displaced Populations / Migrants | ExposureUnit | Vulnerability.affected_group | High-exposure vulnerable group |
| Drug / Alcohol Abuse | Vulnerability (sensitivity) | — | Social vulnerability driver |
| Economic Inequality | Vulnerability.vuln_type | — | Core socioeconomic vulnerability |
| Energy Insecurity | UrbanSystem (energy_telecom) | Vulnerability | System + vulnerability compound |
| Environmental Degradation | Hazard (slow-onset) | — | Add to slow-onset vocabulary |
| Ethnic Inequality | Vulnerability.vuln_type | — | Social vulnerability |
| Food Insecurity | Vulnerability.vuln_type | — | Compound vulnerability |
| Gender Inequality | Vulnerability.vuln_type | — | Social vulnerability |
| Homelessness | Vulnerability (exposure high) | ExposureUnit | Highly exposed population |
| Inadequate Educational Systems | Barrier (social+institutional) | Vulnerability (adaptive_capacity) | System-level social barrier |
| Inadequate Health Systems | Barrier (social+institutional) | Vulnerability | Public health system gap |
| Inadequate Infrastructure | Infrastructure.condition (poor/critical) | Barrier (institutional) | Infrastructure state |
| Inadequate Public Transportation Systems | UrbanSystem (mobility_transport) | Barrier (institutional) | System deficiency |
| Inadequate Sanitation Systems | UrbanSystem (hydrological_water) | Barrier (institutional) | System deficiency |
| Informal Housing / Settlements | Infrastructure.condition | Vulnerability | Physical-social compound |
| Insecure Municipal Finances | Barrier (financial) | FinancingSource context | Direct financial barrier |
| Invasive Species | Hazard (slow-onset ecological) | — | Add to slow-onset vocabulary |
| Lack of Affordable Housing | Vulnerability | Barrier (social) | Social vulnerability driver |
| Lack of Green Space | Infrastructure (green, service_coverage low) | — | Green infrastructure gap |
| Lack of Investment | Barrier (financial) | FinancingSource | Financial barrier |
| Lack of Social Cohesion | Vulnerability (adaptive_capacity) | — | Weakens collective capacity |
| Loss of Biodiversity | Hazard (slow-onset ecological) | — | Add to slow-onset vocabulary |
| Political Instability | Barrier (political) | — | Governance barrier |
| Poor Air Quality | Hazard (slow-onset / chemical_change) | — | Add to slow-onset vocabulary |
| Poor Governance / Regulatory Climate | Barrier (regulatory+political) | EnablingCondition (absent) | Governance barrier |
| Population Growth / Overpopulation | City/ExposureUnit context | — | Deployment context |
| Poverty | Vulnerability.vuln_type | — | Foundational vulnerability driver |
| Sea Level Rise / Coastal Erosion | Hazard (slow-onset) | — | Add explicitly to slow-onset vocab |
| Shifting Macroeconomic Trends | Barrier (financial) | — | Macro-financial barrier |
| Structural Racism | Vulnerability.vuln_type | — | Systemic vulnerability |
| Subsidence | Hazard (mass_movement) | — | Add explicitly |
| Traffic Congestion | UrbanSystem (mobility_transport) | — | System stress |
| Traffic Injuries | Outcome (failure_mode) | Vulnerability | Safety context |
| Uncontrolled Urban Development | Barrier (regulatory) | — | Regulatory barrier |
| Undiversified Economy | Vulnerability (adaptive_capacity) | — | Economic adaptive capacity |
| Unemployment | Vulnerability.vuln_type | — | Economic vulnerability |
| Urban Blight | Infrastructure.condition | Vulnerability | Physical-social compound |
| Water Insecurity | UrbanSystem (hydrological_water) | Vulnerability | System + vulnerability |
| Youth Disenfranchisement | Vulnerability.affected_group | — | Specific vulnerable group |
