# Plan: Migrate Ontology Source to JSON-LD (v1.0)

## Status (2026-08-18)

Phases 1-3 (critical path) are **done**: `ontology/context.jsonld`,
`ontology/ontology-v1.0.jsonld`, `ontology/vocabularies/*.jsonld` (8 files),
and `scripts/export/generate_exports.py` + the CI step in
`.github/workflows/pages.yml` all exist and are verified (viewer smoke-tested
against v1.0, all three exported RDF files round-trip parse clean with
rdflib). This doc was written 2026-05-07 against the then-current schema
(v0.3, published the same day) and was never updated across the five
ontology versions that shipped afterward (v0.4 -> v0.7), so several factual
claims below were stale by the time the migration actually ran. Corrections
are inline, marked `[2026-08-18]`. Phase 2b (editor rebuild) and Phase 4
(docs/discovery polish) remain undone, per plan.

## Why

The ontology is currently a proprietary JSON structure that only our viewer can consume. By making the source format JSON-LD, the ontology *is* a standard linked-data artifact — no sync layer, no dual-source maintenance, and anyone with RDF tooling can consume it directly. OWL/Turtle and SKOS exports become one-way CI-generated artifacts from a standard source.

## Key Decisions (already made)

- **Namespace:** `https://ontology.adaptbase.us/ont/` (prefix `ab:`), version-stable IRIs
- **Vocabularies:** `https://ontology.adaptbase.us/vocab/` (prefix `abv:`)
- **Reification:** RDF-star for edge properties (claim_ids, is_primary, etc.)
- **License:** CC-BY 4.0
- **Distribution:** OWL/Turtle/SKOS generated in CI, published via GitHub Pages

---

## Phase 1: JSON-LD Context & Source Migration

### 1a. Write the `@context`

Create `ontology/context.jsonld` — a standalone JSON-LD 1.1 context that maps existing keys to IRIs:

```jsonld
{
  "@context": {
    "@version": 1.1,
    "ab": "https://ontology.adaptbase.us/ont/",
    "abv": "https://ontology.adaptbase.us/vocab/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "dcterms": "http://purl.org/dc/terms/",
    "prov": "http://www.w3.org/ns/prov#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",

    "id": "@id",
    "types": { "@id": "ab:definesClass", "@container": "@set" },
    "relationships": { "@id": "ab:definesProperty", "@container": "@set" },
    "label": "rdfs:label",
    "definition": "rdfs:comment",
    "source": { "@id": "rdfs:domain", "@type": "@id" },
    "target": { "@id": "rdfs:range", "@type": "@id" },
    "version": "dcterms:hasVersion",
    "updated": { "@id": "dcterms:modified", "@type": "xsd:dateTime" },
    "domain": "dcterms:subject",
    "properties": { "@id": "ab:hasProperty", "@container": "@set" },
    "vocabulary": { "@id": "ab:boundToVocabulary" },
    "cardinality": "ab:cardinality",
    "claim_ids": { "@id": "prov:wasDerivedFrom", "@type": "@id", "@container": "@set" }
  }
}
```

This was illustrative — the real context, `ontology/context.jsonld`, is the
ground truth now; **[2026-08-18]** it covers every field actually in use
(the illustrative version above missed `notes`, `extract_hint`,
`vocabulary_bindings`, `update_note`, `version_notes`, `domain_label`, and
more), plus the vocab-file container fields (`categories`, `hazards`,
`dimensions`, `sectors`, etc.) that turned out to need their own terms too —
without them, rdflib silently drops those keys during JSON-LD expansion
rather than erroring, which is easy to miss (each vocab file round-tripped
through with only 0-1 triples until this was caught). One correction to the
approach itself: `source`/`target` (and `vocabulary`) can't use
`"@type": "@id"` the way this draft assumed, because their values are plain
strings like `"Solution"` (kept that way so the existing viewer keeps
reading them unchanged) — under `@type: "@id"` those resolve as *relative to
the document's base URI*, not through the `ab:`/`abv:` prefixes, producing
garbage IRIs like `file:///.../ontology/Solution`. Fixed by emitting
explicit, already-resolved `rdfs:domain`/`rdfs:range`/`ab:boundToVocabulary`
keys directly in the migration script instead of relying on context-driven
coercion for those three fields. The important thing from the original plan
still holds: existing fields keep their literal values and gain semantic
meaning without being renamed.

### 1b. Convert ontology-v1.0.json to JSON-LD

The new source file (`ontology/ontology-v1.0.jsonld`) is structurally identical to the current JSON but adds:

1. `"@context": "./context.jsonld"` at the top
2. `"@id": "https://ontology.adaptbase.us/ont/"` as the ontology IRI
3. `"@type": "owl:Ontology"` on the root document
4. `"@id": "ab:Solution"` and `"@type": "owl:Class"` on each entity type
5. `"@id": "ab:mitigates"` and `"@type": "owl:ObjectProperty"` on each relationship

The existing keys (`id`, `label`, `definition`, `properties`, etc.) remain unchanged — the `@context` gives them RDF semantics.

### 1c. Convert vocabulary files to JSON-LD

Each vocabulary file (`hazards.json`, `solution-categories.json`, etc.) gets a `@context` reference and SKOS typing:

- Root object → `skos:ConceptScheme`
- Categories/top-level items → `skos:Concept` with `skos:topConceptOf`
- Child items → `skos:Concept` with `skos:broader`
- Existing `name` → mapped to `skos:prefLabel` via context
- Crosswalk fields (`undrr_terms[]`) → mapped to `skos:altLabel` via context

---

## Phase 2: Update Viewer & Editor

### 2a. Viewer (minimal changes)

The viewer's `ontology-adapter.js` already transforms the raw JSON into a graph structure. JSON-LD keys it doesn't recognize (`@context`, `@id`, `@type`) are simply ignored by the existing transform. The required changes:

- Update `versions.json` paths to point to `.jsonld` files
- **[2026-08-18] Correction:** no `ontologyToGraph()` change was needed.
  Confirmed by reading the actual code: it builds nodes/edges from
  `type.id` / `rel.source` / `rel.target` / `rel.id` directly and never
  touches `@id` at all — there's no "canonical identifier" fallback to add.
  Verified end-to-end: v1.0.jsonld loads with the same 21 nodes / 60 edges
  as v0.8.json, zero console errors, zero code changes.
- Vocabulary loader: unchanged (JSON-LD is still JSON — `categories[].hazards[]` still works)

### 2b. Editor

Rebuild the editor's save logic to:
- Preserve `@context`, `@id`, `@type` fields when writing
- Update `versions.json` with `.jsonld` extension
- The editor-server.py `/api/save-ontology` endpoint needs no structural change (it writes JSON; JSON-LD is JSON)

---

## Phase 3: OWL/Turtle & SKOS Export (CI-generated)

### 3a. Export script (`scripts/export/generate_exports.py`)

A single Python script that:
1. Loads the `.jsonld` source files
2. Parses them with `rdflib` (which natively understands JSON-LD)
3. Serializes to Turtle (`.ttl`) and RDF/XML (`.owl`)
4. Generates a combined SKOS file from all vocabulary JSON-LD files

Because the source is already JSON-LD, rdflib can parse it directly — no custom mapping layer needed. The script is ~100 lines, not a multi-module system.

### 3b. Handle the duplicate relationship IDs

**[2026-08-18]** This was 5 when the doc was written (2026-05-07, same day
v0.3 shipped with exactly 5: `DEPLOYED_IN`, `IMPLEMENTED_BY`, `PRODUCES`,
`SPECIFIES`, `USES_INSTRUMENT`). It grew across the versions this doc wasn't
updated for — 7 as of v0.5.0 (+`GOVERNS`, `WITHIN`), **10** as of v0.6
(+`ADDRESSES` and `TARGETS`, each with 3 rows, +`FUNDED_BY`) — and has held
at 10 since. v0.8 didn't change the count (the seven re-anchored edges shift
*which* source duplicates an existing id, not whether one does).

Implemented naming rule, applied uniformly to all 48 predicate ids (not just
the 10 that need it today — see rationale below): every predicate gets an
umbrella `@id`, `ab:` + camelCase(predicate id) — e.g. `ab:deployedIn`,
`ab:usesInstrument` — as the `owl:ObjectProperty` carrying `rdfs:label` /
`rdfs:comment` / the extract hint. For the 10 duplicated predicates, each
`(source, target)` row *additionally* gets a specific `@id`,
`ab:{source}{Predicate}{Target}` in camelCase — e.g.
`ab:actionDeployedInJurisdiction`, `ab:capitalProjectDeployedInJurisdiction`
— declared `rdfs:subPropertyOf` the umbrella, with that row's own
`rdfs:domain`/`rdfs:range`. For the other 38 single-row predicates the
umbrella IRI *is* the specific IRI; no second one is minted. Minting the
umbrella for all 48 up front means a currently-unique predicate that later
gains a second row never needs its existing IRI renamed — it just gains a
new child IRI under the umbrella that's already there. The viewer still
keys on `id` + `source` + `target` (unchanged literal fields), so existing
behavior is fully preserved — confirmed by smoke test, zero code changes.

### 3c. Handle RDF-star edge properties

**[2026-08-18] Correction:** 48 is the distinct predicate-*id* count, not
the count of relationship *rows* carrying `claim_ids` — that's 57 of the 60
rows (three have none: `SHAPES`, `REDUCES_EXPOSURE`, `INFORMS` — worth a
follow-up on whether that's intentional). More fundamentally, RDF-star
doesn't apply to `scripts/export/generate_exports.py`'s output at all: this
repo's JSON-LD is the ontology *schema* (TBox — class/property
definitions), not asserted instance edges, so there's nothing to reify here.
`claim_ids` already resolves to `prov:wasDerivedFrom` via the context. The
syntax below becomes relevant only if/when the *instance* knowledge graph
(adaptbase-core, Supabase-backed, out of this repo's scope) is exported with
its actual per-edge claim provenance:

For the relationships with `claim_ids` and typed properties, the Turtle export would use RDF-star syntax:

```turtle
<<:solution1 ab:mitigates :hazard1>> ab:isPrimary true ;
    prov:wasDerivedFrom <https://ontology.adaptbase.us/claims/uuid-here> .
```

rdflib 7+ serializes this natively when given quoted triples in the graph.

### 3d. CI pipeline

GitHub Action on push to `main`:
```yaml
- uv run python scripts/export/generate_exports.py
- Deploy exports/ to gh-pages branch (or publish as release artifact)
```

No manual regeneration. No stale-check. The exports are ephemeral build artifacts, not committed source.

---

## Phase 4: Documentation & Discovery

- `exports/README.md` — brief consumer guide (what each file is, how to use it)
- Add content negotiation via GitHub Pages: serve `.ttl` with `text/turtle` MIME type (via `_headers` file or redirect rules)
- Link from the viewer UI: "Download as OWL" / "Download as SKOS" buttons
- Update the repo README with a "Standard Formats" section

---

## What Changes vs. What Stays

| Aspect | Before (v0.3) | After (v1.0) |
|--------|---------------|--------------|
| Source format | Custom JSON | JSON-LD (still JSON, with `@context`) |
| Source files | `ontology-v0.3.json` | `ontology-v1.0.jsonld` |
| Vocab files | `*.json` | `*.jsonld` (same structure + context) |
| Viewer consumption | Works | Works (JSON-LD is JSON) |
| Editor | Works | Minor update to preserve `@` keys |
| OWL/Turtle | Does not exist | CI-generated from source |
| SKOS | Does not exist | CI-generated from source |
| Sync burden | N/A | Zero (CI generates on push) |
| External tool compatibility | None | Full (rdflib, Protégé, SPARQL, etc.) |

---

## Sequencing

1. **Write the `@context`** — the intellectual core; maps every field to an IRI
2. **Convert source files** — add `@context` reference + `@id`/`@type` annotations
3. **Verify viewer still works** — should be trivial since JSON-LD is JSON
4. **Write export script** — short, because rdflib parses JSON-LD natively
5. **Set up CI** — GitHub Action to generate and publish exports
6. **Update editor** — preserve `@` keys on save
7. **Documentation** — consumer guide, viewer download links

Phases 1–3 are the critical path. Phase 4–7 can follow incrementally.

---

## Open Questions

- **Vocabulary file extension:** ~~Use `.jsonld`...~~ **[2026-08-18] Resolved: `.jsonld`.** Done — all 8 files converted.
- **Context location:** ~~Inline...~~ **[2026-08-18] Resolved: shared external `ontology/context.jsonld`,** referenced via relative path (`./context.jsonld` from the ontology source, `../context.jsonld` from `vocabularies/*.jsonld`). `enums.jsonld` additionally layers a file-local `@vocab` fallback on top of the shared context (see §1c note) — its 20 blocks are dynamically-named top-level keys, not an array under one field name like every other vocab file, so a static context term list can't enumerate them.
- **Claim IRI pattern:** `https://ontology.adaptbase.us/claims/{uuid}` — **still open.** `claim_ids` resolves to `prov:wasDerivedFrom` in the context, but this ontology repo's JSON-LD is schema-only (TBox) — there's no instance data here to attach a claim IRI to. This matters when the *instance* knowledge graph (adaptbase-core, Supabase-backed) is exported with real per-edge claim provenance, which is out of this repo's scope; confirm the base URL with whoever owns that schema before treating it as load-bearing there.
