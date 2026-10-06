#!/usr/bin/env python3
"""Regenerate ontology/vocabularies/*.jsonld from their *.json sources.

Run with: uv run scripts/export/build_vocab_jsonld.py [--check]

Each .jsonld twin is the .json file plus the shared context and SKOS typing:
one skos:ConceptScheme per vocabulary (per block, for enums.json), one
skos:Concept per term, skos:topConceptOf on top-level terms, skos:broader +
skos:inScheme on nested ones. The JSON keys and values are untouched; the
JSON-LD keys are appended after them, which is what the viewer and editor
expect (they read the .json files and ignore the .jsonld ones).

--check exits 1 if any twin on disk differs from what would be generated.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VOCAB_DIR = REPO / "ontology" / "vocabularies"
CONTEXT = "../context.jsonld"
ABV = "abv:"

# vocabulary id -> (nesting path). Each level is the key holding the child
# array; term IRIs are built from the ids along the path when `path_iri` is
# true, and from the leaf id alone when it is false.
SCHEMES = {
    "hazards": {"levels": ["categories", "hazards"], "path_iri": False},
    "crf-goals": {"levels": ["dimensions", "goals"], "path_iri": False},
    "solution-categories": {
        "levels": ["categories", "subcategories"],
        "path_iri": True,
    },
    "urban-systems": {"levels": ["sectors", "subsectors", "systems"], "path_iri": True},
    "vulnerable-populations": {"levels": ["populations"], "path_iri": False},
    "jurisdiction-kind": {"levels": ["terms"], "path_iri": False},
    "solution-concepts": {"levels": ["concepts"], "path_iri": False},
}


def strip_ld(obj):
    """Return a copy without @-keys and skos:* keys (idempotent re-generation)."""
    if isinstance(obj, dict):
        return {
            k: strip_ld(v)
            for k, v in obj.items()
            if not k.startswith("@") and not k.startswith("skos:")
        }
    if isinstance(obj, list):
        return [strip_ld(x) for x in obj]
    return obj


def type_terms(terms, scheme_iri, levels, path_iri, parent_iri, prefix):
    rest = levels[1:]
    for t in terms:
        iri = f"{prefix}-{t['id']}" if path_iri else f"{ABV}{scheme_iri}-{t['id']}"
        t["@id"] = iri
        t["@type"] = "skos:Concept"
        if parent_iri is None:
            t["skos:topConceptOf"] = {"@id": f"{ABV}{scheme_iri}"}
        else:
            t["skos:broader"] = {"@id": parent_iri}
            t["skos:inScheme"] = {"@id": f"{ABV}{scheme_iri}"}
        if rest and rest[0] in t:
            type_terms(t[rest[0]], scheme_iri, rest, path_iri, iri, iri)


def build_scheme(vocab_id, data):
    spec = SCHEMES[vocab_id]
    out = {"@context": CONTEXT}
    out.update(data)
    root = spec["levels"][0]
    type_terms(
        out[root], vocab_id, spec["levels"], spec["path_iri"], None, f"{ABV}{vocab_id}"
    )
    out["@id"] = f"{ABV}{vocab_id}"
    out["@type"] = "skos:ConceptScheme"
    return out


def build_enums(data):
    out = {}
    for block, body in data.items():
        if not isinstance(body, dict) or "values" not in body:
            out[block] = body
            continue
        b = dict(body)
        for v in b["values"]:
            v["@id"] = f"{ABV}enums-{block}-{v['id']}"
            v["@type"] = "skos:Concept"
            v["skos:topConceptOf"] = {"@id": f"{ABV}enums-{block}"}
        b["@id"] = f"{ABV}enums-{block}"
        b["@type"] = "skos:ConceptScheme"
        out[block] = b
    # enums.json's blocks are dynamically named top-level keys, so the file
    # layers a @vocab fallback on the shared context (Decision 34).
    out["@context"] = [CONTEXT, {"@vocab": "https://ontology.adaptbase.us/vocab/"}]
    return out


def build_crosswalk(data):
    out = {"@context": CONTEXT}
    out.update(data)
    for m in out["mappings"]:
        if m.get("match_type") == "exact":
            m["skos:exactMatch"] = [
                {"@id": f"{ABV}hazards-{h}"} for h in m["hazard_ids"]
            ]
    return out


def build(vocab_id, data):
    if vocab_id == "enums":
        return build_enums(data)
    if vocab_id == "cdp-hazard-crosswalk":
        return build_crosswalk(data)
    if vocab_id in SCHEMES:
        return build_scheme(vocab_id, data)
    raise SystemExit(
        f"no JSON-LD rule for {vocab_id}.json; add one to build_vocab_jsonld.py"
    )


def main() -> int:
    check = "--check" in sys.argv
    stale = []
    for src in sorted(VOCAB_DIR.glob("*.json")):
        vocab_id = src.stem
        data = strip_ld(json.loads(src.read_text()))
        text = json.dumps(build(vocab_id, data), indent=2, ensure_ascii=False) + "\n"
        dst = src.with_suffix(".jsonld")
        if check:
            if not dst.exists() or dst.read_text() != text:
                stale.append(dst.name)
        else:
            dst.write_text(text)
            print(f"wrote {dst.relative_to(REPO)}")
    if stale:
        print("stale .jsonld twins: " + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
