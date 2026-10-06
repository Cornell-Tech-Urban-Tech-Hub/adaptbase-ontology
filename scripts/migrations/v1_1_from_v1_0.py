#!/usr/bin/env python3
"""Build ontology/ontology-v1.1.jsonld and the v1.1 vocabulary edits from v1.0.

Run with: uv run scripts/migrations/v1_1_from_v1_0.py
Re-runnable: ontology-v1.1.jsonld, solution-concepts.json and versions.json are
rebuilt from v1.0 + the seed each time (a hand edit to them is overwritten);
enums.json and solution-categories.json are edited in place and skipped when the
v1.1 blocks are already present.

What it applies is the v1.1 decision set of 2026-10-06 (Anthony, after
consulting Fengze), recorded in ontology/decisions-log.md Decisions 35-43 and
summarised in ontology/review/V1.1-CHANGE-LIST.md §0. Every rule below carries
the decision it implements.
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ONT = REPO / "ontology"
VOC = ONT / "vocabularies"
SRC = ONT / "ontology-v1.0.jsonld"
DST = ONT / "ontology-v1.1.jsonld"
CONCEPT_SEED = Path(__file__).with_name("solution-concepts-seed.json")

UPDATED = "2026-10-06T12:00:00.000Z"


def load(p):
    return json.loads(p.read_text())


def dump(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def camel(pred):
    parts = pred.lower().split("_")
    return parts[0] + "".join(w.capitalize() for w in parts[1:])


def prop(id, type, required=False, **kw):
    p = {"id": id, "type": type, "required": required}
    p.update(kw)
    return p


def enum_prop(id, block, values, required=False, note=None):
    p = prop(id, "enum", required, values=values)
    if note:
        p["note"] = note
    p["vocabulary_binding"] = {"vocab": "enums", "field": block}
    p["ab:boundToVocabulary"] = {"@id": f"abv:enums-{block}"}
    return p


def observations(scalar, note_extra=""):
    """Decision 40 (topic E): progress-type properties are a dated series."""
    return prop(
        f"{scalar}_observations",
        "array<object>",
        note=(
            f"v1.1 (Decision 40). Dated observations of `{scalar}`: each element is "
            "{value, as_of, as_of_basis, source_type, claim_ids}. `value` takes the "
            f"same values as `{scalar}`; `as_of` is the date the status describes "
            "(year or month precision; null if unknown), not the document date; "
            "`as_of_basis` is stated | document_date | reporting_cycle; `source_type` "
            "follows enums.claim_source_type; `claim_ids` is the element's own "
            f"provenance. The scalar `{scalar}` is derived: the value with the latest "
            "`as_of` (on a tie, the existing value). Promotion appends; it never "
            "files a newer observation as a conflict." + note_extra
        ),
    )


def by_id(items, id):
    return next(x for x in items if x["id"] == id)


def drop_props(t, ids):
    before = len(t["properties"])
    t["properties"] = [p for p in t["properties"] if p["id"] not in ids]
    assert len(t["properties"]) == before - len(ids), (t["id"], ids)


def add_props(t, props, after=None):
    if after is None:
        # keep claim_ids last on edges
        tail = [p for p in t["properties"] if p["id"] == "claim_ids"]
        head = [p for p in t["properties"] if p["id"] != "claim_ids"]
        t["properties"] = head + props + tail
    else:
        i = [p["id"] for p in t["properties"]].index(after) + 1
        t["properties"][i:i] = props


def main() -> None:
    o = load(SRC)
    types = o["types"]
    rels = o["relationships"]
    T = {t["id"]: t for t in types}

    # ------------------------------------------------------------------ A. Solution
    s = T["Solution"]
    s["definition"] = (
        "A reusable class of climate adaptation intervention, technology or approach — "
        "'green roofs', 'cooling centres', 'managed retreat' — shared by every city that "
        "deploys it. Classified by identity (what it IS); function is expressed via typed "
        "relationships (MITIGATES, OPERATES_ON, WORKS_BY, PRODUCES). A named programme, "
        "project, ordinance, facility or pilot in one place is an Action (or a "
        "CapitalProject), never a Solution; it IMPLEMENTS the Solution class."
    )
    s["extract_hint"] = (
        "Look for the reusable class an intervention belongs to — e.g., 'green roofs', "
        "'flood early warning system', 'mangrove restoration', 'cooling centres' — and "
        "prefer a name from the solution-concepts vocabulary. A named local programme or "
        "project ('Cool Roofs for Communities', 'Bayou Greenways 2020', 'the City's "
        "Retrofit Grants Program') is an Action that IMPLEMENTS the class; do not emit it "
        "as a Solution. If the class is real but absent from the vocabulary, emit it with "
        "proposed: true."
    )
    s["notes"] = (
        "Solutions are reusable classes of intervention, independent of any specific "
        "deployment location or plan. v1.1 (Decision 35): a Solution property must be true "
        "of every deployment of the class. The deployment-grain properties "
        "(year_of_deployment, maturity_level, equity_focus, target_populations) were "
        "removed; their facts live on Action (start_year, equity_focus, "
        "target_populations) or are derived across Actions (maturity). `concept_id` binds "
        "the node to the governed solution-concepts list; `category_id`, `subcategory_id` "
        "and `ipcc_action_types` are copied from the concept by the seeder and never "
        "written by extraction."
    )
    drop_props(
        s,
        {"year_of_deployment", "maturity_level", "equity_focus", "target_populations"},
    )
    by_id(s["properties"], "description")["note"] = (
        "v1.1 (Decision 35): the class definition — what the Solution is, in general, "
        "with no city, year or project. Chunk extraction does not write it; a sentence "
        "about one deployment is provenance and belongs in the evidence row."
    )
    by_id(s["properties"], "alternative_names")["note"] = (
        "Synonyms of the class ('white roofs' for cool roofs). Seeded from the concept's "
        "aliases; extraction may add. The legacy key `aliases` is renamed to this in v1.1."
    )
    cid = by_id(s["properties"], "category_id")
    cid["required"] = False
    for pid in ("category_id", "subcategory_id", "ipcc_action_types"):
        p = by_id(s["properties"], pid)
        p["derived_from"] = "concept_id"
        p["note"] = (
            "v1.1 (Decision 35): derived — copied from the solution-concepts entry when "
            "`concept_id` is set, by the seeder only; extraction never writes it. Present "
            "exactly when `concept_id` is."
        )
    add_props(
        s,
        [
            prop(
                "concept_id",
                "string",
                vocabulary="solution-concepts",
                note=(
                    "v1.1 (Decision 35). The governed concept this Solution is; identity-grade, "
                    "like Hazard.hazard_id. Null for an open-catalog node not yet mapped. New "
                    "concepts enter only through the proposal queue (a `proposed: true` unit "
                    "reviewed by a maintainer), never by extraction."
                ),
                **{"ab:boundToVocabulary": {"@id": "abv:solution-concepts"}},
            )
        ],
        after="description",
    )
    s["vocabulary_bindings"] = [
        {"vocab": "solution-concepts", "field": "concept_id"},
        {"vocab": "solution-categories", "field": "category_id, subcategory_id"},
        {"vocab": "enums", "field": "ipcc_action_types"},
    ]

    # ------------------------------------------------------------------ D. Action
    a = T["Action"]
    a["definition"] = (
        "A specific activity that an actor has proposed, committed to or carried out in a "
        "particular place and timeframe. Most Actions are specified by a Plan; a specific "
        "activity found in a budget, a progress report or a project page is still an Action "
        "when its Plan is unknown. An Action is the activity, not the asset it builds and not "
        "a budget line (that is a CapitalProject). Distinct from Solution, which is the "
        "reusable class an Action IMPLEMENTS. A deployment of a Solution that a plan cites in "
        "another city is an Action DEPLOYED_IN that city."
    )
    st = by_id(a["properties"], "status")
    st["values"] = [
        "not_started",
        "committed",
        "in_planning",
        "under_implementation",
        "on_hold",
        "completed",
        "cancelled",
    ]
    st["note"] = (
        "Implementation status as of the latest observation (see status_observations). "
        "Definitions per value in enums.json#action_status (Decision 39); aligned with C40, "
        "ICLEI and GCoM action status vocabularies, with not_started and on_hold added in v1.1."
    )
    st["vocabulary_binding"] = {"vocab": "enums", "field": "action_status"}
    st["ab:boundToVocabulary"] = {"@id": "abv:enums-action_status"}
    add_props(
        a,
        [
            prop(
                "alternative_names",
                "array<string>",
                note="v1.1 (Decision 39). Other names the action is known by; replaces the legacy key `aliases`.",
            ),
        ],
        after="action_name",
    )
    add_props(a, [observations("status")], after="status")
    add_props(
        a,
        [
            prop(
                "is_pilot",
                "boolean",
                note="v1.1 (Decision 39). True when the source calls the activity a pilot, trial or demonstration; written only when true. Pilot-ness is orthogonal to status.",
            ),
        ],
        after="is_priority",
    )
    add_props(a, [observations("financing_status")], after="financing_status")
    add_props(
        a,
        [
            enum_prop(
                "equity_focus",
                "equity_focus",
                ["none", "co_benefit", "primary_target"],
                note="v1.1 (Decision 36, from Solution). Whether equity is a primary design target of this action, a documented co-benefit, or not addressed. Design intent as the source states it; distinct from REDUCES_EXPOSURE, which asserts that exposure fell.",
            ),
            prop(
                "target_populations",
                "array<string>",
                vocabulary="vulnerable-populations",
                note="v1.1 (Decision 36, from Solution). Vulnerable population groups this action is designed to serve, as the source states. Bound to vulnerable-populations.",
                **{"ab:boundToVocabulary": {"@id": "abv:vulnerable-populations"}},
            ),
        ],
    )
    a["vocabulary_bindings"] = [
        {"vocab": "enums", "field": "action_status"},
        {"vocab": "enums", "field": "financing_status"},
        {"vocab": "enums", "field": "equity_focus"},
        {"vocab": "vulnerable-populations", "field": "target_populations"},
    ]
    a["notes"] = (
        a["notes"]
        + " v1.1: a parent Plan is no longer required (Decision 39); equity_focus and "
        "target_populations moved here from Solution (Decision 36); status is a dated "
        "series (Decision 40); financing is recorded through FundingAllocation —FUNDS→ "
        "Action (Decision 43), replacing FUNDED_BY and USES_INSTRUMENT on Action."
    )

    # ------------------------------------------------------------------ Plan
    pl = T["Plan"]
    add_props(
        pl,
        [
            prop(
                "alternative_names",
                "array<string>",
                note="v1.1 (Decision 39). Other titles the plan is cited by; replaces the legacy key `aliases`.",
            )
        ],
        after="plan_title",
    )
    ps = by_id(pl["properties"], "plan_status")
    ps.update(
        enum_prop(
            "plan_status",
            "plan_status",
            ["draft", "adopted", "under_review", "superseded", "expired"],
            note="v1.1 (Decision 40): enum (was free text). Status of the plan document as of the latest observation.",
        )
    )
    add_props(pl, [observations("plan_status")], after="plan_status")
    pl.setdefault("vocabulary_bindings", []).append(
        {"vocab": "enums", "field": "plan_status"}
    )

    # ------------------------------------------------------------------ CapitalProject
    cp = T["CapitalProject"]
    add_props(cp, [observations("construction_phase")], after="construction_phase")
    add_props(cp, [observations("financing_status")], after="financing_status")
    cp["notes"] = (
        cp.get("notes", "")
        + " v1.1: financing is recorded through FundingAllocation —FUNDS→ CapitalProject (Decision 43); FUNDED_BY and USES_INSTRUMENT on CapitalProject are retired."
    ).strip()

    # ------------------------------------------------------------------ B. context off catalog nodes
    drop_props(T["UrbanSystem"], {"condition", "capacity", "service_coverage"})
    T["UrbanSystem"]["notes"] = (
        T["UrbanSystem"].get("notes", "")
        + " v1.1 (Decision 37): condition, capacity and service_coverage moved to the TARGETS edge; they describe one city's system, not the shared class."
    ).strip()
    drop_props(T["Barrier"], {"severity_score", "affected_stakeholder"})
    T["Barrier"]["notes"] = (
        T["Barrier"].get("notes", "")
        + " v1.1 (Decision 37): severity_score and affected_stakeholder moved to the FACES edge."
    ).strip()
    drop_props(
        T["Vulnerability"],
        {"exposure_score", "sensitivity_score", "adaptive_capacity_score"},
    )
    T["Vulnerability"]["notes"] = (
        T["Vulnerability"].get("notes", "")
        + " v1.1 (Decision 37): exposure_score, sensitivity_score and adaptive_capacity_score moved to the EXPERIENCES edge."
    ).strip()

    # ------------------------------------------------------------------ G. ResilienceGoal hint only
    T["ResilienceGoal"]["extract_hint"] = (
        "One of the 22 City Resilience Framework goals, stated as an objective — e.g., "
        "'improve public health outcomes', 'ensure continuity of critical services'. Not a "
        "plan's own goal numbers, headings or pillars ('Goal WR1', 'Vision 04', pillar "
        "titles); those are the plan's wording and go in local_label on the SETS or PURSUES "
        "edge that links to the CRF goal."
    )

    # ------------------------------------------------------------------ Finance (Decision 43)
    fs = T.pop("FinancingSource")
    fs["id"] = "FundingStream"
    fs["label"] = "Funding Stream"
    fs["@id"] = "ab:FundingStream"
    fs["definition"] = (
        "A named pot of money with an owner: a grant programme, fund, budget line, ballot "
        "measure, fee or appropriation — 'Hazard Mitigation Grant Program', 'Green Climate "
        "Fund', 'Oakland General Fund', 'Measure FF', 'stormwater utility fee'. Renamed from "
        "FinancingSource in v1.1. Not an organisation (that is a Stakeholder) and not a kind "
        "of money ('grants'; that is instrument_class on a FundingAllocation)."
    )
    fs["notes"] = (
        "v1.1 (Decision 43). Identity: its own Wikidata QID where one exists (Green Climate "
        "Fund); otherwise owner + normalised name, so 'General Fund' in Oakland and in "
        "Berkeley are two streams. The owner is the ADMINISTERED_BY target. Carries no "
        "allocation amount — a programme ceiling is max_award; an allocation is a "
        "FundingAllocation. accreditation_modality (v0.1.1) captures AF/GCF access "
        "arrangements."
    )
    fs["extract_hint"] = (
        "Look for named funding programmes, funds, budget lines, measures and fees — "
        "'FEMA's Hazard Mitigation Grant Program', 'the City's General Fund', 'Measure FF', "
        "'the stormwater utility fee'. An organisation ('FEMA', 'the World Bank') is a "
        "Stakeholder; a kind of money with nothing named ('grants', 'private investment') "
        "is instrument_class on the FundingAllocation, not a stream."
    )
    drop_props(fs, {"amount_usd"})
    stype = by_id(fs["properties"], "source_type")
    stype["id"] = "stream_type"
    stype["values"] = [
        "programme",
        "fund",
        "budget_line",
        "ballot_measure",
        "fee_or_levy",
        "appropriation",
        "other",
    ]
    stype["note"] = (
        "v1.1: what kind of pot this is (was source_type: municipal | national | …, which is now source_tier on the FundingAllocation)."
    )
    stype["vocabulary_binding"] = {"vocab": "enums", "field": "stream_type"}
    stype["ab:boundToVocabulary"] = {"@id": "abv:enums-stream_type"}
    add_props(
        fs,
        [
            prop(
                "max_award",
                "number",
                note="v1.1. Programme ceiling as stated ('grants of up to £100,000'); a property of the programme, not an allocation.",
            ),
            prop("max_award_currency", "string", note="ISO 4217 code for max_award."),
        ],
        after="stream_type",
    )
    fs["vocabulary_bindings"] = [
        b for b in fs.get("vocabulary_bindings", []) if b.get("field") != "source_type"
    ] + [{"vocab": "enums", "field": "stream_type"}]
    T["FundingStream"] = fs

    fi = T["FinancialInstrument"]
    fi["definition"] = (
        "One specific issued or contracted financial instrument with its own terms — a bond "
        "issue, a loan, a lease: 'Harris County 2018 Flood Bond Program', 'Miami Forever "
        "Bond'. Narrowed in v1.1: a kind of instrument ('a grant', 'a ground lease', 'PPP') "
        "is never a FinancialInstrument node; it is instrument_class / instrument_type on "
        "the FundingAllocation."
    )
    fi["notes"] = (
        fi["notes"]
        + " v1.1 (Decision 43): amount_usd and the free-text issuer removed — the "
        "draw is on the FundingAllocation, the issuer is the ISSUED_BY edge. Debt-service "
        "properties stay, because one bond issue legitimately has one principal."
    )
    fi["extract_hint"] = (
        "Look for a specifically named bond, loan, lease or fund with its own terms — 'the "
        "$2.5 billion 2018 flood bond', 'a 30-year general obligation bond issued in 2021'. "
        "Capture principal, term, interest rate and annual debt service when stated. A "
        "generic 'through a bond' or 'via a ground lease' is an instrument_class on the "
        "FundingAllocation, not a node."
    )
    drop_props(fi, {"amount_usd", "issuer"})
    it = by_id(fi["properties"], "instrument_type")
    it["values"] = it["values"][:-1] + [
        "loan",
        "tax_abatement",
        "insurance",
        "ground_lease",
        "other",
    ]
    it["note"] = (
        "Subtype of instrument_class; v1.1 adds loan, tax_abatement, insurance, ground_lease."
    )

    fa = {
        "id": "FundingAllocation",
        "label": "Funding Allocation",
        "definition": (
            "One flow of money toward one or more Actions or CapitalProjects, as a source "
            "states it: an award, an appropriation, a bond draw, a pledge, or a bare "
            "'funded through grants'. The node that carries amount, currency, period, "
            "status, and the two comparison axes source_tier (who pays) and "
            "instrument_class (in what form). Instance type: never merges by name across "
            "documents."
        ),
        "properties": [
            prop(
                "label",
                "string",
                note="Optional; the source's own name for the award or line ('HMGP award 2019').",
            ),
            prop("amount", "number", note="As stated, never converted at extraction."),
            prop("currency", "string", note="ISO 4217 code."),
            enum_prop(
                "amount_qualifier",
                "amount_qualifier",
                [
                    "exact",
                    "up_to",
                    "approximately",
                    "total_programme",
                    "share_of_total",
                ],
            ),
            prop(
                "period_start_year",
                "integer",
                note="A single-year allocation has start = end.",
            ),
            prop("period_end_year", "integer"),
            enum_prop(
                "funding_status",
                "funding_status",
                [
                    "potential",
                    "applied",
                    "committed",
                    "awarded",
                    "disbursed",
                    "withdrawn",
                ],
                note="Stage of the money as of the latest observation.",
            ),
            observations("funding_status"),
            enum_prop(
                "source_tier",
                "source_tier",
                [
                    "local_government",
                    "regional_or_state",
                    "national",
                    "international_multilateral",
                    "private",
                    "philanthropic",
                    "utility_ratepayer",
                    "mixed",
                ],
                note="Axis A: who pays. Stated when no funder node is named; derived from the PROVIDED_BY target's stakeholder_type when one is.",
            ),
            enum_prop(
                "instrument_class",
                "instrument_class",
                [
                    "grant",
                    "debt",
                    "own_revenue",
                    "fee_or_levy",
                    "tax_based",
                    "private_investment",
                    "public_private_partnership",
                    "risk_transfer",
                    "land_or_in_kind",
                    "blended",
                    "other",
                ],
                note="Axis B: what form the money takes. Replaces the mixed financing_model vocabulary.",
            ),
            enum_prop(
                "instrument_type",
                "instrument_type",
                it["values"],
                note="Optional subtype of instrument_class (same list as FinancialInstrument.instrument_type).",
            ),
            prop(
                "is_climate_specific",
                "boolean",
                note="True when the money was earmarked for climate or resilience, as opposed to a general stream drawn on.",
            ),
        ],
        "vocabulary_bindings": [
            {"vocab": "enums", "field": "amount_qualifier"},
            {"vocab": "enums", "field": "funding_status"},
            {"vocab": "enums", "field": "source_tier"},
            {"vocab": "enums", "field": "instrument_class"},
            {"vocab": "enums", "field": "instrument_type"},
        ],
        "notes": (
            "v1.1 (Decision 43). Every funding statement is one FundingAllocation with at "
            "least one FUNDS edge; PROVIDED_BY and USES_INSTRUMENT exist only when the text "
            "names the funder or the instrument. One award paying for three actions is one "
            "node with three FUNDS edges (share_percent on each), so it is summed once. Two "
            "awards to the same action from the same funder are two nodes. Money facts never "
            "sit on the funder, the stream or a kind."
        ),
        "extract_hint": (
            "Look for any statement that money went or will go to an action or project — "
            "'funded through a FEMA HMGP award of $2.1M (2019)', 'financed by the 2018 flood "
            "bond', 'supported by the City's General Fund', 'through grants and a ground "
            "lease'. Record amount, currency and year as stated; set source_tier and "
            "instrument_class from the wording; link PROVIDED_BY only to a funder the text "
            "names. Do not infer a funder from the city's name."
        ),
        "@id": "ab:FundingAllocation",
        "@type": "owl:Class",
    }
    # insert after FundingStream in the types array
    types[:] = [t if t["id"] != "FundingStream" else fs for t in types]
    fi_index = [t["id"] for t in types].index("FinancialInstrument")
    types.insert(fi_index, fa)

    # ------------------------------------------------------------------ relationships
    R = lambda id, src=None, tgt=None: [
        r
        for r in rels
        if r["id"] == id
        and (src is None or r["source"] == src)
        and (tgt is None or r["target"] == tgt)
    ]

    # B. IMPLEMENTS (Decision 37, core#321 D4)
    (impl,) = R("IMPLEMENTS")
    add_props(
        impl,
        [
            prop(
                "scale_quantity",
                "number",
                note="v1.1 (Decision 37). Size of this deployment as stated ('500 trees', '12 km of levee').",
            ),
            prop("scale_unit", "string", note="Unit of scale_quantity, as stated."),
            prop(
                "is_primary",
                "boolean",
                note="True when this Solution is the main class the Action implements, where an Action implements several.",
            ),
        ],
    )
    impl["notes"] += (
        " v1.1: carries the deployment's scale and whether this is the Action's primary class. Cost, status and year stay on the Action (no duplicate data)."
    )

    # TARGETS ×3
    for r in R("TARGETS"):
        add_props(
            r,
            [
                enum_prop(
                    "condition",
                    "system_condition",
                    ["excellent", "good", "fair", "poor", "critical"],
                    note="v1.1 (Decision 37, from UrbanSystem). Condition of this city's system as the source states it.",
                ),
                prop(
                    "capacity",
                    "string",
                    note="v1.1 (Decision 37, from UrbanSystem). Stated capacity of this city's system.",
                ),
                prop(
                    "service_coverage",
                    "string",
                    note="v1.1 (Decision 37, from UrbanSystem). Stated service coverage of this city's system.",
                ),
            ],
        )
    # FACES
    (faces,) = R("FACES")
    add_props(
        faces,
        [
            prop(
                "severity_score",
                "number",
                note="v1.1 (Decision 37, from Barrier). How severe this barrier is for this action.",
            ),
            prop(
                "affected_stakeholder",
                "string",
                note="v1.1 (Decision 37, from Barrier). Who the barrier falls on, for this action.",
            ),
        ],
    )
    # EXPERIENCES
    (exp,) = R("EXPERIENCES")
    add_props(
        exp,
        [
            prop(
                "exposure_score",
                "number",
                note="v1.1 (Decision 37, from Vulnerability).",
            ),
            prop(
                "sensitivity_score",
                "number",
                note="v1.1 (Decision 37, from Vulnerability).",
            ),
            prop(
                "adaptive_capacity_score",
                "number",
                note="v1.1 (Decision 37, from Vulnerability).",
            ),
        ],
    )
    # PRESCRIBES (Decisions 38, 39, 40)
    (pres,) = R("PRESCRIBES")
    stage = by_id(pres["properties"], "implementation_stage")
    stage["values"] = st["values"]
    stage["note"] = (
        "Stage of implementation as of the latest observation; same values and definitions as Action.status (enums.json#action_status, Decision 39)."
    )
    stage["vocabulary_binding"] = {"vocab": "enums", "field": "action_status"}
    stage["ab:boundToVocabulary"] = {"@id": "abv:enums-action_status"}
    add_props(
        pres, [observations("implementation_stage")], after="implementation_stage"
    )
    add_props(
        pres,
        [
            prop(
                "local_label",
                "string",
                note="v1.1 (Decision 38). The plan's own short name for the prescribed thing ('Cool Roofs for Communities'), kept when the mention is folded onto a shared Solution. The full quote stays in the evidence row.",
            )
        ],
    )
    pres["notes"] += (
        " v1.1: when a named programme is behind the prescription, it is an Action (SPECIFIES + IMPLEMENTS) and this edge is not used."
    )

    # IMPLEMENTED_IN (Decision 3): unchanged; note
    (ii,) = R("IMPLEMENTED_IN")
    ii["notes"] += (
        " v1.1 (Decision 38): a deployment that a plan cites in another city is an Action in that city (IMPLEMENTS + DEPLOYED_IN), not a property of this edge; no deployment_year was added."
    )

    # F. local_label on goal edges (Decision 41)
    for rid in ("SETS", "PURSUES", "DEMONSTRATES_PROGRESS_ON"):
        (r,) = R(rid)
        add_props(
            r,
            [
                prop(
                    "local_label",
                    "string",
                    note="v1.1 (Decision 41). The plan's own goal wording ('Goal WR1: Live with water') kept when it is mapped to a CRF goal; the quote stays in the evidence row.",
                )
            ],
        )
    (ct,) = R("CONTRIBUTES_TO")
    ct["definition"] = ct["definition"].replace(
        "TARGETS_GOAL (action-level planning intent)",
        "PURSUES (action-level planning intent)",
    )
    by_id(ct["properties"], "contribution_description")["note"] = (
        "v1.1 (Decision 41): class-level only — how this solution class advances the goal in "
        "general ('green roofs absorb rainfall, reducing runoff'). Never one plan's sentence; "
        "both ends of this edge are shared nodes. A plan's own wording goes on SETS or PURSUES."
    )
    # claim_ids on the three edges that had no provenance (REDUCES_EXPOSURE, SHAPES, INFORMS)
    for r in rels:
        if not any(p["id"] == "claim_ids" for p in r.get("properties", [])):
            r.setdefault("properties", []).append(
                prop("claim_ids", "array<uuid>", True)
            )

    # Finance edges (Decision 43)
    retired = {
        ("FUNDED_BY", "Action"),
        ("FUNDED_BY", "CapitalProject"),
        ("USES_INSTRUMENT", "Action"),
        ("USES_INSTRUMENT", "CapitalProject"),
        ("CHANNELS_THROUGH", "FinancingSource"),
    }
    rels[:] = [r for r in rels if (r["id"], r["source"]) not in retired]

    def edge(
        id,
        src,
        tgt,
        definition,
        props,
        notes,
        hint,
        cardinality="many-to-many",
        multi=False,
    ):
        r = {
            "id": id,
            "label": id.lower().replace("_", " "),
            "source": src,
            "target": tgt,
            "definition": definition,
            "properties": props + [prop("claim_ids", "array<uuid>", True)],
            "cardinality": cardinality,
            "notes": notes,
            "extract_hint": hint,
        }
        umbrella = f"ab:{camel(id)}"
        if multi:
            r["@id"] = (
                f"ab:{src[0].lower() + src[1:]}{''.join(w.capitalize() for w in id.lower().split('_'))}{tgt}"
            )
            r["@type"] = "owl:ObjectProperty"
            r["rdfs:subPropertyOf"] = {"@id": umbrella}
        else:
            r["@id"] = umbrella
            r["@type"] = "owl:ObjectProperty"
        r["rdfs:domain"] = {"@id": f"ab:{src}"}
        r["rdfs:range"] = {"@id": f"ab:{tgt}"}
        return r

    funds_note = "v1.1 (Decision 43). One allocation may FUNDS several targets (share_percent on each) so a joint award is recorded and summed once. Replaces FUNDED_BY on this target type."
    funds_hint = "Attach the allocation to the activity or project the text says the money pays for. If one award covers several, one allocation with several FUNDS edges."
    new_edges = [
        edge(
            "FUNDS",
            "FundingAllocation",
            "Action",
            "The allocation pays for this action.",
            [
                prop(
                    "share_percent",
                    "number",
                    note="Share of the allocation that goes to this target, when the source states a split.",
                )
            ],
            funds_note,
            funds_hint,
            multi=True,
        ),
        edge(
            "FUNDS",
            "FundingAllocation",
            "CapitalProject",
            "The allocation pays for this capital project.",
            [
                prop(
                    "share_percent",
                    "number",
                    note="Share of the allocation that goes to this target, when the source states a split.",
                )
            ],
            funds_note,
            funds_hint,
            multi=True,
        ),
        edge(
            "PROVIDED_BY",
            "FundingAllocation",
            "Stakeholder",
            "The organisation that provides the money, at the organisation grain ('supported by FEMA').",
            [],
            "v1.1 (Decision 43). Governments pay as Stakeholders (the county government), never as Jurisdictions (the place). Present only when the text names the organisation.",
            "Link to the funder the text names — 'supported by FEMA', 'Harris County will pay'. Do not infer the city as funder from the document's author.",
            multi=True,
        ),
        edge(
            "PROVIDED_BY",
            "FundingAllocation",
            "FundingStream",
            "The named pot of money the allocation is drawn from ('a Hazard Mitigation Grant Program award').",
            [],
            "v1.1 (Decision 43). 'Everything FEMA funds' is the union of allocations PROVIDED_BY FEMA and allocations PROVIDED_BY streams FEMA ADMINISTERED_BY. Present only when the text names the stream.",
            "Link to the programme, fund or budget line the text names — 'an HMGP award', 'from the General Fund', 'Measure FF proceeds'.",
            multi=True,
        ),
        edge(
            "USES_INSTRUMENT",
            "FundingAllocation",
            "FinancialInstrument",
            "The allocation is drawn through this specific issued instrument.",
            [],
            "v1.1 (Decision 43): retargeted from Action / CapitalProject (v0.8) to the allocation. Only for a named instrument; a kind ('through a bond') is instrument_class on the allocation.",
            "Link only when a specific bond, loan or lease is named — 'financed by the 2018 flood bond'.",
        ),
        edge(
            "ADMINISTERED_BY",
            "FundingStream",
            "Stakeholder",
            "The organisation that runs the funding stream.",
            [],
            "v1.1 (Decision 43, core#298 O4). The stream's owner; part of the stream's identity when it has no QID of its own.",
            "'FEMA's Hazard Mitigation Grant Program' → HMGP ADMINISTERED_BY FEMA.",
            cardinality="many-to-one",
            multi=True,
        ),
        edge(
            "ADMINISTERED_BY",
            "FundingStream",
            "Jurisdiction",
            "The local government whose stream this is, when the government Stakeholder has no verified id.",
            [],
            "v1.1 (Decision 43, core#298 O4). Local streams ('General Fund', a stormwater fee) are keyed to the Jurisdiction because it always has a verified id; the government Stakeholder may not.",
            "'the City's General Fund' in an Oakland plan → General Fund ADMINISTERED_BY Oakland.",
            cardinality="many-to-one",
            multi=True,
        ),
        edge(
            "ISSUED_BY",
            "FinancialInstrument",
            "Stakeholder",
            "The organisation that issued the instrument.",
            [],
            "v1.1 (Decision 43). Replaces the free-text FinancialInstrument.issuer.",
            "'Harris County's 2018 flood bond' → the bond ISSUED_BY Harris County.",
            cardinality="many-to-one",
        ),
    ]
    # place finance edges after CONTINGENT_ON
    ci = [r["id"] for r in rels].index("CONTINGENT_ON") + 1
    rels[ci:ci] = new_edges

    # ------------------------------------------------------------------ vocabularies manifest
    V = o["vocabularies"]
    sc = by_id(V, "solution-categories")
    sc["description"] = (
        "12 categories and 101 subcategories; the tier above solution-concepts. v1.1 added a governance_and_policy category and non-tech subcategories."
    )
    sc["bound_to"] = [
        "Solution.category_id",
        "Solution.subcategory_id",
        "solution-concepts.subcategory_id",
    ]
    V.insert(
        V.index(sc) + 1,
        {
            "id": "solution-concepts",
            "label": "Solution Concepts",
            "type": "internal",
            "url": "",
            "description": "Governed list of reusable adaptation intervention classes (the unit a Solution node IS), seeded in v1.1 from the CDP 2023 controlled action labels, the names reused across plans in the graph, and the subcategories that name a concrete intervention. Closed to the extractor; grows through the proposal queue.",
            "bound_to": ["Solution.concept_id"],
            "terms_count": None,
            "@id": "abv:solution-concepts",
            "@type": "skos:ConceptScheme",
        },
    )
    fm = by_id(V, "enums.financing_model")
    fm["description"] = (
        "DEPRECATED in v1.1 (Decision 43): mixed 'who pays' and 'in what form' on one axis. Replaced by enums.source_tier and enums.instrument_class; each value's replacement is in enums.json."
    )
    fm["bound_to"] = []
    by_id(V, "enums.instrument_type")["bound_to"] = [
        "FinancialInstrument.instrument_type",
        "FundingAllocation.instrument_type",
    ]
    by_id(V, "enums.instrument_type")["terms_count"] = len(it["values"])
    by_id(V, "enums.equity_focus")["bound_to"] = ["Action.equity_focus"]
    vp = by_id(V, "vulnerable-populations")
    vp["bound_to"] = [
        "Action.target_populations" if b == "Solution.target_populations" else b
        for b in vp["bound_to"]
    ]
    am = by_id(V, "enums.accreditation_modality")
    am["bound_to"] = [
        b.replace("FinancingSource.", "FundingStream.") for b in am["bound_to"]
    ]
    for t in (T["ResilienceGoal"],):
        t["notes"] = t["notes"].replace("TARGETS_GOAL", "PURSUES")
    for r in R("DEMONSTRATES_PROGRESS_ON"):
        r["notes"] = r["notes"].replace("TARGETS_GOAL", "PURSUES")
    by_id(V, "enums.financing_status")["bound_to"] = [
        "Action.financing_status",
        "CapitalProject.financing_status",
    ]

    def enum_row(block, label, desc, bound, n):
        return {
            "id": f"enums.{block}",
            "label": label,
            "type": "internal",
            "url": "",
            "description": desc,
            "bound_to": bound,
            "terms_count": n,
            "@id": f"abv:enums-{block}",
            "@type": "skos:ConceptScheme",
        }

    V.extend(
        [
            enum_row(
                "action_status",
                "Action status",
                "Implementation status values with definitions (Decision 39).",
                ["Action.status", "PRESCRIBES.implementation_stage"],
                7,
            ),
            enum_row(
                "plan_status",
                "Plan status",
                "Status of a plan document (Decision 40).",
                ["Plan.plan_status"],
                5,
            ),
            enum_row(
                "system_condition",
                "System condition",
                "Condition of an urban system in one city, on the TARGETS edge (Decision 37).",
                ["TARGETS.condition"],
                5,
            ),
            enum_row(
                "stream_type",
                "Funding stream type",
                "What kind of pot a FundingStream is (Decision 43).",
                ["FundingStream.stream_type"],
                7,
            ),
            enum_row(
                "source_tier",
                "Funding source tier",
                "Axis A of the finance model: who pays (Decision 43).",
                ["FundingAllocation.source_tier"],
                8,
            ),
            enum_row(
                "instrument_class",
                "Instrument class",
                "Axis B of the finance model: what form the money takes; instrument_type values nest under it (Decision 43).",
                ["FundingAllocation.instrument_class"],
                11,
            ),
            enum_row(
                "funding_status",
                "Funding status",
                "Stage of an allocation (Decision 43).",
                ["FundingAllocation.funding_status"],
                6,
            ),
            enum_row(
                "amount_qualifier",
                "Amount qualifier",
                "How an allocation amount is stated (Decision 43).",
                ["FundingAllocation.amount_qualifier"],
                5,
            ),
        ]
    )

    # ------------------------------------------------------------------ header, notes, metadata
    o["version"] = "v1.1"
    o["updated"] = UPDATED
    o["update_note"] = (
        "v1.1 — the single bump planned in core worklist item 4, cut from the 2026-10-06 decision "
        "set (Decisions 35–43). Solution keeps only class-level properties and binds to a new "
        "governed solution-concepts vocabulary; deployment context moves to Action and to the "
        "asserting edges (IMPLEMENTS, TARGETS, FACES, EXPERIENCES, PRESCRIBES); Action no longer "
        "needs a parent Plan, gains equity_focus / target_populations / is_pilot / "
        "alternative_names, and its status (with every other progress-type property) becomes a "
        "dated observation series with defined values; plan goal wording lives in local_label on "
        "SETS / PURSUES / PRESCRIBES; the finance model is rebuilt around a FundingAllocation node "
        "with two comparison axes (source_tier, instrument_class), FinancingSource becomes "
        "FundingStream, FUNDED_BY / CHANNELS_THROUGH are retired. The hazard vocabulary is "
        "unchanged (flood parent and UHI synonym deferred, Decision 42)."
    )
    o["version_notes"].insert(
        0,
        {
            "version": "v1.1",
            "date": "2026-10-06",
            "summary": o["update_note"],
            "changes": [
                {
                    "type": "added",
                    "text": "FundingAllocation type; FUNDS, PROVIDED_BY, ADMINISTERED_BY, ISSUED_BY edges; USES_INSTRUMENT retargeted to FundingAllocation (Decision 43)",
                },
                {
                    "type": "renamed",
                    "text": "FinancingSource → FundingStream; source_type → stream_type; amount_usd replaced by max_award (Decision 43)",
                },
                {
                    "type": "removed",
                    "text": "FUNDED_BY (Action, CapitalProject), USES_INSTRUMENT (Action, CapitalProject), CHANNELS_THROUGH; FinancialInstrument.amount_usd and .issuer (Decision 43)",
                },
                {
                    "type": "added",
                    "text": "enums: source_tier, instrument_class, funding_status, amount_qualifier, stream_type; instrument_type + loan, tax_abatement, insurance, ground_lease; financing_model deprecated with a value map (Decision 43)",
                },
                {
                    "type": "added",
                    "text": "vocabularies/solution-concepts.json (112 concepts, v0) bound to Solution.concept_id; solution-categories + governance_and_policy category (5 subcategories) and 4 non-tech subcategories elsewhere, 92 → 101 (Decision 35)",
                },
                {
                    "type": "removed",
                    "text": "Solution.year_of_deployment, maturity_level, equity_focus, target_populations; category_id no longer required — category_id, subcategory_id, ipcc_action_types are derived from concept_id (Decision 35)",
                },
                {
                    "type": "changed",
                    "text": "Solution and Action definitions and extract hints: a named programme is an Action; an Action needs no parent Plan (Decisions 35, 39)",
                },
                {
                    "type": "added",
                    "text": "Action.equity_focus, Action.target_populations (Decision 36); Action.alternative_names, Plan.alternative_names, Action.is_pilot (Decision 39)",
                },
                {
                    "type": "changed",
                    "text": "Action.status and PRESCRIBES.implementation_stage share enums.action_status with definitions; + not_started, on_hold (Decision 39)",
                },
                {
                    "type": "added",
                    "text": "*_observations dated series on Action.status, Action.financing_status, CapitalProject.construction_phase / financing_status, Plan.plan_status, PRESCRIBES.implementation_stage, FundingAllocation.funding_status; Plan.plan_status becomes an enum (Decision 40)",
                },
                {
                    "type": "changed",
                    "text": "UrbanSystem.condition/capacity/service_coverage → TARGETS; Barrier.severity_score/affected_stakeholder → FACES; Vulnerability scores → EXPERIENCES; IMPLEMENTS + scale_quantity, scale_unit, is_primary (Decision 37)",
                },
                {
                    "type": "added",
                    "text": "local_label on PRESCRIBES, SETS, PURSUES, DEMONSTRATES_PROGRESS_ON; CONTRIBUTES_TO.contribution_description restricted to class-level text and its definition's TARGETS_GOAL reference fixed to PURSUES (Decisions 38, 41)",
                },
                {
                    "type": "changed",
                    "text": "ResilienceGoal extract_hint excludes a plan's own goal numbering and headings (Decision 42)",
                },
                {
                    "type": "added",
                    "text": "claim_ids on REDUCES_EXPOSURE, SHAPES and INFORMS (the three edges that had no provenance property)",
                },
                {
                    "type": "added",
                    "text": "scripts/export/build_vocab_jsonld.py regenerates the vocabulary .jsonld twins; scripts/migrations/v1_1_from_v1_0.py is the migration",
                },
            ],
        },
    )
    m = o["metadata"]
    m["types_count"] = len(types)
    m["relationships_count"] = len(rels)
    m["vocabularies_count"] = len(V)
    m["change_history"].insert(
        0,
        (
            f"v1.1 (2026-10-06): Solution → class-level only + solution-concepts; deployment context "
            f"to Action and edges; dated status observations; plan goal wording on edges; finance "
            f"rebuilt around FundingAllocation (FinancingSource → FundingStream). {len(types)} types, "
            f"{len(rels)} relationships, {len({r['id'] for r in rels})} predicate ids."
        ),
    )
    dump(DST, o)
    print(
        f"wrote {DST.relative_to(REPO)}: {len(types)} types, {len(rels)} relationships, {len({r['id'] for r in rels})} predicate ids, {len(V)} vocab rows"
    )

    # ------------------------------------------------------------------ enums.json
    e = load(VOC / "enums.json")
    if "action_status" in e:
        print("enums.json already at v1.1; skipped")
        e = None

    def block(source, usage, values, note=None):
        b = {"_source": source, "_usage": usage}
        if note:
            b["_note"] = note
        b["values"] = [{"id": i, "name": n, "description": d} for i, n, d in values]
        return b

    if e is not None:
        e["action_status"] = block(
            "C40 / ICLEI / GCoM action status vocabularies, with definitions written for v1.1 from the Christchurch and Houston status briefs (adaptbase-core #264–#268, #336)",
            "Action.status, PRESCRIBES.implementation_stage; the `value` of each *_observations element",
            [
                (
                    "not_started",
                    "Not started",
                    "Declared by a plan or report; no work has begun. Covers 'no action to date', 'no progress to date', 'not progressed', 'lead agency still to be determined'.",
                ),
                (
                    "committed",
                    "Committed",
                    "Adopted and resourced (budget, lead or timeline assigned) but delivery has not begun. Use not_started when the source says nothing has happened.",
                ),
                (
                    "in_planning",
                    "In planning",
                    "Work has begun but nothing is delivered: scoping, brief agreed, design, consultant appointed, feasibility, 'preliminary work undertaken'.",
                ),
                (
                    "under_implementation",
                    "Under implementation",
                    "Delivery is underway: in progress, being progressed, partially delivered, delivered and ongoing.",
                ),
                (
                    "on_hold",
                    "On hold",
                    "Work began and is paused or delayed with no stated end: 'on hold', 'paused', 'delayed pending funding'. Distinct from cancelled.",
                ),
                (
                    "completed",
                    "Completed",
                    "Done: delivered, adopted, established, launched, built.",
                ),
                (
                    "cancelled",
                    "Cancelled",
                    "Will not proceed: 'not proceeding', 'did not proceed', 'dropped', 'lacks feasibility'.",
                ),
            ],
            "v1.1 (Decision 39). One definition per value so extraction, the researcher and reviewers read the same thing; adaptbase-core's VALUE_GLOSSES copy is deleted once these reach its prompts.",
        )
        e["plan_status"] = block(
            "v1.1 (Decision 40)",
            "Plan.plan_status",
            [
                (
                    "draft",
                    "Draft",
                    "Published for consultation or internal review; not adopted.",
                ),
                (
                    "adopted",
                    "Adopted",
                    "Formally adopted or approved by the issuing body and in force.",
                ),
                (
                    "under_review",
                    "Under review",
                    "An adopted plan being revised or evaluated for replacement.",
                ),
                (
                    "superseded",
                    "Superseded",
                    "Replaced by a later plan (see Plan SUPERSEDES Plan).",
                ),
                ("expired", "Expired", "Past its horizon with no successor named."),
            ],
        )
        e["system_condition"] = block(
            "v1.1 (Decision 37); was UrbanSystem.condition",
            "TARGETS.condition",
            [
                ("excellent", "Excellent", "New or as-new; no deficiencies."),
                ("good", "Good", "Minor deficiencies; performs as intended."),
                ("fair", "Fair", "Noticeable deterioration; performance affected."),
                (
                    "poor",
                    "Poor",
                    "Significant deterioration; failure likely without intervention.",
                ),
                ("critical", "Critical", "Failed or failing; service at risk."),
            ],
        )
        e["stream_type"] = block(
            "v1.1 (Decision 43); replaces FinancingSource.source_type",
            "FundingStream.stream_type",
            [
                (
                    "programme",
                    "Programme",
                    "A recurring grant or assistance programme (HMGP, BRIC).",
                ),
                (
                    "fund",
                    "Fund",
                    "A standing fund (Green Climate Fund, a resilience trust fund).",
                ),
                (
                    "budget_line",
                    "Budget line",
                    "A named line in a government budget (General Fund, a CIP line).",
                ),
                (
                    "ballot_measure",
                    "Ballot measure",
                    "A voter-approved measure or bond act (Measure FF).",
                ),
                (
                    "fee_or_levy",
                    "Fee or levy",
                    "A dedicated fee, rate or levy (stormwater utility fee).",
                ),
                (
                    "appropriation",
                    "Appropriation",
                    "A one-off legislative appropriation.",
                ),
                ("other", "Other", "None of the above."),
            ],
        )
        e["source_tier"] = block(
            "v1.1 (Decision 43); axis A of the finance model",
            "FundingAllocation.source_tier (stated when no funder is named; derived from the funder's stakeholder_type otherwise)",
            [
                (
                    "local_government",
                    "Local government",
                    "City, county or municipal government money.",
                ),
                (
                    "regional_or_state",
                    "Regional or state",
                    "State, province, region or metropolitan authority.",
                ),
                ("national", "National", "National government and its agencies."),
                (
                    "international_multilateral",
                    "International / multilateral",
                    "Development banks, climate funds, UN agencies, foreign aid.",
                ),
                ("private", "Private", "Companies, developers, lenders, investors."),
                (
                    "philanthropic",
                    "Philanthropic",
                    "Foundations and charitable giving.",
                ),
                (
                    "utility_ratepayer",
                    "Utility ratepayer",
                    "Utility revenue from rates and charges.",
                ),
                (
                    "mixed",
                    "Mixed",
                    "The source states several tiers for one allocation and does not split them.",
                ),
            ],
        )
        e["instrument_class"] = block(
            "v1.1 (Decision 43); axis B of the finance model; instrument_type values nest under these",
            "FundingAllocation.instrument_class",
            [
                ("grant", "Grant", "Non-repayable funding: grants, cost-shares."),
                ("debt", "Debt", "Borrowed money: bonds, loans, revolving funds."),
                (
                    "own_revenue",
                    "Own revenue",
                    "Pay-as-you-go from the owner's own budget: appropriations, direct allocation.",
                ),
                (
                    "fee_or_levy",
                    "Fee or levy",
                    "Dedicated charges on users or property: special assessments, rates.",
                ),
                (
                    "tax_based",
                    "Tax-based",
                    "Instruments built on tax flows: tax increment financing, tax abatement.",
                ),
                (
                    "private_investment",
                    "Private investment",
                    "Equity or direct private capital.",
                ),
                (
                    "public_private_partnership",
                    "Public-private partnership",
                    "A structured PPP or concession.",
                ),
                ("risk_transfer", "Risk transfer", "Insurance and similar."),
                (
                    "land_or_in_kind",
                    "Land or in-kind",
                    "Ground leases, land contributions, in-kind works.",
                ),
                (
                    "blended",
                    "Blended",
                    "A stated mix of public, private and philanthropic capital in one allocation.",
                ),
                ("other", "Other", "None of the above; describe in the evidence."),
            ],
        )
        e["funding_status"] = block(
            "v1.1 (Decision 43; adaptbase-core#298 §4.4)",
            "FundingAllocation.funding_status",
            [
                (
                    "potential",
                    "Potential",
                    "Identified as a possible source; nothing sought.",
                ),
                ("applied", "Applied", "An application or request has been made."),
                (
                    "committed",
                    "Committed",
                    "The funder has committed; nothing awarded yet.",
                ),
                ("awarded", "Awarded", "Formally awarded or appropriated."),
                ("disbursed", "Disbursed", "Money has been paid out."),
                ("withdrawn", "Withdrawn", "Rescinded, declined or lapsed."),
            ],
        )
        e["amount_qualifier"] = block(
            "v1.1 (Decision 43; adaptbase-core#298 §4.4)",
            "FundingAllocation.amount_qualifier",
            [
                ("exact", "Exact", "The stated figure is the allocation."),
                ("up_to", "Up to", "A ceiling ('up to $5M')."),
                ("approximately", "Approximately", "A rounded or estimated figure."),
                (
                    "total_programme",
                    "Total programme",
                    "The figure is the whole programme or bond, not this allocation's share.",
                ),
                (
                    "share_of_total",
                    "Share of total",
                    "The figure is a share of a larger stated total.",
                ),
            ],
        )
        itb = e["instrument_type"]
        itb["_note"] += (
            " v1.1 (Decision 43): now also the optional subtype of FundingAllocation.instrument_class; added loan, tax_abatement, insurance, ground_lease. Not added: community land trust (an ownership model), developer agreement (a contract), investment fund (a FundingStream)."
        )
        itb["_usage"] = (
            "FinancialInstrument.instrument_type, FundingAllocation.instrument_type"
        )
        other = itb["values"].pop()
        itb["values"] += [
            {
                "id": "loan",
                "name": "Loan",
                "description": "A plain loan from a bank, agency or fund, not otherwise typed",
                "instrument_class": "debt",
            },
            {
                "id": "tax_abatement",
                "name": "Tax abatement",
                "description": "Forgone property or other tax used to finance a project",
                "instrument_class": "tax_based",
            },
            {
                "id": "insurance",
                "name": "Insurance",
                "description": "An insurance or risk-transfer contract financing recovery",
                "instrument_class": "risk_transfer",
            },
            {
                "id": "ground_lease",
                "name": "Ground lease",
                "description": "A long-term lease of public land used to finance development",
                "instrument_class": "land_or_in_kind",
            },
            other,
        ]
        class_of = {
            "green_bond": "debt",
            "general_obligation_bond": "debt",
            "revenue_bond": "debt",
            "tax_increment_financing": "tax_based",
            "special_assessment": "fee_or_levy",
            "sustainability_linked_loan": "debt",
            "climate_bond": "debt",
            "resilience_bond": "debt",
            "blended_finance": "blended",
            "revolving_fund": "debt",
            "grant": "grant",
            "federal_cost_share": "grant",
            "state_cost_share": "grant",
            "municipal_capital_appropriation": "own_revenue",
            "ratepayer_funded": "fee_or_levy",
            "direct_allocation": "own_revenue",
            "outcome_bond": "debt",
            "other": "other",
        }
        for v in itb["values"]:
            if "instrument_class" not in v:
                v["instrument_class"] = class_of[v["id"]]
        fmb = e["financing_model"]
        fmb["_deprecated"] = (
            "v1.1 (Decision 43). Mixed 'who pays' and 'in what form'. Not bound to any property; each value maps to source_tier or instrument_class as listed on the value (replaced_by)."
        )
        fmb["_usage"] = "none (deprecated); was USES_INSTRUMENT.financing_model"
        repl = {
            "grants": "instrument_class:grant",
            "municipal_budget": "source_tier:local_government + instrument_class:own_revenue",
            "national_government": "source_tier:national",
            "regional_funds": "source_tier:regional_or_state",
            "public_private_partnership": "instrument_class:public_private_partnership",
            "commercial_loans": "instrument_class:debt (instrument_type:loan)",
            "development_banks": "source_tier:international_multilateral",
            "climate_funds": "source_tier:international_multilateral",
            "green_bonds": "instrument_class:debt (instrument_type:green_bond)",
            "blended_finance": "instrument_class:blended",
            "private_sector": "source_tier:private",
            "international_oda": "source_tier:international_multilateral",
        }
        for v in fmb["values"]:
            v["replaced_by"] = repl[v["id"]]
        e["equity_focus"]["_usage"] = (
            "Action.equity_focus (v1.1, from solution.equity_focus)"
        )
        e["financing_status"]["_usage"] = (
            "Action.financing_status, CapitalProject.financing_status"
        )
        dump(VOC / "enums.json", e)

    # ------------------------------------------------------------------ solution-categories.json
    sc = load(VOC / "solution-categories.json")
    sc["_note"] += (
        " v1.1 (Decision 35): tier 1–2 of the Solution taxonomy; tier 3 is solution-concepts.json. "
        "Added governance_and_policy (zoning, codes, insurance mandates, retreat, governance bodies) "
        "and non-tech subcategories the corpus needed (resilience hubs, heat action planning, "
        "informal-settlement upgrading, water demand management). Vendor-grain subcategory names "
        "are kept for id stability in adaptbase-core's vocabulary_terms."
    )
    cats = sc["categories"]
    if any(c["id"] == "governance_and_policy" for c in cats):
        print("solution-categories.json already at v1.1; skipped")
    else:
        by_id(cats, "health")["subcategories"].append(
            {"id": "community_resilience_hubs", "name": "Community Resilience Hubs"}
        )
        by_id(cats, "health")["subcategories"].append(
            {"id": "heat_action_planning", "name": "Heat Action Planning and Response"}
        )
        by_id(cats, "water")["subcategories"].append(
            {
                "id": "water_demand_management",
                "name": "Water Demand Management (restrictions, pricing)",
            }
        )
        by_id(cats, "buildings")["subcategories"].append(
            {
                "id": "informal_settlement_upgrading",
                "name": "Informal Settlement Upgrading",
            }
        )
        cats.append(
            {
                "id": "governance_and_policy",
                "name": "Governance, Policy and Planning Instruments",
                "framework_mappings": {
                    "c40_action_categories": ["Governance & Planning"],
                    "gcom_hazard_focus": [],
                    "ipcc_action_types": ["institutional"],
                    "iclei_milestone": "C. Plan",
                    "iclei_pathways": ["resilient", "equitable_people_centered"],
                    "sdg_goals": ["SDG11", "SDG13", "SDG16"],
                },
                "subcategories": [
                    {
                        "id": "adaptation_governance",
                        "name": "Adaptation Governance Bodies and Mainstreaming",
                    },
                    {
                        "id": "land_use_and_zoning",
                        "name": "Land Use, Zoning and Development Regulation",
                    },
                    {
                        "id": "codes_and_standards",
                        "name": "Codes, Standards and Mandates",
                    },
                    {
                        "id": "retreat_and_buyouts",
                        "name": "Managed Retreat and Buyout Programmes",
                    },
                    {
                        "id": "adaptation_planning_process",
                        "name": "Adaptation Planning and Monitoring Frameworks",
                    },
                ],
            }
        )
        dump(VOC / "solution-categories.json", sc)

    # ------------------------------------------------------------------ solution-concepts.json (new)
    seed = load(CONCEPT_SEED)
    sub2cat = {s["id"]: c["id"] for c in cats for s in c["subcategories"]}
    concepts = []
    for x in seed:
        assert x["subcategory_id"] in sub2cat, x
        concepts.append(
            {
                "id": x["id"],
                "name": x["name"],
                "aliases": x["aliases"],
                "definition": x["definition"],
                "category_id": sub2cat[x["subcategory_id"]],
                "subcategory_id": x["subcategory_id"],
                "ipcc_action_types": x["ipcc_action_types"],
                "cdp_labels": x["cdp_labels"],
                "status": "active",
                "added_in": "v1.1",
            }
        )
    dump(
        VOC / "solution-concepts.json",
        {
            "_source": "v1.1 (Decision 35) seed: the 115 CDP 2023 controlled action labels (adaptbase-core cdp_solution_crosswalk.json; every label is a concept or an alias), the Solution names reused by two or more plans in the graph on 2026-10-01 (adaptbase-core#321 §2.6 d), and solution-categories subcategories that name a concrete intervention.",
            "_usage": "Solution.concept_id. Each concept carries the category_id, subcategory_id and ipcc_action_types that the seeder copies onto the Solution node; extraction never writes those three.",
            "_note": "Governed, growing list: closed to the extractor (a class not on the list is emitted with proposed: true and reviewed), open through the proposal queue. New concepts arrive as a PR to this file with added_in set; deprecation keeps the id with status: deprecated and replaced_by. cdp_labels records which CDP controlled labels fold into the concept, for the CDP import. aliases are identity-grade synonyms for the resolver.",
            "concepts": concepts,
        },
    )
    print(f"wrote vocabularies/solution-concepts.json: {len(concepts)} concepts")

    # ------------------------------------------------------------------ versions.json
    vs = load(ONT / "versions.json")
    if vs[0]["value"] != "v1.1":
        vs.insert(
            0,
            {
                "path": "../ontology/ontology-v1.1.jsonld",
                "label": "v1.1",
                "value": "v1.1",
            },
        )
    dump(ONT / "versions.json", vs)


if __name__ == "__main__":
    main()
