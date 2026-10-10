#!/usr/bin/env python3
"""Build ontology/ontology-v1.3.jsonld from v1.2.

Run with: uv run scripts/migrations/v1_3_from_v1_2.py
Re-runnable: ontology-v1.3.jsonld and versions.json are rebuilt from v1.2.

v1.3 is one decision (Decision 55, Anthony 2026-10-10): a public body says
which government it belongs to — `Stakeholder BELONGS_TO Jurisdiction` — with
a name + jurisdiction identity rule for Stakeholders.
"""

import json
from copy import deepcopy
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ONT = REPO / "ontology"
SRC = ONT / "ontology-v1.2.jsonld"
DST = ONT / "ontology-v1.3.jsonld"
VERSION = "v1.3"
DATE = "2026-10-10"
UPDATED = "2026-10-10T12:00:00.000Z"


def load(p):
    return json.loads(p.read_text())


def dump(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    o = deepcopy(load(SRC))
    rels = o["relationships"]
    if not any(r["id"] == "BELONGS_TO" for r in rels):
        gov = next(i for i, r in enumerate(rels) if r["id"] == "GOVERNS" and r["target"] == "Jurisdiction")
        rels.insert(
            gov + 1,
            {
                "id": "BELONGS_TO",
                "label": "belongs to",
                "source": "Stakeholder",
                "target": "Jurisdiction",
                "definition": "The stakeholder is a body of this jurisdiction's government: a city department, office or council, a regional or county authority, a national ministry or agency.",
                "properties": [
                    {"id": "claim_ids", "type": "array<uuid>", "required": False},
                ],
                "cardinality": "many-to-one",
                "notes": "v1.3 (Decision 55). Public bodies only: NGOs, companies, universities, community groups and international organisations take no BELONGS_TO. The target's level matches stakeholder_type (municipal_government → city, regional_government → state/province/county/region, national_government → country). Distinct from GOVERNS (governing authority over a territory) and MEMBER_OF (membership of a body). Identity: two Stakeholders with the same normalised name or alternative_names entry and the same BELONGS_TO target are the same body.",
                "extract_hint": "Usually inferred, not extracted: the plan's city for a municipal body, that city's country for a national body. State it when the text names the government ('the Ministry of Health of Ghana', 'Miami-Dade County's Internal Services Department').",
                "@id": "ab:stakeholderBelongsToJurisdiction",
                "@type": "owl:ObjectProperty",
                "rdfs:domain": {"@id": "ab:Stakeholder"},
                "rdfs:range": {"@id": "ab:Jurisdiction"},
            },
        )
    st = next(t for t in o["types"] if t["id"] == "Stakeholder")
    note = " v1.3 (Decision 55): a public body points at the government it belongs to via BELONGS_TO → Jurisdiction; same name + same BELONGS_TO target is the same body."
    if "Decision 55" not in (st.get("notes") or ""):
        st["notes"] = (st.get("notes") or "") + note
    md = o.get("metadata") or {}
    if "relationships_count" in md:
        md["relationships_count"] = len(rels)
    o["version"] = VERSION
    o["updated"] = UPDATED
    o["update_note"] = (
        "v1.3 — one decision (Decision 55, 2026-10-10): a public body says which government "
        "it belongs to (Stakeholder BELONGS_TO Jurisdiction: city department → city, regional "
        "authority → region, national ministry → country), and Stakeholders gain a name + "
        "jurisdiction identity rule."
    )
    o["version_notes"] = [n for n in o.get("version_notes", []) if n.get("version") != VERSION]
    o["version_notes"].insert(
        0,
        {
            "version": VERSION,
            "date": DATE,
            "summary": o["update_note"],
            "changes": [
                {"type": "added", "text": "BELONGS_TO (Stakeholder → Jurisdiction), many-to-one, public bodies only (Decision 55)"},
                {"type": "changed", "text": "Stakeholder notes: identity by normalised name + BELONGS_TO target (Decision 55)"},
            ],
        },
    )
    dump(DST, o)
    print(f"wrote {DST.name}: {len(o['types'])} types, {len(rels)} edges")
    vs = load(ONT / "versions.json")
    if vs[0]["value"] != VERSION:
        vs.insert(0, {"path": f"../ontology/ontology-{VERSION}.jsonld", "label": VERSION, "value": VERSION})
        dump(ONT / "versions.json", vs)


if __name__ == "__main__":
    main()
