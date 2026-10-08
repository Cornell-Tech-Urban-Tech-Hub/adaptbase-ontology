# AdaptBase Ontology v1.1 — top-to-bottom review

**Reviewer:** Claude Fable 5.1 (read-only review; no files edited)
**Date:** 2026-10-06
**Scope read in full:** `CLAUDE.md`, `README.md` (Future improvements), `ontology/ontology-v1.1.jsonld`, `ontology/context.jsonld`, all nine `vocabularies/*.json` + `vocabularies/README.md`, `decisions-log.md`, `framework-crosswalk.md`, both `OPUS-ONTOLOGY-REVIEW-2026-04-29-*.md`, `V1.1-CHANGE-LIST.md`, `scripts/validate_ontology.py`, plus `scripts/export/build_vocab_jsonld.py --check` (exit 0: all `.jsonld` twins are in sync) and a scratch integrity script run over the JSON (counts, domain/range, reachability, bindings, vocab cross-references).
**Also folded in** (from the core-repo agent review relayed mid-session): the researcher-behaviour effect of `vocabulary_binding` links, the 13 removed property keys still on live rows, and `alternative_names` missing from Stakeholder.

Finding IDs are `C-n` (Consistency), `L-n` (Logical soundness), `Y-n` (Clarity), `P-n` (Completeness & parsimony), `V-n` (Provenance & conventions), `A-n` (Alignment). "Advances" names the README *Future ontology improvements* item a fix would move, or `—`.

---

## 1. Overall verdict

v1.1 is structurally sound where it counts: every relationship's domain and range resolves, no type is unreachable, the metadata counts (22 / 64 / 36) are correct, the JSON-LD twins regenerate cleanly, and the v0.8 → v1.1 arc (catalog nodes hold only class-level facts; deployment context lives on Action or the asserting edge; dated status series; finance rebuilt around `FundingAllocation`) is coherent and well argued in the decisions log. The weaknesses are concentrated in three places. First, the *principle* that catalog nodes carry no place-dependent values was applied to Solution, UrbanSystem, Barrier and Vulnerability in v1.1 but **not to Hazard** (`severity`, `frequency`, `trend`, `return_period`, `climate_scenario`, `projection_year` still sit on the shared Hazard node) and not to `BLOCKS` / `REQUIRES`, whose Barrier and EnablingCondition ends are free-text instance nodes attached to shared Solutions. Second, the **vocabularies lag the ontology**: `urban-systems.json` contains Solutions (green roofs, permeable surfaces, constructed wetlands, early-warning systems, resilience hubs) as "systems", so `OPERATES_ON` can be self-referential; `mechanism_vocabulary` contains governance and financial values the Mechanism definition explicitly excludes (and a live-data check shows the vocabulary has never been applied: 807 Mechanism nodes, all singleton free-text names, `mechanism_type` set on 4 — so the real question is whether Mechanism should be a node at all); four type-level `vocabulary_bindings` name enum blocks that do not exist; and the hazard list has three pairs an extractor cannot tell apart. Third, the **supporting documents have not kept pace**: `framework-crosswalk.md` §1–2 and §4 still describe v0.1 (Actor, TimePoint, `FUNDED_BY.amount_usd`, 13 C40 categories), the metadata `design_notes` still present the retired `FinancingSource/CHANNELS_THROUGH` model as current, `vocabularies/README.md` documents a file that does not exist and a third deprecation convention, and `validate_ontology.py` is not a validator — nothing in the repo mechanically checks domain/range, bindings or counts. None of this is a BLOCKER in the sense of making the ontology unusable today, but two items (Mechanism vocabulary vs definition; Solutions inside the UrbanSystem vocabulary) are genuine self-contradictions and are marked as such.

---

## 2. Findings

### 2.1 Consistency

**C-1 · MAJOR · Four type-level `vocabulary_bindings` point at enum blocks that do not exist.**
Location: `ontology-v1.1.jsonld` — `Solution.vocabulary_bindings[{vocab:"enums", field:"ipcc_action_types"}]`, `Stakeholder.vocabulary_bindings[{vocab:"enums", field:"actor_type"}]`, `EnablingCondition.vocabulary_bindings[{field:"condition_type"}]`, `Barrier.vocabulary_bindings[{field:"barrier_type"}]`.
Evidence: `enums.json` has blocks `ipcc_action_type` (singular), `implementing_actor_type`, `enabling_condition_type`; there is no `actor_type`, `condition_type`, `barrier_type` or `ipcc_action_types`. Correspondingly the manifest rows `enums.ipcc_action_type`, `enums.implementing_actor_type`, `enums.enabling_condition_type` all show `bound_to: []`, and those four properties carry inline `values` arrays instead (so the two copies can drift — `co_benefit_category` and `municipal_program` are in the same state, see C-2). This is the same bug class fixed twice before (v0.4.1 `UrbanSystem`, v1.0 `Outcome.beneficiary_program`).
Fix: rename the four `field` values to the real block names (or rename the blocks), add property-level `vocabulary_binding` + `ab:boundToVocabulary`, and drop the inline `values`. Note the core-repo caveat: adding a `vocabulary_binding` changes how the researcher treats the property (it stops filling it until the researcher rule is updated) — do this in one pass with the core prompt change, not piecemeal.
Advances: —

**C-2 · MINOR · 36 enum properties are inline-only; 7 enum blocks are unbound duplicates of inline lists.**
Location: inline-only enums on `Hazard.{hazard_source,severity,trend,climate_scenario}`, `Stakeholder.{stakeholder_type,org_form,authority_level}`, `Jurisdiction.{climate_zone,coastal_status,income_classification}`, `Place.place_type`, `Outcome.{co_benefit_type,beneficiary_program}`, `Plan.plan_type`, `Action.spatial_scale`, `EnablingCondition.condition_type`, `Barrier.barrier_type`, `FinancialInstrument.instrument_type`, `Supplier.role`, `Vulnerability.vuln_type`, `PlanningData.{data_type,spatial_coverage}`, and 8 relationship properties (`DEPENDS_ON.dependency_type`, `SETS.priority_level`, `DEMONSTRATES_PROGRESS_ON.evidence_level`, `REDUCES.mechanism_of_reduction`, `ISSUES.adoption_status`, `EXPOSES.impact_severity`, `ADDRESSES.assessment_scope`, `BLOCKS.severity`). Unbound blocks: `ipcc_action_type`, `implementing_actor_type`, `enabling_condition_type`, `co_benefit_category`, `municipal_program`, `claim_source_type`, `claim_confidence`, `governance_relationship_type`, `financing_model` (deprecated).
Evidence: `FinancialInstrument.instrument_type` has 22 inline values *and* `enums.instrument_type` exists with the same 22 — but `FundingAllocation.instrument_type` is bound to the block while `FinancialInstrument.instrument_type` is not. `DEMONSTRATES_PROGRESS_ON.evidence_level` is inline while `Outcome.evidence_level` and `PRODUCES.evidence_level` are bound. Decision 34 noted "three inconsistent shapes" and normalised 7; the remaining 36 were left.
Fix: adopt one rule — an enum with a definition per value lives in `enums.json` and is bound; an enum with no definitions is inline. Then either give the inline lists definitions and move them, or delete the five unbound duplicate blocks. (Pair with the researcher-rule change in C-1.)
Advances: —

**C-3 · MAJOR · `Mechanism.mechanism_type` instructs the extractor to use a property that does not exist.**
Location: `Mechanism.properties[mechanism_type].note`: "use other + mechanism_type_other_description for outliers"; `enums.mechanism_vocabulary.values[other].description`: "Use with mechanism_other_description."
Evidence: Mechanism declares only `mechanism_type` and `description`. Two different non-existent property names are cited. The GC-1 convention (Decision 22: every `other` gets a `_other_description` companion) is also unmet on `FundingAllocation.instrument_type`, `FundingAllocation.instrument_class`, `FundingStream.stream_type`, `Jurisdiction.{climate_zone,coastal_status,income_classification}`, `Place.place_type`, `Stakeholder.org_form` (has one) vs `Supplier.role` (no `other` at all), `jurisdiction-kind:other`.
Fix: add `mechanism_type_other_description` (and the missing companions, or record in the decisions log that GC-1 is retired and `other` is explained in the evidence row — the FundingAllocation note already says "describe in the evidence", so pick one).
Advances: —

**C-4 · MAJOR · Cardinality declarations contradict the property notes on the same edge.**
Location: `IMPLEMENTS` — `cardinality: "many-to-one"` but `is_primary.note`: "where an Action implements several"; `ISSUES` — `many-to-one` but `notes`: "Can have multiple issuers for regional or multi-jurisdictional plans"; `SUPERSEDES` — `one-to-one` (a 2024 strategy routinely supersedes two or three earlier plans); `IMPLEMENTED_BY (Action)` — `cardinality: "many"` (not a value used anywhere else; the other 63 use `many-to-many | many-to-one | one-to-many | one-to-one`).
Fix: `IMPLEMENTS` → many-to-many; `ISSUES` → many-to-many; `SUPERSEDES` → many-to-many; `IMPLEMENTED_BY` → many-to-many. Add a cardinality enum check to the structural validator (P-10).
Advances: —

**C-5 · MINOR · Alias/alternative-name property is named three different ways and missing on the type with the most alias rows.**
Location: `Solution.alternative_names`, `Plan.alternative_names`, `Action.alternative_names` (v1.1), `Jurisdiction.aliases` (unchanged), Stakeholder — none; `solution-concepts.json` entries use `aliases`.
Evidence: core reports 228 Stakeholder rows carrying `aliases` with no declared home; Decision 39 renamed the key "on Action and Plan" only.
Fix: add `Stakeholder.alternative_names`; rename `Jurisdiction.aliases` → `alternative_names` (vocab-file `aliases` can stay — it is a different artefact). Also make `Stakeholder.name` required (it is the only named type whose name is `required: false`).
Advances: —

**C-6 · MINOR · Property schema drift inside Plan.**
Location: `Plan.plan_title`, `adoption_year`, `planning_horizon_years`, `total_actions`, `total_budget_mentioned`, `monitoring_approach`, `plan_uri`, `document_url`, `plan_status` use `label` / `definition` / `notes: ""`; every other property in the file uses `note`. `plan_status` has *both* `definition` ("draft, adopted, active, completed, superseded") and `note` ("enum (was free text)") and its `definition` lists two values (`active`, `completed`) that are not in `values` or in `enums.plan_status`.
Fix: normalise the eight Plan properties to `note`; rewrite `plan_status.definition` to the five enum values.
Advances: —

**C-7 · MINOR · Money is modelled two ways: forced-USD scalars vs amount + currency.**
Location: `Action.cost_usd`, `CapitalProject.total_capex_usd`, `annual_opex_usd`, `FinancialInstrument.principal_amount_usd`, `annual_debt_service_usd`, `Outcome.monetized_value_usd`, `ExposureUnit.asset_value` ("USD") vs `FundingAllocation.{amount,currency}` ("As stated, never converted at extraction") and `FundingStream.{max_award,max_award_currency}`.
Evidence: Decision 43 states conversion happens at read time with a dated rate; the seven `_usd` fields require conversion at extraction.
Fix: v1.2 — rename to `cost` + `cost_currency` etc. (or declare the `_usd` fields as read-time derived). Advances: *Finance follow-ons (currency conversion at read time)*.

**C-8 · MINOR · Year-field naming is inconsistent across the three "activity" types.**
Location: `Action.start_year / end_year`; `CapitalProject.start_year / completion_year`; `FundingAllocation.period_start_year / period_end_year`; `FinancialInstrument.issuance_year / maturity_year`; `Plan.adoption_year`.
Fix: pick `start_year / end_year` for activities; keep instrument/plan terms. Advances: —

**C-9 · MINOR · Vocabulary ID character sets differ per file.**
Location: `hazards.json` ids `rcc.earthquake` (dot prefix, 21 entries) and `air-borne_disease`, `vector-borne_disease`, `water-borne_disease` (hyphens); `solution-categories.json` — 46 of 101 subcategory ids contain commas, parentheses or hyphens and 8 end in a trailing underscore (`leak_detection,_water_efficiency,_and_evaporation_`), one has a typo (`commmunity_engagement_platforms…`); `urban-systems.json` sector ids `agriculture__food_systems`, `emergency__disaster_management` (double underscore); every other vocabulary uses `[a-z0-9_]`.
Evidence: these ids become IRIs (`abv:solution-categories/…`) in the `.jsonld` twins and OWL/SKOS exports; commas and parentheses in IRI local names round-trip through rdflib but are hostile to SPARQL, Neo4j labels and URL routing. The solution-categories note says vendor-grain names are "kept for id stability in adaptbase-core's vocabulary_terms".
Fix: for solution-categories, add a clean `id` and keep the legacy string as `legacy_id` with a one-time core migration — the derived-copy design (Decision 35) means only the seeder writes `subcategory_id`, so this is cheap now and expensive later. Normalise hazard hyphens. Advances: *Re-review the Solution concept list* (same pass).

**C-10 · MINOR · `_usage` strings in vocabulary files reference the pre-v0.1 extraction schema, not the ontology.**
Location: `hazards.json._usage` ("hazards.hazards_addressed[].hazard_id"), `urban-systems.json._usage` ("urban_systems.systems_affected[]"), `crf-goals.json._usage` ("outcomes.resilience_goals[]"), `enums.ipcc_action_type._usage` ("identity.ipcc_action_type.values"), `enums.enabling_condition_type._usage` ("context.enabling_conditions[].type"), `enums.mechanism_vocabulary._usage` ("mechanisms.primary_mechanism.value"), `vulnerable-populations._usage` ("Solution.target_populations[]" — moved to Action in v1.1), `enums.accreditation_modality._usage` ("FinancingSource." — renamed v1.1).
Fix: rewrite `_usage` as `Type.property` / `EDGE.property` paths, or generate them from the manifest `bound_to`. Advances: —

**C-11 · MINOR · Three deprecation conventions.**
Location: `enums.financing_model` uses `_deprecated` + per-value `replaced_by`; `solution-concepts.json._note` prescribes `status: deprecated` + `replaced_by`; `vocabularies/README.md` §Deprecating Terms prescribes `"deprecated": true` + `deprecated_reason` + `use_instead`. The context maps `_deprecated` → `owl:deprecated` and `status` → `ab:termStatus`, so only the first two are even expressible in RDF.
Fix: standardise on `status: deprecated` + `replaced_by` (+ `deprecated_in`), map `status` values in the context, and update the README. Advances: —

**C-12 · MINOR · Version strings agree; decisions-log summary table and headers do not.**
Evidence: `versions.json`, `CLAUDE.md`, `README.md`, `version_notes[0]`, `metadata.change_history[0]` all say v1.1 / 2026-10-06 ✔. But `decisions-log.md` header still says "Project: Resilience Scanner", the *Ontology Evolution Summary* table totals "21 types / 53 relationships" and lists v0.2 twice (two different v0.2s), and `References` cites "C40 Climate Hazards (13 categories, 31 hazards)".
Fix: regenerate the table from `version_notes` or delete it. Advances: —

---

### 2.2 Logical soundness

**L-1 · BLOCKER · The Mechanism definition excludes exactly the values the Mechanism vocabulary contains.**
Location: `Mechanism.definition`: "Strictly functional/operational — financial and governance mechanisms are captured by FinancialInstrument and EnablingCondition respectively." `enums.mechanism_vocabulary` contains `govern` ("Regulate, plan, coordinate, or incentivize (e.g., building codes, zoning, carbon pricing)"), `regulate` ("rules, standards, permits, or enforcement"), `shift_risk` ("Transfer, insure, or redistribute risk (e.g., parametric insurance, risk pooling)"), `adapt_behavior`.
Evidence: Decision 7 recorded the collision and deferred it; Decision 27 reaffirmed "Mechanism … is explicitly the functional/operational process"; the values were never removed. An extractor reading the definition will refuse `govern`; one reading the enum will emit it. The vocabulary also overlaps internally: `restore` vs `restore_regenerate` (both "wetland restoration"), `govern` vs `regulate`, `monitor` vs `sense_and_detect`, `absorb` vs `buffer`.
Fix (my call): keep the values and **widen the definition** — "the process by which a solution achieves its effect: physical (absorb, harden…), informational (sense, forecast, alert…), or institutional (govern, regulate, shift_risk)". Governance-as-mechanism is real (zoning *works by* regulating). Merge `restore` into `restore_regenerate`; state the `govern`/`regulate` boundary (regulate = rule + enforcement; govern = coordination/planning/incentive).
Advances: *Mechanism concept list (CQ-43)*.

**Live-data check (2026-10-06, read-only query of core `v_entities` / `v_edges`).** Mechanism *is* in the graph — 807 nodes, 871 `Solution —WORKS_BY→ Mechanism` edges (≈1 in 9 of the 7,635 Solutions) — but not as a controlled dimension: `mechanism_type`, the type's only required property, is set on **4 of 807** (3 × `other`, 1 free text "recycle water from multiple sources"); `description` is set on 779; and **all 807 canonical names are singletons** — "make a structure watertight", "let it trickle out more slowly", "island", "reflect light away", "Stormwater disconnection", "ongoing energy audits", "converting waste to biofuels" (not adaptation). The 18 vocabulary values have never been applied; the extractor writes a phrase as the node name and skips the enum. So the definition/vocabulary contradiction above is real but currently academic — nothing in the data depends on either reading — and the prior question is whether Mechanism earns a node type at all. 807 unmergeable phrases are a worse `Solution.description`.
**Recommendation (my call):** keep the dimension, lose the node. Replace `Mechanism` + `WORKS_BY` with `Solution.mechanisms: array<enum>` bound to `enums.mechanism_vocabulary` (or `mechanism_type` as a property on a `WORKS_BY`-less Solution; a node is only warranted once a Mechanism concept list exists and has something to say beyond a label). Re-judge the 807 phrases against the 18 values in core — a large share map cleanly ("water absorption", "retaining rain water" → `absorb`; "air pollution monitoring", "Early leak detection" → `monitor`/`sense_and_detect`; "insulation", "reflect light away" → `insulate`; "hardening of building systems" → `harden`; "manage surface water" → `redirect`/`absorb`) — and quarantine the rest as evidence. Do the definition widening (above) first so the enum the phrases are judged against is coherent. This moves item #4 in the change list from "fix the vocabulary" to "decide node vs property, then fix the vocabulary", and makes the README's *Mechanism concept list* item the gate for ever reinstating the node.

**L-2 · BLOCKER · `urban-systems.json` contains Solutions as systems, so `OPERATES_ON` is self-referential and the identity principle is broken on the UrbanSystem side.**
Location: `urban_ecology > blue_green_infrastructure > {constructed_wetlands "Constructed Wetlands & Bioswales", permeable_surfaces, green_roofs_walls}`; `governance_finance > emergency_management > {early_warning "Early Warning Systems (EWS)", evacuation_sheltering}`; `socioeconomic_health > social_capital > resilience_hubs`; `hydrological_water > coastal_riverine_defenses > hard_engineering "Seawalls, levees, tidal barrages"`; `governance_finance > financial_risk > insurance_markets`; `socioeconomic_health > public_health > disease_monitoring "Vector-Borne Disease Monitoring"`.
Evidence: each of these is also a solution-concept (`constructed_wetland`, `bioswale`, `permeable_pavement`, `green_roof`, `early_warning_system`, `emergency_shelter`, `resilience_hub`, `sea_wall`, `levee`, `climate_insurance`, `disease_surveillance`). The `OPERATES_ON` definition ("deployed within, protects, or modifies this urban system") makes "green_roof OPERATES_ON green_roofs_walls" legal and meaningless. The vocab README even gives "Hydrological Water → Stormwater Management → Bioswales" as the example hierarchy. Also `socioeconomic_health > public_health > vulnerable_populations` is a population group (duplicates the `vulnerable-populations` vocabulary and `ExposureUnit`), not a system.
Fix: remove the Solution-shaped systems (map them to the system they sit on: `green_roofs_walls` → `residential_fabric`/`commercial` building stock; `permeable_surfaces` → `local_streets`/`parks_plazas`; `early_warning` → `government_emergency`; `hard_engineering` → a new `shorelines_and_riverbanks` system); remove `vulnerable_populations`; record the rule "an UrbanSystem is something a city *has* regardless of adaptation; if it is also a concept it is a Solution".
Advances: — (new item; recommend adding "UrbanSystem vocabulary review" to the README list)

**L-3 · MAJOR · Two UrbanSystem sectors can never be used.**
Location: `urban-systems.json` sectors `agriculture__food_systems` and `emergency__disaster_management` have `subsectors: []`; `UrbanSystem.system_id` is `required: true` and the viewer/validation resolves `system_id` from the leaf list.
Evidence: added in v0.1.1 from corpus mining ("we will accept the new urban sector recommendation instead to tag these", decisions-log 2026-04-24) but never populated; `emergency__disaster_management` also overlaps `governance_finance > emergency_management`, `built_environment > civic_institutional > government_emergency`, `public_health > emergency_medical` and `informal_service_systems > community_disaster_response`.
Fix: either populate both with ≥2 systems each (agriculture: `peri_urban_farmland`, `urban_agriculture_sites`, `food_distribution`; emergency: move `early_warning`, `evacuation_sheltering`, `emergency_medical`, `government_emergency` under it) or delete them and the two `sector` enum values. My call: populate agriculture, consolidate emergency.
Advances: —

**L-4 · MAJOR · Hazard is the one catalog node that still carries one-place facts.**
Location: `Hazard.{frequency, severity, trend, return_period, climate_scenario, climate_scenario_other_description, projection_year}` — seven of its ten properties.
Evidence: Decision 35/37's rule — "a catalog node never holds a value that depends on one place or one plan" — moved `condition/capacity/service_coverage`, `severity_score`, and the three vulnerability scores to edges, but "coastal_flood has return_period 1-in-100 under SSP5-8.5 by 2050" is Miami's fact, not the class's; the second city to assert a different value is a conflict on a node shared by every plan in the corpus. The Hazard `notes` do not even mention the issue. `AFFECTED_BY (Jurisdiction → Hazard)` already carries `indicators` (JSONB) and `source_dataset` for exactly this content, and `Plan ADDRESSES Hazard` carries `assessment_scope/assessment_year`.
Fix: move the seven properties to `Plan ADDRESSES Hazard` (plan-grain, where `climate_scenario`/`projection_year` sit naturally beside `assessment_year`). Hazard keeps `hazard_id`, `hazard_category`, `hazard_source`, `c40_arup_category`. This is the one place the v1.1 principle was not finished.
*Revised 2026-10-07 (Anthony; see §5.2):* this originally read "to `AFFECTED_BY` (jurisdiction-grain) and/or `Plan ADDRESSES Hazard`". `AFFECTED_BY` is dropped as a destination. It is one edge per jurisdiction–hazard pair, shared by every plan for that city and by every reference dataset, so two plans' values would collide on it, which is L-4's problem one level down.
Advances: — (new; the biggest single consistency-with-principle item)

**L-5 · MAJOR · `BLOCKS` and `REQUIRES` attach instance-grain nodes to the shared Solution.**
Location: `BLOCKS (Barrier → Solution)`, `REQUIRES (Solution → EnablingCondition)`.
Evidence: Barrier and EnablingCondition are free-text nodes (`barrier: string`, `condition: string`) with no vocabulary; the extract hints give one-city examples ("community opposition", "regulatory barrier prevents deployment of green infrastructure in the right-of-way", "needs technical capacity in the water utility"). Decision 33 classed both edges as "catalog↔catalog laterals … untouched", but neither Barrier nor EnablingCondition is a catalog type (no vocab, no merge key). The leak signature Decision 33 describes (two-hop traversal transfers one city's fact to every city on the Solution) applies: "What blocks green roofs in Legazpi?" → Houston's HOA rules.
Fix: either (a) make Barrier/EnablingCondition catalog types by binding `barrier`/`condition` to a small controlled list (then BLOCKS/REQUIRES are legitimately class-level: "green roofs REQUIRE structural load capacity"), or (b) re-anchor BLOCKS to `Barrier → Action` beside FACES and REQUIRES to `Action → EnablingCondition`. My call: (a) — the class-level knowledge ("what does this kind of solution generally need?") is the valuable one, and FACES already covers the instance grain. Until then, add the precedence rule used for PRODUCES/RESULTS_IN to the hints.
Advances: —

**L-6 · MAJOR · `PRODUCES` / `RESULTS_IN` duplicate the Outcome node's own required properties.**
Location: `Outcome.outcome_type (required)`, `Outcome.evidence_level`; `PRODUCES.properties.outcome_type (required)`, `PRODUCES.evidence_level`; `RESULTS_IN.outcome_type (required)`, `RESULTS_IN.evidence_level`.
Evidence: `PRODUCES` and `RESULTS_IN` are declared `one-to-many` (an Outcome has one producer), so the edge value and the node value can only ever agree or conflict. Decision 37's "no duplicate data" rule was applied to IMPLEMENTS but not here.
Fix: drop `outcome_type` and `evidence_level` from both edges. Advances: —

**L-7 · MAJOR · `ExposureUnit` and `Vulnerability` have no identifying property.**
Location: `ExposureUnit.properties` = `population_count, asset_value, vulnerable_ratio, social_capital_index, affected_group` — all optional; `Vulnerability.properties` = `vuln_type, vuln_type_other_description, affected_group` — all optional.
Evidence: both are instance types (Decision 33: "ExposureUnit is instance-typed and place-bound"), yet neither has a required `name` or `description`. An ExposureUnit with only `population_count: 50000` cannot be displayed, de-duplicated, or re-identified by a second extraction. Every other instance type (Action, Plan, CapitalProject, Outcome, Indicator, Barrier, EnablingCondition, PlanningData, Place) has a required name or description.
Fix: add `name` (required) and `description` to both. Advances: —

**L-8 · MAJOR · `Place.place_type` cannot type the sites the new `DEPLOYED_IN → Place` edge is defined for.**
Location: `DEPLOYED_IN (Action → Place).definition`: "a park, river, creek, watershed, street or facility"; `Place.place_type.values`: `watershed, corridor, coastline, site, park, infrastructure_zone, other`.
Evidence: river, creek, street and facility — four of the six examples in the edge definition, and the SuDS-on-Via-Pacini example in its hint — fall to `site` or `other`. `Place` also lacks `Place WITHIN Place` (a creek within a watershed, a park within a district) while Jurisdiction has `WITHIN` self-nesting.
Fix: add `waterbody`, `street`, `facility` (and probably `neighbourhood_area` for non-administrative named areas) to `place_type`; add `WITHIN (Place → Place)` under the existing `ab:within` umbrella. Advances: — (follows Decision 44)

**L-9 · MAJOR · Three hazard pairs share matching terms, so an extractor has no rule to pick one.**
Location: `hazards.json` — `extreme_hot_weather` (undrr_terms "extreme heat") vs `heat_wave` ("heat wave", "heat stress", "extreme heat event"); `extreme_cold_weather` vs `cold_wave`; `subsidence` vs `rcc.subsidence_chronic` (**both** list "land subsidence"); `air-borne_disease` vs `rcc.disease_outbreak` (both list "epidemic" and "pandemic"); `rcc.sea_level_rise` is named "Sea Level Rise / Coastal Erosion" (two hazards, one id; erosion is a geohazard process, SLR a slow-onset environmental one); `drought` absorbs "water stress" (already in `known_gaps`).
Evidence: the CDP crosswalk has to invent a distinction ("Heat stress" → `heat_wave`, "Extreme heat" → `extreme_hot_weather`) that `hazards.json` itself does not state. Decision 42 declined parents; it did not address leaf overlap.
Fix: add a one-line `definition` to every hazard (none has one — see Y-3) with the boundary stated (heat_wave = multi-day event above a threshold; extreme_hot_weather = chronic/seasonal regime), de-duplicate the shared `undrr_terms`, split `rcc.sea_level_rise` into `sea_level_rise` and `coastal_erosion`, and add `water_stress` as a sibling of `drought`. Advances: —

**L-10 · MAJOR · `ISSUES.adoption_status` is a second, different plan-status enum.**
Location: `ISSUES (Stakeholder → Plan).adoption_status: draft | adopted | revised` vs `Plan.plan_status: draft | adopted | under_review | superseded | expired` (+ dated observations, Decision 40).
Evidence: the same fact ("the plan is a draft") can be written in two places with incompatible value sets and only one of them is dated.
Fix: remove `adoption_status` from ISSUES (keep `claim_ids`). Advances: —

**L-11 · MINOR · `PRESCRIBES.implementation_stage` is Action.status at a grain v1.1 says not to use.**
Location: `PRESCRIBES.notes`: "when a named programme is behind the prescription, it is an Action (SPECIFIES + IMPLEMENTS) and this edge is not used"; `PRESCRIBES.implementation_stage` + `_observations` + `implementation_timeline` + `is_priority` all duplicate Action properties.
Evidence: after Decision 35/39 a prescription with any implementation detail *is* an Action; what remains on PRESCRIBES is the bare "the plan calls for X". The dated-observation machinery on this edge will rarely fire.
Fix: keep `local_label`, `is_priority`, `claim_ids`; drop `implementation_stage(_observations)` and `implementation_timeline` in v1.2 (check live counts first). Advances: —

**L-12 · MINOR · Required-but-derivable fields are declared inconsistently.**
Location: `Hazard.hazard_category (required)`, `UrbanSystem.sector (required)`, `UrbanSystem.subsector`, `ResilienceGoal.dimension (required)` are all fully determined by the sibling id, yet only `Solution.{category_id,subcategory_id,ipcc_action_types}` carry `derived_from`. v0.3 removed `hazard_name`/`goal_text` as "denormalized labels"; the category/dimension fields are the same thing.
Fix: mark the four as `derived_from: <id field>`, `required: false`, seeder-written. Advances: —

**L-13 · MINOR · `REDUCES.mechanism_of_reduction` re-encodes the risk triad as an enum.**
Location: `REDUCES (Solution → Vulnerability).mechanism_of_reduction: reduces_exposure | reduces_sensitivity | increases_adaptive_capacity | multi_pathway`.
Evidence: `reduces_exposure` is the `REDUCES_EXPOSURE` edge (now Action-grain); putting it as a value on the class-grain `REDUCES` edge lets the class assert what Decision 33 moved to the instance.
Fix: restrict to `reduces_sensitivity | increases_adaptive_capacity | both`. Advances: —

**L-14 · MINOR · `source_tier` derivation from `stakeholder_type` is under-specified.**
Location: `FundingAllocation.source_tier.note`: "derived from the PROVIDED_BY target's stakeholder_type when one is"; `Stakeholder.stakeholder_type` has no `philanthropic` value (foundations are `ngo`?), and `community`, `academic` have no tier.
Fix: add `philanthropic` to `stakeholder_type` (and `other`), and write the 9→8 mapping table in the note or in `enums.source_tier._note`. Advances: *Finance follow-ons*.

---

### 2.3 Clarity

**Y-1 · MAJOR · The CRF goals have names only; the extractor is asked to map plan goals onto 22 labels with no definitions.**
Location: `crf-goals.json` — every goal has `id`, `name`, `dimension`; no `description`. `ResilienceGoal.extract_hint` examples ("ensure continuity of critical services") match no goal name (closest `crf_goal_13` "Effective operation & maintenance of utilities" or `crf_goal_15` "Protective infrastructure").
Evidence: Decision 41/42 report 78 % of ResilienceGoal rejects were plan headings; with `local_label` that wording now has a home, but the mapping step still has nothing to map *to* beyond a title. Adjacent goals (`crf_goal_01` housing vs `crf_goal_15` protective infrastructure for a flood-proofing programme; `crf_goal_09` security vs `crf_goal_21` emergency preparedness) have no boundary text.
Fix: add the CRF 2024 one-paragraph goal descriptions (they exist in the Arup document) and an `includes`/`excludes` line per goal. Advances: —

**Y-2 · MAJOR · Supplier vs Stakeholder(private_sector) has no boundary and the hints give the same example to both.**
Location: `Supplier.extract_hint`: "engineering services from AECOM"; `IMPLEMENTED_BY (CapitalProject).extract_hint`: "design-build by AECOM"; `Stakeholder.definition`: "Commercial suppliers are modeled separately as Supplier"; `Stakeholder.stakeholder_type` includes `private_sector`.
Evidence: the same firm is a Supplier (SUPPLIES Action) and a Stakeholder (IMPLEMENTED_BY, role "design-build contractor"). `Supplier.role` (`manufacturer, system_integrator, service_provider, consultant`) overlaps `IMPLEMENTED_BY.role` free text. Decision 32 merged GovernanceStructure into Stakeholder on exactly this reasoning ("two types with overlapping extents produce systematic inter-annotator disagreement").
Fix (my call): fold Supplier into Stakeholder (`stakeholder_type: private_sector`, optional `supplier_role`), keep `SUPPLIES` as `Stakeholder → Action`. Advances: —

**Y-3 · MAJOR · Vocabulary entries without definitions: hazards (50/50), urban systems (74/74), solution subcategories (99/101), CRF goals (22/22), several enum blocks.**
Location: `hazards.json` (only `undrr_terms`, no definition); `urban-systems.json` (one-line `examples` only); `solution-categories.json` (names only except EbA/CbA `_note`); `enums.{implementing_actor_type, enabling_condition_type, co_benefit_category, asset_class, municipal_program}` (name only).
Evidence: `solution-concepts.json` shows the right pattern (every entry has `definition`, `aliases`); the tiers above it do not. `hazard_id` is "identity-grade, like Hazard.hazard_id" per the Solution note — but Hazard has less definitional support than Solution.
Fix: one `definition` line per term, starting with hazards and urban systems (the two bound to required properties). Advances: *Re-review the Solution concept list* (subcategories).

**Y-4 · MAJOR · Finance-flavoured Solution concepts vs finance types: no rule says when "insurance" is a Solution and when it is a FundingAllocation.**
Location: concepts `climate_insurance` (aliases "insurance scheme"), `resilience_lending` (aliases "revolving loan fund", "PACE financing"), `disaster_contingency_fund`, `resilience_incentive`, `payments_for_ecosystem_services` vs `instrument_type: insurance, revolving_fund, loan`, `instrument_class: risk_transfer`, `stream_type: fund`, `FinancialInstrument.definition` ("a bond issue, a loan, a lease").
Evidence: "the city established a $5M disaster contingency fund" is simultaneously an Action IMPLEMENTS `disaster_contingency_fund` and a FundingStream(`stream_type: fund`). Decision 43 settled generic-kind-vs-node for instruments but not Solution-vs-finance-node.
Fix: add a boundary note to `FundingStream` and to the five concepts: a finance programme is a **Solution** when the plan proposes to *create or expand* it as an adaptation measure (the city's own action) and a **FundingStream/Allocation** when money is *drawn from* it to pay for something else; both can be true and should then both be recorded. Advances: *Finance follow-ons*.

**Y-5 · MINOR · `action_status` definitions let one word land on two values.**
Location: `enums.action_status` — `committed`: "Adopted and resourced … delivery has not begun"; `completed`: "Done: delivered, **adopted**, established, launched". `funding_status.committed` ("funder has committed; nothing awarded") vs `awarded` ("Formally awarded or appropriated") — "committed" and "awarded" are used interchangeably in US grant language.
Fix: in `completed`, replace "adopted" with "adopted (of a policy or ordinance, when adoption is the deliverable)"; in `funding_status`, add "use `committed` only when the source distinguishes commitment from award". Advances: —

**Y-6 · MINOR · Definitions by exclusion / by example only.**
Location: concept `hazard_mapping.definition`: "Mapping hazard extent and probability other than flood and heat"; `emergency__disaster_management` sector: "Distinct from general governance by emphasizing operational readiness"; `Supplier.definition` (list of roles); `Indicator.definition` (one example); `EnablingCondition.definition` vs `Barrier.definition` differ only by the words "required for" / "impedes" with identical type enums and no guidance on "absence of X" (is "lack of funding" a Barrier(financial) or a missing EnablingCondition(financial)? The crosswalk §4.2 maps the same RCC stress to both).
Fix: state the EnablingCondition/Barrier rule (Barrier = the source names an obstacle; EnablingCondition = the source names a prerequisite; "lack of X" is a Barrier); give `hazard_mapping` a positive definition. Advances: —

**Y-7 · MINOR · `jurisdiction-kind` crosses the Jurisdiction/Place and Jurisdiction/Stakeholder lines.**
Location: `jurisdiction-kind:neighborhood` — "Smallest recognized administrative **or community-defined** area"; `district` examples include "Dharavi (Mumbai)" (a slum, not an administrative unit); `special_district` ("South Florida Water Management District") — the same entity is a `Stakeholder(utility)` when it IMPLEMENTS or ADMINISTERS and a Jurisdiction when it is a territory.
Evidence: `Jurisdiction.definition` requires a Wikidata QID and administrative status; `Place.definition` covers non-jurisdictional features.
Fix: restrict `neighborhood` to administratively recognised units; add a one-line note on `special_district` (territory → Jurisdiction; the authority → Stakeholder GOVERNS it). Advances: —

**Y-8 · MINOR · Solution-concept IPCC typing is inconsistent for monitoring/digital concepts.**
Location: `flood_monitoring_network`, `asset_monitoring`, `digital_twin`, `heat_stress_monitoring`, `climate_monitoring_network`, `hydrological_modelling`, `heat_mapping` → `ipcc_action_types: ["social"]`; `wildfire_detection` → `["structural_physical","social"]`; `enums.ipcc_action_type.social` = "Educational, informational, behavioral".
Evidence: sensor networks are structural/technological under AR6 Ch.14 (which has an "informational" sub-type under social); the current assignment is defensible only with that note. `prescribed_burning` sits under category `buildings`.
Fix: add an `_note` on `ipcc_action_type.social` saying informational systems are typed `social`; move `prescribed_burning` to `nature`. Advances: *Re-review the Solution concept list*.

**Y-9 · MINOR · Copy-paste notes that do not fit the edge.**
Location: `DEMONSTRATES_PROGRESS_ON.local_label.note`: "The **plan's** own goal wording" (the source is an Outcome); `FUNDS (Action/CapitalProject).extract_hint` identical text on both; `DEPLOYED_IN (Place)` identical text on both rows; `Barrier.notes` still says "Barriers include a 'political' type not present in enabling conditions" (false since v0.4.1) and "Properties capture severity, affected stakeholders" (moved in v1.1).
Fix: edit. Advances: —

---

### 2.4 Completeness and parsimony

**P-1 · MAJOR · No `Claim`/`Source` type, although "claims as provenance" is a stated design principle and two enum blocks exist for it.**
Location: `enums.claim_source_type`, `enums.claim_confidence` (unbound); `*_observations[].source_type` ("follows enums.claim_source_type"); every edge's `claim_ids: array<uuid>`; `context.jsonld` maps `claim_ids` → `prov:wasDerivedFrom` and `evidence_cases` (declared on no type).
Evidence: the ontology references a Claim with `source_type`, `confidence`, source URL and quote (Decision 10, v0.1 release note) but never defines it, so the JSON-LD/OWL export has `prov:wasDerivedFrom` pointing at untyped UUIDs and the two enum blocks are dangling. This is a dead end in the provenance path at the ontology layer (it is presumably closed in core's evidence table, but the ontology is published as the schema).
Fix: add a minimal `Claim` type (`claim_id`, `quote`, `source_url`, `source_type`, `confidence`, `document_date`, `page`) typed `prov:Entity`, bind the two blocks, and declare that node properties trace via `_observations[].claim_ids` or the evidence row. Advances: — (recommend adding to README list)

**P-2 · MAJOR · No home for a specific hazard *event* (the 2017 flood, the 2025 heat wave).**
Location: `Hazard` is a shared class; `Outcome.extract_hint`: "system failed during extreme heat event"; `RESULTS_IN.extract_hint`: "failed to reach elderly residents during the 2025 heat wave"; `AFFECTED_BY` is dataset-grained.
Evidence: plans and progress reports anchor outcomes, status changes and funding (post-disaster HMGP awards) to named events; today that is free text in `description`. Not raised by the Opus reviews (they asked for compound hazards, which was deferred).
Fix: v1.2 candidate — `HazardEvent` (name, hazard_id, jurisdiction, start/end date, losses) with `INSTANCE_OF → Hazard`, `OCCURRED_IN → Jurisdiction`, and `TRIGGERED_BY (Action|FundingAllocation → HazardEvent)`. Low extraction cost (events are proper-named). Advances: — (new)

**P-3 · MAJOR · Bloat: enum blocks and properties with no consumer.**
Location: `enums.governance_relationship_type` (six relationship *names* — `MANDATES`, `ISSUED_BY`, `IMPLEMENTS`… — from the student schema; unbound; two of its values collide with live predicate ids); `enums.financing_model` (deprecated; still counted in `vocabularies_count: 36`); `Hazard.hazard_source` (vocabulary-provenance flag, derivable from the id prefix); `Hazard.c40_arup_category` (derivable from `hazards.json`); `Outcome.beneficiary_program` + `enums.municipal_program` (never cited in any CQ or decision since v0.2; overlaps `asset_class` 9/11 values); `FundingStream.accreditation_modality` (AF/GCF-only, 8 values, `not_applicable` for every US stream); `Jurisdiction.codes`, `Jurisdiction.admin_level` (fine, but `population`/`population_year` on Jurisdiction duplicate what Wikidata resolves at read time); `CapitalProject.is_climate_relevant` ("Not an extraction-time field").
Fix: delete `governance_relationship_type`; move `financing_model` to a `deprecated/` section outside the manifest count; mark `hazard_source`, `c40_arup_category` as `derived_from: hazard_id`; decide `beneficiary_program` on first real use (I would cut it). Advances: —

**P-4 · MAJOR · Solution-categories: the tier above the concepts has not been reviewed to the same rule as the concepts.**
Location: `solution-categories.json`. (a) **Duplicate after v1.1:** `governance_and_policy > codes_and_standards` + `land_use_and_zoning` vs `buildings > building_code_and_permit_management,_code_enforcement,_and_land_use_planning` (concept `resilient_building_code` is filed under the latter, `hazard_zoning` under the former). (b) **Factual error:** `buildings > reflective_coatings_(cool_roof,_green_roof)` — a green roof is not a reflective coating; `green_roof` concept is nonetheless filed there. (c) **Same thing in three places:** permeable surfaces (`infrastructure > permeable_surfaces`, `nature > natural_water_drainage_(bioswales,_rain_gardens,…)`, and the urban-systems term); early warning (`communication_and_community > early_warning_systems_and_alerts`, `water > water_level_monitoring_and_alerting`, `health > heat_stress_monitoring`, `planning_and_monitoring > climate_analytics,_hazard_forecasting`); relocation (`infrastructure > infrastructure_planning_and_relocation`, `governance_and_policy > retreat_and_buyouts`, `planning_and_monitoring > migration_and_resettlement_management`); wildfire (`buildings > wildfire_resilience_systems` vs `planning_and_monitoring > wildfire_prediction,_detection_and_suppression`). (d) **24 subcategories have no concept**, including `codes_and_standards` (new in v1.1) and `fleet_electrification_and_charging_systems`, `vehicle_to_grid…`, `virtual_power_plants…`, `building_management_systems_for_energy_efficiency…` — the mitigation/tech-vendor families Decision 35 explicitly dropped at concept level but kept at subcategory level. (e) `framework_mappings.gcom_hazard_focus` uses the retired 13 C40 category ids (`wave_action`, `insects_and_microorganisms`) and the string `"cross-cutting"` inside a hazard-id array; `governance_and_policy.gcom_hazard_focus: []`.
Fix: in the concept re-review pass, apply "if no concept can live here, the subcategory goes", merge the duplicates listed, rename `reflective_coatings…` → `roof_treatments` (or move `green_roof` under `nature`), and re-key `gcom_hazard_focus` to HIPs cluster ids. Advances: *Re-review the Solution concept list*.

**P-5 · MAJOR · Identity-not-function: honoured at concept level, leaky at category level.**
Location: `solution-categories.json` categories are mostly *sectors* (`water`, `food`, `buildings`, `energy`, `transportation`, `health`) — i.e. *where* a solution acts (which is what `OPERATES_ON UrbanSystem` is for) — while two are *functions* (`planning_and_monitoring`, `communication_and_community`) and `finance`/`governance_and_policy` are *instrument kinds*. Function-named subcategories: `damage_recovery_(flood,_fire,_cyclone)`, `disaster_response_logistics`, `infrastructure_monitoring`, `transportation_monitoring`, `water_demand_management`, `heat_action_planning`, `supply_chain_agility_and_visibility`.
Evidence: the README promises "classified by what they ARE"; the concept layer delivers it (`sea_wall`, `rain_garden`); the category layer mixes three axes. The practical cost: `category_id` is now derived from `concept_id` (Decision 35), so a wrong category axis costs nothing at extraction but every category-level query ("share of nature-based solutions") inherits it.
Fix: when the concept list is re-reviewed, re-derive categories on one axis. My call: keep the sector axis (it is what practitioners filter by) and state that explicitly ("tier 1 = the sector the solution belongs to; function is on `WORKS_BY`; the system acted on is `OPERATES_ON`"), folding `planning_and_monitoring`/`communication_and_community` into `governance_and_policy` and `health`. Advances: *Re-review the Solution concept list*.

**P-6 · MINOR · Free-text properties that duplicate a node type or vocabulary.**
Location: `FACES.affected_stakeholder: string` (vs Stakeholder); `PlanningData.data_source: string` ("Organization or agency that produced this data" — vs Stakeholder via a `PRODUCED_BY` edge); `PARTICIPATES_IN.participation_role` example "funder" (now `PROVIDED_BY`); `Plan.total_budget_mentioned: string` (vs FundingAllocation); `CapitalProject.funding_year_breakdown: string` (vs `FundingAllocation.period_*` + FUNDS); `IMPLEMENTED_IN.{zone_type,land_use_type}: string` (vs Place / urban-systems); `Indicator.data_source: string`.
Fix: convert the first two to edges; remove "funder" from the example; mark the budget strings as legacy pending FundingAllocation fill rates. Advances: *`IMPLEMENTED_IN` deployment properties*.

**P-7 · MINOR · Overlaps inside enum blocks.**
Location: `co_benefit_category`: `economic` vs `revenue_stability`, `operational_cost_reduction`, `tax_base_protection`, `asset_protection` (four sub-kinds of economic with no parent link); `evidence_level` (`anecdotal, measured, rigorously_evaluated`) vs `claim_confidence` (`anecdotal, measured, modeled, self_reported, expert_assessment`) — two scales sharing two values; `Vulnerability.vuln_type` (`poverty`, `housing_insecurity`, `gender_inequality`) vs `vulnerable-populations` (`low_income_households`, `tenure_insecure_residents`, `women_and_girls`) — the condition and the group are the same extraction target; `Hazard.severity` and `EXPOSES.impact_severity` carry identical value lists.
Fix: add `parent` on the four finance co-benefits; document the evidence_level/claim_confidence split (outcome-strength vs claim-method); write the vuln_type-vs-population rule ("vuln_type is the driver, affected_group is who"). Advances: *population-group concept node*.

**P-8 · MINOR · Gaps in `urban-systems.json` that the asset_class enum already names.**
Location: `asset_class` has `solid_waste`, `schools`, `public_buildings`, `coastal_protection`; urban-systems has only `informal_solid_waste`, no formal solid-waste system, no `public_buildings` beyond `government_emergency`, no housing-stock-as-asset beyond density classes, no `cemeteries/burial`, no `cultural_heritage` (a recurring plan target).
Fix: add `solid_waste_management` subsector (collection, landfill, transfer) under `hydrological_water` or a renamed `utilities` sector; add `cultural_heritage_sites` under `built_environment`. Advances: —

**P-9 · MINOR · Stakeholder lacks an identity key, which is why `ADMINISTERED_BY → Jurisdiction` had to exist.**
Location: `Stakeholder.properties` (no `wikidata_qid`, no `ror_id`, no `lei`); `ADMINISTERED_BY (FundingStream → Jurisdiction).definition`: "when the government Stakeholder has no verified id".
Fix: add optional `wikidata_qid` (and `ror_id` for academic/NGO) to Stakeholder; once filled, the Jurisdiction fallback row can be retired. Advances: *Finance follow-ons (FundingAward registry with external ids)*.

**P-10 · MAJOR · No structural validator exists; `scripts/validate_ontology.py` is a v0.3 LLM experiment.**
Location: `scripts/validate_ontology.py` — docstring "Validate ontology v0.3 by LLM-assisted population"; default `--ontology ontology/draft-v0.json` (deleted in Decision 19); hard-codes `phase2_nodes = ["Vulnerability","TimePoint","Infrastructure","ExposureUnit"]` and `EXPERIENCES_VULN`, `IMPROVES`, `REPORTS_TO`; requires Supabase + Anthropic keys.
Evidence: every mechanical finding in this review (C-1, C-4, L-6, L-10, manifest `bound_to` rows citing the removed `PRODUCES(CapitalProject->Outcome)`, three hazard `undrr_terms` collisions, 24 concept-less subcategories) is a 20-line check. CLAUDE.md tells authors to "run `uv run scripts/validate_ontology.py`"? — no, it lists it under `scripts/` as "validate_ontology.py" with no caveat.
Fix: replace with `scripts/check_ontology.py` (pure-Python, no network): domain/range ∈ types; cardinality ∈ enum; every `vocabulary_binding.vocab/field` resolves; inline `values` == bound block; manifest `terms_count` and `bound_to` resolve; counts match; every vocab id matches `^[a-z0-9_]+$` (or the agreed pattern); no duplicate aliases/undrr_terms across entries; every concept's subcategory→category agrees; `build_vocab_jsonld.py --check`. Wire into the Pages CI step. Advances: —

---

### 2.5 Provenance and modelling conventions

**V-1 · MAJOR · `claim_ids` is required on 34 edges and optional on 30, with no stated rule.**
Location: optional on `RESULTS_IN, SPECIFIES(×2), IMPLEMENTS, PURSUES, COVERS, ADDRESSES(×3), SUPERSEDES, TARGETS(×3), ENGAGES, GENERATES, LOCATED_IN, SHIFTS_RISK_TO, GOVERNS(×2), COORDINATES_WITH, BLOCKS, MEMBER_OF, DEPLOYED_IN(×4), REALIZES, AFFECTED_BY`; required on the rest.
Evidence: Decision 10: "Relationships: claim_ids (required)"; Decision 30: "every new row carries claim_ids (optional), consistent with the action/plan-grain convention" — but `FUNDS`, `PROVIDED_BY`, `ADMINISTERED_BY` (v1.1, action-grain) are required, and `MITIGATES` (class-grain) is required. There is no grain pattern. `LOCATED_IN` is optional because it is auto-emitted; that is the only principled case.
Fix: make `claim_ids` required everywhere except edges the pipeline derives (`LOCATED_IN`, the Jurisdiction `WITHIN` hierarchy from Wikidata, `AFFECTED_BY` from datasets), and say so in a design note. Advances: —

**V-2 · MAJOR · Node-level values have no declared provenance path.**
Location: every type's `properties` (e.g. `Action.cost_usd`, `Plan.adoption_year`, `FundingAllocation.amount`) — no `claim_ids`; only the seven `*_observations` arrays carry per-value `claim_ids`; `evidence_cases` is mapped in the context but declared on no type.
Evidence: the README says "Every value can trace back to a claim with a source URL"; at the ontology layer only edge values and dated observations can. The `FundingAllocation.amount` — the single most contested number in the model — has no in-schema provenance slot.
Fix: either declare a node-level `claim_ids` convention once (design note: "every node property value is backed by an evidence row keyed (node_id, property); `claim_ids` on nodes is implicit") or add `claim_ids` to the instance types. Advances: —

**V-3 · MAJOR · Dated-status coverage is incomplete and the observation object is not in the context.**
Location: Decision 40 covers `Action.status`, `Action.financing_status`, `CapitalProject.{construction_phase,financing_status}`, `Plan.plan_status`, `PRESCRIBES.implementation_stage`, `FundingAllocation.funding_status`. Not covered though equally time-varying: `Hazard.{severity,trend}` (see L-4), `FinancialInstrument.credit_rating`, `Jurisdiction.{climate_zone? no; income_classification yes}`, `TARGETS.condition` (a system's condition changes between plans — it was moved to the edge in v1.1 without a date), `Indicator.measured_value` (has `recorded_year`, fine). The observation element keys `value`, `as_of`, `as_of_basis`, `source_type` are not terms in `context.jsonld`, so in the RDF export the series is an opaque blank node with no predicates (there is no `@vocab`; undefined keys are dropped by JSON-LD processors).
Fix: add `TARGETS.condition_observations` (or `as_of` on TARGETS) and `credit_rating_observations`; add the four keys + `observations` container to the context (`ab:observationValue`, `ab:asOf` typed `xsd:gYearMonth`, `ab:asOfBasis`, `ab:sourceType`). Advances: —

**V-4 · MINOR · JSON-LD context gaps and collisions.**
Location: keys present in `ontology-v1.1.jsonld` but not in the context: `design_notes`, `topic`, `date`, `text`; in `solution-categories.json`: `c40_action_categories`, `gcom_hazard_focus`, `iclei_milestone`, `iclei_pathways`, `sdg_goals`; in `solution-concepts.json`: `unmapped_cdp_labels`, `was`. Both `definition` and `description` map to `rdfs:comment`, so a type's definition and a property's description are indistinguishable in RDF; `summary` also → `rdfs:comment`. `type` → `ab:kind` while `@type` is also used — fine but worth a comment. The `enums.json` twin relies on a file-local `@vocab` fallback (Decision 34) which the other files do not have, so the same key is an IRI in one file and dropped in another.
Fix: add the missing terms; map `definition` → `skos:definition`, keep `description` → `rdfs:comment`, `summary` → `dcterms:description`. Advances: —

**V-5 · MINOR · Stale design notes in `metadata.design_notes` describe retired models as current.**
Location: `design_notes["Resilience Finance — Five-Axis Split (v0.2)"]`: "The full project-level financing chain is now: FinancingSource ←FUNDED_BY← CapitalProject →USES_INSTRUMENT→ FinancialInstrument ←CHANNELS_THROUGH← FinancingSource" (all three retired in v1.1); `["Action-level CDP edges & FUNDED_BY landing (v0.6)"]`; `["Solution vs Action"]` cites `CONTAINS_ACTION` and `TARGETS_GOAL` (never existed under those ids — `SPECIFIES`, `PURSUES`); `["Epistemic Hierarchy"]` cites `SETS_GOAL`/`TARGETS_GOAL`; `["CapitalProject Edge Economy"]` cites `PROTECTS ExposureUnit` and `REDUCES_EXPOSURE via Solution`. Type/edge `notes` also still cite `FUNDED_BY` 22×, `FinancingSource` 22×, `GovernanceStructure` 14×, `Location` 5× (in `DEPLOYED_IN` notes "the duplicate DEPLOYED_IN row … Action → Location"), `Hazard.vocabulary_bindings.note` → "alignment/framework-crosswalk.md" (directory does not exist), `FundingStream.accreditation_modality.note` → "Distinct from source_type".
Evidence: Decision 41 fixed exactly one such reference (`TARGETS_GOAL` in `CONTRIBUTES_TO`); the design notes were not swept. If `notes` reach extraction prompts, the extractor is told about edges it cannot emit.
Fix: add a `superseded_by`/`status: historical` flag on design notes, or rewrite them to v1.1; grep-sweep `notes` for the retired ids (the scratch check in P-10 can gate this). Advances: —

**V-6 · MINOR · Removed property keys still on live rows (core-repo report).**
Location: 10 removed keys on live `Solution`, `Barrier`, `UrbanSystem`, `FinancialInstrument` nodes (`year_of_deployment`, `maturity_level`, `equity_focus`, `target_populations`, `severity_score`, `affected_stakeholder`, `condition`, `capacity`, `service_coverage`, `amount_usd`/`issuer`) and 3 on `USES_INSTRUMENT` edges (`amount_usd`, `share_percent`, `financing_model`).
Evidence: v1.1 declared the new homes (`FACES`, `TARGETS`, `FundingAllocation`) but the migration note in V1.1-CHANGE-LIST §5.2 ("mark the removed Solution keys deprecated until the data repair has cleared the last row") covers only Solution.
Fix: the v1.2 change list should carry, per removed key, either the target edge/property and a backfill rule or an explicit "drop" with reason; the ontology can help by adding `replaced_by` metadata on removed properties in `version_notes.changes` (a `removed` entry with `moved_to`). Advances: —

---

### 2.6 Alignment with stated principles and external frameworks

**A-1 · MAJOR · `framework-crosswalk.md` is a v0.1 document with two current sections grafted on.**
Location: header "Version 0.1 · 2026-04-23 · Status: Draft"; §1 "C40/Arup — 13 categories, 31 hazards" (replaced by HIPs in v0.4), "`PRESCRIBES.implementation_stage` — Gap" (added v0.3), "Funding mechanism → `FinancialInstrument`"; §2 cites `Actor`, `REPORTS_TO`, `PUBLISHED_AT`, `EXPERIENCES_VULN`, `SETS_GOAL`, `Plan -[ESTABLISHES]-> Policy`, `Solution -[IMPLEMENTED_IN]-> City`, `Solution -[FACES]-> Barrier`, `Indicator -[RECORDED_AT]-> TimePoint`, "ICLEI's action concept = our Solution"; §3 GCoM table cites `FUNDED_BY.amount_usd`, `FinancingSource.source_type`, `TimePoint.year`, "Our 7 sectors" (now 9); §4 RCC cites `Infrastructure.condition`, `Vulnerability.vuln_type = "ethnic_inequality"`/`"unemployment"` (not in the enum), proposes `rcc_stresses_environmental` (never created — the RCC stresses went into HIPs clusters); two sections are numbered 5. Only §3's v0.6/v0.6.1 subsections and §5 (geo coding) are current.
Fix: rewrite as a v1.1 crosswalk keyed by current ids (one table per framework: C40/Arup → `hazards.json.c40_arup_category`; CDP → `cdp-hazard-crosswalk.json` + concepts' `cdp_labels` + `action_status`; GCoM CRF → `FundingAllocation.{source_tier,instrument_class}`, `Action.status`; ICLEI → `solution-categories.iclei_*`; IPCC AR6 → `ipcc_action_types`, risk triad; UNDRR HIPs/Sendai → clusters, ExposureUnit; CRF 2024 → `crf-goals`). Move the RCC history to an appendix. Advances: —

**A-2 · MAJOR · `vocabularies/README.md` documents an ontology that no longer exists.**
Location: "13 categories, 30+ specific hazards"; "7 main categories"; `resilience-attributes.json` (file absent; v0.2 removed it per the Opus-2 response); "Deployment scales" and "Implementation status" enum blocks (removed v0.4.1); "Mechanism seed vocabulary (guidance, not constraint)" and "Free Text (No Validation): mechanisms.primary_mechanism" (authoritative since v0.3); "Schema Changelog v1.1 (2026-03-28)" (a different "v1.1"); paths `packages/ontology/schemas/…` (monorepo-era); "Source of Truth: Database tables" for hazards/solution-categories (contradicts CLAUDE.md: "Controlled vocabularies live in ontology/vocabularies").
Fix: cut to the current file list (now correct in its top half), the JSON-LD twin rule, the one deprecation convention (C-11), and a pointer to CLAUDE.md for process. Advances: —

**A-3 · MAJOR · Decision 22's GC-1 convention and Decision 10's `claim_ids` rule are recorded but not applied uniformly** — see C-3 and V-1. **Decision 37's "no duplicate data"** is violated by L-6 and L-11. **Decisions 35/37's catalog rule** is violated by L-4 and L-5. These are listed here so the alignment dimension has them in one place; the fixes are above.

**A-4 · MINOR · `IMPLEMENTED_IN` deployment properties** — already on the README list (Decision 38). Evidence confirms: `deployment_context`, `zone_type`, `area_km2`, `population_density`, `land_use_type` are one-edge-per-(Solution, Jurisdiction) and `IMPLEMENTED_IN.extract_hint` now says to prefer `Action DEPLOYED_IN`. Fix: drop all five in v1.2; `Place` + `DEPLOYED_IN → Place` now covers `zone_type`. Advances: *`IMPLEMENTED_IN` deployment properties*.

**A-5 · MINOR · `Action.action_kind` and the Mechanism concept list** — both correctly held back (README list). No new evidence to change that; L-1 should land first so the Mechanism list has a definition to grow under.

**A-6 · MINOR · `instrument_type` gaps (community land trust, developer agreement, investment fund)** — the `enums.instrument_type._note` already records the reasoning ("ownership model / contract / FundingStream"). Suggest closing the README item by moving that sentence to the decisions log as a one-line Decision 45 and adding `community_land_trust` as a **Solution concept** under `governance_and_policy` (it is an adaptation measure cities adopt, not an instrument). Advances: *`instrument_type` gaps*.

**A-7 · MINOR · Opus-review items that were closed with a flaw.**
(a) Opus-1 §5b (UrbanSystem doing two jobs) was closed by GC-2 ("no `is_instance`") — but v1.1 then moved `condition/capacity/service_coverage` to `TARGETS`, which is the right fix; the vocab still contains instance-shaped entries (L-2), so the underlying concern is half-closed. (b) Opus-1 §1f added both `maladaptation` outcome_type and `SHIFTS_RISK_TO`; the boundary ("temporal/functional" vs "spatial") is stated only in `SHIFTS_RISK_TO.notes`, not in `enums.outcome_type.maladaptation.description`. (c) Opus-2 Q5 chose `RISK_ASSESSED_IN (Hazard → Plan)`; it was later merged into `Plan ADDRESSES Hazard` (fine) but the per-plan hazard characterisation it was meant to hold (`climate_scenario`, `projection_year`) stayed on Hazard (L-4) — so the longitudinal query Opus asked for ("how did flood risk change between the 2015 and 2024 plan?") is still not answerable without conflicting values on the shared node.

---

## 3. Done well — keep

- **The catalog/instance split and its enforcement by topology** (Decision 33, finished for Solution/UrbanSystem/Barrier/Vulnerability in v1.1). Making the wrong query inexpressible rather than filtered is the right instinct; extend it (L-4, L-5), don't soften it.
- **Solution concepts as a governed, closed-to-extractor list with `proposed: true`**, aliases, one-line definitions, `cdp_labels`, `status`/`added_in`, and the explicit `unmapped_cdp_labels` with reasons. This is the best-specified vocabulary in the repo and the template the others should follow (Y-3).
- **Derived-copy with one writer** for `category_id`/`subcategory_id`/`ipcc_action_types` (Decision 35). Cheap queries, no two-writer conflicts; generalise it (L-12).
- **Dated observation series with `as_of_basis`** (Decision 40). The basis field is the detail most schemas miss; keep the node shape.
- **The FundingAllocation model** — two orthogonal closed axes, "generic kinds are never nodes", one node per flow with `share_percent` fan-out, `amount_qualifier`, "never converted at extraction". Finish it by making the rest of the money fields follow the same rule (C-7).
- **`action_status` with a definition per value**, sourced from real status briefs. Do the same for every bound enum.
- **The `ADDRESSES`/`TARGETS`/`DEPLOYED_IN` duplicate-id-by-grain convention** with umbrella + specific IRIs (Decision 34). It scales and the viewer handles it.
- **Precedence rules in extract hints** (PRODUCES vs RESULTS_IN, IMPLEMENTED_IN vs DEPLOYED_IN, Solution vs Action). Add them wherever two edges can both fire (L-5, Y-4).
- **`cdp-hazard-crosswalk.json`'s `match_type` + `known_gaps`** — honest about ambiguity instead of forcing a map.
- **Decision 42's refusals** (no flood parent, UHI is not a hazard) — correct, and the reasoning is written down.
- **Wikidata QID as Jurisdiction PK with the ODbL/GADM license notes** — do the same for Stakeholder (P-9).

---

## 4. Prioritised change list for a v1.2 migration (top 10, by impact ÷ effort)

| # | Change | Findings | Effort | Why first |
|---|---|---|---|---|
| 1 | **Structural validator** `scripts/check_ontology.py` + CI step (domain/range, cardinality enum, binding resolution, inline==block, manifest `bound_to`/`terms_count`, id charset, cross-entry alias/term collisions, concept→subcategory→category, twins `--check`). | P-10, C-1, C-4, V-5 | S | Every other item below is verifiable by it; it prevents the fourth recurrence of the stale-binding bug. |
| 2 | **Fix the four dangling type-level bindings and normalise the 36 inline enums** to one rule; coordinate with the core researcher-rule change so bound properties keep being filled. | C-1, C-2 | S (ontology) / M (core prompt) | Mechanical errors in the live schema; cheap once #1 exists. |
| 3 | **Move Hazard's seven one-place properties to `Plan ADDRESSES Hazard` only** (revised 2026-10-07, §5.2). | L-4, A-7c | M | Completes the v1.1 principle; unblocks the longitudinal-risk query; Hazard becomes a pure catalog node. |
| 4 | **Decide Mechanism node vs property, then fix the vocabulary.** Live data: 807 Mechanism nodes, all singleton free-text names, `mechanism_type` filled on 4. Recommended: retire the `Mechanism` type and `WORKS_BY`; add `Solution.mechanisms: array<enum>` bound to a widened `mechanism_vocabulary` (institutional/informational values legitimised; `restore` merged into `restore_regenerate`; `_other_description` added); re-judge the 807 phrases against the enum in core. | L-1, C-3 | S (ontology) / M (core re-judge) | Removes a literal contradiction and converts an unusable node population into a queryable dimension; the Mechanism concept list becomes the gate for reinstating a node. |
| 5 | **UrbanSystem vocabulary pass:** remove Solution-shaped and population-shaped systems; populate or delete the two empty sectors; add solid waste / cultural heritage; one definition per term. | L-2, L-3, P-8, Y-3 | M | `OPERATES_ON` and `TARGETS` are only as good as this list; `system_id` is a required field. |
| 6 | **Hazard leaf clean-up:** definitions with boundaries for the three ambiguous pairs, de-dupe `undrr_terms`, split SLR/erosion, add `water_stress`, normalise ids. | L-9, C-9 | S–M | Directly improves extraction precision on the most-used catalog type; the CDP crosswalk already shows where it hurts. |
| 7 | **Drop duplicated edge properties:** `PRODUCES/RESULTS_IN.{outcome_type,evidence_level}`, `ISSUES.adoption_status`, `REDUCES.mechanism_of_reduction: reduces_exposure`, `PRESCRIBES.implementation_stage(_observations)`/`implementation_timeline` (after live-count check), the five `IMPLEMENTED_IN` deployment props. Fix the four cardinalities. | L-6, L-10, L-11, L-13, A-4, C-4 | S | Pure deletion plus four string edits; removes conflict surfaces. Closes a README item. |
| 8 | **Identity hygiene on instance types:** `name` (required) + `description` on ExposureUnit and Vulnerability; `Stakeholder.name` required, `Stakeholder.alternative_names`, `Stakeholder.wikidata_qid`; `Jurisdiction.aliases` → `alternative_names`; `Place.place_type` + `waterbody/street/facility`; `Place WITHIN Place`. | L-7, C-5, P-9, L-8 | S | Small adds with immediate payoff for merge/display; absorbs the core-repo Stakeholder alias rows. |
| 9 | **`claim_ids` required on all non-derived edges; `Claim` type declared; observation keys and missing terms added to the context; `definition` → `skos:definition`.** | V-1, P-1, V-3, V-4 | M | Makes the "claims as provenance" promise true in the published schema and in the RDF export. |
| 10 | **Solution-categories tier review in the same pass as the concept re-review:** merge the v1.1 code/zoning duplicate, fix `reflective_coatings`, cut the 24 concept-less subcategories (or give them concepts), re-key `gcom_hazard_focus` to HIPs ids, clean ids with `legacy_id`, decide the tier-1 axis. Plus fold Supplier into Stakeholder. | P-4, P-5, C-9, Y-2 | L | Largest payoff for category-level analytics but depends on the full-extraction evidence the README already says to wait for; schedule it as the concept re-review, not before. |

Documentation items that should ride along but are not migration-script work: rewrite `framework-crosswalk.md` to v1.1 (A-1); cut `vocabularies/README.md` to what is true (A-2); sweep `design_notes` and `notes` for retired ids (V-5); regenerate the decisions-log evolution table (C-12); one deprecation convention (C-11); `_usage` strings (C-10). Items I would **not** take up: compound/cascading hazards and NbS preconditions (correctly deferred in the Opus round; nothing in v1.1 changes that); a parent Flood term (Decision 42 stands); re-splitting Infrastructure from UrbanSystem (the `TARGETS`-edge move was the right resolution).

---

## 5. Addendum (2026-10-07): decisions from the core repo for v1.2

*Added after the review, from the Probable Futures integration plan in
adaptbase-core (`_planning/to-do/PROBABLE-FUTURES-HAZARD-DATA-PLAN.md` §10,
`_planning/to-do/HAZARD-CONTEXT-TO-ADDRESSES-PLAN.md`). Decisions are
Anthony's, 2026-10-07; they are proposals for Fengze's review like the rest
of this document. Live counts are from read-only queries of core on
2026-10-07.*

### 5.1 `AFFECTED_BY` (Jurisdiction → Hazard): one entry per source

**Today.** `AFFECTED_BY` declares a required scalar `source_dataset` and an
`indicators` object. In the live graph:

- The 4,615 edges imported from WRI carry `source` (not `source_dataset`)
  and `indicators`. None has the required property.
- Of the 826 edges extracted from plan text, 23 carry `source_dataset`
  meaning *the dataset the plan cites* (e.g. London → Subsidence: "BGS's
  Property Subsidence Assessment dataset"), and 91 carry `indicators`.
- 113 edges are supported by both WRI and a plan document, because core
  allows one edge per (subject, predicate, object).

Core is adding Probable Futures (CC BY 4.0, 31 maps on a 22 km grid, six
warming levels) alongside WRI. Its values stay in a table outside the graph,
and the graph gets an `AFFECTED_BY` edge where a stated materiality rule says
the hazard is material. One edge may then be supported by WRI, Probable
Futures and the city's own plan at once.

**Change.**

- Add a required `sources` object keyed by source id. Each entry has
  `kind: dataset | plan_document`.
  - *dataset* entries: `dataset_version`, `materiality_rule` (`id`,
    `version`), the maps or indicators that passed (each tagged direct or
    indirect, with a direction), a score such as `frequency_ratio`, and
    `indicators`.
  - *plan_document* entry: `cited_datasets` (array of strings). **Edges
    extracted from plan text are kept** as this entry; it carries no scalar
    hazard characterisation (§5.2).
- Deprecate the top-level `source_dataset` and `indicators`.
- Definition: "This jurisdiction is affected by this hazard, supported by
  one or more sources: a reference dataset under a stated materiality rule,
  or a plan document. One edge per jurisdiction–hazard pair; sources are
  never merged or averaged."
- `notes`: drop the WRI-specific wording. `extract_hint`: keep the plan-text
  guidance.
- `claim_ids` stays optional; dataset entries are derived, as V-1 already
  proposes.

### 5.2 L-4 narrowed: a plan's hazard details go on `ADDRESSES` only

Live: **388 plan statements from 85 plans sit on 36 of the 50 Hazard
nodes** (`frequency` 252, `trend` 50, `projection_year` 40,
`return_period` 31, `severity` 14, `climate_scenario` 1). The node keeps
only the first one promoted. Coastal flood's `frequency` is "typically",
from Berkeley's plan; San Francisco's "approximately twice per year" and
NYC's "1% annual chance" lost.

**Change.** Remove the seven properties from `Hazard`. Declare them on
`ADDRESSES` for the `Plan → Hazard` pair only (not `Action → Hazard` or
`ResilienceGoal → Hazard`), with the same types and enums. Add a Hazard
`notes` line: "a plan's characterisation of a hazard is on its `ADDRESSES`
edge; the node holds only the vocabulary term." Core moves the 388
statements onto the plans' `ADDRESSES` edges (all 388 trace to a Plan; 36
already have the edge).

### 5.3 Jurisdiction

- **`geometry` is the one coordinate representation.** Live, coordinates
  sit in the declared `geometry` (a Point on 143) *and* in operational
  `latitude` / `longitude` keys (1,061). Keep `geometry` as declared; core
  migrates the 1,061 into it.
- **Reword `geometry`'s note** from "Polygons deliberately excluded to avoid
  ODbL contamination from OSM" to "Polygons only from sources whose licence
  allows redistribution; never from OSM." Core plans area-weighted sampling
  of gridded data over jurisdiction boundaries; the licence rule stays, and
  the blanket exclusion goes.
- **`jurisdiction_kind` stays required.** It is set on 0 of 1,924 today;
  core fills it from Wikidata P31.
- **`climate_zone`**: name the source in the note. Probable Futures'
  climate-zones map at 1.0°C, mapped to the five groups by Köppen letter.

### 5.4 Hazard vocabulary (with item 6)

When `water_stress` is added, core links Probable Futures' water-balance and
drought-likelihood maps to it directly, alongside `drought`. Id
normalisation is fine; core keys its map-to-hazard links by `hazard_id` and
re-keys in the submodule-bump PR.

### 5.5 Design note

Add one: *large quantitative reference data (climate projections,
indicators at scale) lives in tables outside the graph; the graph carries
edges derived from it by a stated, versioned rule, with per-source
provenance.* This records why Probable Futures adds no node type, and sets
the pattern for later datasets.

### 5.6 Decisions after Fengze's review (Anthony, 2026-10-08)

- **Item 4 (retire Mechanism): not in v1.2.** `Mechanism` and `WORKS_BY` stay
  as they are (807 nodes, 871 edges). Revisit separately.
- **Evidence moves: in place, with a run-scoped rollback**, not a new row with
  `supersedes`. Each edited row records its before-image and the editing run's
  id in `metadata._remediation`, the before-images are also written to a backup
  file, and a rollback script restores a run. This is now the single rule for
  backfill and remediation (core `PROPERTY-EVIDENCE-CONVENTION.md` §7a), as
  Fengze asked: one mechanism, not two. It applies to the §5.2 Hazard move.
- **Fengze's other points are accepted:** item 2 waits for the core `_bucket`
  rule; item 9 keeps `claim_ids` optional and states that provenance is the
  evidence store; §5.3 coordinates are a reported backfill plus a
  misattribution worklist, not a copy.
- **Two taxonomies considered:**
  - *Weitz Urban Adaptation Tech Taxonomy (2025-05-15).* `solution-categories`
    already carries all 90 of its families verbatim; the decision on
    re-deriving tier 1 (item 10 / P-4 / P-5) is pending.
  - *Climate Bonds Resilience Taxonomy (CBRT v1).* Its licence is personal-use
    only, so no CBRT content enters this repo; a concept-to-CBRT crosswalk is
    **dropped**. Core may read it privately to find missing concepts.
  - **Add `Action.resilience_contribution`** (enum: `adapted` — makes the
    acting party's own asset or activity resilient; `enabling` — builds the
    resilience of others). The split is the EU Taxonomy's (Regulation (EU)
    2020/852, Art. 11 and Art. 16), not CBRT's, so it carries no licence
    restriction. Optional; filled by extraction and the property-fill lane.

