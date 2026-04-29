# AdaptBase Ontology — CLAUDE.md

## What this is

This repo contains the formal ontology for **AdaptBase** (also referred to as "Resilience Scanner" in legacy files). The ontology models how cities adapt to climate change — entity types, relationships, and controlled vocabularies that structure an evidence base spanning hazards, solutions, financing, implementation, and outcomes.

The ontology is maintained as versioned JSON files in `ontology/` and displayed via a browser-based viewer at `index.html`.

**Current version:** v0.3.1 (2026-04-29)

---

## Repo layout (what matters for the viewer)

```
index.html                    # Main public-facing app
styles/tokens.css             # Design tokens
styles/app.css                # App styles
scripts/
  ontology-adapter.js         # Loads/parses ontology JSON; version registry
  graph.js                    # D3 canvas force-directed graph
  inspector.js                # Side panel: node/edge detail + inline editing
  comments.js                 # Hardcoded mock comment threads
  app.js                      # Bootstrap: wires UI, search, edit mode, save
ontology/
  ontology-v0.3.1.json        # Current version
  ontology-v0.2.json          # Version history
schemas/vocabularies/         # Controlled vocabularies (hazards, systems, etc.)
mining/                       # Pipeline for grounding vocab in corpus data
```

---

## Running the viewer locally

```bash
./start-viewer.sh             # starts python http.server + opens browser
# or manually:
python3 -m http.server 8765   # then open http://127.0.0.1:8765/
```

No build step — plain HTML/CSS/JS with D3 loaded from unpkg CDN.

---

## Ontology structure

The ontology JSON has three top-level keys:

```json
{
  "types": [...],          // Entity types (nodes): id, label, definition, properties, vocabulary_bindings
  "relationships": [...],  // Edge types: id, label, source, target, definition, properties
  "vocabularies": [...]    // Controlled vocabularies: label, description, type (external|internal)
}
```

Version metadata lives at the top level: `version`, `updated`, `domain`.

---

## Mining pipeline (Python)

The `mining/` directory contains an automated pipeline for grounding ontology vocabularies in real corpus data (221 published solutions + 5,552 CDP city actions). It pulls from Supabase and uses LLM calls via a LiteLLM proxy. See `mining/README.md` for usage.

This pipeline is a dev/research tool — it does not affect the viewer.

---

## Key design decisions

- **Solutions classified by identity, not function** — what a solution IS, not what it does; function expressed as typed relationships (MITIGATES, OPERATES_ON, etc.)
- **Vocabularies as guidance, not hard constraints** — advisory validation, not blocking
- **Claims as provenance** — every extraction value traces to a claim UUID in Supabase
- All non-obvious design calls are logged in `decisions-log.md`

---

## Version management

**Always increment the ontology version before committing changes.** Follow semver patch increments (e.g., v0.3 → v0.3.1 → v0.3.2) for viewer/tooling changes; minor increments (v0.3 → v0.4) for ontology schema changes.

When bumping the version:
1. Copy `ontology/ontology-v<current>.json` → `ontology/ontology-v<new>.json` and update `"version"` and `"update_note"` inside it
2. Prepend the new entry to `ontology/versions.json`
3. Update `**Current version:**` in this file and the filename in the repo layout section above

---

## Out of scope for this repo

- Supabase database, extraction pipeline, deep researcher agent — those live in the main resilience-scanner monorepo
- Neo4j graph population — planned for post-May 15
- OWL/Protégé formalization — future work
