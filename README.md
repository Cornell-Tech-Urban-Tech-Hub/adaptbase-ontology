# Resilience Ontology Development

## Overview

Formalizing the Resilience Scanner extraction schema (v1.2) into an OWL ontology for the knowledge graph. This work builds on an existing, working extraction system with ~200 published research cases and thousands of CDP-imported actions.

## What Already Exists

### Working Extraction System
- **Extraction Schema v1.2**: JSON Schema defining 7 ontology dimensions (identity, hazards, urban_systems, mechanisms, implementation, outcomes, context)
- **Controlled Vocabularies**: Hazards, solution categories, urban systems, CRF goals, IPCC action types, resilience attributes
- **Claims Architecture**: First-class claims in Supabase with extraction_schema JSONB fields referencing claim UUIDs
- **Published Research**: ~200 cases in `research_versions` table with populated extraction schemas
- **CDP Database**: 11,842 city-reported actions imported as solutions

### Files and Directories
- `schemas/extraction-schema-v1.json` - JSON Schema for solutions.extraction_schema (JSONB)
- `schemas/vocabularies/` - Controlled vocabulary files (see [Vocabulary Integration](schemas/vocabularies/README.md))
- `schemas/prompts/` - Research agent and synthesis prompts
- `schemas/validation/` - Schema validation reports
- `resources/` - Source documents (CDP data, CRF framework, student ontology)

**Legacy documentation**: See `README-legacy-extraction-docs.md` for extraction schema architecture details.

---

## Ontology Development Plan

### Goals

1. **Formalize extraction schema as OWL ontology** - Transform the working v1.2 schema into formal types, relationships, and constraints
2. **Validate against populated data** - Ensure ontology accurately represents the ~200 cases and CDP actions
3. **Bind to external vocabularies** - Map to IPCC AR6, C40/Arup, CityGML, UNDRR, CRF 2024
4. **Enable GraphRAG queries** - Support multi-hop Cypher queries in Neo4j (NL → Cypher → result set → synthesis)
5. **Document design decisions** - Log every non-obvious call with rationale

### Approach

This is **ontology induction from an existing schema**, not building from scratch:

1. **Analyze populated extraction schemas** - Query Supabase to see what fields are actually used across cases
2. **Identify node types** - Extract entity types from the 7 dimensions
3. **Identify relationships** - Infer edge types from cross-dimension references and claim relationships
4. **Formalize as OWL** - Use Protégé to build v0.1 ontology with types, relationships, properties
5. **Validate** - Check ontology against held-out cases
6. **Iterate** - Refine based on gaps, edge cases, and alignment with external vocabularies

---

## Ontology Design Principles

### Four-Dimension Architecture

The ontology organizes around **four core dimensions** (separate node types, not flat taxonomy):

| Dimension | What it classifies | Controlled Vocabulary Source |
|---|---|---|
| **Hazards / Stresses** | Climate-driven threats | C40/Arup Climate Hazard Typology (30+ hazards, 13 categories) |
| **Solutions** | The intervention itself | Solution taxonomy (7 categories, ~100 subcategories) |
| **Urban Systems** | What part of the city it operates on | Custom hierarchical taxonomy (7 sectors, 50+ systems) |
| **Mechanisms** | How it works | Free text now, cluster later (seed: absorb, redirect, harden, monitor, govern) |

**Key Decision**: Solution hierarchy organized by **what solutions ARE** (identity), not what they do. What they do is expressed as typed relationships to hazard and mechanism nodes.

### External Frameworks to Integrate

Already referenced in extraction schema; need formal ontology bindings:

- **IPCC AR6 adaptation action typology** - structural/physical, social, institutional, ecosystem-based (crosscutting attribute on solution nodes)
- **C40/Arup Climate Hazard Typology** - 13 categories, 30+ specific hazards → `hazards.json`
- **City Resilience Framework 2024** - 22 goals across 4 dimensions → `crf-goals.json`
- **CDP project finance fields** - financing models, funding sources, instruments
- **UNDRR Sendai Framework** - hazard/exposure/vulnerability/risk definitions
- **Student ontology governance relationships** - MANDATES, FACILITATED_BY, HINDERED_BY, etc.

### Claims as Provenance

Every structured value in the extraction schema references claim UUIDs from the `claims` table. The ontology must preserve this:

```
Solution → extraction_schema dimension → claim UUID → claims table → source document
```

Graph queries can traverse to source evidence: `MATCH (s:Solution)-[:MITIGATES]->(h:Hazard) RETURN s, h, claims`

---

## Repository Structure

```
packages/ontology/
├── README.md                              # This file
├── README-legacy-extraction-docs.md       # Legacy extraction schema docs
├── schemas/
│   ├── extraction-schema-v1.json          # JSON Schema (source of truth for dimensions)
│   ├── vocabularies/
│   │   ├── README.md                      # Vocabulary integration strategy
│   │   ├── solution-categories.json       # From solution_taxonomy table
│   │   ├── hazards.json                   # C40/Arup → hazards table
│   │   ├── crf-goals.json                 # City Resilience Framework 2024
│   │   ├── urban-systems.json             # Hierarchical taxonomy (7 sectors, 50+ systems)
│   │   ├── resilience-attributes.json     # ARUP City Resilience Index attributes
│   │   └── enums.json                     # Multi-source enums (IPCC, CDP, custom)
│   ├── prompts/
│   │   ├── research-agent-prompt.md       # Deep researcher instructions
│   │   └── synthesis-prompt.md            # Schema → narrative report
│   └── validation/
│       ├── schema-validation-published-solutions.md
│       └── schema-validation-cdp-actions.md
├── resources/
│   ├── CDP_cities_adaptation_fact_table/  # 11,842 rows
│   ├── city-resilience-framework-2024v2.pdf
│   └── ruowen-climate-adaptation.py       # Student's schema (governance vocab source)
├── papers/
│   └── 2412.00608v3.pdf                   # OntoKGen methodology reference
├── plans/
│   ├── ontology-build-brief.md            # Original brief (pre-schema discovery)
│   └── firewall_project_context.md        # Project context
├── ontology/                              # Formal ontology development (NEW)
│   ├── draft-v0.json                      # Machine-readable ontology
│   ├── draft-v0.md                        # Human-readable docs
│   ├── types.json                         # Node types
│   ├── relationships.json                 # Edge types
│   ├── vocabularies.json                  # Vocabulary bindings
│   └── decisions-log.md                   # Design decisions log
├── alignment/                             # Mappings to external ontologies (NEW)
│   ├── student-ontology-map.md
│   ├── undrr-hazard-map.json
│   ├── ipcc-ar6-map.json
│   └── crf-2024-map.json
├── extractions/                           # Case-level extractions (if re-extracting)
│   └── v1/
├── holdout/                               # Stress testing (NEW)
│   └── extraction-results/
└── cases/                                 # Sample cases (NEW)
    └── raw/
```

**Note**: Extraction schema and vocabularies already exist in `schemas/`. Ontology development adds formalization in `ontology/`, alignment in `alignment/`, and validation in `holdout/`.

---

## Ontology Viewer

An interactive web-based viewer/editor for the ontology is available at `viewer.html`.

### How to Use

**Option 1: VSCode Task (Recommended)**
1. Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`)
2. Run Tasks: Run Task
3. Select "Ontology Viewer"
4. Open browser to http://127.0.0.1:8765/viewer.html

**Option 2: Shell Script**
```bash
cd packages/ontology
./start-viewer.sh
```
Opens browser automatically to the viewer.

**Option 3: VSCode Live Server Extension**
1. Install "Live Server" extension
2. Right-click `viewer.html` → "Open with Live Server"

**Option 4: Manual**
```bash
cd packages/ontology
python3 -m http.server 8765
# Then open http://127.0.0.1:8765/viewer.html
```

### Viewer Features

- Load ontology JSON files (drag & drop or file picker)
- Interactive graph visualization (vis.js)
- Click nodes/edges to inspect properties
- Edit types and relationships inline
- Export modified ontology as JSON
- Filter by domain (planning vs. solutions)
- Sample ontology included (click "Load Sample")

### Current Status

- Viewer expects `ontology/draft-v0.json` (will be created in next step)
- Can use "Load Sample" to see demo ontology
- After relationship extraction, can load actual ontology

---

## Development Status

**Current Version**: v0.1.1 (2026-04-26)

**Completed**:
1. ✅ v0.1.0: Base ontology with 15 entity types, 25 relationships, vocabulary bindings
2. ✅ Phase D: Distribution gaps analysis (added 2 urban sectors)
3. ✅ Phase A: Mechanism clustering (validated 12-mechanism seed taxonomy)
4. ✅ **Phase P: Plan entity expansion (v0.1.1)**
   - 10 properties: plan_title*, plan_type*, adoption_year*, planning_horizon_years, total_actions, total_budget_mentioned, monitoring_approach, plan_uri, document_url, plan_status (*required)
   - 10 relationships: AUTHORED_BY, IMPLEMENTED_BY, ALIGNS_WITH, SUPERSEDES, SUPERSEDED_BY, COVERS_LOCATION, CONTAINS_ACTION, ADDRESSES_HAZARD, TARGETS_URBAN_SYSTEM, REFERENCES
   - Source: 50 resilience plans (100RC, CDP, C40) parsed and analyzed via LLM

**Next Steps**:
1. V3 pipeline integration: Generate extraction schema from ontology-v0.1.1.json
2. Expand Framework entity (similar to Plan corpus mining approach)
3. Map additional external vocabularies (CityGML, UNDRR hazard taxonomy)
4. Validate ontology against held-out cases

---

## Corpus Mining Pipeline

An automated pipeline for grounding ontology vocabularies in real corpus data. Extracts patterns from published solutions and CDP actions, generates LLM proposals for vocabulary gaps, and applies human-reviewed decisions to canonical vocabulary files.

### Pipeline Overview

```
Depth corpus (221 solutions)  →  LLM extraction  →  Clustering  →  Proposals
Breadth corpus (5,552 CDP)    →  LLM categorize  →  Gap analysis →     ↓
                                                                    Review UI
                                                                        ↓
                                                                   Apply to vocab
```

### Running the Pipeline

See `mining/README.md` for detailed usage. Quick start:

```bash
# 1. Pull corpora from Supabase (idempotent, cached locally)
uv run packages/ontology/mining/scripts/pull_depth_corpus.py --stats
uv run packages/ontology/mining/scripts/pull_breadth_corpus.py --stats

# 2. Phase D: Distribution & coverage analysis
uv run packages/ontology/mining/scripts/phase_d_distribution.py --all

# 3. Phase A: Mechanism clustering (optional)
uv run packages/ontology/mining/scripts/phase_a_extract_mechanisms.py
uv run packages/ontology/mining/scripts/phase_a_cluster_mechanisms.py
uv run packages/ontology/mining/scripts/phase_a_propose_taxonomy.py

# 4. Review proposals via web UI
uv run packages/ontology/mining/scripts/review_server.py  # → http://localhost:8769

# 5. Apply approved decisions to vocabularies
uv run packages/ontology/mining/scripts/apply_decisions.py --phase distribution
```

### Results

**Phase D (Distribution Gaps)**:
- Analyzed 221 published solutions vs. 5,552 CDP actions across 4 dimensions
- Found 3 vocabulary gaps → added 2 urban sectors (agriculture & food systems, emergency & disaster management)
- Identified systematic coverage patterns (e.g., slow-onset environmental stresses +10.6pp in breadth)

**Phase A (Mechanism Clustering)**:
- Extracted 2,862 mechanism candidates from research narratives and claims
- Clustered into 2,067 semantic groups
- Generated 49 taxonomy proposals
- **Result**: Existing 12-mechanism seed vocabulary validated as comprehensive (0 additions needed)
- Confirms Sprint 4 expansion with tech-native types (sense_and_detect, forecast_and_model, automate_and_control, inform_and_alert) successfully anticipated corpus patterns

### Pipeline Components

- **Corpus extraction** (`pull_*.py`) — Pulls published solutions + CDP actions to local parquet cache
- **LLM categorization** (`phase_d_distribution.py`) — Concurrent Haiku categorization with checkpoint resumption
- **Clustering** (`phase_a_cluster_mechanisms.py`) — Embedding-based hierarchical clustering (scikit-learn)
- **Proposal generation** (`phase_a_propose_taxonomy.py`) — Sonnet generates canonical names, definitions, external vocab crosswalks
- **Review server** (`review_server.py`) — FastAPI + interactive HTML viewer with keyboard controls
- **Decision applier** (`apply_decisions.py`) — Routes approved decisions to vocabulary files, logs rejections

All decisions logged in `ontology/decisions-log.md` with rationales for traceability.

---

## Integration with Broader System

### Data Flow

```
Crawler discovers solutions → solutions table (draft)
CDP importer loads actions → solutions table (draft)
                                    ↓
Deep researcher picks up drafts → extracts claims → claims table
                                                 → populates extraction_schema JSONB
                                    ↓
Synthesis prompt → narrative markdown → research_versions table
                                    ↓
Ontology formalization → Neo4j graph → GraphRAG query layer
```

### GraphRAG Architecture

**Query Flow**: Natural language → Cypher generation → exposed result set → LLM synthesis

All four steps logged and inspectable. The result set is the epistemic ground truth.

### 90-Day Plan Context

This ontology work is **Weeks 5-8** of the 90-day plan:

- **Weeks 1-4**: Extraction schema built, deep researcher running, CDP batch imported ✅ DONE
- **Weeks 5-6**: Architecture formalization, adaptation mechanism typologies (current phase)
- **Weeks 7-8**: Ontology induction from full corpus, relationship clustering
- **Weeks 9-10**: Populate Neo4j, sanity-check queries
- **Weeks 11-12**: GraphRAG pipeline with test harness

---

## Key Design Decisions

### Solutions: What They ARE vs. What They DO

**Decision**: Solution taxonomy classifies by **identity** (what the solution is), not **function** (what it does).

**Rationale**: Function is expressed as typed relationships:
- `Solution -[:MITIGATES]-> Hazard`
- `Solution -[:OPERATES_ON]-> UrbanSystem`
- `Solution -[:USES_MECHANISM]-> Mechanism`

This enables multi-hop queries: "Find solutions that mitigate coastal flooding by hardening energy infrastructure."

### Vocabularies as Guidance, Not Constraints

**Decision**: Vocabulary files provide **guidance** rather than rigid schema enforcement. Validation is advisory, not blocking.

**Rationale**: Allows handling edge cases, new terms, and genuine ambiguity without breaking extraction. Invalid terms flagged for review but don't stop the researcher.

### Claims as First-Class Objects

**Decision**: Every value in extraction_schema references claim UUIDs. Claims are rows in the `claims` table with `claim_text`, `source_url`, `confidence`, etc.

**Rationale**: Enables provenance tracking, re-classification as ontology evolves, and graph queries that traverse to source evidence.

---

## Tools and Technologies

- **Ontology Editor**: Protégé (for OWL formalization)
- **Graph Database**: Neo4j (for knowledge graph)
- **Schema Validation**: JSON Schema + custom validators
- **Vocabulary Management**: JSON files synced from Supabase tables
- **Diagram Tools**: draw.io (architecture sketches), WebVOWL (ontology visualization)

---

## References

- **Extraction Schema**: `schemas/extraction-schema-v1.json`
- **Vocabulary Strategy**: `schemas/vocabularies/README.md`
- **Legacy Architecture Docs**: `README-legacy-extraction-docs.md`
- **OntoKGen Methodology**: `papers/2412.00608v3.pdf`
- **Project Context**: `plans/firewall_project_context.md`
