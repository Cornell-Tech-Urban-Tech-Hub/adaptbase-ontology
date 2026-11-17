#!/usr/bin/env python3
"""Build ontology/ontology-v1.8.jsonld from v1.7, and add the v1.8 vocabulary term.

Run with: uv run scripts/migrations/v1_8_from_v1_7.py
Re-runnable: the term is added once; ontology-v1.8.jsonld and versions.json are rebuilt.
Then run scripts/export/build_vocab_jsonld.py for the vocabulary twins.

v1.8 is one decision (Decision 61, Anthony 2026-11-11): 'Storm (type not stated)', the
parent of the storm types, for a source that says only 'storms'. It follows v1.7's
'Flood (type not stated)' and carries the same rule. No type, relationship or property
changes.
"""

import json
from copy import deepcopy
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ONT = REPO / "ontology"
SRC = ONT / "ontology-v1.7.jsonld"
DST = ONT / "ontology-v1.8.jsonld"
HAZARDS = ONT / "vocabularies" / "hazards.json"
VERSION = "v1.8"
DATE = "2026-11-11"
UPDATED = "2026-11-11T18:00:00.000Z"

STORM = {
    "id": "storm_type_not_stated",
    "name": "Storm (type not stated)",
    "c40_arup_category": None,
    "hazard_source": "c40_arup",
    "undrr_terms": ["storm", "storms", "storm events", "severe weather", "coastal storm"],
    "broader_of": [
        "cyclone_hurricane_typhoon",
        "tropical_storm",
        "storm_surge",
        "rain_storm",
        "electrical_storm",
        "severe_wind",
        "tornado",
        "heavy_snow",
        "ice_hail_freezing_rain",
    ],
    "added_in": VERSION,
    "_note": "v1.8 (Decision 61): the parent of the storm types, for sources that say only 'storms'.",
    "definition": (
        "A storm where the passage names no type. Use only then: a passage that indicates a "
        "hurricane or typhoon, a tropical storm, storm surge, intense rainfall, lightning, "
        "damaging wind, a tornado, snow or ice takes cyclone_hurricane_typhoon, tropical_storm, "
        "storm_surge, rain_storm, electrical_storm, severe_wind, tornado, heavy_snow or "
        "ice_hail_freezing_rain."
    ),
}


def load(p):
    return json.loads(p.read_text())


def dump(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def by_id(items, id):
    return next(x for x in items if x["id"] == id)


def add_vocabulary_term() -> int:
    h = load(HAZARDS)
    met = by_id(h["categories"], "meteorological_hydrological")
    if not any(t["id"] == STORM["id"] for t in met["hazards"]):
        at = next(i for i, t in enumerate(met["hazards"]) if t["id"] == "tropical_storm")
        met["hazards"].insert(at + 1, STORM)
    dump(HAZARDS, h)
    return sum(len(c["hazards"]) for c in h["categories"])


def main() -> None:
    n_haz = add_vocabulary_term()
    o = deepcopy(load(SRC))

    hz = by_id(o["types"], "Hazard")
    hz["definition"] = hz["definition"].replace("54 specific hazards", f"{n_haz} specific hazards")
    old = "never fold it into a flood type the text does not name."
    new = (
        old + " A generic 'storms' with no type stated is 'Storm (type not stated)', by the "
        "same rule."
    )
    assert old in hz["extract_hint"]
    if new not in hz["extract_hint"]:
        hz["extract_hint"] = hz["extract_hint"].replace(old, new)

    v = by_id(o["vocabularies"], "hazards")
    v["description"] = v["description"].replace("54 specific hazards", f"{n_haz} specific hazards")
    v["terms_count"] = n_haz

    md = o["metadata"]
    summary = (
        f"v1.8 (2026-11-11): one vocabulary term (Decision 61): Storm (type not stated). "
        f"{n_haz} hazards: {md['types_count']} types, {md['relationships_count']} relationships."
    )
    md["change_history"] = [h for h in md.get("change_history", []) if not h.startswith("v1.8 ")]
    md["change_history"].insert(0, summary)

    o["version"] = VERSION
    o["updated"] = UPDATED
    o["update_note"] = (
        "v1.8 — one decision (Decision 61): 'Storm (type not stated)', the parent of the storm "
        "types, for a source that says only 'storms'. Same rule as 'Flood (type not stated)': "
        "used only when the passage names no type."
    )
    o["version_notes"] = [n for n in o.get("version_notes", []) if n.get("version") != VERSION]
    o["version_notes"].insert(
        0,
        {
            "version": VERSION,
            "date": DATE,
            "summary": o["update_note"],
            "changes": [
                {"type": "added", "text": "hazards.json: storm_type_not_stated, used only when the passage names no storm type (Decision 61)"},
                {"type": "changed", "text": "Hazard.extract_hint: a generic 'storms' takes the new term and is never folded into a type the text does not name"},
            ],
        },
    )
    dump(DST, o)
    print(f"wrote {DST.name}: {n_haz} hazards")
    vs = load(ONT / "versions.json")
    if vs[0]["value"] != VERSION:
        vs.insert(0, {"path": f"../ontology/ontology-{VERSION}.jsonld", "label": VERSION, "value": VERSION})
        dump(ONT / "versions.json", vs)


if __name__ == "__main__":
    main()
