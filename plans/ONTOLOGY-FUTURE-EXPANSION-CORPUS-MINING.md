# Ontology Future Expansion: Corpus Mining

## Context

This document outlines the **corpus mining phase** of ontology development, scheduled for **Weeks 7-8** of the 90-day plan. This phase builds on the formalized v0.1 ontology extracted from the extraction schema structure.

**What we have at this stage:**
- Formalized v0.1 ontology with node types and relationships extracted from extraction schema v1.2
- ~10,000 solutions with populated extraction_schema JSONB fields
- 224 published research versions (narrative markdown)
- 129,099 claims with provenance (source documents, confidence scores)
- Controlled vocabularies (hazards, solutions, urban systems, CRF goals)

**What corpus mining adds:**
- Emergent relationship types not explicitly modeled in the schema
- Formal mechanism taxonomy (cluster free-text mechanism descriptions)
- Implicit entity types mentioned in claims but not in schema
- Co-occurrence patterns and implicit constraints
- Empirical validation of schema-derived types

---

## When This Happens

**Timeline:** Weeks 7-8 of 90-day plan

**Prerequisites:**
- ✅ Extraction schema v1.2 formalized as v0.1 ontology (Weeks 5-6)
- ✅ Deep researcher running for 1+ month, populating extraction schemas
- ✅ CDP batch extraction complete
- ✅ Schema-grounded ontology validated against held-out cases

**Why wait until Weeks 7-8:**
- By then, the researcher has been running for ~6 weeks, producing more high-quality extractions
- Schema-grounded ontology provides baseline to compare against
- Sufficient data volume for statistical clustering and pattern detection

---

## Data Sources for Mining

### 1. Solutions Table (extraction_schema JSONB)
**Volume:** ~10,000+ solutions with populated schemas

**What to mine:**
- Free-text mechanism descriptions (`mechanisms.primary_mechanism`, `mechanisms.secondary_mechanisms`)
- Technical component descriptions (`mechanisms.technical_components`)
- Barrier descriptions (`context.barriers`)
- Enabling condition descriptions (`context.enabling_conditions`)
- Co-benefit descriptions (`outcomes.co_benefits`)
- Failure mode descriptions (`outcomes.failure_modes`)

**Method:** Cluster similar free-text values, propose formal types

### 2. Claims Table
**Volume:** 129,099 claims with `claim_text`, `source_url`, `confidence`

**What to mine:**
- Named entities mentioned in claims (organizations, technologies, frameworks not in schema)
- Implicit relationships (e.g., "Solution X was replicated in City Y after success in City Z" → replication relationship)
- Temporal relationships (e.g., "deployed after policy change" → temporal constraints)
- Causal claims (e.g., "reduced flood damage by 30%" → effectiveness relationship with quantified property)

**Method:** NER + relationship extraction using LLM

### 3. Research Versions Table
**Volume:** 224 published narrative reports

**What to mine:**
- Section structure patterns (which dimensions appear in which narrative sections?)
- Cross-case comparative statements (e.g., "Similar to Barcelona's approach...")
- Meta-claims about solution categories (e.g., "Nature-based solutions typically require...")

**Method:** Document analysis, extract comparative and categorical claims

### 4. CDP Data (11,842 Actions)
**Volume:** 11,842 city-reported adaptation actions

**What to mine:**
- Distribution analysis: which hazards/solution categories/urban systems are most common?
- Underrepresented combinations (e.g., "Heat + Transportation" is rare in curated cases but common in CDP)
- Vocabulary gaps (terms used in CDP that don't map to controlled vocabularies)

**Method:** Statistical distribution analysis, gap detection

---

## Extraction Methodology

### Phase A: Mechanism Clustering (Primary Target)

**Problem:** Mechanism dimension uses free text with seed vocabulary guidance. Need to formalize into a controlled vocabulary.

**Steps:**
1. Extract all `mechanisms.primary_mechanism` and `mechanisms.secondary_mechanisms` values from extraction_schema JSONB
2. Cluster using embedding similarity (OpenAI text-embedding-3-small via LiteLLM proxy)
3. For each cluster:
   - Propose canonical mechanism type name
   - Draft definition (1-2 sentences)
   - List representative examples from cluster
   - Count solution instances
   - Flag ambiguous cases for manual review

**Expected Output:** `ontology/mechanism-taxonomy-v0.json` with:
```json
{
  "mechanisms": [
    {
      "id": "absorb",
      "name": "Absorb / Buffer",
      "definition": "Capture, store, or attenuate hazard impacts through material or ecological buffering capacity.",
      "examples": ["bioswales capture stormwater", "wetlands buffer storm surge", "green roofs absorb rainfall"],
      "solution_count": 847,
      "subclusters": ["water_retention", "impact_attenuation", "energy_absorption"]
    }
  ]
}
```

### Phase B: Named Entity Recognition on Claims

**Problem:** Claims mention entities not modeled in schema (e.g., specific technologies, standards, certifications).

**Steps:**
1. Sample 10,000 claims (stratified by solution category and hazard type)
2. Run NER extraction via LLM with prompt:
   - Extract: organizations, technologies, standards/frameworks, policies, financial instruments
   - For each entity: type, canonical name, context snippet
3. Cluster by entity type
4. Propose new node types if frequency > threshold (e.g., >50 mentions)

**Expected Output:** `ontology/emergent-entities-v0.json` with candidates for inclusion

### Phase C: Relationship Pattern Mining

**Problem:** Some relationships are implicit in claims but not modeled in schema.

**Steps:**
1. Sample claims mentioning multiple entities (e.g., "Solution X in City A was funded by Organization B")
2. Extract triples: (subject, predicate, object)
3. Cluster predicates by semantic similarity
4. Propose relationship types with:
   - Source/target type constraints
   - Frequency count
   - Evidence claims
   - Ambiguities / edge cases

**Expected Discoveries:**
- `Solution -[:FUNDED_BY]-> Organization` (from implementation.financing paths)
- `Solution -[:REPLICATED_FROM]-> Solution` (from context.comparable_implementations)
- `Solution -[:CERTIFIED_BY]-> Standard` (from claims mentioning certifications)
- `City -[:MEMBER_OF]-> CityNetwork` (from governance claims)

**Expected Output:** `ontology/emergent-relationships-v0.json`

### Phase D: Distribution Analysis (CDP Focus)

**Problem:** Curated case library has selection bias. CDP data shows what cities actually report.

**Steps:**
1. Compare curated case distribution vs. CDP distribution across:
   - Hazard types addressed
   - Solution categories
   - Urban systems affected
   - Implementing actor types
   - Scale of deployment
2. Identify systematic gaps:
   - Hazards overrepresented in CDP but rare in cases (e.g., drought, landslide)
   - Solution types common in CDP but missing from taxonomy
   - Geographic biases (regions underrepresented in case library)
3. Propose ontology expansions to cover underrepresented areas

**Expected Output:** `ontology/distribution-analysis-v0.md` with recommendations

---

## LLM-Assisted Extraction Pipeline

### Mechanism Clustering Prompt Template

```markdown
You are analyzing free-text mechanism descriptions from climate adaptation solutions. Your task is to propose a formal mechanism taxonomy.

**Input:** 1,247 mechanism descriptions (provided as JSON array)

**Task:**
1. Cluster semantically similar descriptions
2. For each cluster, propose:
   - **Canonical name** (1-3 words, verb or noun phrase)
   - **Definition** (1-2 sentences explaining how this mechanism works)
   - **Subcategories** (if cluster has clear sub-patterns)
   - **Representative examples** (3-5 actual descriptions from cluster)
   - **Ambiguous cases** (descriptions that don't fit cleanly)

**Output format:** JSON array of mechanism types

**Constraints:**
- Prefer existing seed vocabulary terms (absorb, redirect, harden, monitor, govern, shift_risk, adapt_behavior, restore_regenerate) when applicable
- Only propose new terms when cluster doesn't fit existing vocabulary
- Flag overlaps where a description could belong to multiple mechanisms
```

### Named Entity Extraction Prompt Template

```markdown
You are extracting structured entities from climate adaptation research claims.

**Claim:** "The Green Climate Fund provided $15M to finance Barcelona's Superblock program, which was certified under the C40 Cities Climate Leadership Group framework."

**Extract:**
- **Organizations:** Green Climate Fund, C40 Cities Climate Leadership Group
- **Financial Instruments:** grant (implied from "provided")
- **Standards/Frameworks:** C40 Cities Climate Leadership Group framework
- **Solutions:** Superblock program
- **Cities:** Barcelona
- **Amounts:** $15M

**For each entity, provide:**
- Entity type (organization, technology, standard, policy, financial_instrument, etc.)
- Canonical name
- Context snippet (10-15 words showing entity in context)

**Output:** JSON array of entities
```

### Relationship Extraction Prompt Template

```markdown
You are extracting typed relationships from climate adaptation claims.

**Claim:** "Singapore's ABC Waters program was replicated in Copenhagen as the Cloudburst Management Plan, adapting the bioswale design to Nordic climate conditions."

**Extract relationships:**
1. `(Cloudburst Management Plan, REPLICATED_FROM, ABC Waters program)`
   - Evidence: "was replicated in Copenhagen"
   - Confidence: high
2. `(Cloudburst Management Plan, IMPLEMENTED_IN, Copenhagen)`
   - Evidence: "in Copenhagen"
   - Confidence: high
3. `(Cloudburst Management Plan, ADAPTED_FROM, bioswale design)`
   - Evidence: "adapting the bioswale design"
   - Confidence: medium

**For each relationship:**
- Source entity (with type)
- Relationship predicate (verb phrase, present tense)
- Target entity (with type)
- Evidence snippet from claim
- Confidence (high/medium/low)

**Output:** JSON array of typed triples
```

---

## Integration with Schema-Grounded Ontology

**Corpus mining outputs are proposals, not automatic additions.**

### Decision Framework for Inclusion

**Include emergent type/relationship if:**
1. ✅ Appears in >50 solutions or >500 claims (statistical significance)
2. ✅ Cannot be represented with existing types + properties
3. ✅ Enables new graph queries that matter for research/policy
4. ✅ Has clear definition and boundaries (not just noise)
5. ✅ Validated against held-out cases

**Defer emergent type/relationship if:**
- ❌ Rare (<20 solutions) and no external vocabulary justification
- ❌ Can be represented as property of existing type
- ❌ Definitional ambiguity or overlap with existing types
- ❌ Only appears in CDP data (may be reporting artifact, not ontological distinction)

### Reconciliation Process

1. **Load proposals:** Load `emergent-entities-v0.json` and `emergent-relationships-v0.json`
2. **Review session:** For each proposal, decide:
   - Include in ontology (add to `draft-v1.json`)
   - Represent as property (modify existing type)
   - Defer (log in `decisions-log.md` with rationale)
   - Reject (not ontologically meaningful)
3. **Update vocabularies:** If including, add to appropriate vocabulary file
4. **Update schema:** If schema changes required, bump to v1.3
5. **Validate:** Run against held-out cases to ensure new types/relationships extract cleanly

---

## Expected Outputs

### Deliverables

1. **`ontology/mechanism-taxonomy-v0.json`** - Formalized mechanism types from clustering
2. **`ontology/emergent-entities-v0.json`** - Named entities extracted from claims (candidates)
3. **`ontology/emergent-relationships-v0.json`** - Implicit relationships from claims (candidates)
4. **`ontology/distribution-analysis-v0.md`** - CDP vs. case library gap analysis
5. **`ontology/corpus-mining-review.md`** - Decision log: what to include, defer, or reject
6. **`ontology/draft-v1.json`** - Updated ontology incorporating approved emergent types

### Updated Vocabularies

- **`schemas/vocabularies/mechanisms.json`** (NEW) - Formalized mechanism taxonomy
- **`schemas/vocabularies/enums.json`** (UPDATED) - Add any new enum values
- **`schemas/extraction-schema-v1.3.json`** (IF NEEDED) - Schema update if new dimensions/fields required

---

## Success Metrics

**Quantitative:**
- Mechanism taxonomy reduces free-text variance by >60% (most descriptions map to controlled terms)
- Emergent relationship types enable >10 new Cypher query patterns not possible with v0.1 schema
- Distribution analysis identifies <5 major gaps requiring ontology expansion

**Qualitative:**
- Mechanism definitions are clear, non-overlapping, and mappable to IPCC/CRF frameworks
- Emergent entities have consensus definitions (no "one person's technology is another's policy" ambiguity)
- CDP gap analysis reveals actionable insights (not just "CDP is noisy")

**Validation:**
- All approved emergent types extract cleanly from held-out cases
- No ontology bloat: new types represent genuine distinctions, not just renaming existing concepts

---

## Risks and Mitigations

### Risk: Over-fitting to CDP Noise
**Symptom:** Emergent types reflect CDP reporting quirks, not real ontological distinctions

**Mitigation:**
- Cross-validate against curated case library
- Require external vocabulary justification (IPCC, CRF, UNDRR) for rare terms
- Distinguish "reporting artifact" from "underrepresented phenomenon"

### Risk: Mechanism Clustering Produces Junk
**Symptom:** Clusters are incoherent, definitions too generic or too narrow

**Mitigation:**
- Start with seed vocabulary as cluster anchors
- Manual review of cluster coherence before proposing formal types
- Compare against literature typologies (from Weeks 5-6 literature agent task)

### Risk: Entity Extraction Yields Noise
**Symptom:** NER extracts proper nouns that aren't ontologically meaningful (e.g., specific street names)

**Mitigation:**
- Frequency threshold (>50 mentions across corpus)
- Type constraints (only extract organization, technology, standard, policy, financial_instrument)
- Manual review of high-frequency entities before inclusion

### Risk: Relationship Mining Finds Spurious Patterns
**Symptom:** Extracted triples don't represent real semantic relationships

**Mitigation:**
- Require evidence from multiple sources (not single claim)
- Cross-check against schema-grounded relationships (most relationships should already exist)
- Focus on high-confidence extractions (LLM self-assessment)

---

## Tools and Scripts

### Clustering Pipeline
```bash
# Extract mechanism free-text from extraction schemas
uv run scripts/extract_mechanism_text.py > data/mechanisms-raw.json

# Cluster using embeddings
uv run scripts/cluster_mechanisms.py \
  --input data/mechanisms-raw.json \
  --output ontology/mechanism-taxonomy-v0.json \
  --min-cluster-size 20

# Review clusters interactively
uv run scripts/review_mechanism_clusters.py
```

### Named Entity Extraction
```bash
# Sample claims for NER
uv run scripts/sample_claims.py \
  --stratify-by solution_category,hazard \
  --sample-size 10000 \
  --output data/claims-sample.json

# Run NER extraction (batch LLM job)
uv run scripts/extract_entities_from_claims.py \
  --input data/claims-sample.json \
  --output ontology/emergent-entities-v0.json \
  --model sonnet
```

### Distribution Analysis
```bash
# Compare curated vs CDP distributions
uv run scripts/compare_distributions.py \
  --curated-source research_versions \
  --cdp-source solutions \
  --output ontology/distribution-analysis-v0.md
```

---

## Connection to 90-Day Plan

This corpus mining phase is **Weeks 7-8** of the ontology development track:

**Before (Weeks 5-6):**
- ✅ Schema-grounded ontology formalized (draft-v0.json)
- ✅ Literature agent surveyed mechanism typologies
- ✅ Alignment with external vocabularies complete

**During (Weeks 7-8):**
- **Corpus mining** (this document)
- Mechanism clustering and formalization
- Emergent entity/relationship extraction
- Distribution gap analysis

**After (Weeks 9-10):**
- Populate Neo4j with draft-v1 ontology
- Run Cypher queries to validate new relationship types
- Identify remaining ontology gaps from query failures

**Weeks 11-12:**
- GraphRAG pipeline using finalized ontology
- Test harness validates query coverage

---

## References

- **Extraction Schema:** `schemas/extraction-schema-v1.json`
- **Vocabularies:** `schemas/vocabularies/README.md`
- **Schema-Grounded Ontology:** `ontology/draft-v0.json` (output of Weeks 5-6)
- **OntoKGen Paper:** `papers/2412.00608v3.pdf` (methodology reference for corpus-based ontology induction)
- **90-Day Plan:** `plans/firewall_project_context.md`

---

## Status

**Phase:** Not started (scheduled for Weeks 7-8)

**Prerequisites:** 
- [ ] Schema-grounded ontology v0.1 complete
- [ ] Deep researcher running for 6+ weeks
- [ ] CDP batch extraction complete
- [ ] ~10K solutions with populated extraction_schema

**Next action (when ready):** Extract mechanism free-text corpus and run clustering pipeline
