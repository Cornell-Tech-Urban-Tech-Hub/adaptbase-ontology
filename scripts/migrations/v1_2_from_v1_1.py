#!/usr/bin/env python3
"""Build ontology/ontology-v1.2.jsonld and the v1.2 vocabulary edits from v1.1.

Run with: uv run scripts/migrations/v1_2_from_v1_1.py
Re-runnable: ontology-v1.2.jsonld and versions.json are rebuilt from v1.1 each
time (a hand edit to them is overwritten); hazards.json, urban-systems.json and
enums.json are edited in place and each step is skipped when already applied.

What it applies is the v1.2 decision set of 2026-10-08 (Anthony), recorded in
ontology/decisions-log.md Decisions 45-53 and in adaptbase-core
_planning/to-do/ONTOLOGY-V1.2-ADOPTION-PLAN.md Part A (items D1-D8, P1-P11).
Its input was the review in ontology/review/FABLE-ONTOLOGY-REVIEW-2026-10-06.md
(§4 change list, §5 addendum). Every rule below names the item it implements.
"""

import json
from copy import deepcopy
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ONT = REPO / "ontology"
VOC = ONT / "vocabularies"
SRC = ONT / "ontology-v1.1.jsonld"
DST = ONT / "ontology-v1.2.jsonld"
DEFS = Path(__file__).with_name("v1_2_definitions.json")

VERSION = "v1.2"
DATE = "2026-10-08"
UPDATED = "2026-10-08T12:00:00.000Z"


def load(p):
    return json.loads(p.read_text())


def dump(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def prop(id, type, required=False, **kw):
    p = {"id": id, "type": type, "required": required}
    p.update(kw)
    return p


def bind(p, block):
    p["vocabulary_binding"] = {"vocab": "enums", "field": block}
    p["ab:boundToVocabulary"] = {"@id": f"abv:enums-{block}"}
    return p


def by_id(items, id):
    return next(x for x in items if x["id"] == id)


def pget(owner, id):
    return next(p for p in owner["properties"] if p["id"] == id)


def drop_props(owner, ids):
    have = {p["id"] for p in owner["properties"]}
    missing = set(ids) - have
    assert not missing, (owner.get("id"), owner.get("source"), missing)
    out = [p for p in owner["properties"] if p["id"] in ids]
    owner["properties"] = [p for p in owner["properties"] if p["id"] not in ids]
    return out


def add_props(owner, props, after=None):
    have = {p["id"] for p in owner["properties"]}
    dup = {p["id"] for p in props} & have
    assert not dup, (owner.get("id"), dup)
    if after is None:
        tail = [p for p in owner["properties"] if p["id"] == "claim_ids"]
        head = [p for p in owner["properties"] if p["id"] != "claim_ids"]
        owner["properties"] = head + props + tail
    else:
        i = [p["id"] for p in owner["properties"]].index(after) + 1
        owner["properties"][i:i] = props


# Machine-readable record of every removed or renamed key (P11). adaptbase-core
# generates its `deprecated` property-key registry entries from this list.
REMOVED_KEYS: list[dict] = []


def removed(owner, key, moved_to, item):
    REMOVED_KEYS.append(
        {"owner": owner, "key": key, "moved_to": moved_to, "item": item}
    )


ALT_NAMES_NOTE = (
    "v1.2 (P4). Other names this node is known by: spellings, abbreviations, former "
    "names, and the names of mentions merged into it. Every name added by a merge is "
    "backed by its own evidence row, so undoing the merge removes the name. Used to "
    "match new mentions to this node; for registry types a name match proposes a "
    "candidate and never merges on its own (identity stays on verified ids)."
)


def main() -> None:
    o = load(SRC)
    types = o["types"]
    rels = o["relationships"]
    T = {t["id"]: t for t in types}

    def R(id, src=None, tgt=None):
        out = [
            r
            for r in rels
            if r["id"] == id
            and (src is None or r["source"] == src)
            and (tgt is None or r["target"] == tgt)
        ]
        assert out, (id, src, tgt)
        return out

    # ------------------------------------------------------------- D2 + D8. Hazard
    # A plan's characterisation of a hazard moves off the shared Hazard node onto
    # that plan's ADDRESSES edge (Plan -> Hazard only). Review L-4, narrowed §5.2.
    hz = T["Hazard"]
    seven = [
        "frequency",
        "severity",
        "trend",
        "return_period",
        "climate_scenario",
        "climate_scenario_other_description",
        "projection_year",
    ]
    moved = drop_props(hz, seven)
    hz["notes"] = (
        hz["notes"]
        + " v1.2 (Decision 45): a plan's characterisation of a hazard (frequency, "
        "severity, trend, return period, scenario, projection year, indicators) is on "
        "that plan's ADDRESSES edge; the Hazard node holds only the vocabulary term "
        "and is shared by every city and plan."
    )
    for vb in hz["vocabulary_bindings"]:
        if "note" in vb:
            vb["note"] = vb["note"].replace(
                "alignment/framework-crosswalk.md", "framework-crosswalk.md"
            )
    addr = R("ADDRESSES", "Plan", "Hazard")[0]
    for p in moved:
        p = deepcopy(p)
        p["note"] = (
            p.get("note", "")
            + " v1.2 (Decision 45): moved from the Hazard node; the value is this "
            "plan's statement."
        ).strip()
        p["note"] = p["note"].replace(
            "Target year for which the hazard characterization applies",
            "Target year for which this plan's hazard characterisation applies",
        )
        add_props(addr, [p])
        removed("Hazard", p["id"], "ADDRESSES(Plan->Hazard)." + p["id"], "D2")
    add_props(
        addr,
        [
            prop(
                "indicators",
                "object",
                note=(
                    "v1.2 (Decision 46). Quantified hazard figures the plan states, "
                    'keyed by indicator, e.g. {"flooded_area_square_miles": 440}. '
                    "Values as stated in the plan, never converted."
                ),
            )
        ],
    )
    addr["notes"] = (
        addr["notes"]
        + " v1.2: this edge is where a plan's own characterisation of a hazard lives "
        "(Decisions 45, 46). One edge per plan and hazard, so two plans for the same "
        "city never collide."
    )
    addr["extract_hint"] = (
        addr["extract_hint"]
        + " Put what the plan says about the hazard (how often, how severe, its trend, "
        "return period, scenario, projection year, stated figures) on this edge, "
        "never on the Hazard."
    )
    T["Hazard"]["extract_hint"] = (
        T["Hazard"]["extract_hint"]
        + " Emit only the hazard term; what a plan says about the hazard goes on the "
        "plan's ADDRESSES edge."
    )

    # ------------------------------------------------------------- D1. AFFECTED_BY
    ab = R("AFFECTED_BY")[0]
    for k in ("source_dataset", "indicators"):
        drop_props(ab, [k])
        removed("AFFECTED_BY", k, "AFFECTED_BY.sources.<source_id>", "D1")
    removed("AFFECTED_BY", "source", "AFFECTED_BY.sources.<source_id>", "D1")
    add_props(
        ab,
        [
            prop(
                "sources",
                "object",
                True,
                note=(
                    "v1.2 (Decision 47). One entry per supporting source, keyed by a "
                    "source id (e.g. wri_city_hazards, probable_futures, "
                    "plan_documents); entries are never merged or averaged, and each "
                    "has its own evidence rows so one can be withdrawn without "
                    "touching the others. Every entry has kind: dataset | "
                    "plan_document. A dataset entry has dataset_version, "
                    "materiality_rule {id, version}, the maps or indicators that "
                    "passed (each tagged direct | indirect, with a direction), a "
                    "score such as frequency_ratio, and indicators. The "
                    "plan_document entry has cited_datasets (array of strings) and "
                    "no scalar hazard characterisation: a plan's figures go on its "
                    "ADDRESSES edge. Replaces the top-level source_dataset and "
                    "indicators."
                ),
            )
        ],
    )
    ab["definition"] = (
        "This jurisdiction is affected by this hazard, supported by one or more "
        "sources: a reference dataset under a stated materiality rule, or a plan "
        "document. One edge per jurisdiction–hazard pair; sources are never merged "
        "or averaged."
    )
    ab["notes"] = (
        "Direct link between a jurisdiction and a hazard that threatens it. Complements "
        "the indirect path Hazard → EXPOSES → ExposureUnit → LOCATED_IN → Jurisdiction. "
        "v1.2 (Decision 47): every supporting source is an entry in `sources`. Dataset "
        "entries are derived by a stated, versioned rule (see the design note on "
        "reference data); claim_ids stays optional because those entries are derived."
    )
    ab["extract_hint"] = (
        "Look for statements that a city or region faces, is exposed to, or is "
        "threatened by a specific hazard — e.g., 'Miami faces increased coastal "
        "flooding risk', 'the city is highly exposed to extreme heat'. Record the "
        "datasets the plan cites for it in the plan_documents entry; put the plan's "
        "own figures on its ADDRESSES edge."
    )

    # ------------------------------------------------------------- D3. Jurisdiction
    j = T["Jurisdiction"]
    pget(j, "geometry")["note"] = (
        "GeoJSON geometry. A Point from Wikidata P625 (centroid) is the default and "
        "the one coordinate representation (v1.2, Decision 48: no separate latitude / "
        "longitude). Polygons only from sources whose licence allows redistribution; "
        "never from OSM (ODbL)."
    )
    pget(j, "climate_zone")["note"] = (
        "Köppen climate group of the jurisdiction today. v1.2 (Decision 48): sourced "
        "from Probable Futures' climate-zones map at 1.0 °C warming (the level closest "
        "to the recent climate), mapped to the five groups by Köppen letter; projected "
        "zones are reference data outside the graph."
    )
    pget(j, "jurisdiction_kind")["note"] += (
        " Filled from Wikidata P31 (instance of) when not stated."
    )
    al = pget(j, "aliases")
    al["id"] = "alternative_names"
    al["note"] = ALT_NAMES_NOTE
    removed("Jurisdiction", "aliases", "Jurisdiction.alternative_names", "P4")

    # ------------------------------------------------------------- D5. Action
    act = T["Action"]
    add_props(
        act,
        [
            bind(
                prop(
                    "resilience_contribution",
                    "enum",
                    values=["adapted", "enabling"],
                    note=(
                        "v1.2 (Decision 49). Whose resilience the action builds: "
                        "adapted = the acting party's own assets or activities; "
                        "enabling = other people's or the city's. The split follows "
                        "the EU Taxonomy (Regulation (EU) 2020/852, Art. 11 and 16). "
                        "Optional; leave empty when the text does not say."
                    ),
                ),
                "resilience_contribution",
            )
        ],
    )

    # ---------------------------------------- Mechanism: the escape value's description
    # mechanism_type's note has told the extractor since v0.4 to "use other +
    # mechanism_type_other_description for outliers", but no such property was
    # ever declared, so the extractor could not write the description (found
    # by the 2026-10-08 classification A/B: 16 of 49 mechanisms chose other —
    # composting, biofuels, sedimentation, filtration — and none could say
    # what). Declared like Vulnerability.vuln_type_other_description.
    add_props(
        T["Mechanism"],
        [
            prop(
                "mechanism_type_other_description",
                "string",
                note="Free-text description when mechanism_type = other (Decision 54).",
            )
        ],
        after="mechanism_type",
    )

    # ------------------------------------------------------------- P3. duplicated edge properties
    for r in R("PRODUCES", "Solution", "Outcome") + R("RESULTS_IN", "Action", "Outcome"):
        drop_props(r, ["outcome_type", "evidence_level"])
        for k in ("outcome_type", "evidence_level"):
            removed(f"{r['id']}({r['source']}->{r['target']})", k, f"Outcome.{k}", "P3")
        r["notes"] = (
            r.get("notes", "")
            + " v1.2 (Decision 50): outcome_type and evidence_level live on the Outcome "
            "node only; the edge no longer repeats them."
        ).strip()
    iss = R("ISSUES")[0]
    drop_props(iss, ["adoption_status"])
    removed("ISSUES", "adoption_status", "Plan.plan_status_observations", "P3")
    red = R("REDUCES")[0]
    mor = pget(red, "mechanism_of_reduction")
    mor["values"] = ["reduces_sensitivity", "increases_adaptive_capacity", "both"]
    mor["note"] = (
        "v1.2 (Decision 50): how the solution class reduces the vulnerability. "
        "Exposure is not a value here: reducing exposure is asserted at deployment "
        "grain by Action REDUCES_EXPOSURE. multi_pathway was renamed both."
    )
    imp_in = R("IMPLEMENTED_IN")[0]
    five = ["deployment_context", "zone_type", "area_km2", "population_density", "land_use_type"]
    drop_props(imp_in, five)
    for k in five:
        removed("IMPLEMENTED_IN", k, "Action DEPLOYED_IN Place (site); evidence only", "P3")
    imp_in["notes"] = (
        imp_in.get("notes", "")
        + " v1.2 (Decision 50): the five deployment properties were removed; a "
        "deployment's site is Action DEPLOYED_IN Place."
    ).strip()
    for r in R("IMPLEMENTS") + R("ISSUES") + R("SUPERSEDES") + R("IMPLEMENTED_BY"):
        r["cardinality"] = "many-to-many"

    # ------------------------------------------------------------- P4. alternative_names
    for tid in (
        "Stakeholder",
        "FundingStream",
        "Supplier",
        "Mechanism",
        "Barrier",
        "EnablingCondition",
        "Vulnerability",
        "CapitalProject",
        "Place",
        "FinancialInstrument",
    ):
        add_props(T[tid], [prop("alternative_names", "array<string>", note=ALT_NAMES_NOTE)])
    for tid in ("Solution", "Plan", "Action"):
        pget(T[tid], "alternative_names")["note"] = ALT_NAMES_NOTE
    for tid in ("Solution", "Plan", "Action", "Stakeholder"):
        removed(tid, "aliases", f"{tid}.alternative_names", "P4")

    # ------------------------------------------------------------- P6. Place
    pl = T["Place"]
    pt = pget(pl, "place_type")
    pt["values"] = [
        "watershed",
        "waterbody",
        "corridor",
        "coastline",
        "site",
        "facility",
        "street",
        "park",
        "infrastructure_zone",
        "neighbourhood_area",
        "other",
    ]
    pt["note"] = (
        "Category of non-jurisdictional geographic feature. v1.2 (Decision 51): + "
        "waterbody (river, creek, lake, bay), street, facility (a named building or "
        "plant), neighbourhood_area (a named area with no administrative status)."
    )
    wp = deepcopy(R("WITHIN", "Place", "Jurisdiction")[0])
    wp.update(
        {
            "target": "Place",
            "definition": "This place lies within the larger target place (a creek within a watershed, a park within a corridor).",
            "cardinality": "many-to-one",
            "notes": "v1.2 (Decision 51). Nesting of non-administrative places; the outermost place still has WITHIN → Jurisdiction.",
            "extract_hint": "Look for one named place inside another — e.g., 'Brays Bayou in the Buffalo Bayou watershed'.",
            "@id": "ab:placeWithinPlace",
            "rdfs:range": {"@id": "ab:Place"},
        }
    )
    rels.insert(rels.index(R("WITHIN", "Place", "Jurisdiction")[0]) + 1, wp)

    # ------------------------------------------------------------- P7. names on instance types
    for tid in ("ExposureUnit", "Vulnerability"):
        add_props(
            T[tid],
            [
                prop("name", "string", True, note="v1.2 (Decision 51). Short name that identifies this node, e.g. 'residents of the Zone A floodplain'."),
                prop("description", "string", note="v1.2 (Decision 51)."),
            ],
            after=None,
        )
        # name and description first
        props = T[tid]["properties"]
        T[tid]["properties"] = props[-2:] + props[:-2]
    pget(T["Stakeholder"], "name")["required"] = True

    # ------------------------------------------------------------- P9. bindings
    fixes = {
        "Solution": ("ipcc_action_types", "ipcc_action_type"),
        "Stakeholder": ("actor_type", "implementing_actor_type"),
        "EnablingCondition": ("condition_type", "enabling_condition_type"),
        "Barrier": ("barrier_type", "enabling_condition_type"),
    }
    for tid, (bad, good) in fixes.items():
        vb = next(b for b in T[tid]["vocabulary_bindings"] if b["field"] == bad)
        vb["field"] = good
    E = load(VOC / "enums.json")
    blocks = {k: [v["id"] for v in b["values"]] for k, b in E.items() if isinstance(b, dict) and "values" in b}
    prop_binds = {
        ("Solution", "ipcc_action_types"): "ipcc_action_type",
        ("Stakeholder", "stakeholder_type"): "implementing_actor_type",
        ("EnablingCondition", "condition_type"): "enabling_condition_type",
        ("Barrier", "barrier_type"): "enabling_condition_type",
        ("FinancialInstrument", "instrument_type"): "instrument_type",
        ("Outcome", "co_benefit_type"): "co_benefit_category",
        ("Outcome", "beneficiary_program"): "municipal_program",
    }
    for (tid, pid), block in prop_binds.items():
        p = pget(T[tid], pid)
        assert p["values"] == blocks[block], (tid, pid, block)
        bind(p, block)
    ob = next(b for b in T["Outcome"]["vocabulary_bindings"] if "beneficiary_program" in b["field"])
    ob["field"] = ob["field"].replace("beneficiary_program", "municipal_program")
    dpo = R("DEMONSTRATES_PROGRESS_ON")[0]
    p = pget(dpo, "evidence_level")
    assert p["values"] == blocks["evidence_level"]
    bind(p, "evidence_level")

    # ------------------------------------------------------------- P8. notes sweep
    sweep = {
        "FinancingSource": "FundingStream",
        "FUNDED_BY": "FUNDS",
        "GovernanceStructure": "Stakeholder",
        "CONTAINS_ACTION": "SPECIFIES",
        "TARGETS_GOAL": "PURSUES",
        "SETS_GOAL": "SETS",
    }
    hist = []

    def sweep_text(s, where):
        if not isinstance(s, str):
            return s
        for old, new in sweep.items():
            if old in s:
                hist.append((where, old))
        return s

    for t in types:
        for k in ("definition", "notes", "extract_hint"):
            sweep_text(t.get(k), f"{t['id']}.{k}")
        for p in t["properties"]:
            sweep_text(p.get("note"), f"{t['id']}.{p['id']}")
    for r in rels:
        for k in ("definition", "notes", "extract_hint"):
            sweep_text(r.get(k), f"{r['id']}({r['source']}->{r['target']}).{k}")
    # Notes that would instruct an extractor with a retired id are rewritten;
    # notes that only record history ("absorbed from GovernanceStructure",
    # "replaces FUNDED_BY") keep the old name.
    rewrites = [
        (T["ResilienceGoal"], "notes", "SETS_GOAL (plan aspiration)", "SETS (plan aspiration)"),
        (R("PURSUES")[0], "notes", "between SETS_GOAL (plan aspiration)", "between SETS (plan aspiration)"),
        (R("PRESCRIBES")[0], "notes", "Distinct from CONTAINS_ACTION (specific time-bound commitments)", "Distinct from SPECIFIES (a plan's specific, time-bound Actions)"),
        (T["Action"], "notes", "and FUNDED_BY FinancingSource (funding_source_s)", "and a funding edge (funding_source_s; FUNDED_BY, retired in v1.1)"),
        (T["CapitalProject"], "notes", "and FUNDED_BY FinancingSource (landing the edge referenced since v0.2)", "and a funding edge (FUNDED_BY, retired in v1.1)"),
    ]
    for owner, key, old, new in rewrites:
        assert old in owner[key], (owner.get("id"), old)
        owner[key] = owner[key].replace(old, new)
    hist.clear()
    for t in types:
        for k in ("definition", "notes", "extract_hint"):
            sweep_text(t.get(k), f"{t['id']}.{k}")
    for r in rels:
        for k in ("definition", "notes", "extract_hint"):
            sweep_text(r.get(k), f"{r['id']}({r['source']}->{r['target']}).{k}")
    STALE_DESIGN = {
        "Resilience Finance — Five-Axis Split (v0.2)",
        "Action-level CDP edges & FUNDED_BY landing (v0.6)",
        "CapitalProject Edge Economy (v0.2, revised v0.6)",
        "Solution vs Action",
        "Epistemic Hierarchy for Resilience Goals",
    }
    for dn in o["metadata"]["design_notes"]:
        if dn["topic"] in STALE_DESIGN:
            dn["status"] = "historical"
            dn["superseded_by"] = (
                "v1.1 Decision 43 (finance) / v1.1 Decisions 35-41 (Solution, Action, goals)"
            )
    o["metadata"]["design_notes"].extend(
        [
            {
                "topic": "Reference data outside the graph (v1.2)",
                "note": (
                    "Large quantitative reference data (climate projections, indicators "
                    "at scale) lives in tables outside the graph. The graph carries edges "
                    "derived from it by a stated, versioned rule, with per-source "
                    "provenance (AFFECTED_BY.sources). This is why Probable Futures adds "
                    "no node type, and it is the pattern for later datasets (Decision 47)."
                ),
                "status": "current",
            },
            {
                "topic": "Provenance is the evidence store (v1.2)",
                "note": (
                    "Every value in the graph — a node property, an edge property, the "
                    "edge itself, a name merged into alternative_names — is backed by "
                    "one or more evidence rows: the source chunk or URL, an excerpt, "
                    "the method, and as_of where stated. claim_ids stays optional on "
                    "every edge and no Claim type is declared; the evidence store is the "
                    "claim layer (Decision 52)."
                ),
                "status": "current",
            },
        ]
    )

    # ------------------------------------------------------------- vocabularies manifest
    V = o["vocabularies"]
    hzm = by_id(V, "hazards")
    hzm["description"] = (
        "7 hazard clusters and 52 specific hazards from the UNDRR-ISC Hazard Information "
        "Profiles 2025, each with a one-line definition stating its boundary. "
        "Crosswalked to C40/Arup (climate) and RCC (non-climate) sources."
    )
    hzm["terms_count"] = 52
    by_id(V, "urban-systems")["description"] = (
        "Hierarchical classification of urban infrastructure and services (sector → "
        "subsector → system), each system with a definition. An urban system is "
        "something a city has whether or not it adapts; a thing that is also an "
        "intervention is a Solution (v1.2, Decision 53: ten terms retired)."
    )
    ev = by_id(V, "enums.evidence_level")
    ev["bound_to"] = [
        "Outcome.evidence_level",
        "DEMONSTRATES_PROGRESS_ON.evidence_level",
    ]
    by_id(V, "enums.instrument_type")["bound_to"] = [
        "FinancialInstrument.instrument_type",
        "FundingAllocation.instrument_type",
    ]
    for vid, bound in (
        ("enums.ipcc_action_type", ["Solution.ipcc_action_types"]),
        ("enums.implementing_actor_type", ["Stakeholder.stakeholder_type"]),
        ("enums.enabling_condition_type", ["EnablingCondition.condition_type", "Barrier.barrier_type"]),
        ("enums.co_benefit_category", ["Outcome.co_benefit_type"]),
        ("enums.municipal_program", ["Outcome.beneficiary_program"]),
    ):
        by_id(V, vid)["bound_to"] = bound
    V.append(
        {
            "id": "enums.resilience_contribution",
            "label": "Resilience contribution",
            "type": "internal",
            "url": "",
            "description": "Whose resilience an action builds: adapted or enabling (Decision 49, after the EU Taxonomy).",
            "bound_to": ["Action.resilience_contribution"],
            "terms_count": 2,
            "@id": "abv:enums-resilience_contribution",
            "@type": "skos:ConceptScheme",
        }
    )
    gone = {f"{k['owner']}.{k['key']}" for k in REMOVED_KEYS}
    for row in V:
        row["bound_to"] = [
            b
            for b in row.get("bound_to", [])
            if "(CapitalProject->Outcome)" not in b and b not in gone
        ]

    # ------------------------------------------------------------- header, notes, metadata
    o["version"] = VERSION
    o["updated"] = UPDATED
    o["update_note"] = (
        "v1.2 — cut from the 2026-10-08 decision set (Decisions 45–53), whose input was "
        "the 2026-10-06 review and its addendum. A plan's characterisation of a hazard "
        "moves off the shared Hazard node to the plan's ADDRESSES edge; AFFECTED_BY "
        "holds one entry per supporting source; Jurisdiction has one coordinate field; "
        "every named type gets alternative_names; facts stored twice are kept once; the "
        "hazard list gains definitions, water_stress and coastal_erosion; ten "
        "Solution-shaped or population-shaped urban systems are retired; Action gains "
        "resilience_contribution; dangling vocabulary bindings are fixed; and a "
        "structural checker guards the repo."
    )
    o["version_notes"].insert(
        0,
        {
            "version": VERSION,
            "date": DATE,
            "summary": o["update_note"],
            "changes": [
                {"type": "changed", "text": "Hazard.frequency, severity, trend, return_period, climate_scenario, climate_scenario_other_description, projection_year moved to ADDRESSES (Plan → Hazard); ADDRESSES (Plan → Hazard) + indicators (Decisions 45, 46; review L-4 narrowed)"},
                {"type": "changed", "text": "AFFECTED_BY: required `sources` object, one entry per source (dataset | plan_document); top-level source_dataset and indicators removed (Decision 47)"},
                {"type": "changed", "text": "Jurisdiction: geometry is the one coordinate field; polygon note reworded to redistributable sources only; climate_zone source named; aliases → alternative_names (Decisions 48, 51)"},
                {"type": "added", "text": "Action.resilience_contribution {adapted, enabling}, enums.resilience_contribution (Decision 49)"},
                {"type": "added", "text": "Mechanism.mechanism_type_other_description — the property mechanism_type's note has pointed at since v0.4 but never declared (Decision 54)"},
                {"type": "removed", "text": "outcome_type and evidence_level on PRODUCES (Solution → Outcome) and RESULTS_IN; ISSUES.adoption_status; the five IMPLEMENTED_IN deployment properties; reduces_exposure on REDUCES.mechanism_of_reduction (multi_pathway → both) (Decision 50)"},
                {"type": "changed", "text": "Cardinality: IMPLEMENTS, ISSUES, SUPERSEDES, IMPLEMENTED_BY → many-to-many (review C-4)"},
                {"type": "added", "text": "alternative_names on Stakeholder, FundingStream, Supplier, Mechanism, Barrier, EnablingCondition, Vulnerability, CapitalProject, Place, FinancialInstrument; one note on every type (Decision 51)"},
                {"type": "added", "text": "Place.place_type + waterbody, street, facility, neighbourhood_area; WITHIN Place → Place; ExposureUnit and Vulnerability + name (required), description; Stakeholder.name required (Decision 51)"},
                {"type": "changed", "text": "hazards.json: a definition per hazard; + water_stress, coastal_erosion; rcc.sea_level_rise renamed 'Sea level rise' (erosion split out); overlapping undrr_terms de-duplicated (Decision 53)"},
                {"type": "changed", "text": "urban-systems.json: a definition per system; ten terms retired with replaced_by (green roofs, permeable surfaces, constructed wetlands, early warning, evacuation and sheltering, resilience hubs, hard engineering, disease monitoring, insurance markets, vulnerable populations); + cultural_heritage_sites, solid_waste_management, public_health_services (Decision 53)"},
                {"type": "changed", "text": "Vocabulary bindings: four dangling type-level bindings fixed; seven inline enums bound to their enums.json block (inline values kept, checked equal) (review C-1, C-2)"},
                {"type": "added", "text": "Design notes: reference data outside the graph; provenance is the evidence store (claim_ids stays optional, no Claim type) (Decisions 47, 52). Five design notes describing retired models marked historical (review V-5)"},
                {"type": "added", "text": "scripts/check_ontology.py structural checker, run in CI (review P-10)"},
                {"type": "removed_keys", "text": "Every removed or renamed key with its new home, for consumers' key registries (review V-6)", "keys": REMOVED_KEYS},
            ],
        },
    )
    m = o["metadata"]
    m["types_count"] = len(types)
    m["relationships_count"] = len(rels)
    m["vocabularies_count"] = len(V)
    m["change_history"].insert(
        0,
        f"v1.2 ({DATE}): plan hazard details to ADDRESSES; AFFECTED_BY per-source; one "
        f"coordinate field; alternative_names on every named type; duplicated edge facts "
        f"removed; hazard and urban-system definitions, splits and retirements. "
        f"{len(types)} types, {len(rels)} relationships, {len({r['id'] for r in rels})} predicate ids.",
    )
    dump(DST, o)
    print(
        f"wrote {DST.relative_to(REPO)}: {len(types)} types, {len(rels)} relationships, "
        f"{len({r['id'] for r in rels})} predicate ids, {len(V)} vocab rows, "
        f"{len(REMOVED_KEYS)} removed keys"
    )
    if hist:
        print("notes still naming retired ids (left as history):")
        for where, old in hist:
            print(f"   {where}: {old}")

    vocab_edits()


def vocab_edits() -> None:
    D = load(DEFS)

    # ------------------------------------------------------------- enums.json
    E = load(VOC / "enums.json")
    if "resilience_contribution" not in E:
        E["resilience_contribution"] = {
            "_source": "EU Taxonomy for sustainable activities, Regulation (EU) 2020/852, Art. 11 (adapted activities) and Art. 16 (enabling activities)",
            "_usage": "Action.resilience_contribution",
            "_note": "v1.2 (Decision 49). Whose resilience an action builds.",
            "values": [
                {"id": "adapted", "name": "Adapted", "description": "Makes the acting party's own assets, operations or services resilient (a utility floodproofing its own substation)."},
                {"id": "enabling", "name": "Enabling", "description": "Builds the resilience of other people, assets or the city as a whole (a heat warning service, a grant programme for homeowners)."},
            ],
        }
        dump(VOC / "enums.json", E)
        print("enums.json: + resilience_contribution")

    # ------------------------------------------------------------- hazards.json
    H = load(VOC / "hazards.json")
    cats = {c["id"]: c for c in H["categories"]}
    allh = {z["id"]: z for c in H["categories"] for z in c["hazards"]}
    if "water_stress" not in allh:
        mh = cats["meteorological_hydrological"]["hazards"]
        i = [z["id"] for z in mh].index("drought") + 1
        mh.insert(
            i,
            {
                "id": "water_stress",
                "name": "Water stress",
                "c40_arup_category": "water_scarcity",
                "hazard_source": "c40_arup",
                "undrr_terms": ["water stress", "water scarcity", "water shortage", "chronic water shortage", "baseline water stress"],
                "added_in": "v1.2",
            },
        )
    if "coastal_erosion" not in allh:
        geo = cats["geohazards"]["hazards"]
        i = [z["id"] for z in geo].index("subsidence") + 1
        geo.insert(
            i,
            {
                "id": "coastal_erosion",
                "name": "Coastal erosion",
                "c40_arup_category": None,
                "hazard_source": "rcc",
                "undrr_terms": ["coastal erosion", "shoreline erosion", "shoreline retreat", "beach erosion", "cliff erosion", "dune erosion"],
                "added_in": "v1.2",
                "_note": "v1.2 (Decision 53): split from rcc.sea_level_rise ('Sea Level Rise / Coastal Erosion'), which named two hazards. The id has no rcc. prefix; hazard_source carries the source.",
            },
        )
    allh = {z["id"]: z for c in H["categories"] for z in c["hazards"]}
    slr = allh["rcc.sea_level_rise"]
    slr["name"] = "Sea level rise"
    slr["undrr_terms"] = ["sea level rise", "sea-level rise", "relative sea level rise", "rising sea levels"]
    term_moves = {
        "drought": ["water shortage", "water stress"],
        "heat_wave": ["heat stress"],
        "subsidence": ["land subsidence", "ground settlement"],
        "air-borne_disease": ["epidemic", "pandemic"],
        "river_flood": ["inundation"],
    }
    for hid, drop in term_moves.items():
        allh[hid]["undrr_terms"] = [t for t in allh[hid]["undrr_terms"] if t not in drop]
    for t in ("hot days", "rising temperatures", "warmer summers"):
        if t not in allh["extreme_hot_weather"]["undrr_terms"]:
            allh["extreme_hot_weather"]["undrr_terms"].append(t)
    for hid, z in allh.items():
        z["definition"] = D["hazards"][hid]
    missing = set(allh) - set(D["hazards"])
    assert not missing, missing
    H["_note"] = H["_note"].split(" v1.2:")[0] + (
        " v1.2: every hazard has a one-line definition stating its boundary with its "
        "nearest neighbour; water_stress and coastal_erosion added; rcc.sea_level_rise "
        "now means sea level rise only; overlapping undrr_terms de-duplicated "
        "(Decision 53)."
    )
    H["_usage"] = "Hazard.hazard_id, Hazard.hazard_category"
    dump(VOC / "hazards.json", H)
    print(f"hazards.json: {len(allh)} hazards, all defined")

    # ------------------------------------------------------------- urban-systems.json
    U = load(VOC / "urban-systems.json")
    secs = {s["id"]: s for s in U["sectors"]}
    for n in D["new_urban_systems"]:
        ss = next(x for x in secs[n["sector"]]["subsectors"] if x["id"] == n["subsector"])
        if n["id"] not in {y["id"] for y in ss["systems"]}:
            ss["systems"].append({"id": n["id"], "name": n["name"], "examples": n["examples"], "added_in": "v1.2"})
    systems = {y["id"]: y for s in U["sectors"] for ss in s["subsectors"] for y in ss["systems"]}
    for sid, y in systems.items():
        y["definition"] = D["urban_systems"][sid]
    for sid, repl in D["retired_urban_systems"].items():
        y = systems[sid]
        y["status"] = "deprecated"
        y["deprecated_in"] = "v1.2"
        y["replaced_by"] = repl
    missing = set(systems) - set(D["urban_systems"])
    assert not missing, missing
    U["_usage"] = "UrbanSystem.system_id, UrbanSystem.sector, UrbanSystem.subsector"
    U["_note"] = U["_note"].split(" v1.2:")[0] + (
        " v1.2: every system has a definition. Rule: an urban system is something a "
        "city has whether or not it adapts; a thing that is itself an intervention is a "
        "Solution. Ten terms are retired (status: deprecated, replaced_by: the systems "
        "to use instead; an empty list means none). Sector ids may be used as system_id "
        "for sector-level links."
    )
    dump(VOC / "urban-systems.json", U)
    print(f"urban-systems.json: {len(systems)} systems, {len(D['retired_urban_systems'])} retired")

    # ------------------------------------------------------------- versions.json
    vs = load(ONT / "versions.json")
    if vs[0]["value"] != VERSION:
        vs.insert(0, {"path": f"../ontology/ontology-{VERSION}.jsonld", "label": VERSION, "value": VERSION})
        dump(ONT / "versions.json", vs)


if __name__ == "__main__":
    main()
    import subprocess
    import sys

    subprocess.run(
        [sys.executable, str(REPO / "scripts" / "export" / "build_vocab_jsonld.py")], check=True
    )
