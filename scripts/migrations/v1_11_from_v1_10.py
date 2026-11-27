#!/usr/bin/env python3
"""Build ontology/ontology-v1.11.jsonld from v1.10, and add the enums.outcome_basis block.

Run with: uv run scripts/migrations/v1_11_from_v1_10.py
Re-runnable: the enums block is added once; ontology-v1.11.jsonld and versions.json are
rebuilt. Then run scripts/export/build_vocab_jsonld.py for the vocabulary twins.

v1.11 is one decision (Decision 64, Anthony 2026-11-24): every Outcome says in the new
Outcome.basis whether it happened (measured, estimated), is what the place expects an action
to achieve (projected), is what a kind of solution does in no particular place (general), or
is a plan's own desired outcome (target). adaptbase-core read the 1,661 Outcomes in the graph
against their passages: about 500 happened and about 800 are what a plan says will happen,
and nothing on the node told them apart. No type or relationship changes.
"""

import json
from copy import deepcopy
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ONT = REPO / "ontology"
SRC = ONT / "ontology-v1.10.jsonld"
DST = ONT / "ontology-v1.11.jsonld"
ENUMS = ONT / "vocabularies" / "enums.json"
VERSION = "v1.11"
DATE = "2026-11-27"
UPDATED = "2026-11-27T18:00:00.000Z"

D = "v1.11 (Decision 64)."

OUTCOME_BASIS = {
    "_source": "v1.11 (Decision 64)",
    "_usage": "Outcome.basis",
    "_note": (
        "Whether the Outcome happened, is expected, is a general effect of a kind of solution, "
        "or is a plan's own desired outcome. Set on every Outcome. measured, estimated and "
        "projected mean what they mean in value_basis; an Outcome with an Indicator that "
        "carries a figure takes that Indicator's value_basis."
    ),
    "values": [
        {
            "id": "measured",
            "name": "Measured",
            "description": "It happened in the document's own place, and the source observed or counted it after the fact.",
        },
        {
            "id": "estimated",
            "name": "Estimated",
            "description": (
                "It happened or exists in the document's own place, and its size is an estimate "
                "or a model result. A modeled benefit of a measure not yet built, or of a future "
                "scenario, is projected, whatever word the source uses."
            ),
        },
        {
            "id": "projected",
            "name": "Projected",
            "description": (
                "What the document expects an action or a solution to achieve in its own place. "
                "Nothing has been observed yet."
            ),
        },
        {
            "id": "general",
            "name": "General",
            "description": (
                "What a kind of solution does, in no particular place. Never on an Outcome an "
                "Action RESULTS_IN."
            ),
        },
        {
            "id": "target",
            "name": "Target",
            "description": (
                "A plan's own desired outcome: what the plan sets out to bring about, stated as "
                "an aim rather than as the expected result of one action."
            ),
        },
    ],
}

OUTCOME_DEFINITION = (
    "A result of implementing a solution or action: one that was measured or estimated, one the "
    "document expects, a plan's own desired outcome, or what a kind of solution does in general. "
    "The basis property says which. Includes effectiveness indicators, co-benefits, and failure "
    "modes."
)

OUTCOME_HINT_ADD = (
    " Set basis on every Outcome. measured: the passage reports it as something that happened "
    "and was observed or counted ('has reduced', 'were planted', 'met the goal in 2019'). "
    "estimated: it happened or exists and its size is an estimate or a model result ('an "
    "estimated', 'a study valued'). projected: what the document expects an action to achieve "
    "('will reduce', 'is expected to', 'is meant to', 'could'). general: what a kind of solution "
    "does, in no particular place; it belongs on an Outcome a Solution PRODUCES, never on one an "
    "Action RESULTS_IN. target: the plan's "
    "own desired outcome ('Desired outcome:', 'Target outcome:', a row of a results framework). "
    "A modeled or estimated benefit of a measure that is not yet built, or of a future scenario "
    "('under 2 feet of sea-level rise', 'by 2050', 'modeling shows that clustered trees would'), "
    "is projected even when the passage says 'estimated': estimated is only for something that "
    "has already happened or exists. When the Outcome has an Indicator with a measured_value, "
    "basis is that Indicator's value_basis."
)
INDICATOR_HINT_ADD = (
    " A figure a model gives for a measure not yet built, or for a future scenario, has "
    "value_basis projected even when the passage says 'estimated'; estimated is for something "
    "that has already happened or exists."
)
VALUE_BASIS_ESTIMATED = (
    "An estimate or a model result for something that has happened or exists; the source says "
    "estimated, modeled or calculated. A model result for a measure not yet built, or for a "
    "future scenario, is projected."
)


def load(p):
    return json.loads(p.read_text())


def dump(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def by_id(items, id):
    return next(x for x in items if x["id"] == id)


def add_outcome_basis_block() -> int:
    e = load(ENUMS)
    estimated = by_id(e["value_basis"]["values"], "estimated")
    if estimated["description"] != VALUE_BASIS_ESTIMATED:
        estimated["description"] = VALUE_BASIS_ESTIMATED
        dump(ENUMS, e)
    if "outcome_basis" not in e:
        out = {}
        for k, v in e.items():
            out[k] = v
            if k == "value_basis":
                out["outcome_basis"] = OUTCOME_BASIS
        e = out
        dump(ENUMS, e)
    return len(e["outcome_basis"]["values"])


def outcome(o: dict) -> None:
    out = by_id(o["types"], "Outcome")
    out["definition"] = OUTCOME_DEFINITION
    if not any(p["id"] == "basis" for p in out["properties"]):
        at = (
            next(
                i
                for i, p in enumerate(out["properties"])
                if p["id"] == "evidence_level"
            )
            + 1
        )
        out["properties"].insert(
            at,
            {
                "id": "basis",
                "type": "enum",
                # required: every Outcome has one. adaptbase-core's extractor asks
                # once more for a required classification it left empty.
                "required": True,
                "values": [v["id"] for v in OUTCOME_BASIS["values"]],
                "note": (
                    f"{D} Whether the Outcome happened or is expected. measured (it happened and "
                    "was observed or counted), estimated (it happened or exists and its size is "
                    "an estimate or model result), projected (what the document expects an "
                    "action to achieve), general (what a kind of solution does, in no particular "
                    "place; never on an Outcome an Action RESULTS_IN), target (a plan's own "
                    "desired outcome). Set on every Outcome. An Outcome with an Indicator that "
                    "carries a measured_value takes that Indicator's value_basis. Not the same "
                    "question as evidence_level, which grades how rigorous a measurement is."
                ),
                "vocabulary_binding": {"vocab": "enums", "field": "outcome_basis"},
                "ab:boundToVocabulary": {"@id": "abv:enums-outcome_basis"},
            },
        )
    vb = {"vocab": "enums", "field": "outcome_basis"}
    if vb not in out["vocabulary_bindings"]:
        out["vocabulary_bindings"].append(vb)
    if OUTCOME_HINT_ADD not in out["extract_hint"]:
        out["extract_hint"] += OUTCOME_HINT_ADD
    if "Decision 64" not in out["notes"]:
        out["notes"] += (
            f" {D} basis says whether the Outcome was measured, estimated, is projected, is a "
            "general effect of a kind of solution, or is a plan's own target; before v1.11 "
            "nothing on the node told a result from a promise."
        )


def indicator(o: dict) -> None:
    ind = by_id(o["types"], "Indicator")
    if INDICATOR_HINT_ADD not in ind["extract_hint"]:
        ind["extract_hint"] += INDICATOR_HINT_ADD


def main() -> None:
    n_basis = add_outcome_basis_block()
    o = deepcopy(load(SRC))
    types, rels = o["types"], o["relationships"]

    outcome(o)
    indicator(o)

    if not any(v["id"] == "enums.outcome_basis" for v in o["vocabularies"]):
        ev = by_id(o["vocabularies"], "enums.value_basis")
        o["vocabularies"].insert(
            o["vocabularies"].index(ev) + 1,
            {
                "id": "enums.outcome_basis",
                "label": "Outcome basis",
                "type": "internal",
                "url": "",
                "description": (
                    "Whether an Outcome was measured, estimated, is projected, is a general "
                    "effect of a kind of solution, or is a plan's own target (Decision 64)."
                ),
                "bound_to": ["Outcome.basis"],
                "terms_count": n_basis,
                "@id": "abv:enums-outcome_basis",
                "@type": "skos:ConceptScheme",
            },
        )

    md = o["metadata"]
    md["types_count"] = len(types)
    md["relationships_count"] = len(rels)
    md["vocabularies_count"] = len(o["vocabularies"])
    n_pred = len({r["id"] for r in rels})
    summary = (
        f"v1.11 (2026-11-27): did it happen (Decision 64). New Outcome.basis (measured, "
        f"estimated, projected, general, target); the Outcome definition now covers expected "
        f"and general results, and basis says which. {len(types)} types, {len(rels)} "
        f"relationships, {n_pred} predicate ids."
    )
    md["change_history"] = [
        h for h in md.get("change_history", []) if not h.startswith("v1.11 ")
    ]
    md["change_history"].insert(0, summary)

    o["version"] = VERSION
    o["updated"] = UPDATED
    o["update_note"] = (
        "v1.11 — one decision (Decision 64, 2026-11-24): every Outcome says in the new basis "
        "property whether it was measured, estimated, is projected, is a general effect of a "
        "kind of solution, or is a plan's own target. The Outcome definition is widened to "
        "match what the type holds, and the Outcome hint asks for basis on every Outcome."
    )
    o["version_notes"] = [
        n for n in o.get("version_notes", []) if n.get("version") != VERSION
    ]
    o["version_notes"].insert(
        0,
        {
            "version": VERSION,
            "date": DATE,
            "summary": o["update_note"],
            "changes": [
                {
                    "type": "added",
                    "text": "Outcome.basis, bound to the new enums.outcome_basis: measured, estimated, projected, general, target (Decision 64)",
                },
                {
                    "type": "changed",
                    "text": "Outcome.definition: a result that was measured or estimated, one the document expects, a plan's own desired outcome, or what a kind of solution does in general; basis says which (Decision 64)",
                },
                {
                    "type": "changed",
                    "text": "Outcome.extract_hint: set basis on every Outcome; general only under a Solution; an Outcome with a figure takes its Indicator's value_basis (Decision 64)",
                },
                {
                    "type": "changed",
                    "text": "Indicator.extract_hint and enums.value_basis: a model result for a measure not yet built, or for a future scenario, is projected even when the source says 'estimated' (Decision 64)",
                },
            ],
        },
    )
    dump(DST, o)
    print(
        f"wrote {DST.name}: {len(types)} types, {len(rels)} edges, {n_pred} predicate ids"
    )
    vs = load(ONT / "versions.json")
    if vs[0]["value"] != VERSION:
        vs.insert(
            0,
            {
                "path": f"../ontology/ontology-{VERSION}.jsonld",
                "label": VERSION,
                "value": VERSION,
            },
        )
        dump(ONT / "versions.json", vs)


if __name__ == "__main__":
    main()
