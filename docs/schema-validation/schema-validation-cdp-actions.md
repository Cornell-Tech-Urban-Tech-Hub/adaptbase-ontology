# Schema Validation: CDP Actions → Extraction Schema v1

## Methodology

Sampled 10 CDP actions across 6 regions (Africa, Eastern Asia, Europe, Latin America, Middle East). Mapped CDP columns to extraction schema fields and assessed coverage.

---

## CDP Column → Schema Field Mapping

| CDP Column | Schema Location | Confidence | Notes |
|---|---|---|---|
| `action_name_en` | identity.solution_name + identity.solution_category | self_reported | CDP action names encode category (e.g., "Ecosystem-based actions: Ecological corridors") |
| `action_description_en` | identity.solution_description | self_reported | Primary content — BUT often mixes solution with city context |
| `action_hazards_en` | hazards.hazards_addressed | self_reported | **Vocabulary mismatch** — CDP uses different hazard terms (see below) |
| `action_sectors` | urban_systems.systems_affected | self_reported | **Vocabulary mismatch** — CDP uses ISIC sectors, not our categories |
| `action_status` | implementation.implementation_status | self_reported | Needs value mapping (see below) |
| `action_timeframe` | implementation.timeline | self_reported | Coarse buckets: Short/Medium/Long-term |
| `action_total_cost_usd` | implementation.cost.total_cost_usd | self_reported | Often empty (74% null); when present, quality varies |
| `action_funding_sources` | context.enabling_conditions (financial) | self_reported | Multi-select field |
| `action_cobenefits_en` | evidence.co_benefits | self_reported | Well-structured: "Category: Specific benefit" |
| `action_population_impact_pct` | evidence.primary_beneficiaries (scale) | self_reported | Percentage buckets |
| `action_ecosystem_impact_pct` | evidence.outcome_indicators (partial) | self_reported | Percentage buckets |
| `action_resilience_attributes` | mechanisms (partial) | self_reported | Closest to mechanism dimension but different vocabulary |
| `action_in_climate_plan` | context.governance_relationships | self_reported | Yes/No for inclusion in climate action plan |
| `city_name` | implementation.cities[].city_name | — | Always populated |
| `country` | implementation.cities[].country | — | Always populated |
| `region` | implementation.cities[].region | — | Always populated |

---

## Vocabulary Mapping Challenges

### Hazards: CDP → Schema

CDP hazard terms do NOT match our hazards table directly. Mapping needed:

| CDP Hazard Term | Schema hazard_id | Notes |
|---|---|---|
| Urban flooding | flash_surface_flood | Close match |
| River flooding | river_flood | Direct match |
| Coastal flooding (incl. sea level rise) | coastal_flood | Direct match |
| Extreme heat | extreme_hot_weather | Close match |
| Heat stress | heat_wave | Approximate — heat_stress not in table |
| Drought | drought | Direct match |
| Biodiversity loss | — | **NOT IN HAZARDS TABLE** — this is an impact, not a hazard |
| Soil degradation/erosion | — | **NOT IN HAZARDS TABLE** |
| Water stress | drought (approximate) | Not a clean match |
| Increased water demand | drought (approximate) | Not a clean match |
| Infectious disease | vector-borne_disease OR water-borne_disease | Ambiguous without context |
| Fire weather (risk of wildfires) | forest_fire OR land_fire | |
| Storm | rain_storm OR tropical_storm | Ambiguous |

**Key finding**: CDP includes non-climatic hazards (biodiversity loss, soil degradation) and impact-framed terms (water stress, increased water demand) that don't map cleanly to our climate hazard taxonomy. The agent needs a mapping table when processing CDP data.

### Action Status: CDP → Schema

| CDP Status | Schema implementation_status |
|---|---|
| Scoping | scoping |
| Feasibility finalized, but currently no finance secured | scoping |
| Feasibility finalized, and finance partially secured | pilot |
| Implementation underway with completion expected in less than one year | operational |
| Implementation underway with completion expected in more than one year | operational |
| Action in operation (targeted to sector/location) | operational |
| Action in operation (across most of jurisdiction) | operational |
| Action in operation (jurisdiction-wide) | scaling |
| Implementation complete in the reporting year | completed |

### Sectors: CDP → Schema urban_systems

CDP uses ISIC sector codes. Mapping:

| CDP Sector | Schema system_category |
|---|---|
| Water supply | water |
| Sewerage, wastewater management... | water |
| Agriculture | food |
| Forestry | nature |
| Conservation | nature |
| Electricity, gas, steam... | energy |
| Human health and social work | health |
| Real estate activities | buildings |
| Education | communication_and_community |
| Public administration... | planning_and_monitoring |
| Waste management | infrastructure |
| Transport | transportation |

### Co-benefits: CDP → Schema

CDP co-benefits are well-structured and map cleanly:

| CDP Category Prefix | Schema co_benefit.category |
|---|---|
| Economic: | economic |
| Public Health: | public_health |
| Environmental: | environmental |
| Social: | social |

### Resilience Attributes: CDP → Schema mechanisms

CDP `action_resilience_attributes` is the closest match to our mechanism dimension, but uses different vocabulary:

| CDP Attribute | Schema mechanism (approximate) |
|---|---|
| Anticipation & preparedness | monitor |
| Planning & strategy | govern |
| Natural resources | restore_regenerate |
| Infrastructural assets | harden |
| Basic services | harden |
| Community participation | adapt_behavior |
| Coordination & governance | govern |
| Distributive equity | — (no match, equity concern) |
| Backup resources and strategies | shift_risk |
| Decision-making capacity | govern |

---

## Fields CDP CANNOT populate

These schema fields will have no CDP data and must come from curated case research:

| Schema Field | Why CDP Can't Populate |
|---|---|
| mechanisms.primary_mechanism | CDP has no mechanism-of-action field |
| mechanisms.technical_components | CDP descriptions too vague for component extraction |
| evidence.outcome_indicators (specific) | CDP has percentage buckets, not specific metrics |
| evidence.failure_modes | Not asked in CDP questionnaire |
| context.barriers (specific) | Not captured |
| context.replicability | Not assessed |
| context.comparable_implementations | Not captured |
| identity.ipcc_action_type | Partially encoded in action_name (e.g., "Ecosystem-based actions:") |

---

## Fields CDP uniquely provides

These fields are well-covered by CDP but often missing from curated cases:

| Schema Field | CDP Advantage |
|---|---|
| implementation.cost | 26% fill rate with USD amounts |
| context.enabling_conditions (financial) | Detailed funding source breakdown |
| evidence.co_benefits | Structured multi-select with categories |
| action_in_climate_plan | Whether action is part of formal planning |

---

## Summary

**CDP actions can populate ~55-60% of the extraction schema** at `self_reported` confidence. The remaining ~40% (mechanisms, technical components, specific outcomes, barriers, replicability) must come from curated case library research.

**Key vocabulary mapping work needed**:
1. CDP hazard terms → hazards table mapping table (with some terms unmappable)
2. CDP ISIC sectors → urban_systems categories
3. CDP status values → implementation_status
4. IPCC action type partial extraction from CDP action_name prefix

This confirms the SPEC.md assertion: the two datasets are complementary. CDP provides breadth (11K actions, global coverage, funding data, co-benefits) while the case library provides depth (mechanism, technical detail, measured outcomes).
