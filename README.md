# AdaptBase Ontology

An open knowledge framework for **urban climate adaptation** — a structured ontology that
maps the entities, relationships, and vocabularies needed to organize, compare, and
analyze how cities respond to climate hazards.

**Live viewer:** [ontology.adaptbase.us](https://ontology.adaptbase.us/)
**Current version:** v0.4.1 (2026-05-14)

---

## Future ontology improvements

This is the running inbox for things to address in upcoming cycles. We populate it as
issues come up; items here are the next things we work on.

- _Add planned improvements here._

> **For Claude / future planning sessions:** Before starting any non-trivial change,
> read this section. If your work intersects an item, advance that item rather than
> creating parallel work.

---

## What this ontology covers

AdaptBase models the full chain of urban climate adaptation: the **hazards** cities face,
the **solutions** they deploy, the **plans** and **stakeholders** that authorize and
deliver them, the **finance** that pays for them, and the **outcomes** they produce. The
graph spans planning, engineering, financing, implementation, governance, and evaluation.

**Design principles**

- **Solutions are classified by what they ARE, not what they DO.** Function is expressed
  as typed relationships (`MITIGATES`, `OPERATES_ON`, `USES_MECHANISM`) rather than baked
  into the taxonomy.
- **Vocabularies are guidance, not rigid constraints.** Validation is advisory, so
  edge cases and new terms don't break extraction.
- **Provenance is first-class.** Every value can trace back to a claim with a source URL.

The ontology binds to several external frameworks where they exist (C40/Arup Climate
Hazard Typology, IPCC AR6 adaptation action types, City Resilience Framework 2024,
UNDRR Sendai Framework). See `ontology/framework-crosswalk.md` for the mappings.

---

## Using the viewer

Open [ontology.adaptbase.us](https://ontology.adaptbase.us/) and:

- **Explore the graph.** Click any node to inspect its definition, properties, and
  relationships. Click an edge to read about that relationship type.
- **Search.** Type in the search bar to jump to any entity or relationship.
- **Browse vocabularies.** Click the *Vocabularies* stat in the hero to see the
  controlled terms (hazards, urban systems, solution categories, CRF goals, etc.).
- **Read the changelog.** The *Changelog* button shows what's changed across versions.

---

## Leaving feedback

Reviews live in GitHub Issues so the discussion happens where the code is.

1. Open an issue at
   [github.com/Cornell-Tech-Urban-Tech-Hub/adaptbase-ontology/issues](https://github.com/Cornell-Tech-Urban-Tech-Hub/adaptbase-ontology/issues).
2. Apply the **`review`** label.
3. Apply an **`ontology:<entity-or-relationship>`** label so the comment surfaces in the
   right place — for example `ontology:Solution`, `ontology:Hazard`, or
   `ontology:Solution:MITIGATES:Hazard`.

The [Discussions page](https://ontology.adaptbase.us/viewer/discussions.html) on the
viewer aggregates all open `review`-labeled issues and groups them by entity and
relationship.

---

## What a knowledge graph built on this could do

The ontology is the schema. The interesting work begins once it's populated as a
**knowledge graph** — extract instances from reports, plans, and datasets and load them
as nodes and edges spanning thousands of solutions, hundreds of cities, and the actors,
policies, hazards, and funding mechanisms that connect them. At that scale, the graph
itself becomes analytic substrate.

A few directions this opens up:

- **Cross-city comparisons.** Standardize how different municipalities describe their
  solutions so you can surface patterns and transferable strategies.
- **Implementation trackers.** Model the connections between solutions, stakeholders,
  funding, and outcomes to understand what actually works.
- **GraphRAG for adaptation.** LLMs answering policy or research questions can ground
  their reasoning in a typed, traceable graph rather than fuzzy document retrieval.
- **Link prediction — "what's missing?"** Identify edges that *should* exist but don't.
  If Miami-Dade has implemented strategy X for flooding, and Houston has a similar
  hazard profile but no connection to strategy X, the model surfaces that as a
  recommendation. Goes beyond centrality (which finds what's important in the existing
  graph) to find what's *absent*.
- **Subgraph similarity — "find me analogues."** Given a local subgraph (e.g.,
  Miami-Dade's flooding adaptation ecosystem — its actors, policies, infrastructure,
  funding), find structurally similar subgraphs elsewhere. Not keyword matching but
  topological similarity: which cities have a similar configuration of institutional
  relationships, hazard exposures, and strategy portfolios?
- **Temporal graph learning — trajectory prediction.** With timestamps on adoption,
  policy change, and implementation, temporal GNNs can learn adaptation pathways:
  "cities that did A then B then C tend to do D next" — pattern-mining adaptation
  trajectories across the full graph.
- **Emergent solution clusters.** At thousands of nodes, clustering reveals groupings
  that don't map to existing taxonomies — e.g., solutions that span what traditional
  frameworks separate into "infrastructure" and "governance" but co-occur in practice.
  This generates new knowledge about how adaptation actually works vs. how it's
  categorized.
- **Transfer learning across hazard domains.** Solutions for coastal flooding may share
  graph topology (institutional arrangements, funding mechanisms, implementation
  timelines) with wildfire evacuation solutions, even when the content differs. That
  structural similarity is the kind of insight you can't get without graph ML.

---

## What's in this repo

```
adaptbase-ontology/
├── ontology/             # The ontology — JSON definitions + vocabularies + docs
│   ├── ontology-v0.1.json
│   ├── versions.json
│   ├── vocabularies/     # Hazards, urban systems, solution categories, CRF goals…
│   ├── decisions-log.md
│   ├── framework-crosswalk.md
│   └── review/           # Reviewer notes
├── viewer/               # Web viewer (ontology.adaptbase.us)
├── docs/                 # Project documentation, plans, schema reference
├── scripts/              # Dev tooling (Python: editor server, validators)
├── research/             # Archive: corpus mining work used to ground vocabularies
├── start-viewer.sh       # Run the viewer locally
└── start-editor.sh       # Run the local editor (for ontology authors)
```

### About `research/`

`research/` is an archive of the corpus mining work that grounded several vocabularies
in real data. It's not consulted day-to-day, but it's preserved because it documents
**how the vocabularies were validated**:

- `research/mining/` — the LLM extraction pipeline (Python). Pulled corpora from a
  Supabase database, ran clustering and gap analysis, generated taxonomy proposals for
  human review. Result: validated the 12-mechanism seed vocabulary, added two missing
  urban sectors, identified coverage patterns.
- `research/mining/corpus/` — parquet caches of 221 published solutions, 5,552 CDP city
  actions, and 50 resilience plans (100RC, CDP, C40).
- `research/extractions/miami/` — sample extractions used to test the schema end-to-end.
- `research/papers/` — reference papers (e.g., OntoKGen methodology, 2412.00608v3).
- `research/resources/` — external source documents (CDP data, City Resilience
  Framework PDF, etc.).

If we resume corpus-mining work, see `docs/plans/ONTOLOGY-FUTURE-EXPANSION-CORPUS-MINING.md`
for the next-cycle plan.

---

## Local development

```bash
./start-viewer.sh   # http://127.0.0.1:8765/viewer/
./start-editor.sh   # http://127.0.0.1:8766/viewer/editor.html  (requires Python)
```

The viewer is plain HTML/CSS/JS with D3 from a CDN — no build step. The editor adds a
small Python backend (`scripts/editor-server.py`) that writes ontology and vocabulary
files to disk.

For editing conventions and version-bumping rules, see `CLAUDE.md`.

---

## Acknowledgements

AdaptBase is developed by the **Urban Tech Hub at Cornell Tech** in collaboration with
**[Marceta PBC](https://marceta.ai/)**.
