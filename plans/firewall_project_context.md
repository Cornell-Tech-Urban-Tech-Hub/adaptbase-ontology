# Urban Climate Adaptation Technology: Knowledge Graph & Research Infrastructure
## Context document for Claude Code session
### Updated with student ontology assessment and CDP database integration

---

## What this project is

Building a knowledge infrastructure for urban climate adaptation technology research, anchored in a growing case library of 200+ documented solutions and thousands of reported city adaptation actions. This supports the FIREWALL book (MIT Press), the Resilience Scanner platform, and ongoing research at Cornell Tech's Jacobs Urban Tech Hub.

Three interconnected components:
- A **deep research agent** that documents climate adaptation technologies across global cities
- An **extraction schema** (immediate deliverable) that structures what the researcher captures per case
- A **knowledge graph** (Neo4j) built on a formal ontology enabling multi-hop queries across solutions, hazards, urban systems, and mechanisms

---

## Key design decisions already made

**The ontology has four distinct dimensions — separate node types, not one flat taxonomy**

| Dimension | What it classifies |
|---|---|
| Hazards / Stresses | Climate-driven threats — existing taxonomy available |
| Solutions | The intervention — tech, policy, regulation, collective action, nature-based |
| Urban Systems | What part of the city it operates on |
| Mechanisms | How it works — absorb, redirect, harden, monitor, govern, shift risk |

**Solution hierarchy organized by what solutions ARE, not what they do.** What they do is expressed as typed relationships to hazard and mechanism nodes.

**Four external frameworks to import rather than reinvent:**
- IPCC AR6 adaptation action typology (structural/physical, social, institutional, ecosystem-based) — as a crosscutting attribute on solution nodes
- IPCC AR6 Climate Impact Drivers (29 CIDs) — informs hazard taxonomy
- CityGML urban system classification — standard typology for urban system nodes
- UNDRR Sendai Framework terminology — hazard/exposure/vulnerability/risk definitions

**GraphRAG architecture, not plain RAG.** Natural language → Cypher → exposed result set → LLM synthesis. All four steps logged and inspectable. The result set is the epistemic ground truth.

---

## The student's ontology: what to use and what to discard

The student built a schema in Python/Neo4j covering five layers: Urban System, Climate Risk, Governance, Intervention, and Evaluation. It is more competent than expected — she has clearly absorbed the IPCC risk framework and thought carefully about governance structure. However, the solution layer (the core of this project) is drastically underspecified in her schema.

### Extract and use these parts

**The governance-to-intervention relationship types** are well-designed and directly usable as vocabulary for the extraction schema's enabling conditions and barriers fields:
- `ISSUED_BY`, `MANDATES`, `IMPLEMENTS`, `PARTICIPATES_IN` — policy-to-action chain
- `FACILITATED_BY`, `HINDERED_BY` — maps onto enabling conditions / barriers
- `MANAGES`, `FACES`, `COORDINATES_WITH` — actor relationships

**The evaluation and outcome layer** is more granular than the current extraction schema and worth importing:
- `Outcome` node with `evidence_quality` property
- `Indicator` node with `baseline`, `target`, `data_source`
- `ResilienceState` node with `absorption_capacity`, `transformation_capacity` — captures the absorb/adapt/transform resilience framework
- Relationship: `REFLECTS` (Outcome → ResilienceState)

**The risk chain relationships** correctly distinguish physical space impacts from population impacts — a meaningful distinction the current schema doesn't make:
- `AFFECTS_ZONE` (hazard → urban zone)
- `EXPOSES` (hazard → exposure unit / population)
- `WORSENS` (hazard → vulnerability)

**The Vulnerability node structure**: `exposure_score`, `sensitivity_score`, `adaptive_capacity_score`, `affected_group` — aligns with IPCC AR6 vulnerability framework.

### Discard or substantially rebuild

**The AdaptationAction node** is the core node for this project and is essentially a placeholder in her schema. It has only: `action_name`, `status`, `spatial_scale`, `adaptation_type`, `start_year`, `end_year`, `cost_usd`, `co_benefits`. No technology type, no mechanism of action, no nature-based/engineered/social distinction, no replicability, no deployment context. Build this from scratch using the extraction schema.

**The solution taxonomy** is entirely absent. `adaptation_type` is a single free-text property with no controlled vocabulary. This is the whole problem to solve.

**The mechanism dimension** — how solutions work — does not exist.

**The urban systems layer** conflates physical infrastructure, spatial zones, and exposure units in ways that create ambiguous multi-hop queries. Rebuild using CityGML.

**The LOCATED_IN relationship** puts each AdaptationAction in one City, making it impossible to represent a solution deployed across multiple cities or track replication. Restructure to support many-to-many city-solution relationships.

### Framing for Claude Code session
Treat the student's schema as a **source of relationship vocabulary and evaluation structure**, not as an architecture to extend. Import specific relationship types and the evaluation layer; rebuild the solution and urban systems layers from scratch.

---

## Data sources

### Existing case library (200 cases)
Curated, technology-focused solutions — roughly one page per case. Strength: depth and quality. Limitation: selection bias toward documented, replicable tech solutions; underrepresents policy-only actions and low-tech community interventions.

### CDP (Carbon Disclosure Project) database
Approximately 1,000 city-reported adaptation actions from the CDP urban adaptation questionnaire. Strength: scale, geographic distribution, and coverage of the full spectrum of what cities actually report — including policy-only, early-stage, and low-tech actions. Limitation: variable quality, self-reported, often vague on mechanism and technology specifics.

### Role of each in the project
The two datasets are complementary. The case library provides depth for mechanism and technology classification. The CDP database provides breadth and distribution for validating that the ontology covers what cities are actually doing, not just what researchers find interesting. Together they ground the ontology empirically rather than theoretically.

---

## Immediate task: build the extraction schema

### What an extraction schema is
A structured set of fields the researcher populates for each case. Not yet an ontology — it becomes the empirical foundation for the ontology. The schema applies to both the curated case library and the CDP database, though CDP entries will populate fewer fields at higher noise.

### Three layers of fields

**Identity** — what this thing is
- Solution name
- Primary technology or intervention type
- Solution category (controlled vocab — from existing taxonomy, see inputs below)
- Source city/cities (many-to-many — solutions can appear in multiple cities)
- Year of deployment or documentation
- Implementing actor type (municipal government / utility / private / NGO / community / multi-stakeholder)
- Data source (case library / CDP / other)

**Functional** — what it does
- Hazards addressed (controlled vocab — from existing hazard taxonomy)
- Urban systems affected (controlled vocab — from CityGML classification)
- Mechanism of action (free text now, cluster later — seed list: absorb, redirect, harden, monitor, govern, shift risk, adapt behavior, restore/regenerate)
- IPCC action type (controlled vocab — structural/physical, social, institutional, ecosystem-based) as crosscutting attribute
- Primary beneficiaries
- Scale of deployment (neighborhood / district / city / regional)

**Contextual** — conditions and evidence
- Enabling conditions required (regulatory / financial / technical / social — multi-select)
- Known barriers to adoption
- Evidence of effectiveness (anecdotal / measured / rigorously evaluated)
- Outcome indicators where available (maps to student's Indicator node)
- Co-benefits
- Known failure modes or limitations
- Cost range or cost model
- Replicability assessment
- Classification difficulty notes (free text — flag ambiguous cases here, this field drives ontology refinement)
- Key source passages (raw evidence preserved for future reclassification)

### Controlled vocabulary vs. free text
- **Controlled vocabulary:** solution category, hazards, urban systems, implementing actor type, IPCC action type, scale, evidence level, enabling condition types
- **Free text now, formalize later:** mechanism of action, specific barriers, co-benefits, failure modes, source passages

---

## Inputs for the first Claude Code session

The session task is to synthesize these inputs, identify gaps and overlaps, and produce a v1 extraction schema with finalized field list, controlled vocabulary candidates for each field, and recommendations on where to use free text now and formalize later.

1. **Existing solution categories taxonomy** — upload file
2. **Existing hazards taxonomy** — upload file
3. **Existing stresses and shocks taxonomy** — upload file
4. **Student's ontology schema** — available at the GitHub URL, already reviewed (summary above); use for relationship vocabulary and evaluation layer only
5. **CityGML urban system feature type categories** — Building, Bridge, Tunnel, WaterBody, Vegetation, LandUse, Transportation, CityFurniture, ReliefFeature, etc.
6. **IPCC AR6 adaptation action typology** — structural/physical, social, institutional, ecosystem-based with subcategories from Chapter 14
7. **Sample of 10-15 diverse cases** from the existing 200 — spanning tech solutions, policy interventions, and collective action across different hazard types
8. **Sample of 50-100 CDP actions** — spanning different regions, city sizes, hazard types — to surface vocabulary that the curated case library underrepresents

---

## 90-day plan

### Month 1: Foundation and data

**Weeks 1-2: Build the extraction schema and launch the researcher**

Start by pulling 8-10 of the most diverse existing cases — spanning technology solutions, policy interventions, and collective action across different hazard types. Simultaneously pull a sample of 50-100 CDP actions covering different regions and hazard types. Run both sets through Claude asking: what attributes would a researcher need to capture to make these cases comparable and queryable? The CDP sample is critical here because it will surface vocabulary the curated case library underrepresents — policy-only actions, early-stage commitments, low-tech community interventions.

Synthesize with all inputs listed above into a v1 schema. Make controlled vocabulary vs. free text decisions. Add the classification difficulty overflow field. Get the deep researcher running against this schema.

Source capture discipline: key passages and provenance are as important as structured field population. The raw evidence in each case record is what enables reclassification as the ontology evolves.

**Weeks 3-4: CDP batch extraction and student ontology absorption**

Run a full extraction pass over the CDP database using the v1 schema — this is a batch LLM job. Output will be noisy but queryable. The CDP dataset at this stage gives you a large empirical base for ontology induction and reveals where the schema has gaps (fields that can't be populated) or ambiguities (fields that get inconsistent values across similar actions).

In parallel: absorb the student's ontology. Node labels, relationship types, instances — treat as a document to review, not a system to use. Extract the governance relationship types and evaluation layer as controlled vocabulary candidates per the assessment above. This is a few focused sessions, not ongoing collaboration.

Also in weeks 3-4: set up independent tooling stack — Protégé, a separate Neo4j instance, draw.io for architecture sketching, WebVOWL for visualization. Don't build the graph yet, just establish the environment.

---

### Month 2: Ontology development

**Weeks 5-6: Architecture and module design**

Draw.io sketch of the four dimensions as separate modules with explicit connection points. Resolve which existing taxonomies become controlled vocabulary in which module. Integrate the student's governance relationship types and evaluation layer into the architecture at their appropriate positions.

First targeted literature agent task: survey adaptation mechanism typologies. Find the 5-10 most cited classification schemes for how adaptation interventions work (not what they are — how they work). Summarize categories and identify consensus and disagreement. Output directly informs mechanism module design. Frame as a specific research commission with source transparency requirements — no hallucinated citations.

**Weeks 7-8: Ontology induction from the full corpus**

By now the researcher has been running for a month and the CDP extraction is complete. You have substantially more than 200 cases plus the CDP thousand. Run a systematic extraction pass: use Claude to extract typed triples from each case — solution X addresses hazard Y, solution A operates on urban system B, intervention C requires enabling condition D.

Cluster extracted relationship types. Collapse near-synonyms, identify missing distinctions. This clustering, done with LLM assistance but reviewed by you, produces the first draft of the relationship taxonomy — the most original and least borrowable part of the ontology.

Use the CDP data specifically here to check distribution: what hazard types are most commonly addressed across all cities? What solution categories are systematically underrepresented in the curated cases? This shapes where the researcher focuses next.

Second literature agent task: urban systems classification — is there a standard typology adopted widely enough to import? CityGML is the leading candidate; New Urban Agenda and ISO 37120 (city indicators) are alternatives worth surveying.

Formalize as v0.1 OWL file in Protégé: node types and relationship types, minimal instances. Include the student's evaluation layer as a module.

---

### Month 3: Integration and first system

**Weeks 9-10: Populate Neo4j**

Load the growing case library and CDP batch into Neo4j using the v0.1 ontology as schema. Each case becomes a Solution node connected to Hazard, UrbanSystem, Mechanism, and Outcome nodes via defined relationship types. Include provenance: source (case library vs. CDP), extraction date, confidence level.

Run sanity-check Cypher queries: are solution categories consistent? Are hazard connections populated? Where is data thin? Where do CDP entries and case library entries tell different stories about the same solution type? The gap between what you can query and what you want to query tells you what to fix in the ontology and what to send the researcher after.

**Weeks 11-12: First GraphRAG pipeline and ontology refinement**

Build the query layer: NL query → Cypher → exposed result set → LLM synthesis → response. Log all four steps. Build a 10-15 test query evaluation harness with known-answer queries. Run and audit failure modes:
- Cypher generation failures → fix by injecting schema into system prompt
- Empty result sets → ontology gaps or population gaps — fix by refining ontology or directing researcher
- LLM synthesis failures on good data → prompt engineering problem

Third literature agent task: GraphRAG architectures for policy document analysis — what's been published closest to this use case?

---

## Running principles for literature research agents

Each agent task is a targeted research commission, not an open-ended literature sweep:
- Specific question with defined scope
- Required output format (structured summary, not prose)
- Source transparency requirements — full citations, no hallucinated references
- Log: what was asked, what was returned, how it was used

This log becomes methodology documentation for the research program.

The three scheduled agent tasks are:
1. **Weeks 5-6:** Adaptation mechanism typologies — how do interventions work?
2. **Weeks 7-8:** Urban systems classification standards — what's worth importing?
3. **Weeks 11-12:** GraphRAG for policy document analysis — what's been published?

---

## What the student's work contributes (and doesn't)

Her work is an input to be evaluated and selectively absorbed, not a dependency or ongoing collaboration. The governance relationship types and evaluation layer are genuinely useful and save design work. The solution layer — the core of this project — needs to be built from scratch. This project proceeds independently on a separate Neo4j instance with its own ontology architecture.

---

## What you will have at 90 days

- A running deep researcher populating a growing, structured case library
- CDP database batch-extracted and loaded into the same schema
- A v0.1 ontology in Protégé covering four core dimensions with the student's evaluation layer integrated
- A populated Neo4j instance with both case library and CDP data loaded
- A working GraphRAG pipeline with instrumentation and a test harness
- An empirically grounded view of where the ontology needs to grow
- A methodology for targeted literature research agents — itself a contribution given the FIREWALL research focus
