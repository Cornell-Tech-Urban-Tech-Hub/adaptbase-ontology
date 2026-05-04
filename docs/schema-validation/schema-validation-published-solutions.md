# Schema Validation: Published Solutions → Extraction Schema v1

## Methodology

Mapped 3 diverse published solutions from `research_versions` to the extraction schema to verify:
1. Every schema field can be populated from existing research
2. No important information in the research is un-capturable by the schema
3. Controlled vocabulary values match

---

## Solution 1: Seoul Safety App (CBS/Anshimi)

**Profile**: Emergency response platform, flood monitoring, AI/big data, municipal government, Seoul

### Dimension coverage

| Dimension | Field | Populatable? | Notes |
|---|---|---|---|
| **identity** | solution_name | YES | "Seoul Safety App" / "Anshimi" |
| | solution_category | YES | communication_and_community → early_warning_systems_and_alerts |
| | solution_description | YES | Multiple claims describe the system |
| | ipcc_action_type | YES | structural_physical + social |
| | implementing_actor_types | YES | municipal_government |
| | year_of_deployment | YES | 2018 (pilot 2017) |
| **hazards** | hazards_addressed | YES | flash_surface_flood, river_flood |
| **urban_systems** | systems_affected | YES | communication_and_community, planning_and_monitoring |
| **mechanisms** | primary_mechanism | YES | "monitor" — real-time disaster sensing and alerting |
| | secondary_mechanisms | YES | "govern" — emergency coordination |
| | technical_components | YES | CCTV network (39,463 cameras), mobile app, 119 big data center, AI crowd detection, cell broadcasting |
| **implementation** | cities | YES | Seoul |
| | scale_of_deployment | YES | city |
| | implementation_status | YES | operational |
| | timeline | YES | pilot 2017, full launch Oct 2018, upgrades 2022-2023 |
| | cost | PARTIAL | No total cost figure, but contract amounts mentioned |
| | key_actors | YES | SMG, VEMA equivalent, autonomous districts |
| **evidence** | evidence_level | YES | measured (download counts, usage stats) |
| | outcome_indicators | YES | 224,604 downloads, 211,481 service uses |
| | co_benefits | YES | Crime prevention (CCTV dual-use) |
| | failure_modes | NO | Not mentioned in research |
| **context** | enabling_conditions | PARTIAL | Institutional (Korea's WEA system since 2005) |
| | barriers | NO | Not mentioned |
| | replicability | NO | Not explicitly assessed |
| | governance_relationships | YES | National government → local government authority chain |

### Completeness estimate
- identity: 1.0 | hazards: 1.0 | urban_systems: 0.8 | mechanisms: 1.0
- implementation: 0.85 | evidence: 0.7 | context: 0.4
- **Overall: ~0.82**

### Schema gaps identified
- No field for "phased evolution" — solution evolved from pilot → city-wide → AI upgrades. Timeline captures start/end but not phases
- Multiple solution names (CBS, Anshimi, Seoul Safety App) — schema only has one solution_name field

### Recommendations
- Add `alternative_names` array to identity dimension
- Consider adding `implementation_phases` array to implementation dimension (for later versions)

---

## Solution 2: Vancouver Hazard & Risk Explorer

**Profile**: Climate information platform, story map, multi-hazard, municipal

### Dimension coverage

| Dimension | Field | Populatable? | Notes |
|---|---|---|---|
| **identity** | solution_name | YES | "Hazard & Risk Explorer" |
| | solution_category | YES | planning_and_monitoring → decision_support_for_climate_adaptation_planning |
| | ipcc_action_type | YES | social (informational) |
| | implementing_actor_types | YES | municipal_government |
| | year_of_deployment | YES | 2024, target completion 2025 |
| **hazards** | hazards_addressed | YES | heat_wave, coastal_flood, forest_fire + earthquake (not in hazard table) |
| **urban_systems** | systems_affected | YES | planning_and_monitoring |
| **mechanisms** | primary_mechanism | YES | "adapt_behavior" — public information and awareness |
| | technical_components | YES | Interactive platform, spatial data, story map, HRVA methodology |
| **implementation** | cities | YES | Vancouver |
| | scale_of_deployment | YES | city |
| | cost | NO | No cost data in research |
| | key_actors | YES | VEMA, Resilience Mapping Canada |
| **evidence** | evidence_level | YES | anecdotal (no measured outcomes yet — too new) |
| | outcome_indicators | NO | Platform too new for impact data |
| | co_benefits | YES | Equity improvement, multilingual access (12 languages) |
| **context** | enabling_conditions | YES | institutional (Resilient Vancouver Strategy mandate) |
| | replicability | YES | Comparable North Shore implementation described |
| | governance_relationships | YES | FACILITATED_BY Resilient Vancouver Strategy |

### Completeness estimate
- identity: 1.0 | hazards: 0.9 | urban_systems: 0.7 | mechanisms: 0.8
- implementation: 0.6 | evidence: 0.3 | context: 0.7
- **Overall: ~0.71**

### Schema gaps identified
- **Earthquake is not in the hazards table** — the current hazards taxonomy only covers climate-driven hazards (flood, heat, wildfire, drought, wind). Seismic hazards are absent. Vancouver's platform covers earthquake alongside climate hazards.
- No field for "accessibility features" (12-language translations) — could go in co_benefits or a new field
- "Similar implementations" (North Shore story map) — no field for comparable deployments. Could be captured in replicability.assessment free text.

### Recommendations
- Decide whether seismic hazards belong in the hazard taxonomy (they overlap with climate in cascading risk scenarios)
- Comparable/reference implementations could become a field in context.replicability

---

## Solution 3: Wellington Lifelines Outage Modelling

**Profile**: Infrastructure resilience modeling, earthquake, multi-utility, NZ$3.9B investment programme

### Dimension coverage

| Dimension | Field | Populatable? | Notes |
|---|---|---|---|
| **identity** | solution_name | YES | "Wellington Resilience Programme" |
| | solution_category | YES | planning_and_monitoring → climate_analytics OR infrastructure → infrastructure_inspection_and_hardening |
| | ipcc_action_type | YES | structural_physical + institutional |
| | implementing_actor_types | YES | multi_stakeholder (16 utility providers + local government) |
| **hazards** | hazards_addressed | PARTIAL | subsidence, landslide (in table), but primary hazard is earthquake (not in table) |
| **urban_systems** | systems_affected | YES | Multiple: water, energy, transportation, infrastructure, communication_and_community |
| **mechanisms** | primary_mechanism | YES | "monitor" — modeling and simulation of infrastructure cascading failures |
| | secondary_mechanisms | YES | "harden" — investment programme to strengthen infrastructure |
| | technical_components | YES | RiskScape model, PDC teams, MERIT economic modeling, time-stamped outage maps |
| **implementation** | cities | YES | Wellington region |
| | scale_of_deployment | YES | regional |
| | cost | YES | NZ$3.9B total, Phase 1: 28% committed, 20% contingent, 51% unfunded |
| | timeline | YES | 3 phases, Phase 1 = years 1-7, published Dec 2017 |
| | key_actors | YES | GNS Science, Wellington Lifelines Group, Wellington Water, Kapiti Coast DC |
| **evidence** | evidence_level | YES | modeled |
| | outcome_indicators | YES | $6B GDP loss avoided, $16B do-nothing vs $10B with investment |
| | co_benefits | YES | Reduced losses from smaller earthquakes and other perils |
| **context** | enabling_conditions | YES | institutional (Wellington Lifelines Group coordination) |
| | barriers | YES | financial (51% unfunded for Phase 1) |
| | replicability | PARTIAL | First study of this complexity in NZ |
| | governance_relationships | YES | FACILITATED_BY Wellington Lifelines Group, COORDINATES_WITH 16 utility providers |

### Completeness estimate
- identity: 0.9 | hazards: 0.6 | urban_systems: 1.0 | mechanisms: 1.0
- implementation: 0.9 | evidence: 0.9 | context: 0.8
- **Overall: ~0.87**

### Schema gaps identified
- **Earthquake again not in hazards table** — Wellington's primary hazard
- **Multi-utility interdependency modeling** — the solution's core innovation (modeling cascading failures across 16 utilities) doesn't have a clean field. It's partly captured in technical_components and partly in mechanisms
- **Phased investment programme** — cost field captures total but not the phase breakdown or funding status per phase
- **Category classification difficulty** — this solution spans planning_and_monitoring (modeling) AND infrastructure (hardening investments). The schema has one primary category. Need classification_difficulty_notes.

### Recommendations
- Seismic hazards decision needed (same as Vancouver)
- Consider allowing multiple solution_category assignments (primary + secondary)
- Cost field could benefit from a structured breakdown (phases, funding status)

---

## Cross-Solution Findings

### Fields always populatable (from these 3 solutions)
- identity: solution_name, solution_description, solution_category, ipcc_action_type, implementing_actor_types
- hazards: hazards_addressed (when hazard is in taxonomy)
- urban_systems: systems_affected
- mechanisms: primary_mechanism, technical_components
- implementation: cities, scale_of_deployment

### Fields frequently missing
- evidence.failure_modes (1/3 solutions)
- implementation.cost (1/3 solutions had no data)
- context.barriers (1/3)
- context.replicability (often not explicitly assessed)

### Taxonomy gaps discovered
1. **Seismic hazards absent** — earthquake, tsunami not in hazards table. 2/3 solutions addressed earthquake. Need to decide: add non-climate hazards or note as out of scope?
2. **Multi-category solutions** — Wellington spans planning + infrastructure. Schema allows only one primary category.
3. **Solution evolution/phases** — schema captures start/end but not phased deployment
4. **Alternative names** — solutions often have multiple names (CBS vs Anshimi vs Seoul Safety App)

### Schema adjustments recommended
1. Add `identity.alternative_names` (string array) — low effort, high value
2. Add `identity.secondary_category` — allows dual classification
3. Expand `implementation.cost` with optional `phases` array
4. Note seismic hazards gap in classification_difficulty_notes for now; decide on taxonomy expansion in Month 2
5. Add `context.comparable_implementations` for reference deployments
