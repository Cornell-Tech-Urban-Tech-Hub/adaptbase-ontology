# Ontology Design Decisions Log

**Project:** Resilience Scanner - Climate Adaptation Solutions Ontology  
**Version:** 0.5.0  
**Last Updated:** 2026-05-15

---

## Purpose

This log documents key design decisions in the ontology development process, including rationale, alternatives considered, and implications for future work.

---

## Decision 29 (v0.5.0): Location → Jurisdiction rename + Place entity + Wikidata QID as canonical PK

**Date:** 2026-05-15  
**Context:** Replacing the legacy `loc_id` / `cities.csv` lookup system with a proper geographic entity model. The WRI 980-city dataset used arbitrary integers (`loc_id`) as join keys — non-standard, not resolvable externally, limiting. Climate adaptation literature overwhelmingly references jurisdictions (cities, districts, regions), with non-jurisdictional geographic features (watersheds, corridors) as a minority case.

### Decision

Bump to **v0.5.0** (minor — schema change). Four coordinated changes:

**A. Rename `Location` → `Jurisdiction`** — reflects that the vast majority of geographic entities in adaptation planning are governed territories. Updated definition, extract_hint, and all inbound relationships (IMPLEMENTED_IN, COVERS, DEPLOYED_IN, LOCATED_IN, WITHIN).

**B. Rework Jurisdiction properties:**
- **Added:** `wikidata_qid` (canonical PK, required), `jurisdiction_kind` (vocabulary-bound, required), `admin_level` (OSM-style integer hint), `name_local`, `iso_3166_2`, `country_iso` (replaces `country`), `codes` (object: osm_relation_id, geonames_id, gadm_gid, oecd_fua_code), `aliases`, `population_year`
- **Kept:** `name`, `population`, `climate_zone`, `coastal_status`, `income_classification`, `geometry` (redefined as centroid Point only from Wikidata P625)
- **Dropped:** `loc_id` (replaced by wikidata_qid), `deployment_context` (vague, unused), `region` (redundant with admin hierarchy via WITHIN), `location_type` (replaced by jurisdiction_kind vocabulary)

**C. New entity: `Place`** — lightweight type for non-jurisdictional geographic features (watershed, corridor, coastline, site, park, infrastructure_zone). Properties: name (required), place_type (enum, required), geometry, description, wikidata_qid (optional). Linked to containing Jurisdiction via WITHIN.

**D. New relationship: `GOVERNS` (Stakeholder → Jurisdiction)** — models the city-as-institution (Stakeholder, e.g. "City of Miami") governing the city-as-place (Jurisdiction, e.g. "Miami, FL"). This dual modeling is intentional: spatial properties and institutional properties do not belong on the same node.

### Why Wikidata QID as canonical PK

1. **Globally unique** — no collisions, no local integer sequences
2. **CC0 licensed** — zero risk of license contamination
3. **Built-in crosswalks** — ISO 3166, GeoNames, OSM, GADM via Wikidata properties
4. **Resolvable** — any QID can be dereferenced to structured data via SPARQL
5. **Community maintained** — far more durable than any single research dataset

### Why one Jurisdiction type with vocabulary, not class hierarchy

A class hierarchy (City extends Jurisdiction, County extends Jurisdiction, etc.) would:
- Bloat the type list with 15+ near-identical entity structures
- Require promotion/demotion when classifications are debated
- Force extraction models to commit to a class at entity-creation time

Instead: a single `Jurisdiction` type with `jurisdiction_kind` (vocabulary-bound) that can be updated without schema changes, and `admin_level` as a loose ordering hint.

### Why admin_level is a loose hint, not strict hierarchy

OSM admin_levels vary by country (admin_level=6 is a county in the US, a municipality in Germany). We store it as a numeric hint for display/sorting but do NOT enforce hierarchy from it — the WITHIN relationship carries the actual topology.

### ODbL avoidance

OSM relation IDs are stored as passive pointers (`codes.osm_relation_id`) — no geometry, tag data, or derived attributes imported. This keeps all AdaptBase data unencumbered by ODbL share-alike requirements.

### Alternatives considered

- **Option A: Keep Location, add Jurisdiction as separate type** — rejected; would require disambiguating which type to use for cities, creating confusion.
- **Option B: Split into Place + Government** — rejected; overly abstract for the domain. Most geographic entities in adaptation literature ARE jurisdictions.
- **Option C (chosen): Rename Location → Jurisdiction, add Place for non-jurisdictional** — cleanest separation, zero rewiring cost (no Location data exists in DB yet).

---

## Decision 28 (v0.2): Resilience finance extension — CapitalProject entity, debt-service properties, multi-source funding stack via USES_INSTRUMENT/CHANNELS_THROUGH, monetized co-benefits

**Date:** 2026-05-05
**Context:** Meeting with Andy Salkin (Resilient Cities Catalyst), NYC, 5 May 2026. Salkin's brief: help cities prioritize resilience spending in their Capital Improvement Plans (CIPs), and surface evidence to justify more debt-financed adaptation work. Analytical core: *plan↔budget alignment* — comparing what a climate plan says with what the capital budget actually commits.

The v0.1.1 ontology had the financing primitives (`FinancingSource`, `FinancialInstrument`, `CHANNELS_THROUGH`, `USES_INSTRUMENT`) and modeled climate-plan commitments well via `Plan` and `Action`, but three concrete gaps prevented Salkin's use cases:

1. No way to ingest a non-climate capital budget. `Action` is defined as a commitment within a climate plan; Salkin needs to ingest the full CIP from sources like OpenGov and *then* test which line items are climate-relevant.
2. No structured multi-source funding stack. A typical CIP line is funded by, e.g., 40% federal grant + 30% revenue bond + 30% municipal appropriation. The chain `Solution USES_INSTRUMENT FinancialInstrument ← CHANNELS_THROUGH FinancingSource` was incomplete (Solution↔Source not directly connected), carried no debt-service detail, and wasn't grained at the project level.
3. Co-benefits were categorical, not monetized. `Outcome.co_benefit_type` captured kind but not value — Salkin's framing ("show how investments connect to other capital programs — transit, parks, public safety, pensions") needed both monetary value and a beneficiary-program tag.

### Decision

Bump to **v0.2** (minor — schema change). Six coordinated additions:

**A. New entity: `CapitalProject`** — a budget-document line item with project_id, asset_class, total_capex_usd, annual_opex_usd, asset_life_years, construction_phase, funding_year_breakdown, financing_status, is_climate_relevant flag. Distinct from `Action` (climate-plan commitment): a `CapitalProject` is sourced from a CIP / capital budget and may or may not be climate-relevant.

**B. `FinancialInstrument` debt-service properties** — principal_amount_usd, interest_rate, loan_term_years, annual_debt_service_usd, issuance_year, maturity_year, issuer, credit_rating. All optional (extraction tolerant). Enables answering "what is the total annual debt service burden from adaptation projects?"

**C. `FinancialInstrument.instrument_type` extended** with US municipal CIP language: `general_obligation_bond`, `revenue_bond`, `tax_increment_financing`, `special_assessment`, `federal_cost_share`, `state_cost_share`, `municipal_capital_appropriation`, `ratepayer_funded`, `other`. All previous values retained.

**D. New relationships:**
- `REALIZES` (CapitalProject → Action) — bridges climate-plan language and budget-document execution. The plan↔budget alignment edge.
- `COMMISSIONED_BY` (CapitalProject → Stakeholder) — sponsoring agency, distinct from `IMPLEMENTED_BY` (executing party).

**E. Existing relationships extended (duplicate-id rows for CapitalProject as source/target):** `DEPLOYED_IN`, `USES_INSTRUMENT`, `IMPLEMENTED_BY`, `PRODUCES`, and `SPECIFIES` (Plan → CapitalProject). The viewer's edge keying (`id:source:target` per inspector.js:237) tolerates duplicate ids — this preserves semantic identity (the relationship means the same thing whether the source is Action or CapitalProject) without cluttering the schema with parallel names.

`USES_INSTRUMENT` (CapitalProject → FinancialInstrument) carries the full funding-stack per instrument: `amount_usd` (draw amount), `share_percent` (fraction of total project cost), `financing_model` (bound to `enums.json#financing_model`). A multi-source stack is modeled as multiple `USES_INSTRUMENT` edges — one per instrument — each pointing to a `FinancialInstrument` that is itself capitalized by one or more `FinancingSource` nodes via `CHANNELS_THROUGH`.

`CHANNELS_THROUGH` (FinancingSource → FinancialInstrument) extended with `amount_usd` to capture how much a source contributes to an instrument pool (revolving fund tranche, grant award, bond capitalization). For single-source instruments this is the total award; for pooled vehicles (revolving funds, blended finance) it differentiates each contributor's share.

`FACES` is **not** extended to CapitalProject. Capital projects in a CIP have cleared political, financial, and technical vetting to win a budget allocation — modeling them as still facing barriers represents the wrong state.

**F. `Outcome` monetary valuation** — new properties: `monetized_value_usd`, `value_recurrence` (one_time/annual/lifetime), `valuation_method` (free-text), `beneficiary_program` (array, new `municipal_program` enum: transportation, parks_recreation, public_safety, public_health, housing, schools, water_utilities, energy_utilities, pensions, general_revenue, other). `co_benefit_type` extended with five finance-relevant categories: `asset_protection`, `revenue_stability`, `operational_cost_reduction`, `tax_base_protection`, `service_continuity`.

**G. Plan and Action extensions:**
- `Plan.plan_type` extended with `capital_improvement_plan` and `capital_budget`.
- `Action.financing_status` property added, bound to `enums.json#financing_status` (previously orphaned).

**H. New authoritative enum blocks in `enums.json`:** `instrument_type` (formalized), `asset_class`, `construction_phase`, `municipal_program`, `value_recurrence`. The previously-defined-but-unbound `financing_status` and `financing_model` enums now have explicit `_usage` annotations citing their bindings.

### Edge Economy — what was deliberately NOT added

CapitalProject omits direct edges that are reachable via multi-hop paths:
- `IMPLEMENTS Solution` — reach via `REALIZES Action` + `Action IMPLEMENTS Solution`.
- `MITIGATES Hazard` / `REDUCES_EXPOSURE ExposureUnit` / `REDUCES Vulnerability` — reach via Solution.
- `PURSUES ResilienceGoal` — reach via Action.
- `OPERATES_ON UrbanSystem` — collapsed into the `asset_class` property (the local annotation from the budget document).
- `PROTECTS ExposureUnit` — reach via Solution → REDUCES_EXPOSURE.

`BUNDLES_WITH` (CapitalProject ↔ CapitalProject) for cross-program co-financing is deferred until first CIP ingestion shows whether bundles are extractable. `INTERSECTS_RISK_SHED` (CapitalProject → Hazard) is similarly deferred — currently derivable via shared Location/ExposureUnit.

### Five-axis split (extension of Decision 27)

Decision 27 (v0.1.1) established a four-axis split: who funds (`FinancingSource`) → how accredited (`accreditation_modality`) → what instrument carries the capital (`FinancialInstrument`) → what the solution physically does (`Mechanism`).

v0.2 adds a fifth axis at the project grain: **what budget line item receives it** (`CapitalProject`), with debt-service detail surfaced on `FinancialInstrument` (principal, term, rate, annual debt service). The full project-level financing chain:

```
FinancingSource →CHANNELS_THROUGH(amount)→ FinancialInstrument ←USES_INSTRUMENT(amount, share, model)← CapitalProject
```

Sources mix in the instrument (a revolving fund pools multiple source contributions; a bond is backed by one). The instrument then delivers capital to the project. For typical CIP cases (one source, one instrument) the chain degenerates gracefully to a single path; for pooled vehicles, multiple `CHANNELS_THROUGH` edges distinguish each contributor's tranche.

### Worked example — multi-source funding stack

```
CapitalProject {
  project_id: "23-WTR-015",
  project_name: "Watershed Drainage Improvements",
  asset_class: "stormwater",
  total_capex_usd: 50000000,
  asset_life_years: 50
}
  └─ USES_INSTRUMENT(amount: 30M, share: 60%, financing_model: "grants")
       → FinancialInstrument(instrument_type: "federal_cost_share")
            └─ CHANNELS_THROUGH(amount: 30M) ← FinancingSource(name="FEMA BRIC")
  └─ USES_INSTRUMENT(amount: 10M, share: 20%, financing_model: "revolving_loan")
       → FinancialInstrument(instrument_type: "revolving_fund")
            └─ CHANNELS_THROUGH(amount: 60M) ← FinancingSource(name="State SRF")   ← full fund capitalization
  └─ USES_INSTRUMENT(amount: 10M, share: 20%, financing_model: "debt")
       → FinancialInstrument(instrument_type: "revenue_bond", principal: 10M, term: 30, rate: 0.045, annual_debt_service: 615000)
            └─ CHANNELS_THROUGH ← FinancingSource(name="City Water Dept — ratepayer revenue")
  └─ COMMISSIONED_BY → Stakeholder(name="Department of Environmental Protection")
  └─ DEPLOYED_IN → Location(name="South Watershed District")
  └─ REALIZES → Action(action_name="Reduce stormwater flooding in vulnerable neighborhoods")
  └─ PRODUCES → Outcome(outcome_type: "co_benefit", co_benefit_type: "asset_protection", monetized_value_usd: 80000000, value_recurrence: "lifetime", valuation_method: "FEMA BCA", beneficiary_program: ["water_utilities", "transportation"])
```

### Plan↔Budget alignment query (the Salkin use case)

```
MATCH (p1:Plan {plan_type: "climate_action_plan"})-[:SPECIFIES]->(a:Action)-[:PURSUES]->(g:ResilienceGoal),
      (p2:Plan {plan_type: "capital_improvement_plan"})-[:SPECIFIES]->(cp:CapitalProject)-[:REALIZES]->(a)
RETURN g, a, cp, p2
```

→ Returns climate-plan goals whose actions ARE realized by funded capital projects (the aligned ones). Inverse query — actions with no `REALIZES` inbound — surfaces unfunded climate commitments. This is the analytical core of NYC OMB-style climate budgeting.

### Counts

- v0.1.1: 20 types, 44 relationship rows (the v0.1.1 metadata listed 45; it was off by one), 6 vocabularies
- v0.2: 21 types (+CapitalProject), 51 relationship rows (+7: REALIZES, COMMISSIONED_BY new ids; DEPLOYED_IN, USES_INSTRUMENT, IMPLEMENTED_BY, PRODUCES, SPECIFIES duplicate-id rows), 6 vocabularies (enums.json gained 5 authoritative blocks: instrument_type, asset_class, construction_phase, municipal_program, value_recurrence)

---

## Decision 22 (v0.1.1): Restructure hazards.json to UNDRR HIPs 2025 primary

**Date:** 2026-05-04
**Context:** Peer review (Cornell Tech Urban Tech Hub, May 2026) identified that the C40/Arup-primary hazard taxonomy missed two HIPs 2025 clusters — Technological and Societal — buried instead under an `rcc_non_climate` bucket. With no published extractions to invalidate, the better long-term call is to align primary structure with the most current authoritative international standard.

### Decision
Restructure `hazards.json` top-level from C40/Arup-primary to UNDRR-ISC HIPs 2025-primary. Use 7 of 8 HIPs clusters (omit Extraterrestrial as out of scope for urban climate adaptation): meteorological_hydrological, geohazards, environmental, biological, chemical, technological, societal. Keep the curated subset of hazards (don't import all 281 HIPs entries). Add `c40_arup_category` backref on every hazard for legacy crosswalk. Promote technological + societal hazards to first-class clusters. Reclassify tsunami from wave_action to geohazards per HIPs 2025 (geophysical trigger, not meteorological).

### Alternatives Considered
- **Keep C40/Arup primary, add HIPs cluster mapping field** — rejected: leaves technological + societal buried under "rcc_non_climate" naming, which obscures their importance for cascading-failure modeling.
- **Switch to full HIPs 281-hazard list** — rejected: bloats the vocabulary with hazards not relevant to urban adaptation (extraterrestrial, esoteric chemical hazards).

---

## Decision 23 (v0.1.1): ICLEI five-pathway crosswalk on solution categories

**Date:** 2026-05-04
**Context:** Peer review observed that the solution taxonomy mapped to ICLEI milestones (A.Initiate → E.Monitor) but not to ICLEI's five urban-development pathways (low-emission, nature-based, circular, resilient, equitable_people_centered) which are the strategic framing layer above milestones.

### Decision
Add `iclei_pathways[]` to `framework_mappings` on every solution category. Most categories map to 2 pathways; Planning & Monitoring is cross-cutting on all five.

### Implications
Enables queries like "Which solutions advance the equitable people-centered pathway?" and supports cross-walk to ICLEI's GreenClimateCities reporting framework.

---

## Decision 24 (v0.1.1): EbA and CbA as distinct solution subcategories

**Date:** 2026-05-04
**Context:** Peer review noted that Ecosystem-based Adaptation (EbA) and Community-based Adaptation (CbA) are distinct technical concepts in the UNFCCC and IPCC AR6 literature, not interchangeable with generic "nature-based" or "engagement" solutions.

### Decision
Add `ecosystem_based_adaptation_eba` subcategory under `nature` (distinct from urban_greening: EbA is anchored in CBD/UNFCCC framing and emphasizes biodiversity outcomes). Add `community_based_adaptation_cba` subcategory under `communication_and_community` (distinct from generic engagement: CbA frames the community as the lead agent of adaptation, not as an audience to be consulted).

---

## Decision 25 (v0.1.1): Informal service systems as a subsector

**Date:** 2026-05-04
**Context:** Peer review cited IPCC AR6 Ch. 6's critique that ISO 37120 (the source standard underlying our urban-systems taxonomy) misses informal urban systems entirely, even when those systems serve a majority of residents — particularly in cities of the Global South.

### Decision
Add `informal_service_systems` subsector under `socioeconomic_health` covering informal water supply, sanitation, solid waste, transport, energy, food systems, and community-led disaster response. Distinct from existing `informal_settlements` (built-environment / land-tenure axis) and `informal_economies` (livelihood / labor axis): this subsector captures the SERVICE-PROVISION axis where formal infrastructure is absent.

### Alternatives Considered
- **Top-level "Informal Systems" sector** — rejected: would create double-counting with existing informal_settlements and informal_economies entries.
- **Distribute across existing sectors** — rejected: makes the informal-system theme harder to query as a coherent class.

---

## Decision 26 (v0.1.1): Housing tenure as a vulnerability axis (atomic, not derived)

**Date:** 2026-05-04
**Context:** Peer review cited Shelters in the Storm (Bradshaw et al. 2025) on housing-tenure form (co-ops, condos, mobile homes, tenure-insecure residents) as a distinct vulnerability driver not captured by income-only or settlement-form-only framings. Reviewer also flagged intersectional vulnerability as a gap.

### Decision
Add three housing-tenure entries to `vulnerable-populations`: `manufactured_mobile_home_residents`, `cooperative_condo_residents`, `tenure_insecure_residents`. Do NOT add an `intersectional` flag or hard-coded intersectional categories. Intersectionality is expressed by listing multiple atomic groups on the same Vulnerability or Solution node — queries derive the intersection rather than the vocabulary hard-coding it.

### Rationale
Atomic groups + multi-value arrays + queries is more expressive than enumerated intersections. Adding an `intersectional` boolean would be metadata about the source's framing, not about the vulnerability itself; enumerating intersections (e.g., `low_income_elderly`) would explode the vocabulary into a Cartesian product. The reviewer's underlying concern — that intersectional vulnerability be queryable — is satisfied by `array<string>` semantics already in place on `Vulnerability.affected_group` and `Solution.target_populations`.

---

## Decision 27 (v0.1.1): AF/GCF accreditation modalities on FinancingSource (not on mechanism_vocabulary)

**Date:** 2026-05-04
**Context:** Peer review recommended that Adaptation Fund and Green Climate Fund terminology — National Implementing Entities (NIEs), direct access, pooled facilities — should align our `mechanism_vocabulary`. This was a misreading of the ontology: our `Mechanism` entity (and its `mechanism_vocabulary` enum) is explicitly the *functional/operational* process by which a Solution physically achieves adaptation effect (absorb, redirect, harden, sense_and_detect, etc.), not the financial-institutional arrangement. The Mechanism entity definition states explicitly that "financial and governance mechanisms are captured by FinancialInstrument and EnablingCondition respectively" (ontology v0.1, line 301).

### Decision
Add an `accreditation_modality` enum to `enums.json` (NIE, RIE, MIE, direct_access, enhanced_direct_access, pooled_facility, readiness_programme, not_applicable) and an `accreditation_modality` property on `FinancingSource`. Leave `mechanism_vocabulary` untouched. Document the distinction in the FinancingSource notes: source_type (broad funder category) vs. accreditation_modality (institutional access arrangement) vs. FinancialInstrument.instrument_type (structural form of capital) vs. Mechanism.mechanism_type (operational adaptation process).

### Rationale
Conflating finance-institutional arrangements with operational adaptation mechanisms would collapse a useful structural distinction. The four-axis split (who funds → how they're accredited → what instrument carries the capital → what the solution physically does) is the resolution the ontology already commits to; this decision extends it cleanly.

---

## Decision 1: Absorb Student Ontology Planning Vocabulary (Phase 2)

**Date:** 2026-04-14 to 2026-04-15  
**Context:** Ruowen's student ontology focused on adaptation planning, while our ontology was initially solutions-focused.

### Strategic Insight
Solutions exist within the planning context. Adaptation planners are our end users. The "solutions vs planning" framing was a false dichotomy.

### What We Absorbed

**Phase 2a (Critical for Planning Context):**
- **Vulnerability** node (IPCC AR6 framework)
- **REDUCES** relationship (Solution → Vulnerability) - KEY planning outcome
- **IMPROVES** relationship (Solution → Infrastructure/UrbanSystem)
- Spatial targeting properties on IMPLEMENTED_IN
- Actor coordination relationships: COORDINATES_WITH, REPORTS_TO, PARTICIPATES_IN, MONITORS, MANAGES

**Phase 2b (Temporal Modeling):**
- **TimePoint** node for planning cycles and policy windows
- Temporal relationships: STARTED_AT, ISSUED_AT, RECORDED_AT
- Enhanced Barrier with Constraint properties

**Phase 2c (Exposure & Infrastructure):**
- **Infrastructure** node (split from UrbanSystem)
- **ExposureUnit** node (UNDRR alignment)
- Exposure relationships: EXPOSES, SERVES, EXPERIENCES_VULN

### Rationale
1. **User-centered design:** Planners need to contextualize solutions within vulnerability reduction frameworks
2. **Framework alignment:** IPCC AR6, UNDRR Sendai, CRF all emphasize vulnerability reduction and exposure analysis
3. **Reusability:** Solutions appear in plans, so planning vocabulary is essential for solution documentation

### Alternatives Considered
- **Keep ontologies separate:** Rejected - creates integration burden and misses planning context
- **Merge entirely:** Rejected - some student concepts (ClimateHazard properties) are too climate-science focused

### Implications
- Extraction schema must support planning-domain relationships
- Graph queries can now ask: "Which solutions reduce flood vulnerability in low-income neighborhoods?"
- Multi-stakeholder governance is now first-class

---

## Decision 2: Barrier vs. Constraint Terminology

**Date:** 2026-04-15  
**Context:** Student ontology uses "Constraint", we use "Barrier". Both represent obstacles to implementation.

### Decision
**Keep "Barrier" terminology, absorb Constraint properties.**

### Rationale
1. **Domain clarity:** "Barrier" is more common in adaptation literature and clearer to practitioners
2. **Semantic richness:** Absorbed student's properties (severity_score, affected_stakeholder, is_structural) to enhance Barrier
3. **Relationship consistency:** Our "Solution FACES Barrier" reads more naturally than "Solution HINDERED_BY Constraint"

### Enhanced Properties
- `severity_score` - Quantifies barrier severity
- `affected_stakeholder` - Which actor faces this barrier
- `is_structural` - Whether barrier is systemic vs. addressable

### Notes
Student model: Actor FACES Constraint  
Our model: Solution FACES Barrier  
Both perspectives are valid - captures different angles on implementation obstacles.

---

## Decision 3: TimePoint as Node vs. Property

**Date:** 2026-04-15  
**Context:** We already have `year_of_deployment` property on Solution. Do we need a TimePoint node?

### Decision
**Add TimePoint as a node, keep year_of_deployment property.**

### Rationale
1. **Richer temporal modeling:** TimePoint enables policy_cycle tracking beyond simple year
2. **Relationship flexibility:** Multiple entities (Solution, Policy, Indicator) can link to same TimePoint
3. **Time-series data:** RECORDED_AT with multiple TimePoints enables trend analysis
4. **Planning alignment:** Policy cycles ("mayoral term 2020-2024") don't map to single year property

### When to Use Which
- **year_of_deployment property:** Quick lookups, simple temporal context
- **STARTED_AT → TimePoint:** Rich temporal context, policy cycle alignment, multi-entity temporal relationships

### Implications
- Schema must support extracting both simple year and complex temporal periods
- Graph can query: "Which solutions started during the 2020-2024 policy cycle?"

---

## Decision 4: Infrastructure Split from UrbanSystem

**Date:** 2026-04-15  
**Context:** Student ontology has separate Infrastructure node. We had folded this into UrbanSystem.

### Decision
**Create separate Infrastructure node (Phase 2c).**

### Critical Distinction
- **UrbanSystem:** What solutions **operate on** (sector/subsector classification)
- **Infrastructure:** What solutions **improve** (actual infrastructure entities)

### Example
A bioswale (solution):
- **OPERATES_ON:** `hydrological_water` system (UrbanSystem)
- **IMPROVES:** `stormwater_network` (Infrastructure)

### Rationale
1. **Semantic precision:** Operating on vs. improving are fundamentally different relationships
2. **Planning outcomes:** Planners measure success by infrastructure improvements
3. **Green/grey/blue classification:** Infrastructure color (green/grey/blue) is about the infrastructure itself, not the system it's part of
4. **Equity analysis:** Infrastructure SERVES ExposureUnit enables "who benefits" queries

### Properties on Infrastructure
- `infra_type`, `infra_color`, `capacity`, `condition`, `service_coverage`
- Moved `infra_color` from IMPROVES relationship to Infrastructure node itself

### Implications
- More complex extraction: must identify both system operated on AND infrastructure improved
- Richer queries: "Which green infrastructure was improved to serve low-income neighborhoods?"

---

## Decision 5: ExposureUnit Node (UNDRR Alignment)

**Date:** 2026-04-15  
**Context:** UNDRR Sendai Framework defines Risk = Hazard × Exposure × Vulnerability. We had Hazard and Vulnerability, but no Exposure entity.

### Decision
**Add ExposureUnit node to complete UNDRR risk chain.**

### Rationale
1. **Framework completeness:** UNDRR Sendai Framework requires exposure as distinct concept
2. **Quantified exposure:** Plans specify exposed populations and assets with numeric values
3. **Equity analysis:** ExposureUnit enables identifying vulnerable populations
4. **Pathway mapping:** Completes risk chain: Hazard EXPOSES ExposureUnit, ExposureUnit EXPERIENCES_VULN Vulnerability

### Relationships Added
- **EXPOSES** (Hazard → ExposureUnit): What hazard exposes
- **SERVES** (Infrastructure → ExposureUnit): Who benefits from infrastructure
- **EXPERIENCES_VULN** (ExposureUnit → Vulnerability): Exposure-to-vulnerability pathway

### Properties
- `population_count`, `asset_value`, `vulnerable_ratio`, `social_capital_index`

### Implications
- Enables queries: "Which exposure units with >50% vulnerable populations are served by improved green infrastructure?"
- Supports UNDRR reporting requirements

---

## Decision 6: Node vs. Property Trade-offs

**Date:** Throughout Phase 2  
**Context:** When should something be a node vs. a property or relationship property?

### Guidelines Developed

**Make it a NODE when:**
1. **Reused across multiple entities:** TimePoint linked from Solution, Policy, Indicator
2. **Has rich properties:** Vulnerability has 5 properties, not just a type
3. **Subject of relationships:** Infrastructure SERVES ExposureUnit
4. **Framework alignment:** IPCC/UNDRR specify as distinct entity
5. **Query target:** Users will ask "show me all vulnerabilities" or "list all infrastructure"

**Keep as PROPERTY when:**
1. **Simple attribute:** year_of_deployment is sufficient for many use cases
2. **No relationships:** Doesn't connect to other entities
3. **Low reuse:** Only applies to one node type
4. **Implementation detail:** Technical components of mechanisms

**Make it RELATIONSHIP PROPERTY when:**
1. **Context-specific:** service_level only meaningful on SERVES relationship
2. **Temporal value:** Indicator value at specific TimePoint
3. **Qualified relationship:** coordination_type qualifies COORDINATES_WITH

### Examples
- ✅ Node: Vulnerability (rich properties, subject of REDUCES relationship)
- ✅ Property: year_of_deployment on Solution (simple, no relationships)
- ✅ Relationship property: value on RECORDED_AT (time-specific measurement)

---

## Decision 7: Mechanism Semantic Collision

**Date:** 2026-04-15  
**Context:** Student ontology uses "Mechanism" for governance enablers (financial, regulatory). We use "Mechanism" for functional processes (absorb, redirect, harden).

### Decision
**Keep our Mechanism definition, note semantic difference.**

### Student's Mechanism (Governance)
- Financial mechanisms, regulatory mechanisms
- Actor MANAGES Mechanism
- Properties: mechanism_type, source_of_funding, legal_basis, scale_usd

### Our Mechanism (Functional)
- How solution achieves effect: absorb, redirect, harden, monitor, govern
- Solution USES_MECHANISM Mechanism
- Properties: mechanism_type (functional process), technical_components

### Resolution
- **Added:** Actor MANAGES Mechanism relationship with note about semantic collision
- **Deferred:** Renaming Mechanism to "AdaptationMechanism" or creating separate "GovernanceMechanism"
- **Scheduled:** Mechanism taxonomy formalization in Weeks 7-8 will resolve this

### Implications
- Extraction must distinguish functional mechanisms from governance mechanisms
- May need separate nodes in future: FunctionalMechanism vs. GovernanceMechanism

---

## Decision 8: Spatial Targeting - Zone Properties vs. UrbanZone Node

**Date:** 2026-04-14  
**Context:** Student ontology has UrbanZone node. We need sub-city spatial targeting.

### Decision
**Phase 2a: Add zone properties to IMPLEMENTED_IN relationship (quick solution).**  
**Phase 2b+: Deferred creating separate UrbanZone node.**

### Properties Added to IMPLEMENTED_IN
- `zone_type`, `area_km2`, `population_density`, `land_use_type`

### Rationale for Properties Approach
1. **Simplicity:** Most solutions won't have detailed zone data
2. **Extract once:** Zone data captured during city-level extraction
3. **Query support:** "Solutions in high-density residential zones" still works
4. **Future-proof:** Can refactor to UrbanZone node later without breaking existing relationships

### When to Reconsider
- If many solutions specify multiple zones within same city
- If zone-level planning becomes primary use case
- If zones need their own properties (governance, planning status, etc.)

---

## Decision 9: Controlled Vocabularies vs. Free Text

**Date:** Throughout Phase 2  
**Context:** Student ontology has many free-text fields. When should we enforce vocabularies?

### Principles

**Enforce vocabulary when:**
1. **External standard exists:** UNDRR hazards, C40 climate hazards, CRF goals
2. **Enumerable and stable:** infra_color (green/grey/blue), condition levels
3. **Essential for queries:** Domain filters, barrier types
4. **Cross-comparison needed:** Can't compare if everyone uses different terms

**Allow free text when:**
1. **High variability:** Solution names, actor names, zone types
2. **Evolving domain:** Mechanism types (to be formalized later)
3. **Context-dependent:** Deployment context, notes fields
4. **No standard exists:** Many planning concepts lack agreed taxonomies

### Gray Areas (Guidance Only)
- **Mechanism types:** Currently free-text with seed vocabulary for guidance
- **Vulnerability types:** Free-text now, may formalize based on corpus clustering
- **Actor roles:** Enumerated but extensible

### Phase Evolution
1. **Phase 1-2:** Accept free text, build seed vocabularies from extraction
2. **Weeks 7-8:** Formalize via corpus clustering
3. **Post-corpus:** Lock down vocabularies based on evidence

---

## Decision 10: Evidence Tracking - claim_ids on Everything

**Date:** Throughout ontology design  
**Context:** How do we link ontology entities back to source text?

### Decision
**Every relationship has claim_ids property. Nodes have evidence_cases.**

### Rationale
1. **Provenance:** Track which text passage supports each relationship
2. **Evidence evaluation:** Can flag low-confidence vs. high-confidence relationships
3. **Contradiction handling:** Same relationship with conflicting claim_ids shows disagreement
4. **Review workflow:** Enables reviewing extractions at claim level

### Schema
- **Relationships:** `claim_ids: array<uuid>` (required)
- **Nodes:** `evidence_cases: array<string>` (case IDs, optional)

### Implications
- Extraction must generate claim UUIDs and link them to relationships
- Graph queries can filter by evidence strength: "high-confidence REDUCES relationships only"

---

---

## Decision 11: RCC Shocks + Stresses Taxonomy Integration (Sprint 3)

**Date:** 2026-04-23  
**Context:** RCC Shocks and Stresses taxonomy (25 shocks, 45 stresses) loaded from `resources/Shocks and Stresses.xlsx`. Need to determine how to integrate with existing Hazard node and planning domain.

### Decision
**Extend Hazard vocabulary for non-climate shocks. Map stresses to existing nodes. No new Stress node type.**

### Rationale
1. **13 of 25 RCC shocks** are already covered by C40/Arup climate hazard vocabulary — no change needed
2. **12 non-climate shocks** (cyber attack, earthquake, disease outbreak, etc.) added via `hazard_source: "rcc"` property on Hazard — single node, two vocabularies, disambiguated by source
3. **RCC stresses are not a new ontology concept** — they are chronic urban conditions that distribute across existing nodes:
   - Environmental stresses (sea level rise, environmental degradation) → Hazard (slow-onset vocabulary)
   - Socioeconomic stresses (poverty, inequality) → Vulnerability.vuln_type
   - Governance stresses (corruption, poor governance) → Barrier
   - Urban development stresses (aging infrastructure) → Infrastructure.condition / UrbanSystem context

### Alternatives Rejected
- **New Stress node**: Would duplicate Vulnerability (socioeconomic stresses), Barrier (governance stresses), and Hazard (environmental stresses) — high redundancy, low query value
- **Merge all RCC into single Hazard vocabulary**: Mixing acute climate hazards with chronic socioeconomic stresses (poverty, structural racism) in a "Hazard" node would be semantically incoherent

### Changes Made
- Added `hazard_source: enum[c40_arup, rcc]` property to Hazard node
- Updated vocabulary_bindings to reference both C40/Arup and RCC vocabularies
- Full crosswalk documented in `alignment/framework-crosswalk.md` §4

### Deferred
- Extending `hazards.json` with actual RCC shock IDs (vocabulary task, not schema task)
- Formalizing `Vulnerability.vuln_type` controlled vocabulary from RCC stress list
- Adding slow-onset environmental stresses to hazards.json

---

## Decision 12: Framework Crosswalk Approach (Sprint 3)

**Date:** 2026-04-23  
**Context:** Three external frameworks reviewed against Adaptation Planning domain: C40 Impacts Taxonomy, ICLEI 5-Milestones, GCoM CRF.

### Decision
**Crosswalk documentation over ontology restructuring. Two targeted property additions only.**

### Key Findings
1. **ICLEI 5-Milestones**: All 5 milestones are representable in the existing ontology. No new node types needed. The planning lifecycle (Initiate → Investigate → Plan → Implement → Monitor) maps cleanly to Actor → ExposureUnit/Vulnerability → Plan/ResilienceGoal → Solution/Barrier → Outcome/Indicator.
2. **GCoM CRF**: Strong alignment. Our nodes were implicitly designed against GCoM disclosure categories. Minor gap: action implementation stage tracking.
3. **C40 Impacts Taxonomy**: Hazard vocabulary already aligned. Main work is vocabulary metadata (crosswalk from our solution categories to C40 intervention types) — not schema change.

### Changes Made
- Added `implementation_stage: enum[committed, in_planning, under_implementation, completed]` to PRESCRIBES relationship — aligns with C40, ICLEI-D, and GCoM CRF action status
- Full crosswalk documented in `alignment/framework-crosswalk.md`

### Standardization Opportunities (deferred)
- `Plan.plan_type` vocabulary formalization (ICLEI plan type alignment)
- Solution categories → C40/GCoM crosswalk in vocabulary metadata
- `Vulnerability.vuln_type` formal vocabulary

---

## Decision 13: DEPENDS_ON — Solution-to-Solution Dependency (Sprint 4)

**Date:** 2026-04-23
**Context:** Tech-enabled solutions frequently reference prerequisite systems (sensors before predictive maintenance; data exchange before digital twin). The original to-do proposed three separate relationships: POWERED_BY, INTEGRATES_WITH, MONITORS_VIA.

### Decision
**Add one `DEPENDS_ON` (Solution → Solution) relationship with a `dependency_type` property. Reject all three originally-proposed named relationships.**

### Rationale
1. **Edge economy:** Three separate relationship types for one semantic concept (prerequisite) inflates the graph schema and complicates extraction — the LLM must choose between nearly-synonymous labels. One typed relationship is sufficient.
2. **Not tech-exclusive:** Dependency between solutions recurs for non-tech solutions too (e.g., a cooling-center activation program depends on a heat early-warning system regardless of tech content). Naming the relationship `POWERED_BY` would incorrectly imply a tech-only pattern.
3. **CQ coverage:** CQ-31 through CQ-34 and CQ-37 are all expressible with `DEPENDS_ON` + `dependency_type` filter alone.
4. **Conceptual lineage:** ISO/IEC 30145-1's System-of-Systems framing was consulted as prior art. We adopted its conceptual insight (solutions form interdependent stacks) without importing its vocabulary or structure. See decision to ignore 30145-2.

### dependency_type values
- `requires_data_from` — target produces data source needs
- `runs_on_platform` — target provides infrastructure layer
- `integrates_with` — peer interoperability
- `physically_coupled_to` — shared physical infrastructure
- `programmatically_requires` — target is an operational prerequisite

### Extraction guard
Self-referential (Solution → Solution). Extraction must distinguish from `SUPPLIED_BY` (which targets a vendor, not another adaptation solution) and must not create trivial cycles.

### Implications
- Extraction schema will need a `context.solution_dependencies[]` array in Sprint 4
- High-inbound-degree solutions ("platforms") should be flagged for curator review

---

## Decision 14: maturity_level on Solution — Provisional (Sprint 4)

**Date:** 2026-04-23
**Context:** Investor CQs require distinguishing proven solutions from experimental ones. Existing `Outcome.evidence_level` measures strength of evidence for a specific outcome; no property captures solution-class maturity independently of any single deployment.

### Decision
**Add optional `maturity_level` enum to Solution: emerging / demonstrated / established. Mark provisional — CQ-36 is a falsifiability test.**

### Rationale
1. **Conceptually distinct from evidence_level:** Maturity is a property of the solution class (all cities combined); evidence_level is a property of a specific outcome claim. A widely-deployed solution could have poor evidence; a single pilot could have a rigorous RCT.
2. **Investor/planner utility:** CQ-35 (maturity distribution) and CQ-37 (what's emerging in a category) are real questions that `evidence_level` can't answer.
3. **Three levels, not nine:** Rejected full TRL scale — LLMs cannot reliably extract TRL-3 vs. TRL-4 from city plan language. Three levels map to language that appears in practice: pilot / working-reference-deployment / standard-practice.

### Falsifiability condition
CQ-36 is a crosstab test: once ≥20 tech-enabled solutions are extracted, if `maturity_level` and `Outcome.evidence_level` are near-perfectly correlated, `maturity_level` should be removed as redundant. If they diverge meaningfully, it earns its place.

### Implications
- Extraction prompt must distinguish maturity (what documents say about this solution *type* generally) from evidence level (how well *this deployment's outcomes* are documented)

---

## Decision 15: Mechanism Vocabulary Formalization — Tech-Native Types (Sprint 4)

**Date:** 2026-04-23
**Context:** Sprint 4 tech-enabled solutions review identified a gap: digital mechanisms (sense, forecast, automate, alert) were all collapsed into the existing `monitor` seed value, which was originally designed for passive/human-led observation.

### Decision
**Add four tech-native mechanism types to `mechanism_seed_vocabulary` in enums.json. Retain all original eight. Refine `monitor` description to clarify the distinction.**

### New values
- `sense_and_detect` — active digital sensing, discrete event/threshold detection
- `forecast_and_model` — computational forward prediction (ML, simulation, digital twin)
- `automate_and_control` — closed-loop machine actuation without human-in-the-loop
- `inform_and_alert` — targeted dissemination to trigger human action (distinct from automate_and_control: response is human)

### Key distinction
`monitor` = ongoing observation, often passive or human-led
`sense_and_detect` = active digital sensing with event detection logic
`automate_and_control` = machine closes the loop; no human required
`inform_and_alert` = machine opens the loop to a human; human closes it

### Status
Still free-text with seed vocabulary guidance (not a constraint). Full formalization via corpus clustering remains scheduled for Month 2.

---

## Decision 16: Equity Ontology — Vulnerable Populations + Justice Dimensions (Sprint 5)

**Date:** 2026-04-23
**Context:** EDF/Cornell study on AI equity impacts in climate adaptation requires the graph to answer: who is targeted, what equity outcomes are documented, and what justice dimensions are addressed. Previously, `Vulnerability.affected_group` was a free-text string, and no solution-level equity framing existed.

### Decision
**Four targeted additions, one new vocabulary. No new node types.**

1. **`Solution.equity_focus` (enum: none / co_benefit / primary_target)** — solution-level classification of equity intent
2. **`Solution.target_populations` (array<string>, vocab-bound)** — which vulnerable groups the solution is designed to serve
3. **`Outcome.justice_dimension` (array<enum>: distributive / procedural / recognitional / epistemic)** — Shi (2024) justice rubric applied to documented outcomes
4. **`Vulnerability.affected_group` (type change: string → array<string>, vocab-bound)** — replaces free-text with controlled terms
5. **`ExposureUnit.affected_group` (new, array<string>, vocab-bound)** — parallel to Vulnerability; captures population composition of exposure units
6. **`packages/ontology/schemas/vocabularies/vulnerable-populations.json`** — 18 population groups sourced from IPCC AR6, UNDRR Sendai, and EDF equity framing

### Justice dimensions (from Shi 2024 rubric)
| Dimension | What it captures |
|---|---|
| `distributive` | Who bears costs; who receives benefits |
| `procedural` | Who participates in and shapes decisions |
| `recognitional` | Whose knowledge and experience is acknowledged |
| `epistemic` | How knowledge is produced; whose expertise is legitimized |

### Rationale
1. **Study-driven:** EDF research questions require classifying solutions by equity intent and outcomes by justice type. The four dimensions are directly from the study's analytic framework.
2. **No new nodes:** Equity framing is a property of existing entities (Solution, Outcome, Vulnerability, ExposureUnit), not a new structural concept. Adding an "EquityProfile" node would separate equity from the entities it characterizes, making extraction harder and queries more complex.
3. **Two-level equity capture:** `Solution.equity_focus` is a high-level tag (easy to extract, useful for filtering). `Outcome.justice_dimension` is fine-grained evidence (requires more specific documentation). Both are optional — most solutions won't have rich equity documentation.
4. **`equity_focus ≠ justice_dimension`:** `equity_focus` is set on Solution based on design intent (from planning docs, program descriptions). `justice_dimension` is set on Outcome based on what is actually documented (measured or anecdotal evidence). A solution can be `primary_target` with no `distributive` outcomes documented if evidence is absent.
5. **Vocabulary choice:** 18 groups is comprehensive enough to cover IPCC/UNDRR categories and EDF-specific US context (renters, limited English proficiency, environmental justice communities) without over-segmenting. Groups are socially-defined, not geographic, to support cross-city comparison.

### Alternatives rejected
- **EquityDimension node:** Would require Solution -[HAS_EQUITY_PROFILE]-> EquityDimension subgraph — unnecessary complexity when properties on existing nodes are sufficient
- **Free-text `justice_dimension`:** Rejected immediately — the four Shi dimensions are the analytic instrument; they must be controlled values to enable cross-corpus comparison
- **Keeping `affected_group` as free-text:** Inconsistent "elderly" vs "older adults" vs "seniors" would break CQ-5 and CQ-38 query aggregations

### Implications
- Extraction prompt should look for: explicit population targeting language, participation/governance sections, knowledge co-production mentions, equity co-benefit claims
- CQ-5 is now fully expressible (previously deferred)
- CQs 38–44 (new equity section) exercise these additions
- EDF proposal PDF is available at ~/Downloads for reference during researcher prompt design

---

## Decision 17: CHANNELS_THROUGH — FinancingSource ↔ FinancialInstrument Linkage (v0.1)

**Date:** 2026-04-23
**Context:** FinancingSource (who provides money) and FinancialInstrument (how money is structured) were independent leaf nodes off Solution, with no link between them. The "World Bank via green bond" relationship was unrepresentable.

### Decision
**Add `CHANNELS_THROUGH` (FinancingSource → FinancialInstrument) relationship. Keep both types separate.**

### Rationale
1. **Multiple sources per instrument:** A blended finance instrument can have multiple funders. Merging the two types would lose this multiplicity.
2. **Three-way path:** Solution ←FUNDED_BY← FinancingSource →CHANNELS_THROUGH→ FinancialInstrument ←USES_INSTRUMENT← Solution captures the full financing story.
3. **Extraction clarity:** Source and instrument are often co-mentioned in text ("World Bank issued a $50M green bond"). Keeping them as separate nodes with a linking relationship gives the LLM clear extraction targets.

### Alternatives Rejected
- **Merge into single Financing node:** Would lose the many-to-many source↔instrument relationship. Most instruments have multiple funders.

---

## Decision 18: Actor Relationship Pruning (v0.1)

**Date:** 2026-04-23
**Context:** Actor had 7 relationships — more than any non-Solution node. Three were aspirational (absorbed from student ontology) but unlikely to be populated from solution/plan literature.

### Decision
**Remove REPORTS_TO, MONITORS, MANAGES. Keep IMPLEMENTED_BY, PARTICIPATES_IN, COORDINATES_WITH, ISSUED_BY (4 relationships).**

### Removed
| Relationship | Reason |
|---|---|
| REPORTS_TO (Actor → Actor) | Governance hierarchies rarely documented at actor-specific granularity in adaptation plans |
| MONITORS (Actor → Indicator) | M&E responsibility attribution too granular for current extraction scope |
| MANAGES (Actor → Mechanism) | Semantic collision — our Mechanism is functional ("absorb"), not governance ("revolving fund"). Actor "managing" an "absorb" mechanism is incoherent |

### Kept
| Relationship | Reason |
|---|---|
| IMPLEMENTED_BY (Solution → Actor) | Core relationship |
| PARTICIPATES_IN (Actor → Solution) | Distinct from IMPLEMENTED_BY — non-lead involvement |
| COORDINATES_WITH (Actor → Actor) | Multi-stakeholder governance; more prevalent than initially estimated |
| ISSUED_BY (Plan → Actor) | Plan authorship/ownership |

### Implications
- Reduces extraction complexity (fewer Actor-adjacent relationships to disambiguate)
- Can re-add REPORTS_TO/MONITORS/MANAGES if plan-domain extraction reveals they're actually populated

---

## Decision 19: Ontology v0.1 Consolidation

**Date:** 2026-04-23
**Context:** Ontology data was split across 4 files (types.json, relationships.json, vocabularies.json, draft-v0.json). draft-v0.json was stale (missing Sprint 3-5 additions). Maintaining parallel files caused drift.

### Decision
**Consolidate into single `ontology-v0.1.json`. Delete all four source files.**

### Changes in v0.1
- Added CHANNELS_THROUGH (Decision 17)
- Removed REPORTS_TO, MONITORS, MANAGES (Decision 18)
- Removed deprecated MANDATES (previously replaced by Plan PRESCRIBES Solution)
- Removed HINDERS.constraint_type property (values were echoed extraction schema relationship names, not meaningful types)
- Disambiguated Mechanism definition to explicitly state "functional adaptation process only"
- Final counts: 20 types, 34 relationships, 7 vocabularies

### File Changes
- NEW: `ontology/ontology-v0.1.json` — single canonical file
- DELETED: `ontology/draft-v0.json`, `ontology/types.json`, `ontology/relationships.json`, `ontology/vocabularies.json`
- UPDATED: `viewer.html` — single file loader, cross-filter types↔relationships

---

## Decision 20: v0.1.1 — Type Simplification and Relationship Cleanup

**Date:** 2026-04-23
**Context:** Review of v0.1 revealed redundant types, awkward relationship directions, and opportunities to simplify.

### Changes
- **TimePoint removed** — converted to year properties on relevant types (Policy.year_issued, Indicator.recorded_year; Solution.year_of_deployment already existed)
- **Infrastructure merged into UrbanSystem** — added infra_color, condition, capacity, service_coverage as optional properties
- **Policy removed** — regulatory context covered by EnablingCondition + Barrier with condition_type/barrier_type: "regulatory"
- **City renamed to Location** — with location_type enum (city, district, neighborhood, region, watershed, coastline, corridor), GeoJSON geometry, WITHIN self-relationship for hierarchical nesting
- **COORDINATES_WITH removed** — Actor self-relationship not extractable
- **ISSUED_BY reversed** — now Actor ISSUES Plan (active voice, reads naturally)
- **Multiple relationship renames** for clarity (IMPLEMENTED_BY, SUPPLIES, etc.)

### Result
17 types (down from 20), cleaned relationship set

---

## Decision 21: IPCC AR6 Risk-Reduction Pathways

**Date:** 2026-04-23
**Context:** The IPCC AR6 risk framework defines Risk = f(Hazard, Exposure, Vulnerability). The ontology had Solution --mitigates--> Hazard and Solution --reduces--> Vulnerability, but no explicit pathway for exposure reduction. Adaptive capacity was implicit in the Vulnerability definition but not surfaced through relationships.

### Decision
**Explicitly represent all three AR6 risk-reduction pathways as separate relationships:**

1. `Solution --mitigates--> Hazard` — reduce hazard intensity or frequency (e.g., mangrove restoration attenuates storm surge)
2. `Solution --reduces--> Vulnerability` — reduce sensitivity or build adaptive capacity (e.g., social safety net improves coping capacity)
3. `Solution --reduces exposure of--> ExposureUnit` — shield, relocate, or protect exposed populations/assets (e.g., sea wall protects coastal neighborhood)

**Mechanism** (via `Solution --works by--> Mechanism`) describes the functional process by which a solution achieves any of these three pathways — it is orthogonal to the pathway choice.

### Additional: Socially Constructed Vulnerability
Added `UrbanSystem --shapes--> Vulnerability` to reflect the AR6 position that vulnerability is produced through systemic urban conditions (housing quality, infrastructure deficits, service gaps) independent of hazard exposure.

### Rationale
- Makes extraction more precise — the LLM can classify which risk component a solution targets
- Aligns with IPCC AR6 Chapter 17 framework used across adaptation literature
- Keeps Mechanism as a separate node describing HOW (functional process) rather than WHAT (risk component)

---

## Decision 22: v0.3 Peer Review — Governance, Barriers, Hazard Scenarios, Comparability

**Date:** 2026-04-29
**Context:** Full peer review of v0.2 ontology conducted via Claude Opus (OPUS-ONTOLOGY-REVIEW-2026-04-29). Eight clarifying questions resolved. Full punch list implemented in v0.3.

### Key decisions

**BLOCKS vs. FACES direction (Q3):** BLOCKS is Barrier → Solution (must remove barrier for solution to proceed); FACES is Action → Barrier (fuzzier, action may work around it). This captures a real semantic distinction: solutions need barriers removed, actions can sometimes adapt around them. FACES source changed from Solution to Action.

**GovernanceStructure as a separate type:** Rather than overloading Stakeholder with governance semantics, a dedicated GovernanceStructure type captures formal bodies (interagency committees, public agencies, task forces, PPPs) with an authority_level (advisory/regulatory/operational) and mandate_description. GOVERNS (GovernanceStructure → Plan) and MEMBER_OF (Stakeholder → GovernanceStructure) provide the linkages.

**SSP-only climate scenarios (Q1b):** Hazard.climate_scenario uses IPCC AR6 SSP vocabulary (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5). Older RCP references from pre-2023 plans should be mapped to SSP equivalents by extractors. Crosswalk: RCP 4.5 ≈ SSP2-4.5, RCP 8.5 ≈ SSP5-8.5.

**RISK_ASSESSED_IN (Q5):** Added Hazard → Plan relationship to enable longitudinal comparison. Two successive plans can both link to the same hazard node to compare how the assessment changed (projection_year + climate_scenario capture within-plan temporal context; RISK_ASSESSED_IN captures plan-level provenance).

**other + _other_description convention (GC-1):** Every new or tightened enum gets an `other` value plus a companion `_other_description` free-text field. Ensures extraction never fails on outliers while preserving structured labels for ML training.

**Dropped items (GC-2):** EnablingCondition.scale_required and UrbanSystem.is_instance were not added — both are primarily useful for formal inference, not extraction or retrieval.

**Dropped items (user decision):** Solution.deployment_count_range dropped. Aggregation counts belong in graph queries, not schema properties.

**Mechanism vocabulary formalized:** Status changed from guidance-only to authoritative. Added restore, relocate, buffer, insulate, regulate as distinct mechanism types (with precise semantic distinctions from similar values). Added `other` value per GC-1 convention.

**Location comparability fields:** climate_zone (Köppen), population, coastal_status, income_classification (World Bank) added to Location type. Enables cross-city comparability queries.

**Action → Location direct link:** DEPLOYED_IN (Action → Location) added. Where IMPLEMENTED_IN captures general solution deployment geography, DEPLOYED_IN captures where a specific plan action is committed.

### Changes in v0.3

- **New type:** GovernanceStructure
- **New relationships (8):** LOCATED_IN, SHIFTS_RISK_TO, GOVERNS, COORDINATES_WITH (restored), BLOCKS, MEMBER_OF, RISK_ASSESSED_IN, DEPLOYED_IN
- **Modified relationships:** FACES source changed Solution → Action
- **Property additions:** Hazard (climate_scenario, projection_year), Location (4 comparability fields), ResilienceGoal (goal_text), Plan (review_cycle_years, plan_type → enum), Outcome (maladaptation/other + co_benefit_type), Indicator (measurement_period), DEMONSTRATES_PROGRESS_ON (achieved), Vulnerability (vuln_type → enum), PlanningData (7 properties)
- **Property removals:** UrbanSystem.infra_color
- **Vocabulary:** mechanism_seed_vocabulary → mechanism_vocabulary (authoritative), sdg_goals added to solution-categories.json

---

## Deferred Decisions (Post-Phase 2)

### 1. Separate GovernanceMechanism Node
**Why deferred:** Mechanism taxonomy work scheduled for Weeks 7-8  
**Revisit:** After corpus mining clarifies mechanism types

### 2. UrbanZone as Separate Node
**Why deferred:** Zone properties on IMPLEMENTED_IN sufficient for now  
**Revisit:** If multi-zone solutions become common or zones need governance properties

### 3. Outcome Subtypes
**Why deferred:** Outcome currently aggregates effectiveness_indicator, co_benefit, failure_mode  
**Revisit:** If different properties needed for each outcome type

### 4. ~~Policy Subtypes~~
**Resolved:** Policy node removed in v0.1.1 (Decision 20). Regulatory context now covered by EnablingCondition/Barrier with condition_type/barrier_type: "regulatory".

---

## Ontology Evolution Summary

| Phase | Types Added | Relationships Added | Key Decision |
|-------|-------------|---------------------|--------------|
| Initial | 15 | 18 | Solutions-focused baseline |
| Phase 2a | +1 (Vulnerability) | +8 (governance) | Planning context integration |
| Phase 2b | +1 (TimePoint) | +3 (temporal) | Temporal modeling |
| Phase 2c | +2 (Infrastructure, ExposureUnit) | +3 (exposure) | Infrastructure split, UNDRR alignment |
| Sprint 3 | 0 (properties only) | +1 property on PRESCRIBES | Framework crosswalk, RCC integration |
| Sprint 4 | +1 property on Solution | +1 (DEPENDS_ON) | Tech-enabled solution extensions |
| Sprint 5 | +3 properties on Solution, +1 on Outcome, +1 on Vulnerability (type change), +1 on ExposureUnit | 0 new relationships | Equity ontology — vulnerable populations vocabulary, justice dimensions |
| v0.1 | 0 | +1 (CHANNELS_THROUGH), -4 (REPORTS_TO, MONITORS, MANAGES, MANDATES) | Financing linkage, Actor pruning, consolidation |
| v0.1.1 | -3 (TimePoint, Infrastructure, Policy); City→Location | -1 (COORDINATES_WITH), renames/reversals | Type simplification, relationship cleanup |
| v0.1.2 | 0 | +2 (REDUCES_EXPOSURE, SHAPES) | IPCC AR6 risk-reduction pathways, socially constructed vulnerability |
| v0.2 | 0 | -4 deprecated (AUTHORED_BY, ALIGNS_WITH, SUPERSEDED_BY, REFERENCES); +4 restructured; +2 new (ENGAGES, GENERATES) | Public release cleanup — definitions rewritten, deprecated rels removed, schema fields stripped |
| v0.3 | +1 (GovernanceStructure) | +8 (LOCATED_IN, SHIFTS_RISK_TO, GOVERNS, COORDINATES_WITH, BLOCKS, MEMBER_OF, RISK_ASSESSED_IN, DEPLOYED_IN) | Peer review — governance, barriers, hazard scenarios, comparability fields |
| v0.2 | +1 (CapitalProject) | +9 (REALIZES, FUNDED_BY, COMMISSIONED_BY new; DEPLOYED_IN/USES_INSTRUMENT/IMPLEMENTED_BY/PRODUCES/FACES/SPECIFIES duplicate-id rows) | Resilience finance extension (Salkin / RCC, 5 May 2026) — capital-budget line items, debt-service modeling, multi-source funding stack, monetized co-benefits |
| **Total** | **21** | **53** | **Planning + solutions + tech + equity + consolidation + AR6 pathways + public release + peer review + resilience finance** |

---

## References

- **Student Ontology:** `resources/ruowen-climate-adaptation.py`
- **IPCC AR6 WGII:** Chapter 17 (Decision-Making Options for Managing Risk)
- **UNDRR Sendai Framework:** Disaster risk reduction framework
- **CRF 2024:** City Resilience Framework (Resilient Cities Network)
- **C40 Climate Hazards:** Climate hazard typology (13 categories, 31 hazards)

---

## Notes for Future Work

1. **Extraction Schema Update (May 15):** All Phase 2 additions must be added to extraction-schema-v1.json
2. **Viewer Testing:** Ensure all new nodes/relationships render correctly
3. **Query Patterns:** Document example queries enabled by Phase 2 additions
4. **Documentation:** Update TYPES-EXTRACTION-SUMMARY.md and RELATIONSHIPS-EXTRACTION-SUMMARY.md
5. **Validation:** Test ontology against real adaptation plans to validate planning-domain completeness

## Corpus mining distribution — rejected/deferred (2026-04-24)

_Applied from decisions/distribution-decisions.json._

- **[rejected]** `hazard` / `hazard:rcc.inadequate_basic_services` — Inadequate Basic Municipal Services
  - Rationale: Too broad; already covered by rcc.infrastructure_failure when chronic.
- **[rejected]** `solution_category` / `solution_category:waste_management` — Waste Management
  - Rationale: No clear climate adaptation or resilience application.
- **[rejected]** `hazard` / `hazard:rcc.waste_management_systems` — Waste Management Systems
  - Rationale: no clear climate adaptation and resilience application
- **[rejected]** `hazard` / `hazard:rcc.housing_vulnerability` — Housing Vulnerability / Inadequate Housing
  - Rationale: not a climate hazard, should be covered in a vulnerability vocabulary
- **[rejected]** `hazard` / `hazard:rcc.sustainable_mobility_infrastructure` — Sustainable Mobility Infrastructure
  - Rationale: not clear enough connection to adaptation and resilience
- **[rejected]** `urban_sector` / `urban_sector:agricultural_finance_insurance` — Agricultural Finance & Risk Management
  - Rationale: not really urban relevant
- **[rejected]** `solution_category` / `solution_category:disaster_preparedness` — Disaster Preparedness and Emergency Response
  - Rationale: this isnt functional, its sectoral. we will accept the new urban sector recommdnation instead to tag these

## Corpus mining mechanisms — rejected/deferred (2026-04-25)

_Applied from decisions/mechanisms-decisions.json._

- **[rejected]** `mechanism` / `9` — Provide Integrated Climate Decision-Support Tools
  - Rationale: these all seem to be the same example, and it doesnt make sense to add a mechanism for one example. this can also be classified under forecast_and_model
- **[rejected]** `mechanism` / `247` — Deploy Integrated Urban Resilience Assessment Tools
  - Rationale: can be put under forecast_and_model Forecast and Model
- **[rejected]** `mechanism` / `98` — Assess Urban Resilience Using Integrated Models
  - Rationale: categorize under forecast_and_model Forecast and Model
- **[rejected]** `mechanism` / `588` — Model Urban Drainage Systems
  - Rationale: categorize under forecast_and_model Forecast and Model
- **[rejected]** `mechanism` / `228` — Generate Evidence-Based Adaptation Recommendations
  - Rationale: categorize under forecast_and_model
- **[rejected]** `mechanism` / `432` — Train Staff in Climate Modeling Tools
  - Rationale: categorize under forecast_and_model
- **[rejected]** `mechanism` / `48` — Maintain Vulnerable Population Registry
  - Rationale: categorize under monitor and/or govern
- **[rejected]** `mechanism` / `302` — Monitor Hydrological Conditions
  - Rationale: categorize under monitor
- **[rejected]** `mechanism` / `114` — Provide Backup Power via Distributed Energy Storage
  - Rationale: categorize under harden
- **[rejected]** `mechanism` / `10` — Disseminate Real-Time Environmental Data
  - Rationale: categorize under monitor and / or inform_and_alert
- **[rejected]** `mechanism` / `37` — Disseminate Emergency Alerts
  - Rationale: categorize under inform_and_alert
- **[rejected]** `mechanism` / `53` — Assess Resilience Using Standardized Index
  - Rationale: categoriize under monitor and/or govern
- **[rejected]** `mechanism` / `124` — Downscale Climate Projections
  - Rationale: categorize under forecast_and_model
- **[rejected]** `mechanism` / `170` — Deploy Decision-Support Tools
  - Rationale: categorize under forecast_and_model and/or govern
- **[rejected]** `mechanism` / `237` — Model Economic Impacts of Disruptions
  - Rationale: categorize under forecast_and_model
- **[deferred]** `mechanism` / `326` — Deploy Geothermal Heat Pumps
  - Rationale: categorize under harden (for now)
- **[rejected]** `mechanism` / `445` — Establish Performance Targets for Planning Controls
  - Rationale: categorize under monitor and /or govern
- **[rejected]** `mechanism` / `4` — Harden Critical Infrastructure Against Flooding
  - Rationale: categorize under harden

## Corpus mining plans — rejected/deferred (2026-04-26)

_Applied from decisions/plans-decisions.json._

- **[rejected]** `plan_property` / `prop:geographic_scope` — Geographic Scope
  - Rationale: redundant with the geogrpahy relationship
- **[rejected]** `plan_relationship` / `rel:FUNDED_BY` — FUNDED_BY
  - Rationale: these will almost all be funded by municpalities
