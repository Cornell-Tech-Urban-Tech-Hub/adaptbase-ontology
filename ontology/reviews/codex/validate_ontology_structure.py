#!/usr/bin/env python3
import json
import re
import sys
from collections import defaultdict, Counter, deque

if len(sys.argv) < 2:
    print("Usage: validate_ontology_structure.py <ontology-json-path>")
    sys.exit(2)

path = sys.argv[1]
with open(path) as f:
    data = json.load(f)

types = data.get("types", [])
relationships = data.get("relationships", [])
vocabularies = data.get("vocabularies", [])

errors = []
warnings = []

pascal = re.compile(r"^[A-Z][A-Za-z0-9]*$")
relpat = re.compile(r"^[A-Z][A-Z0-9_]*$")
proppat = re.compile(r"^[a-z][a-z0-9_]*$")

type_ids = [t.get("id") for t in types]
type_set = set(type_ids)
vocab_ids = {v.get("id") for v in vocabularies}

# ID naming
for tid in type_ids:
    if not pascal.match(tid or ""):
        errors.append(f"Type ID not PascalCase: {tid}")

for rel in relationships:
    rid = rel.get("id")
    if not relpat.match(rid or ""):
        errors.append(f"Relationship ID not SCREAMING_SNAKE: {rid}")

for t in types:
    for p in t.get("properties", []):
        pid = p.get("id")
        if not proppat.match(pid or ""):
            errors.append(f"Property ID not snake_case: {t.get('id')}.{pid}")
        if "required" not in p:
            warnings.append(f"Missing explicit required flag: {t.get('id')}.{pid}")
        if "vocabulary" in p and p["vocabulary"] not in vocab_ids:
            errors.append(f"Unknown vocabulary on {t.get('id')}.{pid}: {p['vocabulary']}")

# Relationship endpoints and cardinality presence
valid_cardinality = {
    "one-to-one",
    "one-to-many",
    "many-to-one",
    "many-to-many",
}

adj = defaultdict(set)
out_degree = Counter()
in_degree = Counter()

for rel in relationships:
    src = rel.get("source")
    tgt = rel.get("target")
    rid = rel.get("id")

    if src not in type_set:
        errors.append(f"Relationship {rid} source type missing: {src}")
    if tgt not in type_set:
        errors.append(f"Relationship {rid} target type missing: {tgt}")

    if "cardinality" not in rel:
        warnings.append(f"Relationship missing cardinality: {rid}")
    elif rel["cardinality"] not in valid_cardinality:
        warnings.append(f"Relationship {rid} has nonstandard cardinality: {rel['cardinality']}")

    if src in type_set and tgt in type_set:
        adj[src].add(tgt)
        adj[tgt].add(src)
        out_degree[src] += 1
        in_degree[tgt] += 1

# Connectivity and diameter
if type_ids:
    start = type_ids[0]
    dist = {start: 0}
    q = deque([start])
    while q:
        node = q.popleft()
        for nb in adj[node]:
            if nb not in dist:
                dist[nb] = dist[node] + 1
                q.append(nb)

    if len(dist) != len(type_ids):
        missing = sorted(set(type_ids) - set(dist))
        errors.append(f"Type graph disconnected. Unreachable from {start}: {missing}")

    diameter = 0
    for s in type_ids:
        d = {s: 0}
        qq = deque([s])
        while qq:
            n = qq.popleft()
            for nb in adj[n]:
                if nb not in d:
                    d[nb] = d[n] + 1
                    qq.append(nb)
        if d:
            diameter = max(diameter, max(d.values()))

    print("Topology summary")
    print(f"- Types: {len(type_ids)}")
    print(f"- Relationships: {len(relationships)}")
    print(f"- Vocabularies: {len(vocabularies)}")
    print(f"- Diameter (undirected type graph): {diameter}")
    dead_ends = [t for t in type_ids if len(adj[t]) <= 1]
    print(f"- Dead-end/leaf types (degree<=1): {dead_ends}")

    print("\nDegree table")
    for t in type_ids:
        print(f"- {t}: out={out_degree[t]} in={in_degree[t]} undirected={len(adj[t])}")

# Reverse-pair analysis (informational)
pairs = defaultdict(list)
for rel in relationships:
    pairs[(rel.get("source"), rel.get("target"))].append(rel.get("id"))

missing_reverse = []
for (src, tgt), ids in pairs.items():
    if (tgt, src) not in pairs:
        missing_reverse.append((src, tgt, ids))

print("\nInverse-pair coverage")
print(f"- Directional pairs without reverse counterpart: {len(missing_reverse)}")
for src, tgt, ids in missing_reverse:
    print(f"  - {src} -> {tgt}: {', '.join(ids)}")

# Result summary
print("\nValidation results")
if errors:
    print(f"- Errors: {len(errors)}")
    for e in errors:
        print(f"  - {e}")
else:
    print("- Errors: 0")

if warnings:
    print(f"- Warnings: {len(warnings)}")
    for w in warnings:
        print(f"  - {w}")
else:
    print("- Warnings: 0")

sys.exit(1 if errors else 0)
