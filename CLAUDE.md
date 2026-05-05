# AdaptBase Ontology — CLAUDE.md

## Start here

Before planning any non-trivial change, read the **"Future ontology improvements"**
section at the top of `README.md`. If your work intersects an item there, advance that
item rather than creating parallel work.

## What this is

The formal ontology for **AdaptBase** — entity types, relationships, and controlled
vocabularies that model how cities adapt to climate change. Versioned JSON in
`ontology/`, displayed by a browser-based viewer in `viewer/`, deployed to
[ontology.adaptbase.us](https://ontology.adaptbase.us/) via GitHub Pages.

**Current version:** v0.1.1 (2026-05-04)

## Repo layout

```
adaptbase-ontology/
├── ontology/             # Ontology JSON, vocabularies, decisions log, framework crosswalk, reviews
│   ├── ontology-v0.1.json
│   ├── versions.json
│   ├── vocabularies/     # Controlled vocab: hazards, urban systems, solution categories, CRF goals, enums…
│   ├── decisions-log.md
│   ├── framework-crosswalk.md
│   └── review/
├── viewer/               # All web files — index.html, discussions.html, editor.html, scripts/, styles/, img/, content/
├── docs/                 # Planning docs, validation methodology, reference schema/prompts (vestigial)
├── scripts/              # Python: editor-server.py, validate_ontology.py, generate_miami_sample.py
├── research/             # ARCHIVE — corpus mining pipeline; not consulted day-to-day
├── index.html            # Root meta-redirect → viewer/ (so GH Pages root works)
├── start-viewer.sh       # http://127.0.0.1:8765/viewer/
└── start-editor.sh       # http://127.0.0.1:8766/viewer/editor.html
```

## Running locally

```bash
./start-viewer.sh   # plain static server (python3 -m http.server)
./start-editor.sh   # editor backend with /api/save-ontology and /api/save-vocab
```

No build step. D3 loads from a CDN. The viewer fetches `../ontology/...` relative to
`viewer/index.html`, so the local server must serve the **repo root**, not `viewer/`.

## Editing the ontology

- **Types and relationships** live in `ontology/ontology-v<version>.json`.
- **Controlled vocabularies** live in `ontology/vocabularies/*.json` and are loaded by
  both the viewer (read-only) and the editor (read/write via the editor server).
- The editor (`viewer/editor.html` + `scripts/editor-server.py`) writes new versions to
  disk and updates `ontology/versions.json`. Paths in `versions.json` are relative to
  `viewer/` (i.e. start with `../ontology/...`).

### Version management

**Always increment the ontology version before committing changes.** Follow semver:
- **Patch** (`v0.3` → `v0.3.1` → `v0.3.2`) — viewer/tooling changes
- **Minor** (`v0.3` → `v0.4`) — ontology schema changes

When bumping:
1. Copy `ontology/ontology-v<current>.json` → `ontology/ontology-v<new>.json`; update
   `version` and `update_note` inside.
2. Prepend the new entry to `ontology/versions.json` (path: `../ontology/ontology-v<new>.json`).
3. Update `**Current version:**` in this file and in `README.md`.

## Key design decisions

- **Solutions classified by identity, not function.** What a solution IS, not what it
  does; function is expressed via typed relationships (`MITIGATES`, `OPERATES_ON`,
  `USES_MECHANISM`).
- **Vocabularies are guidance, not hard constraints.** Validation is advisory, not
  blocking.
- **Claims as provenance.** Every extracted value traces to a claim UUID with a source.
- All non-obvious design calls go in `ontology/decisions-log.md`.

## `research/`

Archive of the corpus mining work that grounded several vocabularies in real data
(221 published solutions + 5,552 CDP city actions + 50 plans). Not part of the
viewer; not consulted unless the current task explicitly relates to corpus mining.
See `research/mining/README.md` if you need to dig in.

## Out of scope for this repo

- Supabase database, extraction pipeline, deep researcher agent — those live in the
  main adaptbase monorepo (sibling repos under `_dev/adaptbase/`).
- Neo4j graph population — planned for later.
- OWL/Protégé formalization — future work.
