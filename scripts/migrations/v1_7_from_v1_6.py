#!/usr/bin/env python3
"""Build ontology/ontology-v1.7.jsonld from v1.6, and add the v1.7 vocabulary terms.

Run with: uv run scripts/migrations/v1_7_from_v1_6.py
Re-runnable: terms are added once; ontology-v1.7.jsonld and versions.json are rebuilt.
Then run scripts/export/build_vocab_jsonld.py for the vocabulary twins.

v1.7 is one decision (Decision 60, Anthony 2026-10-13 and 2026-10-15): six vocabulary
terms that real plans needed and the lists did not have. No type, relationship or
property changes.
"""

import json
from copy import deepcopy
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ONT = REPO / "ontology"
SRC = ONT / "ontology-v1.6.jsonld"
DST = ONT / "ontology-v1.7.jsonld"
HAZARDS = ONT / "vocabularies" / "hazards.json"
POPULATIONS = ONT / "vocabularies" / "vulnerable-populations.json"
VERSION = "v1.7"
DATE = "2026-11-09"
UPDATED = "2026-11-09T18:00:00.000Z"

FLOOD = {
    "id": "flood_type_not_stated",
    "name": "Flood (type not stated)",
    "c40_arup_category": "flood",
    "hazard_source": "c40_arup",
    "undrr_terms": ["flood", "floods", "flooding", "flood risk", "flood hazard"],
    "broader_of": ["river_flood", "flash_surface_flood", "coastal_flood", "groundwater_flood"],
    "added_in": VERSION,
    "_note": "v1.7 (Decision 60): the parent of the four flood types, for sources that say only 'flooding'.",
    "definition": (
        "Flooding where the passage names no type. Use only then: a passage that indicates "
        "the sea, a river, intense rainfall or groundwater takes coastal_flood, river_flood, "
        "flash_surface_flood or groundwater_flood."
    ),
}

SOIL = {
    "id": "soil_erosion",
    "name": "Soil erosion",
    "c40_arup_category": None,
    "hazard_source": "rcc",
    "undrr_terms": ["soil erosion", "GH0403"],
    "added_in": VERSION,
    "_note": "v1.7 (Decision 60): UNDRR-ISC HIPs 2025 GH0403, cluster Other Geohazard, next to Soil Degradation.",
    "definition": (
        "The inland loss of soil by water or wind. Use coastal_erosion for shoreline material "
        "and subsidence for ground that sinks."
    ),
}

GROUPS = [
    {
        "id": "pregnant_postpartum",
        "name": "Pregnant and Postpartum People",
        "description": "People who are pregnant or have recently given birth, for whom heat, smoke, flooding and disrupted care carry added health risk",
        "added_in": VERSION,
    },
    {
        "id": "informal_workers",
        "name": "Informal Workers",
        "description": "People working outside formal employment and its protections, such as street vendors, waste pickers and day laborers, who often lose income or work exposed during climate events",
        "added_in": VERSION,
    },
    {
        "id": "households_without_cooling",
        "name": "Households without Cooling",
        "description": "Households with no air conditioning or other working means of cooling their home during extreme heat",
        "added_in": VERSION,
    },
    {
        "id": "transit_dependent",
        "name": "Transit-Dependent People",
        "description": "People who rely on public transportation and have no private vehicle, which limits evacuation and access to cooling or services",
        "added_in": VERSION,
    },
]


def load(p):
    return json.loads(p.read_text())


def dump(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def by_id(items, id):
    return next(x for x in items if x["id"] == id)


def add_vocabulary_terms() -> tuple[int, int]:
    h = load(HAZARDS)
    met = by_id(h["categories"], "meteorological_hydrological")
    if not any(t["id"] == FLOOD["id"] for t in met["hazards"]):
        last = max(i for i, t in enumerate(met["hazards"]) if t.get("c40_arup_category") == "flood")
        met["hazards"].insert(last + 1, FLOOD)
    geo = by_id(h["categories"], "geohazards")
    if not any(t["id"] == SOIL["id"] for t in geo["hazards"]):
        geo["hazards"].append(SOIL)
    dump(HAZARDS, h)
    p = load(POPULATIONS)
    have = {g["id"] for g in p["populations"]}
    p["populations"] += [g for g in GROUPS if g["id"] not in have]
    dump(POPULATIONS, p)
    return sum(len(c["hazards"]) for c in h["categories"]), len(p["populations"])


def main() -> None:
    n_haz, n_pop = add_vocabulary_terms()
    o = deepcopy(load(SRC))

    hz = by_id(o["types"], "Hazard")
    hz["definition"] = hz["definition"].replace("50 specific hazards", f"{n_haz} specific hazards")
    old = "A generic 'flooding' with no type stated is not folded into a flood type."
    new = (
        "A generic 'flooding' with no type stated is 'Flood (type not stated)': "
        "never fold it into a flood type the text does not name."
    )
    assert old in hz["extract_hint"] or new in hz["extract_hint"]
    hz["extract_hint"] = hz["extract_hint"].replace(old, new)

    v = by_id(o["vocabularies"], "hazards")
    v["description"] = v["description"].replace("52 specific hazards", f"{n_haz} specific hazards")
    v["terms_count"] = n_haz
    v = by_id(o["vocabularies"], "vulnerable-populations")
    v["description"] = v["description"].replace("21 socially-defined", f"{n_pop} socially-defined")
    if "note" in v:
        v["note"] = v["note"].replace("21 socially-defined", f"{n_pop} socially-defined")
    v["terms_count"] = n_pop

    md = o["metadata"]
    summary = (
        f"v1.7 (2026-11-09): six vocabulary terms (Decision 60): Flood (type not stated), Soil "
        f"erosion, and four vulnerable-population groups. {n_haz} hazards, {n_pop} population "
        f"groups. No type or relationship changes: {md['types_count']} types, "
        f"{md['relationships_count']} relationships."
    )
    md["change_history"] = [h for h in md.get("change_history", []) if not h.startswith("v1.7 ")]
    md["change_history"].insert(0, summary)

    o["version"] = VERSION
    o["updated"] = UPDATED
    o["update_note"] = (
        "v1.7 — one decision (Decision 60): six terms real plans needed. 'Flood (type not "
        "stated)', the parent of the four flood types, for a source that says only 'flooding'; "
        "'Soil erosion' (UNDRR GH0403); and four vulnerable-population groups. Vocabulary only."
    )
    o["version_notes"] = [n for n in o.get("version_notes", []) if n.get("version") != VERSION]
    o["version_notes"].insert(
        0,
        {
            "version": VERSION,
            "date": DATE,
            "summary": o["update_note"],
            "changes": [
                {"type": "added", "text": "hazards.json: flood_type_not_stated, used only when the passage names no flood type (Decision 60)"},
                {"type": "added", "text": "hazards.json: soil_erosion, UNDRR GH0403 (Decision 60)"},
                {"type": "added", "text": "vulnerable-populations.json: Pregnant and Postpartum People, Informal Workers, Households without Cooling, Transit-Dependent People (Decision 60)"},
                {"type": "changed", "text": "Hazard.extract_hint: a generic 'flooding' takes the new term and is never folded into a type the text does not name"},
            ],
        },
    )
    dump(DST, o)
    print(f"wrote {DST.name}: {n_haz} hazards, {n_pop} population groups")
    vs = load(ONT / "versions.json")
    if vs[0]["value"] != VERSION:
        vs.insert(0, {"path": f"../ontology/ontology-{VERSION}.jsonld", "label": VERSION, "value": VERSION})
        dump(ONT / "versions.json", vs)


if __name__ == "__main__":
    main()
