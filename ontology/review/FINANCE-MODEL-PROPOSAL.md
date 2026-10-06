# Finance in the ontology — a rebuild for cross-city comparison (proposal)

*Proposal, 2026-10-06 · Anthony + Claude. **Adopted the same day as Decision 43 and implemented in v1.1** (`scripts/migrations/v1_1_from_v1_0.py`); §8's F1–F7 are all "yes". Kept as the rationale. It replaces the
finance part of adaptbase-core#298 / #342 (O1–O5) and PR #21 topics H and I with one
model, designed from the questions the graph has to answer rather than from the
types v0.1 happened to start with. It keeps every decision from #298 that was
already right.*

## 1. Why rebuild rather than patch

The extraction exists so that patterns can be read **across cities**: what share of
adaptation work each city funds federally, which cities borrow and which pay as
they go, which federal programmes fund the most adaptation, where the funding gap
is. Every such question needs two things the current model does not give:

- a small number of **closed, comparable dimensions** (who pays; in what form; at
  what stage), and
- **nodes that merge across cities**, so that "FEMA" is one node, not eleven.

Three faults in v1.0 block that, all visible in the Houston run
(adaptbase-core `_planning/research-briefs/harvard-finance-demo*.md`):

1. **One vocabulary mixes two axes.** `financing_model` (12 values, on the
   `USES_INSTRUMENT` edge) holds *who* (`national_government`, `development_banks`,
   `private_sector`, `municipal_budget`, `climate_funds`, `international_oda`,
   `regional_funds`) and *how* (`grants`, `commercial_loans`, `green_bonds`,
   `public_private_partnership`, `blended_finance`) in the same field. You cannot
   group by source tier or by form of money, because they are the same column.
   `instrument_type` (18 values, on `FinancialInstrument`) overlaps the *how* half.
2. **Kinds become nodes.** Every mention of "grant" or "public-private partnership"
   became its own `FinancialInstrument` node: 75 nodes named "grant" today, and
   Houston would have made "public-private partnership" five times. Counting
   "actions funded by grants" means counting across 75 differently spelled nodes.
3. **Money facts sit on shared things.** `FinancingSource.amount_usd` and
   `FinancialInstrument.amount_usd` put one city's number on a node other cities
   share. A funder has no single amount; a programme has a ceiling, not an
   allocation.

A fourth, smaller fault: the funding fact has no identity of its own. It is an edge
keyed by `(action, FUNDED_BY, funder)`, so an action that receives two FEMA awards
in two years can hold one amount, and one award that pays for three actions has to
be copied onto three edges and then summed three times.

## 2. What the documents actually say

Six kinds of statement, from the 613 staged `FinancingSource` units (#298 §2) and
the 114 Houston facts (#342 §12):

| statement | example | seen |
|---|---|---|
| an **organisation** gave or will give money | "supported by FEMA", "World Bank", "Rockefeller Foundation" | 217 units |
| a **named pot of money** was drawn on | "Hazard Mitigation Grant Program", "Oakland General Fund", "Measure FF", "stormwater utility fee" | 217 |
| a **kind of money**, no giver named | "through grants", "private investment", "EU funds" | 90 |
| a **kind of arrangement**, nothing named | "ground lease", "tax abatement", "public-private partnership", "a loan" | Houston: 18 of 23 |
| a **specific issued instrument** with its own terms | "Harris County 2018 Flood Bond Program, $2.5B", "Miami Forever Bond" | 5 + Houston 5 |
| a **money fact about the funding itself** | "$2.1M (2019)", "up to £100,000", "awarded", "seeking funding" | on most rows |

And things that are not finance and were swept in: "community land trust" (an
ownership model), "developer agreement" (a contract), organisations staged as
instruments. They go to review, not into the model.

## 3. Principles (from #298 §3, kept)

1. One real-world thing, one node. Roles are edges.
2. A fact enters the graph at the grain its source states. "Funded by FEMA" is not
   "funded by FEMA's HMGP"; "funded through grants" names no funder at all.
3. Nodes are things that exist on their own; properties describe something. A
   funder and a fund exist; "grants" describes the money.
4. Money facts belong to the funding fact, never to the funder or the fund.

And one added here:

5. **Anything that has to be compared across cities is a closed enum or a merging
   node.** Free text is provenance, never a dimension.

## 4. The model

### 4.1 Nodes

| node | what it is | identity | state |
|---|---|---|---|
| **Stakeholder** (existing) | an organisation that gives, administers or issues money: FEMA, HUD, World Bank, City of Houston, Harris County, a foundation | Wikidata QID (organisation resolver, #298 §6) | decided: #298 §4.1, #342 §13 2a |
| **FundingStream** (today's `FinancingSource`, narrowed and renamed) | a named pot of money with an owner: HMGP, Green Climate Fund, Oakland General Fund, Measure FF, Houston's stormwater fee | its own QID if it has one; otherwise `<owner QID>:<normalised name>` | O1, plus the rename |
| **FundingAllocation** (new) | one flow of money, as stated by a source: an award, an appropriation, a bond draw, a pledge. The thing that carries amount, period and status | instance type; never merges by name across documents | new |
| **FinancialInstrument** (existing, narrowed) | one specific issued or contracted instrument with its own terms: a bond issue, a loan, a lease. Keeps `principal_amount_usd`, `interest_rate`, `loan_term_years`, `annual_debt_service_usd`, `issuance_year`, `maturity_year`, `credit_rating` | name + issuer | narrowed; `amount_usd` and `issuer` (string) removed, see 4.3 |

**Generic kinds are never nodes.** "Grants", "a loan", "ground lease", "PPP" are
enum values on the FundingAllocation (4.4). This reverses the 2026-10-05 decision
in #342 §12.1 (one shared `FinancialInstrument` node per kind). Reason: #298 already
makes a generic *funder* a property; making a generic *instrument* a node means
every "share of actions using bonds" query has to union enum values with
nodes-of-kind. With one rule, every such query is one `GROUP BY`. The explorer can
facet on the enum.

### 4.2 Edges

```
FundingAllocation —FUNDS→ Action | CapitalProject        {share_percent, claim_ids}
FundingAllocation —PROVIDED_BY→ Stakeholder | FundingStream   {claim_ids}
FundingAllocation —USES_INSTRUMENT→ FinancialInstrument  {claim_ids}
FundingStream —ADMINISTERED_BY→ Stakeholder | Jurisdiction    {claim_ids}
FinancialInstrument —ISSUED_BY→ Stakeholder                   {claim_ids}
```

Each FundingAllocation has at least one `FUNDS` edge. `PROVIDED_BY` and
`USES_INSTRUMENT` exist only when the text names the funder or the instrument.
"Funded through grants" is a FundingAllocation with `instrument_class: grant`, one
`FUNDS` edge, and no `PROVIDED_BY`. Everything is read from one node type.

`FUNDS` to several targets with `share_percent` is how one award paying for three
actions is recorded once and summed once.

**Retired:** `FUNDED_BY` (Action | CapitalProject → FinancingSource; it becomes a
FundingAllocation with two edges), `USES_INSTRUMENT` from Action and CapitalProject
(moves to the allocation), `CHANNELS_THROUGH` (0 live edges; what it meant is now
`PROVIDED_BY` + `USES_INSTRUMENT` on the same allocation).

**Unchanged:** `Action.cost_usd`, `Action.financing_status`,
`CapitalProject.total_capex_usd`, `annual_opex_usd`, `funding_year_breakdown`,
`CapitalProject.financing_status`. Cost is the thing's own property; funding is the
allocation.

### 4.3 Properties

**FundingAllocation**

| property | type | note |
|---|---|---|
| `label` | string | optional; the source's own name for the award if it has one ("HMGP award 2019") |
| `amount` | number | as stated, never converted |
| `currency` | string (ISO 4217) | |
| `amount_qualifier` | enum `exact \| up_to \| approximately \| total_programme \| share_of_total` | |
| `period_start_year`, `period_end_year` | integer | a single year is start = end |
| `funding_status` | enum `potential \| applied \| committed \| awarded \| disbursed \| withdrawn` | progress-type: a dated-observation series under the v1.1 topic E rule, scalar derived |
| `source_tier` | enum, axis A (4.4) | stated when no funder node is named; derived from the funder when one is |
| `instrument_class` | enum, axis B (4.4) | |
| `instrument_type` | enum, the existing 18 values + the clear Houston additions, nested under `instrument_class` | optional refinement |
| `is_climate_specific` | boolean | the money was earmarked for climate/resilience, as opposed to a general stream drawn on |

**FundingStream** (from `FinancingSource`): keep `source_name`, `source_type`
(renamed to `stream_type`: `programme \| fund \| budget_line \| ballot_measure \|
fee_or_levy \| appropriation \| other`), `accreditation_modality`; add `max_award`
+ `max_award_currency` (a programme ceiling is a property of the programme); drop
`amount_usd`.

**FinancialInstrument**: drop `amount_usd` (the draw is on the allocation) and the
free-text `issuer` (now the `ISSUED_BY` edge); keep the debt-service properties;
`instrument_type` stays, as the subtype of `instrument_class`.

**Stakeholder**: unchanged. Its `stakeholder_type` already distinguishes
`municipal_government`, `regional_government`, `national_government`, `utility`,
`private_sector`, `ngo`, `international_organization`; `source_tier` is derived from
it when the funder is named.

### 4.4 The two axes that replace `financing_model`

**Axis A, `source_tier`: who pays.**
`local_government | regional_or_state | national | international_multilateral |
private | philanthropic | utility_ratepayer | mixed`

**Axis B, `instrument_class`: what form the money takes.** The existing
`instrument_type` values sit under it as subtypes.

| `instrument_class` | `instrument_type` subtypes |
|---|---|
| `grant` | `grant`, `federal_cost_share`, `state_cost_share` |
| `debt` | `general_obligation_bond`, `revenue_bond`, `green_bond`, `climate_bond`, `resilience_bond`, `outcome_bond`, `sustainability_linked_loan`, `revolving_fund`, **`loan`** (new) |
| `own_revenue` | `municipal_capital_appropriation`, `direct_allocation` |
| `fee_or_levy` | `special_assessment`, `ratepayer_funded` |
| `tax_based` | `tax_increment_financing`, **`tax_abatement`** (new) |
| `private_investment` | — |
| `public_private_partnership` | — (today only in `financing_model`) |
| `risk_transfer` | **`insurance`** (new) |
| `land_or_in_kind` | **`ground_lease`** (new) |
| `blended` | `blended_finance` |
| `other` | `other` |

`financing_model` is deprecated: each of its 12 values maps to one `source_tier`
or one `instrument_class`, which is the migration table for the 0 live and N staged
edges that carry it. Not added as instrument types: community land trust (an
ownership model), developer agreement (a contract), investment fund (a stream).

Both axes are closed. "What share of Houston's adaptation funding is federal
grants?" is `GROUP BY source_tier, instrument_class` over FundingAllocation joined
to Jurisdiction through the funded Action.

## 5. Worked examples

*"The East End redevelopment will be financed through a ground lease and property
tax abatements."* (Houston)

```text
FundingAllocation {source_tier: local_government, instrument_class: land_or_in_kind, instrument_type: ground_lease}
    —FUNDS→ Action "East End redevelopment"
FundingAllocation {source_tier: local_government, instrument_class: tax_based, instrument_type: tax_abatement}
    —FUNDS→ Action "East End redevelopment"
```

No funder, stream or instrument node is created. "How many cities use tax
abatement for adaptation?" is one filter.

*"Funded through a FEMA Hazard Mitigation Grant Program award of $2.1M (2019)."*

```text
FundingAllocation {amount: 2100000, currency: USD, amount_qualifier: exact,
                   period_start_year: 2019, funding_status: awarded,
                   source_tier: national, instrument_class: grant}
    —FUNDS→ Action
    —PROVIDED_BY→ FundingStream "Hazard Mitigation Grant Program"
                      —ADMINISTERED_BY→ Stakeholder "FEMA"
```

*"The project is supported by FEMA."* The stream is not stated; the fact is
recorded at the organisation grain:

```text
FundingAllocation {source_tier: national}  —FUNDS→ Action  —PROVIDED_BY→ Stakeholder "FEMA"
```

*"Harris County's $2.5 billion 2018 flood bond will fund the Brays Bayou widening
and the Hunting Bayou detention basin."*

```text
FinancialInstrument "Harris County 2018 Flood Bond" {principal_amount_usd: 2.5e9, issuance_year: 2018}
    —ISSUED_BY→ Stakeholder "Harris County"
FundingAllocation {source_tier: regional_or_state, instrument_class: debt, instrument_type: general_obligation_bond}
    —PROVIDED_BY→ Stakeholder "Harris County"
    —USES_INSTRUMENT→ FinancialInstrument "Harris County 2018 Flood Bond"
    —FUNDS→ CapitalProject "Brays Bayou widening"
    —FUNDS→ CapitalProject "Hunting Bayou detention basin"
```

One allocation, two targets; the bond's principal is stated once.

*"Funded through grants and the City's General Fund."*

```text
FundingAllocation {instrument_class: grant}                                   —FUNDS→ Action
FundingAllocation {source_tier: local_government, instrument_class: own_revenue} —FUNDS→ Action
    —PROVIDED_BY→ FundingStream "General Fund" —ADMINISTERED_BY→ Jurisdiction "Oakland"
```

## 6. Against #298 / #342 (O1–O5)

| | O1–O5 as written | this proposal |
|---|---|---|
| organisations are Stakeholders | yes | same |
| FinancingSource = named stream, `ADMINISTERED_BY` owner | yes (O1, O4) | same; renamed `FundingStream` |
| money facts off the funder and stream | yes (O1) | same |
| money facts on the `FUNDED_BY` edge (O3) | yes | **on a FundingAllocation node**; `FUNDED_BY` retired |
| generic funders as `Action.funding_types[]` (O5) | yes | **a FundingAllocation with no `PROVIDED_BY`**; no Action property |
| generic instruments | one shared node per kind (#342 §12.1) | **enum on the allocation; no node** |
| `financing_model` | kept | **replaced by `source_tier` + `instrument_class`** |
| `CHANNELS_THROUGH` | kept, Stakeholder may be source (O2) | **retired** |
| `FUNDED_BY` may target Stakeholder (O2) | yes | subsumed: `PROVIDED_BY` targets Stakeholder or FundingStream |
| FinancialInstrument | unchanged | named issues only; gains `ISSUED_BY`; loses `amount_usd`, `issuer` |
| several awards, one pair | on evidence rows | **one allocation each** |

Everything #298 decided about identity (QIDs, owner-keyed streams, the naming rule
in §4.3, the resolver, seeding never closing discovery) stands unchanged.

## 7. What happens to what is staged

| staged | becomes |
|---|---|
| 217 organisation units | Stakeholder (retype + QID), as #298 §5 |
| 217 stream units | FundingStream + `ADMINISTERED_BY`, as #298 §5 |
| 90 generic-kind units | a FundingAllocation per funded action with `source_tier` / `instrument_class`; no node for the kind |
| 930 `FUNDED_BY` / `CHANNELS_THROUGH` edges | each `FUNDED_BY` → one FundingAllocation + `FUNDS` + `PROVIDED_BY`; each `CHANNELS_THROUGH` folds its instrument onto the allocation of the same action, else is dropped |
| Houston: 5 named instruments | FinancialInstrument + `ISSUED_BY` |
| Houston: 6 kind mentions, 75 live "grant" nodes | `instrument_class` / `instrument_type` on the allocation; the kind nodes are deleted after their edges are rewritten |
| 43 units carrying `amount_usd` | allocation `amount` or stream `max_award`, sorted at review |

The promotion step already creates nodes and edges from a reviewed unit; what it
needs is a rule that a funding fact promotes as a node plus edges rather than as
one edge. The staged-unit retype and edge-retarget tooling #298 §6 asks for is
the same work.

## 8. Decisions needed

| # | decision | proposal |
|---|---|---|
| F1 | Reify the funding fact (FundingAllocation) rather than carry it on `FUNDED_BY` | yes (Anthony, 2026-10-06: one award to several actions is the common case) |
| F2 | Rename `FinancingSource` → `FundingStream` | yes; the old name invited the organisation/stream mix-up that produced 0 promotions |
| F3 | Generic instrument kinds: enum on the allocation, not shared nodes (reverses #342 §12.1) | yes |
| F4 | Replace `financing_model` with `source_tier` + `instrument_class` | yes; deprecated with a value map |
| F5 | Retire `CHANNELS_THROUGH` | yes (0 live edges) |
| F6 | Ships in v1.1 (one bump with the Solution and plan-goal changes) or v1.2 | **v1.1**, so that funders promote once and never under the retired shape |
| F7 | `funding_status` follows the dated-observation rule (topic E) | yes |

## 9. Cost, honestly

- Six predicate rows change in core's `predicate_edges` (three retired, five
  added); the seed migration generator handles it, but the extraction prompt, the
  judge and the review options all learn a node type that did not exist.
- The explorer and the MCP tools gain a hop: "who funds this action" is
  Action ← `FUNDS` ← FundingAllocation → `PROVIDED_BY`. One SQL view
  (`v_action_funding`) flattens it for every consumer.
- 930 staged edges and 75+ live kind nodes are rewritten in a tracked run. None of
  it is re-extraction: the evidence rows hold every value.
- Houston's funders wait for the bump, as #342 §13 5 already decided. Houston's
  instruments, which #342 wanted promoted first under today's shape, now also
  wait; the delay is the same bump.

## 10. Not in this proposal

- A `FundingAward` sub-type or an award registry with external ids (USAspending,
  SAM). Possible later; nothing here blocks it.
- Currency conversion. `amount` is stored as stated; conversion is a read-time
  concern with a dated rate.
- Modelling of repayment flows, debt-service schedules beyond the existing
  FinancialInstrument properties, or revenue models of a project.
- Delivery arrangements (developer agreements, land trusts, concessions as a
  governance form). They are Stakeholder `org_form` or Mechanism questions.

## 11. Sources

- adaptbase-core#298 (financing model), #342 (staged go, Houston extension, §13
  answers), `_planning/research-briefs/harvard-finance-demo*.md`,
  `reviews/normalize-2026-10-05.csv`.
- adaptbase-ontology PR #21 topics H and I; `ontology-v1.0.jsonld` (FinancingSource,
  FinancialInstrument, FUNDED_BY, USES_INSTRUMENT, CHANNELS_THROUGH);
  `vocabularies/enums.json` (`instrument_type`, `financing_model`,
  `financing_status`).
- Decision 33 (v0.8), on which grain carries deployment facts.
