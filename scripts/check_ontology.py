#!/usr/bin/env python3
"""Structural checker for the ontology and its vocabularies (review P-10, v1.2).

Run with: uv run scripts/check_ontology.py [--version v1.2]

Pure Python, no network. Checks the newest version in ontology/versions.json
unless --version is given. Exits 1 on any ERROR; WARN lines are known legacy
debt that the check reports but does not fail on.

What it checks:
  1. versions.json[0] exists and its `version` field matches its label.
  2. Every relationship's source and target is a declared type; cardinality is
     one of the four allowed values; (id, source, target) is unique.
  3. metadata counts (types, relationships, vocabularies) match the file.
  4. Every type-level and property-level vocabulary_binding resolves to a
     vocabulary file, or for `enums` to a block in enums.json.
  5. A property bound to an enums block that also lists inline values lists
     exactly the block's values (the two copies cannot drift).
  6. Every vocabularies-manifest row resolves (a file or an enums block),
     its `bound_to` entries name a declared property, and `terms_count`
     matches when it is set.
  7. Vocabulary terms: ids unique within a vocabulary; hazards and urban systems
     each carry a definition (v1.2+); no hazard undrr_term or concept alias is
     claimed by two entries; deprecated terms carry deprecated_in and a
     replaced_by whose ids exist.
  8. Every solution concept's subcategory exists in solution-categories.
  9. The JSON-LD vocabulary twins are in sync (build_vocab_jsonld.py --check).
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ONT = REPO / "ontology"
VOC = ONT / "vocabularies"
CARDINALITIES = {"many-to-many", "many-to-one", "one-to-many", "one-to-one"}
ID_RE = re.compile(r"^[a-z0-9_]+$")

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def load(p: Path):
    return json.loads(p.read_text())


def vocab_file(vocab: str) -> Path:
    return VOC / f"{vocab}.json"


def version_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.lstrip("v").split("."))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", help="label in versions.json (default: newest)")
    args = ap.parse_args()

    # 1. versions
    versions = load(ONT / "versions.json")
    row = versions[0] if not args.version else next(
        (v for v in versions if v["value"] == args.version), None
    )
    if row is None:
        print(f"ERROR: {args.version} not in versions.json")
        return 1
    path = (REPO / "viewer" / row["path"]).resolve()
    if not path.exists():
        print(f"ERROR: versions.json points at missing {row['path']}")
        return 1
    o = load(path)
    label = row["value"]
    if o.get("version") != label:
        err(f"{path.name}: version field {o.get('version')!r} != versions.json label {label!r}")
    modern = version_tuple(label) >= (1, 2)

    types = {t["id"]: t for t in o["types"]}
    rels = o["relationships"]
    enums = load(VOC / "enums.json")
    blocks = {k: b for k, b in enums.items() if isinstance(b, dict) and "values" in b}

    # 2. relationships
    seen = Counter()
    for r in rels:
        key = (r["id"], r["source"], r["target"])
        seen[key] += 1
        for end in ("source", "target"):
            if r[end] not in types:
                err(f"{r['id']}: {end} {r[end]!r} is not a declared type")
        if r.get("cardinality") not in CARDINALITIES:
            err(f"{r['id']}({r['source']}->{r['target']}): cardinality {r.get('cardinality')!r} not in {sorted(CARDINALITIES)}")
    for key, n in seen.items():
        if n > 1:
            err(f"relationship {key} declared {n} times")

    # 3. metadata counts
    m = o.get("metadata", {})
    for k, actual in (
        ("types_count", len(types)),
        ("relationships_count", len(rels)),
        ("vocabularies_count", len(o.get("vocabularies", []))),
    ):
        if m.get(k) != actual:
            err(f"metadata.{k} = {m.get(k)} but the file has {actual}")

    # 4 + 5. bindings
    declared: dict[str, set[str]] = defaultdict(set)

    def check_binding(where: str, vb: dict, prop: dict | None) -> None:
        vocab = vb.get("vocab")
        if vocab == "enums":
            for field in [f.strip() for f in vb.get("field", "").split(",") if f.strip()]:
                if field not in blocks:
                    err(f"{where}: binding to enums.{field}, which does not exist")
                elif prop is not None and "values" in prop:
                    want = [v["id"] for v in blocks[field]["values"]]
                    if prop["values"] != want:
                        err(f"{where}: inline values {prop['values']} != enums.{field} {want}")
        elif not vocab_file(vocab).exists():
            err(f"{where}: binding to vocabulary {vocab!r}, which has no file")

    for t in o["types"]:
        for vb in t.get("vocabulary_bindings", []):
            check_binding(f"{t['id']} (type-level)", vb, None)
        for p in t["properties"]:
            declared[t["id"]].add(p["id"])
            if "vocabulary_binding" in p:
                check_binding(f"{t['id']}.{p['id']}", p["vocabulary_binding"], p)
    for r in rels:
        for p in r["properties"]:
            for k in (r["id"], f"{r['id']}({r['source']}->{r['target']})"):
                declared[k].add(p["id"])
            if "vocabulary_binding" in p:
                check_binding(f"{r['id']}({r['source']}->{r['target']}).{p['id']}", p["vocabulary_binding"], p)

    # 6. manifest
    def count_terms(vid: str) -> int | None:
        if vid.startswith("enums."):
            return len(blocks[vid[6:]]["values"]) if vid[6:] in blocks else None
        d = load(vocab_file(vid))
        if vid == "hazards":
            return sum(len(c["hazards"]) for c in d["categories"])
        if vid == "crf-goals":
            return sum(len(x.get("goals", [])) for x in d["dimensions"])
        for key in ("terms", "populations", "mappings", "concepts"):
            if key in d:
                return len(d[key])
        return None

    for v in o.get("vocabularies", []):
        vid = v["id"]
        if vid.startswith("enums."):
            if vid[6:] not in blocks:
                err(f"manifest row {vid}: no such enums block")
                continue
        elif not vocab_file(vid).exists():
            err(f"manifest row {vid}: no vocabulary file")
            continue
        for b in v.get("bound_to", []):
            owner, _, pid = b.rpartition(".")
            if vocab_file(owner).exists():
                continue  # a vocabulary bound to another vocabulary
            if pid not in declared.get(owner, set()):
                err(f"manifest row {vid}: bound_to {b!r} names no declared property")
        if v.get("terms_count") is not None:
            n = count_terms(vid)
            if n is not None and n != v["terms_count"]:
                err(f"manifest row {vid}: terms_count {v['terms_count']} but the vocabulary has {n}")

    # 7. vocabulary terms
    H = load(VOC / "hazards.json")
    hazards = [z for c in H["categories"] for z in c["hazards"]]
    ids = Counter(z["id"] for z in hazards)
    for i, n in ids.items():
        if n > 1:
            err(f"hazards.json: id {i} appears {n} times")
    owner_of = defaultdict(list)
    for z in hazards:
        for t in z.get("undrr_terms", []):
            owner_of[t.lower()].append(z["id"])
        if modern and not z.get("definition"):
            err(f"hazards.json: {z['id']} has no definition")
        if not ID_RE.match(z["id"].replace("rcc.", "")):
            warn(f"hazards.json: id {z['id']!r} is outside [a-z0-9_] (legacy; kept for id stability)")
    for t, owners in owner_of.items():
        if len(owners) > 1:
            err(f"hazards.json: term {t!r} is claimed by {owners}")

    U = load(VOC / "urban-systems.json")
    systems = {}
    sector_ids = set()
    for s in U["sectors"]:
        sector_ids.add(s["id"])
        for ss in s["subsectors"]:
            for y in ss["systems"]:
                if y["id"] in systems:
                    err(f"urban-systems.json: id {y['id']} appears twice")
                systems[y["id"]] = y
    for sid, y in systems.items():
        if modern and not y.get("definition"):
            err(f"urban-systems.json: {sid} has no definition")
        if y.get("status") == "deprecated":
            if not y.get("deprecated_in"):
                err(f"urban-systems.json: deprecated {sid} has no deprecated_in")
            if "replaced_by" not in y:
                err(f"urban-systems.json: deprecated {sid} has no replaced_by")
            for rb in y.get("replaced_by", []):
                if rb not in systems and rb not in sector_ids:
                    err(f"urban-systems.json: {sid} replaced_by {rb!r}, which does not exist")
                elif systems.get(rb, {}).get("status") == "deprecated":
                    err(f"urban-systems.json: {sid} replaced_by {rb!r}, which is itself deprecated")

    # 8. solution concepts → categories
    SC = load(VOC / "solution-concepts.json")
    CAT = load(VOC / "solution-categories.json")
    sub_to_cat = {
        s["id"]: c["id"] for c in CAT["categories"] for s in c.get("subcategories", [])
    }
    alias_owner = defaultdict(list)
    for c in SC["concepts"]:
        sub = c.get("subcategory_id")
        if sub and sub not in sub_to_cat:
            err(f"solution-concepts: {c['id']} subcategory {sub!r} not in solution-categories")
        elif sub and c.get("category_id") and sub_to_cat[sub] != c["category_id"]:
            err(f"solution-concepts: {c['id']} category {c['category_id']!r} but its subcategory belongs to {sub_to_cat[sub]!r}")
        for a in c.get("aliases", []):
            alias_owner[a.lower()].append(c["id"])
        if c.get("status") == "deprecated" and not c.get("replaced_by"):
            err(f"solution-concepts: deprecated {c['id']} has no replaced_by")
    for a, owners in alias_owner.items():
        if len(owners) > 1:
            err(f"solution-concepts: alias {a!r} is claimed by {owners}")
    bad_sub = [s for s in sub_to_cat if not ID_RE.match(s)]
    if bad_sub:
        warn(f"solution-categories: {len(bad_sub)} subcategory ids outside [a-z0-9_] (legacy; kept for core id stability)")

    # 9. JSON-LD twins
    res = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "export" / "build_vocab_jsonld.py"), "--check"],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        err("vocabulary .jsonld twins are out of date: run uv run scripts/export/build_vocab_jsonld.py\n"
            + (res.stdout + res.stderr).strip())

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(
        f"{path.name}: {len(types)} types, {len(rels)} relationships — "
        f"{len(errors)} error(s), {len(warnings)} warning(s)"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
