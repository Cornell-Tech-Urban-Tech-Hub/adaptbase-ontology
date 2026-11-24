#!/usr/bin/env python3
"""Build ontology/ontology-v1.10.jsonld from v1.9, and add the enums.value_basis block.

Run with: uv run scripts/migrations/v1_10_from_v1_9.py
Re-runnable: the enums block is added once; ontology-v1.10.jsonld and versions.json are
rebuilt. Then run scripts/export/build_vocab_jsonld.py for the vocabulary twins.

v1.10 is one decision (Decision 63, Anthony 2026-11-24): an Indicator's measured_value is a
figure for the document's own place, and the new Indicator.value_basis says whether it was
measured, estimated or projected. adaptbase-core read all 383 Outcome -> Indicator pairs that
carried a figure against their passages: 172 were a result in the document's own place; the
rest were another city's result, a national figure, a value quoted from studies, a
projection, or damage from a hazard. Nothing in the graph told them apart. No type or
relationship changes.
"""

import json
from copy import deepcopy
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ONT = REPO / "ontology"
SRC = ONT / "ontology-v1.9.jsonld"
DST = ONT / "ontology-v1.10.jsonld"
ENUMS = ONT / "vocabularies" / "enums.json"
VERSION = "v1.10"
DATE = "2026-11-24"
UPDATED = "2026-11-24T18:00:00.000Z"

D = "v1.10 (Decision 63)."

VALUE_BASIS = {
    "_source": "v1.10 (Decision 63)",
    "_usage": "Indicator.value_basis",
    "_note": (
        "How the figure in Indicator.measured_value was arrived at. Set whenever measured_value "
        "is set. The figure itself always describes the document's own place."
    ),
    "values": [
        {
            "id": "measured",
            "name": "Measured",
            "description": "Observed, counted or recorded after the fact.",
        },
        {
            "id": "estimated",
            "name": "Estimated",
            "description": (
                "An estimate or a model result for something that has happened or exists; the "
                "source says estimated, modeled or calculated."
            ),
        },
        {
            "id": "projected",
            "name": "Projected",
            "description": (
                "What a measure is expected to achieve, or the result of a scenario. Nothing has "
                "been observed yet."
            ),
        },
    ],
}

OUTCOME_HINT_ADD = (
    " An Outcome is the result of something done. Damage, deaths, losses or risk from a hazard "
    "are not Outcomes. A result another city or country achieved, cited as an example, is not "
    "this document's Outcome: skip it. What a kind of solution does in general ('cool roofs "
    "lower indoor temperatures') is an Outcome a Solution PRODUCES, never one an Action "
    "RESULTS_IN."
)
INDICATOR_HINT_ADD = (
    " Put a figure in measured_value only when it describes the document's own place, and say "
    "in value_basis whether it was measured, estimated or projected. Leave measured_value empty "
    "for a figure from another city, a national or global figure, or a value quoted from "
    "studies. A goal not yet reached goes in target."
)


def load(p):
    return json.loads(p.read_text())


def dump(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def by_id(items, id):
    return next(x for x in items if x["id"] == id)


def add_value_basis_block() -> int:
    e = load(ENUMS)
    if "value_basis" not in e:
        out = {}
        for k, v in e.items():
            out[k] = v
            if k == "evidence_level":
                out["value_basis"] = VALUE_BASIS
        e = out
        dump(ENUMS, e)
    return len(e["value_basis"]["values"])


def indicator(o: dict) -> None:
    ind = by_id(o["types"], "Indicator")
    mv = by_id(ind["properties"], "measured_value")
    mv["note"] = (
        f"{D} A figure for the document's own place: observed, estimated or projected there. "
        "Never a figure from another city, a national or global figure, or a value quoted from "
        "studies; leave it empty for those. Set value_basis whenever this is set."
    )
    if not any(p["id"] == "value_basis" for p in ind["properties"]):
        at = next(i for i, p in enumerate(ind["properties"]) if p["id"] == "measured_value") + 1
        ind["properties"].insert(
            at,
            {
                "id": "value_basis",
                "type": "enum",
                "required": False,
                "values": [v["id"] for v in VALUE_BASIS["values"]],
                "note": (
                    f"{D} How measured_value was arrived at: measured (observed or counted after "
                    "the fact), estimated (an estimate or model result for something that "
                    "happened or exists), projected (what a measure is expected to achieve, or a "
                    "scenario). Set whenever measured_value is set."
                ),
                "vocabulary_binding": {"vocab": "enums", "field": "value_basis"},
                "ab:boundToVocabulary": {"@id": "abv:enums-value_basis"},
            },
        )
    vb = {"vocab": "enums", "field": "value_basis"}
    if vb not in ind["vocabulary_bindings"]:
        ind["vocabulary_bindings"].append(vb)
    if INDICATOR_HINT_ADD not in ind["extract_hint"]:
        ind["extract_hint"] += INDICATOR_HINT_ADD
    if "Decision 63" not in ind["notes"]:
        ind["notes"] += (
            f" {D} measured_value holds a figure for the document's own place only, and "
            "value_basis says how it was arrived at; before v1.10 it held any figure the "
            "passage stated."
        )


def outcome(o: dict) -> None:
    out = by_id(o["types"], "Outcome")
    if OUTCOME_HINT_ADD not in out["extract_hint"]:
        out["extract_hint"] += OUTCOME_HINT_ADD


def main() -> None:
    n_basis = add_value_basis_block()
    o = deepcopy(load(SRC))
    types, rels = o["types"], o["relationships"]

    indicator(o)
    outcome(o)

    if not any(v["id"] == "enums.value_basis" for v in o["vocabularies"]):
        ev = by_id(o["vocabularies"], "enums.evidence_level")
        o["vocabularies"].insert(
            o["vocabularies"].index(ev) + 1,
            {
                "id": "enums.value_basis",
                "label": "Value basis",
                "type": "internal",
                "url": "",
                "description": "How an Indicator's measured value was arrived at (Decision 63).",
                "bound_to": ["Indicator.value_basis"],
                "terms_count": n_basis,
                "@id": "abv:enums-value_basis",
                "@type": "skos:ConceptScheme",
            },
        )

    md = o["metadata"]
    md["types_count"] = len(types)
    md["relationships_count"] = len(rels)
    md["vocabularies_count"] = len(o["vocabularies"])
    n_pred = len({r["id"] for r in rels})
    summary = (
        f"v1.10 (2026-11-24): whose figure, and how arrived at (Decision 63). "
        f"Indicator.measured_value is a figure for the document's own place; new "
        f"Indicator.value_basis (measured, estimated, projected). {len(types)} types, "
        f"{len(rels)} relationships, {n_pred} predicate ids."
    )
    md["change_history"] = [h for h in md.get("change_history", []) if not h.startswith("v1.10 ")]
    md["change_history"].insert(0, summary)

    o["version"] = VERSION
    o["updated"] = UPDATED
    o["update_note"] = (
        "v1.10 — one decision (Decision 63, 2026-11-24): an Indicator's measured_value is a "
        "figure for the document's own place, and the new value_basis says whether it was "
        "measured, estimated or projected. The Outcome and Indicator hints say what is not an "
        "Outcome: hazard damage, and another city's result cited as an example."
    )
    o["version_notes"] = [n for n in o.get("version_notes", []) if n.get("version") != VERSION]
    o["version_notes"].insert(
        0,
        {
            "version": VERSION,
            "date": DATE,
            "summary": o["update_note"],
            "changes": [
                {"type": "added", "text": "Indicator.value_basis, bound to the new enums.value_basis: measured, estimated, projected (Decision 63)"},
                {"type": "changed", "text": "Indicator.measured_value: a figure for the document's own place only; never another city's, a national or global figure, or a value quoted from studies (Decision 63)"},
                {"type": "changed", "text": "Outcome.extract_hint and Indicator.extract_hint: hazard damage and another place's result are not Outcomes; a general effect of a kind of solution is an Outcome a Solution PRODUCES (Decision 63)"},
            ],
        },
    )
    dump(DST, o)
    print(f"wrote {DST.name}: {len(types)} types, {len(rels)} edges, {n_pred} predicate ids")
    vs = load(ONT / "versions.json")
    if vs[0]["value"] != VERSION:
        vs.insert(0, {"path": f"../ontology/ontology-{VERSION}.jsonld", "label": VERSION, "value": VERSION})
        dump(ONT / "versions.json", vs)


if __name__ == "__main__":
    main()
