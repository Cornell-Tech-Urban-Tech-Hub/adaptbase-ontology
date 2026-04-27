# AdaptBase Ontology — CLAUDE.md

## What this is

This repo contains the formal ontology for **AdaptBase** (also referred to as "Resilience Scanner" in legacy files). The ontology models how cities adapt to climate change — entity types, relationships, and controlled vocabularies that structure an evidence base spanning hazards, solutions, financing, implementation, and outcomes.

The ontology is maintained as versioned JSON files in `ontology/` and displayed via a browser-based viewer at `viewer.html`.

**Current version:** v0.1.1 (2026-04-26)
**Publication target:** May 14, 2026 — GitHub Pages + expert review invitations

---

## Repo layout (what matters for the viewer)

```
viewer.html                   # Main public-facing app
styles/tokens.css             # Design tokens
styles/app.css                # App styles
scripts/
  ontology-adapter.js         # Loads/parses ontology JSON; version registry
  graph.js                    # D3 canvas force-directed graph
  inspector.js                # Side panel: node/edge detail + inline editing
  comments.js                 # CURRENTLY: hardcoded mock comment threads
  app.js                      # Bootstrap: wires UI, search, edit mode, save
ontology/
  ontology-v0.1.json          # Version history
  ontology-v0.1.1.json        # Latest
schemas/vocabularies/         # Controlled vocabularies (hazards, systems, etc.)
mining/                       # Pipeline for grounding vocab in corpus data
```

---

## Running the viewer locally

```bash
./start-viewer.sh             # starts python http.server + opens browser
# or manually:
python3 -m http.server 8765   # then open http://127.0.0.1:8765/viewer.html
```

No build step — plain HTML/CSS/JS with D3 loaded from unpkg CDN.

---

## Public publication plan

**Goal:** Publish this repo publicly so domain experts can view and comment on the ontology via GitHub Issues.

### What needs to happen before going public

1. **Comments backend — GitHub Issues integration** (not yet built)
   - `scripts/comments.js` currently contains hardcoded mock reviewer threads
   - Needs to be replaced with real GitHub Issues read/write via the GitHub REST API
   - Public viewers should be able to read comments without auth; submitting a comment requires GitHub OAuth or a token flow
   - Repo and issue labels should be designed: one issue per node/edge, or a discussion-thread model

2. **Edit mode — restrict or remove for public**
   - `viewer.html` has an "Edit" button that unlocks inline editing of ontology types and relationships
   - The save flow currently just downloads a JSON file locally (no server write) — so it's functionally harmless for read-only deployments
   - Decision pending: hide the Edit button entirely in the public build, or keep it with a note that changes won't persist without repo access
   - The simplest approach: add a `?edit=true` query param guard or a `EDIT_ENABLED` flag in `ontology-adapter.js` that defaults to `false`

3. **Branding / naming cleanup**
   - Several places still say "Resilience Scanner" (header, hero text, HTML title) — decide whether to update to "AdaptBase" before going public

4. **Sensitive files audit** — check nothing in `resources/` or `plans/` should stay private

### What's already safe for public
- All ontology JSON files in `ontology/`
- All vocabulary files in `schemas/vocabularies/`
- The viewer UI itself (no secrets, no server-side code)

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

## Out of scope for this repo

- Supabase database, extraction pipeline, deep researcher agent — those live in the main resilience-scanner monorepo
- Neo4j graph population — planned for post-May 15
- OWL/Protégé formalization — future work
