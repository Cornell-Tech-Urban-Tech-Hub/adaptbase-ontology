# Urban Climate Adaptation Technology: Knowledge Graph & Research Infrastructure

## What this project is

Building a knowledge infrastructure for urban climate adaptation technology research, anchored in a growing case library of 200+ documented solutions and thousands of reported city adaptation actions. This supports the FIREWALL book (MIT Press), the Resilience Scanner platform, and ongoing research at Cornell Tech's Jacobs Urban Tech Hub.

Three interconnected components:
- A **deep research agent** that documents climate adaptation technologies across global cities
- An **extraction schema** that structures what the researcher captures per solution, organized by ontology dimensions
- A **knowledge graph** (Neo4j) built on a formal ontology enabling multi-hop queries across solutions, hazards, urban systems, and mechanisms

---

## Architecture

### Data flow

```
Crawler discovers solutions → solutions table (draft)
CDP import tool loads actions → solutions table (draft)
                                        ↓
Deep researcher picks up drafts → extracts claims → claims table
                                                  → populates extraction schema (solutions.extraction_schema JSONB)
                                        ↓
Synthesis prompt → narrative markdown → research_versions table
```

### Where things live

| What | Where | Description |
|---|---|---|
| Extraction schema | `solutions.extraction_schema` (JSONB) | Dimensional metadata + claim UUID references |
| Claims | `claims` table | First-class objects with text, source, confidence, validation |
| Narrative reports | `research_versions` table | Synthesized markdown with footnotes |
| Solution taxonomy | `solution_taxonomy` table | 7 categories, ~100 subcategories |
| Hazards | `hazards` table | 30+ climate hazards, 13 categories (C40/Arup Typology) |
| Schema definition | `schemas/extraction-schema-v1.json` | JSON Schema for the JSONB structure |
| Controlled vocabs | `schemas/vocabularies/` | 5 vocabulary files (see below) |
| Prompts | `schemas/prompts/` | Research agent + synthesis prompts |
| Validation results | `schemas/validation/` | Schema tested against published solutions + CDP |

### Controlled Vocabularies

**Vocabulary-First Architecture**: The extraction schema references external vocabulary files rather than embedding controlled terms as inline enums. This design enables:
- Rich taxonomies without verbose schema definitions
- Vocabularies that evolve independently of schema structure
- LLM agents selecting most appropriate terms from detailed vocabularies
- Easy integration with external standards (IPCC, C40, CRF)

All vocabularies are documented in `schemas/vocabularies/README.md` with integration guidance for crawler and researcher agents.

**Vocabulary Files and Provenance:**

| Vocabulary File | Source | Content | Sync Strategy |
|---|---|---|---|
| `solution-categories.json` | `solution_taxonomy` table | 7 categories, ~100 subcategories | Synced from Supabase (is_active = true) |
| `hazards.json` | C40/Arup Climate Hazard Typology → `hazards` table | 13 categories, 30+ specific hazards | Synced from Supabase (is_active = true) |
| `crf-goals.json` | City Resilience Framework 2024 v2 (Resilient Cities Network) | 4 dimensions, 22 resilience goals | External standard reference |
| `urban-systems.json` | Custom hierarchical taxonomy for climate adaptation | 7 sectors, 20+ subsectors, 50+ granular systems | Custom (interdependency analysis) |
| `enums.json` | CDP project fields, IPCC AR6, custom enums | Actor types, scales, financing models, implementation status, etc. | Multi-source compilation |

---

## Ontology dimensions

The extraction schema organizes research into seven dimensions that map to the knowledge graph's eventual shape:

| Dimension | What it captures | Controlled vocab source |
|---|---|---|
| **Identity** | What the solution IS — name, category, actors, year | `solution_taxonomy` table; IPCC AR6 action types |
| **Hazards** | What climate threats it addresses; `resilience_hazards` (v1.2) for non-climate shocks | C40/Arup Climate Hazard Typology (31 hazards, 13 categories) → `hazards` table |
| **Urban Systems** | What part of the city it operates on | Advanced hierarchical urban systems taxonomy (7 sectors, 50+ granular systems) |
| **Mechanisms** | HOW it works | Free text (seed: absorb, redirect, harden, monitor, govern, shift_risk, adapt_behavior, restore_regenerate) |
| **Implementation** | Deployment context — cities, scale, timeline, financing, actors | CDP financing fields; enum values for scale, status, financing models |
| **Outcomes** | Effectiveness, co-benefits, failure modes, CRF goals | City Resilience Framework 2024 (22 goals); evidence level enum; co-benefit categories |
| **Context** | Enabling conditions, barriers, replicability, governance; `resilience_frameworks` (v1.2) for CRF driver tags | Condition type enums; governance relationship vocab (from student ontology) |

### Claims as first-class objects

Every structured value in the extraction schema is grounded in claims stored in the `claims` table. The schema holds **references** (UUID arrays), not embedded claim text:

```json
{
  "hazards_addressed": [
    {
      "hazard_id": "flash_surface_flood",
      "is_primary": true,
      "claim_ids": ["uuid-1", "uuid-2"]
    }
  ]
}
```

Graph query path: solution → extraction_schema dimension → claim UUID → `claims` row → source document.

The `claims` table already exists with 6,914 rows. Key columns: `claim_text`, `source_url`, `source_title`, `source_type`, `confidence`, `validation_score`, `solution_id`, `document_id`, `chunk_id`.

---

## Key design decisions

**Solution hierarchy organized by what solutions ARE, not what they do.** What they do is expressed as typed relationships to hazard and mechanism nodes.

**Five external frameworks integrated:**
- **IPCC AR6 adaptation action typology** — crosscutting attribute on solutions (structural/physical, social, institutional, ecosystem-based)
- **C40/Arup Climate Hazard Typology** — authoritative urban hazard taxonomy (13 categories, 30+ specific hazards)
- **City Resilience Framework 2024** (Resilient Cities Network) — 22 goals across 4 dimensions (Health & Wellbeing, Economy & Society, Infrastructure & Environment, Leadership & Planning). CRF drivers are captured at import time in `context.resilience_frameworks` (v1.2+); CRF goals mapped post-research to `outcomes.resilience_goals`.
- **CDP Cities Adaptation Database** — financing models, funding sources, project lifecycle fields
- **UNDRR Sendai Framework** — hazard/exposure/vulnerability/risk definitions

**Note on Urban Systems**: The hierarchical urban systems taxonomy (7 sectors → 20+ subsectors → 50+ granular systems) is a custom classification designed for climate adaptation interdependency analysis, not derived from CityGML (which is a 3D geometry standard for city modeling).

**GraphRAG architecture, not plain RAG.** NL → Cypher → exposed result set → LLM synthesis. All four steps logged and inspectable.

**Extraction schema IS the research.** The agent populates it with sourced claims. When complete enough, a synthesis prompt transforms it into a narrative report. Early synthesis attempts (~40% completeness) serve as gap-identification diagnostics.

---

## Data sources

### Existing case library (~200 cases, in Supabase)
Published research in `research_versions` as markdown with footnoted claims. Strength: depth, mechanism detail, measured outcomes. Limitation: selection bias toward documented tech solutions.

### CDP database (11,842 rows)
At `resources/CDP_cities_adaptation_fact_table/`. Three record types: goals, actions, projects. CDP actions are imported as standard draft solutions via a batch import tool. They look identical to crawler-discovered solutions — the researcher doesn't know or care about the origin. Strength: scale, global coverage, structured funding/co-benefit data. Limitation: variable quality, self-reported, vague on mechanism.

### Student's ontology schema
At `resources/ruowen-climate-adaptation.py`. Used for **governance relationship vocabulary and evaluation layer only** (MANDATES, FACILITATED_BY, ISSUED_BY, HINDERED_BY; Indicator/Outcome nodes). The solution layer is built from scratch.

---

## Synthesis pipeline

The researcher attempts synthesis at configurable completeness thresholds:
- **~40% completeness** — gap identification draft. Explicit `[GAP: ...]` markers. Generates research directives.
- **~70% completeness** — near-publishable draft with minor gap flags.
- **After gap-filling** — final synthesis when completeness plateaus.

The synthesis prompt maps ontology dimensions to narrative sections:

| Report Section | Schema Dimensions |
|---|---|
| Solution Overview | identity + hazards + mechanisms.primary |
| Technical Components | mechanisms.technical_components |
| Implementation Details | implementation |
| Benefits and Impacts | outcomes |
| Challenges and Limitations | context.barriers + outcomes.failure_modes |
| Replicability and Scaling | context.replicability + context.enabling_conditions |

---

## Extraction schema changelog

### v1.2 (2026-04-09)
**New fields:**
- `hazards.resilience_hazards` — array of free-text non-climate shock/stress labels (e.g., "Earthquake", "Cyber Attack", "Financial Crisis"). Used when a source (e.g., 100RC) treats resilience holistically and includes threats that don't map to the C40/Arup climate hazard typology.
- `context.resilience_frameworks` — array of framework classification objects capturing which resilience framework drivers/sub-dimensions a solution was tagged with at import time. Initially populated by the 100RC importer with CRF (City Resilience Framework) drivers.

**Motivation:** 100 Resilient Cities (100RC) initiative data includes both climate and non-climate hazards, and organizes solutions by CRF drivers. Capturing this at import time preserves source provenance and enables CRF-based filtering and analysis without requiring full researcher passes.

### v1.1 (prior)
Timeline sub-fields (base_year, start_year, target_year, end_year, timeframe_category, events), financing sub-fields (financing_model, financing_status, funding_sources, investment_needed, financial_instruments), resilience_attributes in mechanisms, and resilience_goals in outcomes.

---

## OntoKGen methodology notes (Month 2 reference)

Paper: *Leveraging LLM for Automated Ontology Extraction and Knowledge Graph Generation* (arXiv:2412.00608). PDF at `papers/2412.00608v3.pdf`.

Key elements for Month 2:
1. **Iterative CoT for ontology extraction** — multi-round refinement, maps to our corpus extraction plan
2. **User-guided refinement** — LLM proposes, humans approve
3. **Cypher generation pipeline** — aligns with our GraphRAG architecture
4. **Corpus-to-ontology induction** — run against hundreds of populated schemas to discover missed relationship types

Related work: OntoGenix (ScienceDirect 2024), Fusion-Jena automatic KG creation (GitHub).

Decision deferred to Month 2: automated extraction as discovery tool vs. primary method.

---

## 90-day plan

### Month 1: Foundation and data

**Weeks 1-2**: Build extraction schema, research agent prompt, synthesis pipeline. Test end-to-end on published solutions. Import CDP actions as draft solutions.

**Weeks 3-4**: Deep researcher running against schema. CDP batch in queue. Student ontology absorbed (governance vocab, evaluation layer). Tooling environment set up (Protégé, Neo4j, draw.io).

### Month 2: Ontology development

**Weeks 5-6**: Architecture sketch — four dimensions as modules. Literature agent task: adaptation mechanism typologies.

**Weeks 7-8**: Ontology induction from full corpus. Cluster relationship types. CDP distribution analysis. Literature agent: urban systems classification standards. Formalize as v0.1 OWL.

### Month 3: Integration and first system

**Weeks 9-10**: Populate Neo4j. Sanity-check Cypher queries. Identify gaps.

**Weeks 11-12**: GraphRAG pipeline with test harness. Literature agent: GraphRAG architectures for policy analysis.

### What you will have at 90 days
- Running deep researcher populating structured case library
- CDP batch loaded as draft solutions, enriched by researcher
- v0.1 ontology in Protégé covering four core dimensions
- Populated Neo4j instance with both datasets
- Working GraphRAG pipeline with instrumentation
- Empirically grounded view of where the ontology needs to grow

---

## File structure

```
packages/ontology/
├── README.md                              # This file
├── schemas/
│   ├── extraction-schema-v1.json          # JSON Schema for solutions.extraction_schema
│   ├── vocabularies/
│   │   ├── README.md                      # Vocabulary integration strategy
│   │   ├── solution-categories.json       # From solution_taxonomy table
│   │   ├── hazards.json                   # C40/Arup Climate Hazard Typology → hazards table
│   │   ├── crf-goals.json                 # City Resilience Framework 2024 (22 goals)
│   │   ├── urban-systems.json             # Hierarchical urban systems taxonomy
│   │   └── enums.json                     # Non-table-backed enums (actor types, financing, etc.)
│   ├── prompts/
│   │   ├── research-agent-prompt.md       # Deep researcher instructions
│   │   └── synthesis-prompt.md            # Schema → narrative report
│   └── validation/
│       ├── schema-validation-published-solutions.md
│       └── schema-validation-cdp-actions.md
├── resources/
│   ├── CDP_cities_adaptation_fact_table/   # 11,842 rows
│   ├── city-resilience-framework-2024v2.pdf # CRF 2024 source document
│   ├── jon-climate-company.json           # Structural reference
│   └── ruowen-climate-adaptation.py       # Student's schema
└── papers/
    └── 2412.00608v3.pdf                   # OntoKGen paper
```
