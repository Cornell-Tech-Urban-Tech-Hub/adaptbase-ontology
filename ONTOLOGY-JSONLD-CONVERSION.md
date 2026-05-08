# Plan: Migrate Ontology Source to JSON-LD (v1.0)

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

This is illustrative — the real context will need to handle all field names in the current JSON. The important thing: existing fields get semantic meaning without renaming them.

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
- In `ontologyToGraph()`: read `@id` as the canonical type identifier (fallback to `id` for backwards compat during transition)
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

### 3b. Handle the 5 duplicate relationship IDs

In the JSON-LD source, give each duplicate a distinct `@id`:

```json
{ "@id": "ab:actionDeployedIn", "id": "DEPLOYED_IN", "source": "Action", "target": "Location", ... }
{ "@id": "ab:capitalProjectDeployedIn", "id": "DEPLOYED_IN", "source": "CapitalProject", "target": "Location", ... }
```

Add `rdfs:subPropertyOf` linking both to `ab:deployedIn`. The viewer still keys on `id` field ("DEPLOYED_IN") so existing behavior is preserved.

### 3c. Handle RDF-star edge properties

For the 48 relationships with `claim_ids` and typed properties, the Turtle export uses RDF-star syntax:

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

## Open Questions (resolve before starting)

- **Vocabulary file extension:** Use `.jsonld` (clear signal) or keep `.json` with a `@context` inside (less disruption to existing tooling)?
- **Context location:** Inline in each file, or a shared external `context.jsonld` referenced via relative path?
- **Claim IRI pattern:** `https://ontology.adaptbase.us/claims/{uuid}` — confirm this is the right base even though claims live in Supabase?
