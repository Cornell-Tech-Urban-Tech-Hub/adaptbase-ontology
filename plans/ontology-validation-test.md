# Ontology Validation Test Plan

**Date:** 2026-04-16  
**Purpose:** Quick quality check of ontology v0.3 against actual solutions, claims, and source documents  
**Time Budget:** 1.5-2 hours  
**Method:** Claim-centric validation using LLM

---

## Objective

Validate that our ontology (19 types, 30 relationships) can accurately represent the **solution → claim → source document** pipeline we're actually extracting. Identify gaps, awkward fits, and missing concepts before finalizing the design.

---

## Approach: Claim-Centric Validation

**Method:** Start with solutions, examine their claims, trace to source documents, and validate ontology coverage.

**Rationale:** This validates against our actual data pipeline rather than arbitrary documents.

### Step 1: Sample Selection (10 min)

Query Supabase for 3-5 solutions with rich claim sets from diverse sources:

```sql
-- Get solutions with many claims from diverse sources
SELECT 
  s.id, 
  s.solution_name, 
  s.city,
  s.country,
  COUNT(DISTINCT c.id) as claim_count,
  COUNT(DISTINCT c.document_id) as document_count,
  ARRAY_AGG(DISTINCT d.source_organization) as sources
FROM solutions s
JOIN claims c ON s.id = c.solution_id
JOIN documents d ON c.document_id = d.id
WHERE c.claim_text IS NOT NULL
  AND d.processing_status = 'complete'
GROUP BY s.id, s.solution_name, s.city, s.country
HAVING COUNT(DISTINCT c.id) >= 5  -- At least 5 claims
ORDER BY claim_count DESC, document_count DESC
LIMIT 5;
```

**Selection criteria:**
- ✅ Solutions with rich claim sets (5+ claims each)
- ✅ Claims from multiple source documents
- ✅ Diverse sources (C40, CDP, 100RC, etc.)
- ✅ Different geographic contexts

**Fallback if needed:**
```sql
-- Get specific solution types with claims
SELECT s.*, COUNT(c.id) as claim_count
FROM solutions s
JOIN claims c ON s.id = c.solution_id
WHERE s.solution_name IS NOT NULL
GROUP BY s.id
HAVING COUNT(c.id) >= 3
LIMIT 10;
```

---

### Step 2: LLM-Based Claim Analysis (30-45 min for 3-5 solutions)

**Script:** `scripts/validate_ontology.py`

#### A. Get Solution + Claims + Documents

For each sampled solution:
1. Fetch solution metadata (name, city, description)
2. Fetch all claims for that solution
3. For each claim, get the source document metadata
4. Group claims by document for analysis

```sql
-- Get complete solution → claim → document chain
SELECT 
  s.id as solution_id,
  s.solution_name,
  s.city,
  c.id as claim_id,
  c.claim_text,
  c.claim_type,
  c.confidence_score,
  d.id as document_id,
  d.title as document_title,
  d.document_type,
  d.source_organization
FROM solutions s
JOIN claims c ON s.id = c.solution_id
JOIN documents d ON c.document_id = d.id
WHERE s.id = '[solution_id from Step 1]'
ORDER BY d.id, c.claim_type;
```

#### B. LLM Prompt Structure

For each solution, call LLM with complete claim set:

**System context:**
- Complete ontology (19 types, 30 relationships) from `draft-v0.json`
- Definitions, properties, relationship semantics
- Focus areas: Phase 2 additions

**User prompt:**
```
Analyze this climate adaptation solution and its extracted claims to validate ontology coverage.

SOLUTION:
Name: [solution_name]
Location: [city, country]
Description: [if available]

EXTRACTED CLAIMS (grouped by source document):
[Document 1: title]
- Claim 1 (type: hazard_addressed): "text..."
- Claim 2 (type: mechanism): "text..."
...

[Document 2: title]
- Claim 3 (type: outcome): "text..."
...

ONTOLOGY:
[types and relationships from draft-v0.json]

TASK:
For each claim, map it to ontology nodes and relationships. Identify what works well and what doesn't fit.

Output structured JSON:
{
  "solution_info": {
    "name": "...",
    "location": "...",
    "claim_count": N,
    "document_count": M
  },
  "claim_mappings": [
    {
      "claim_id": "uuid",
      "claim_text": "...",
      "claim_type": "hazard_addressed",
      "ontology_mapping": {
        "nodes": ["Hazard(flood)", "Solution(bioswale)"],
        "relationships": ["MITIGATES(bioswale→flood)"],
        "fit_quality": "perfect|good|awkward|missing",
        "notes": "Why this mapping works or doesn't"
      }
    },
    ...
  ],
  "coverage_by_node_type": {
    "Solution": {"claims": 1, "fit": "good"},
    "Hazard": {"claims": 5, "fit": "perfect"},
    "Vulnerability": {"claims": 2, "fit": "awkward", "issue": "sensitivity vs exposure unclear"},
    "Infrastructure": {"claims": 3, "fit": "good"},
    "ExposureUnit": {"claims": 0, "fit": "missing"},
    ... (all 19 types)
  },
  "coverage_by_relationship": {
    "MITIGATES": {"claims": 5, "fit": "perfect"},
    "REDUCES": {"claims": 2, "fit": "good"},
    "IMPROVES": {"claims": 1, "fit": "awkward", "issue": "vs OPERATES_ON confusion"},
    ... (all 30 types)
  },
  "gaps": {
    "unmappable_claims": [
      {"claim_id": "...", "claim_text": "...", "reason": "No node type for this concept"}
    ],
    "awkward_mappings": [
      {"claim_id": "...", "claim_text": "...", "forced_mapping": "...", "better_approach": "..."}
    ],
    "missing_relationships": ["Needed: Actor FUNDS Solution (vs FUNDED_BY FinancingSource)"]
  },
  "phase2_assessment": {
    "vulnerability_coverage": "2 claims mapped, but sensitivity vs exposure unclear",
    "infrastructure_split": "IMPROVES vs OPERATES_ON distinction worked in 1/3 cases",
    "exposure_chain": "0 claims mentioned ExposureUnit - may not appear in current data",
    "temporal_modeling": "1 claim with TimePoint (planning cycle mentioned)",
    "actor_coordination": "0 actor-to-actor relationships in claims"
  },
  "temporal_analysis": {
    "temporal_references": [
      {
        "quote": "deployed in 2020",
        "type": "simple_date",
        "reused": false,
        "relates_to_other_temporal": false
      },
      {
        "quote": "part of 2018-2024 planning cycle",
        "type": "planning_cycle",
        "reused": true,
        "mentioned_count": 3
      },
      {
        "quote": "commissioned in Q2 2020 after council approval",
        "type": "milestone_event",
        "reused": false,
        "relates_to_other_temporal": true,
        "sequence": "approval → commissioning"
      }
    ],
    "summary": {
      "total_temporal_refs": 12,
      "simple_dates": 8,
      "planning_cycles": 3,
      "milestone_events": 1,
      "reused_temporal_refs": 3,
      "temporal_chains": 0
    },
    "recommendation": "Mostly simple dates - consider TimePoint as property. Planning cycles appear - may need PlanningCycle node."
  }
}
```

**Key instructions:**
- Map EACH claim to ontology (don't skip claims that don't fit - flag them!)
- Focus on Phase 2 additions (Vulnerability, Infrastructure, ExposureUnit, new relationships)
- Rate fit quality: perfect (exact match), good (clear mapping), awkward (forced), missing (can't map)
- Track coverage: which node/relationship types appear in claims? Which don't?
- Be critical - we want to find ontology limitations AND data gaps

#### C. Process LLM Outputs

For each solution, save:
- Raw LLM JSON output: `validation/llm-output-solution-[id]-claims.json`
- Markdown summary: `validation/solution-[id]-[name-slug]-claims.md`

---

### Step 2.5: Source Document Expansion (30-40 min for 3-5 solutions)

**Purpose:** After exhausting claims, process source documents to discover additional ontology-relevant information. This reveals:
- What % of ontology scope our current claims cover
- What degree of context expansion the ontology enables for future research

#### A. Get Source Documents for Each Solution

For each solution from Step 1, identify unique source documents:

```sql
-- Get unique source documents for a solution
SELECT DISTINCT
  d.id,
  d.title,
  d.document_type,
  d.source_organization,
  d.pdf_url
FROM documents d
JOIN claims c ON d.id = c.document_id
WHERE c.solution_id = '[solution_id]'
  AND d.processing_status = 'complete'
ORDER BY d.document_type, d.title;
```

For each document, get relevant excerpts (not full text - too expensive):
- Introduction/summary section
- Sections mentioning the solution
- Planning/governance sections
- Results/outcomes sections

#### B. LLM Prompt for Document Expansion

For each source document, call LLM with:

**System context:**
- Complete ontology (19 types, 30 relationships)
- **Already-mapped claims** from Step 2 for this solution
- Focus: Find ontology-relevant info NOT captured in existing claims

**User prompt:**
```
Analyze this source document to find additional ontology-relevant information beyond what was already extracted as claims.

SOLUTION: [name]
LOCATION: [city, country]

ALREADY EXTRACTED CLAIMS:
[List of claim texts already processed in Step 2]

SOURCE DOCUMENT EXCERPT:
[Document title, type, organization]
[Relevant sections - intro, solution mentions, planning, outcomes]

ONTOLOGY:
[types and relationships from draft-v0.json]

TASK:
Find ontology-relevant information in this document that is NOT covered by the existing claims above.

Focus on:
1. **Planning context**: Policies, actors, barriers, enabling conditions, timeframes
2. **Vulnerability details**: Exposure, sensitivity, adaptive capacity specifics
3. **Infrastructure details**: What infrastructure, capacity, condition, who it serves
4. **Actor coordination**: Multi-stakeholder governance, reporting relationships
5. **Temporal context**: Planning cycles, policy windows, implementation timelines
6. **Exposure quantification**: Affected populations, asset values, vulnerable groups

Output structured JSON:
{
  "document_info": {
    "title": "...",
    "type": "...",
    "organization": "..."
  },
  "expansion_findings": {
    "new_nodes": [
      {
        "type": "Actor",
        "instance": "City Department of Public Works",
        "source": "quote from document",
        "why_not_in_claims": "Actor roles not extracted in current claim types"
      },
      ...
    ],
    "new_relationships": [
      {
        "type": "COORDINATES_WITH",
        "source": "Department A",
        "target": "Department B",
        "source_quote": "...",
        "why_not_in_claims": "Multi-stakeholder coordination not in claim taxonomy"
      },
      ...
    ],
    "enrichment_opportunities": [
      {
        "existing_claim": "Solution reduces flood risk",
        "additional_context": "Document specifies reduces sensitivity by improving drainage capacity for 50,000 residents",
        "ontology_enrichment": "Could add ExposureUnit(50k residents) + SERVES relationship"
      },
      ...
    ]
  },
  "coverage_assessment": {
    "claim_coverage_pct": "estimated % of ontology-relevant info captured in claims",
    "major_gaps": ["Planning context", "Actor coordination", "Temporal details"],
    "well_covered": ["Hazards", "Mechanisms"]
  },
  "temporal_analysis": {
    "temporal_references": [
      {
        "quote": "...",
        "type": "simple_date | planning_cycle | milestone_event | policy_window",
        "reused": "is this temporal reference mentioned multiple times?",
        "relates_to_other_temporal": "does it sequence with other temporal things?"
      }
    ],
    "summary": {
      "total_temporal_refs": N,
      "by_type": {"simple_dates": N, "planning_cycles": N, "milestone_events": N},
      "reused_refs": N,
      "temporal_chains": N
    },
    "design_recommendation": "properties | PlanningCycle node | Event node | hybrid"
  }
}
```

**Key instructions:**
- Don't repeat what's already in claims - focus on NEW ontology-relevant info
- Tag why each finding wasn't in claims (claim type doesn't exist, not prioritized, etc.)
- Quantify coverage: what % of document's ontology-relevant content is in claims?
- Identify enrichment opportunities: where could claims be enhanced?

#### C. Process Document Expansion Outputs

For each document, save:
- Raw LLM JSON: `validation/llm-output-doc-[id]-expansion.json`
- Markdown summary: `validation/doc-[id]-expansion.md`

---

### Step 3: Cross-Solution Analysis (30-40 min)

After processing all solutions (claims + source document expansion), synthesize findings:

#### A. Claim Coverage Analysis (Current Extraction)

**Which node types appeared in claims?**
- Count claims mapped to each node type
- Identify node types with 0 claims (potential over-design OR data gaps)
- Identify node types with many claims but poor fit (ontology issue)

**Which relationship types appeared in claims?**
- Count claims mapped to each relationship type
- Identify relationships with 0 claims
- Identify relationships with awkward fits

**Example output:**
```
CLAIM COVERAGE (across 5 solutions, 87 claims):

Node Coverage:
✅ Hazard: 43 claims (perfect fit)
✅ Solution: 5 claims (good fit)
⚠️  Vulnerability: 7 claims (awkward - sensitivity unclear)
⚠️  Infrastructure: 3 claims (good fit, but IMPROVES vs OPERATES_ON confusion)
❌ ExposureUnit: 0 claims (not in current data)
❌ TimePoint: 1 claim (rare in claim text)
❌ Actor: 0 claims (actors not extracted)

Relationship Coverage:
✅ MITIGATES: 38 claims (perfect fit)
✅ USES_MECHANISM: 12 claims (good fit)
⚠️  REDUCES: 5 claims (works but implicit, not explicit)
⚠️  IMPROVES: 2 claims (confusion with OPERATES_ON)
❌ COORDINATES_WITH: 0 claims
❌ EXPOSES: 0 claims
❌ PARTICIPATES_IN: 0 claims
```

#### B. Document Expansion Analysis (Future Potential)

**Which node types appeared in source docs but NOT in claims?**
- Count new node instances found in document expansion
- Identify ontology-relevant content that current claims miss
- Estimate % coverage: what portion of ontology scope do current claims capture?

**Example output:**
```
DOCUMENT EXPANSION (same 5 solutions, 12 source documents):

New Nodes Found in Docs (not in claims):
✅ Actor: 23 instances across 8 docs
   - Why not in claims: Actor extraction not in current claim taxonomy
   - Examples: "Department of Public Works", "Climate Resilience Office", "Community Board 3"
   
✅ ExposureUnit: 8 instances across 4 docs
   - Why not in claims: Exposure quantification not extracted
   - Examples: "50,000 residents in flood zone", "2,500 low-income households"
   
✅ Policy: 11 instances across 6 docs
   - Why not in claims: Policy context not prioritized
   - Examples: "Green Infrastructure Plan 2020", "Zoning Amendment §74-52"

⚠️  TimePoint: 15 instances across 7 docs
   - Why not in claims: Temporal context mentioned but not structured
   - Examples: "2018-2022 planning cycle", "commissioned in Q2 2020"

New Relationships Found:
✅ COORDINATES_WITH: 12 instances (Actor→Actor collaboration)
✅ PARTICIPATES_IN: 18 instances (Actor→Solution implementation)
✅ EXPOSES: 6 instances (Hazard→ExposureUnit)
✅ SERVES: 8 instances (Infrastructure→ExposureUnit)
⚠️  ISSUED_AT: 9 instances (Policy→TimePoint)

Coverage Estimate:
- Current claims cover ~40-50% of ontology-relevant content in source docs
- Major gaps: Planning context (actors, policies), exposure quantification, temporal details
- Well-covered: Hazards, mechanisms, basic outcomes
```

#### C. Coverage Gap Categories

Synthesize into actionable categories:

1. **Ontology validates, data missing (expand extraction)**
   - Example: Actor nodes - ontology works, just not extracted yet
   - Action: Add actor extraction to claim taxonomy
   
2. **Ontology validates, data exists (enrichment opportunity)**
   - Example: ExposureUnit - docs quantify exposure, claims don't capture it
   - Action: Enhance claim extraction to capture exposure numbers

3. **Ontology issue (design problem)**
   - Example: IMPROVES vs OPERATES_ON confusion even in docs
   - Action: Clarify distinction or merge relationships

4. **Ontology over-designed (not in data)**
   - Example: If TimePoint doesn't appear even in full docs
   - Action: Consider removing or simplifying

5. **Data limitation (not in this doc type)**
   - Example: COORDINATES_WITH might only appear in planning docs, not solution descriptions
   - Action: Note for validation against different doc types

#### B. Fit Quality Distribution

**How many claims mapped cleanly vs awkwardly?**
- Perfect fit: claim → ontology mapping is exact
- Good fit: claim → ontology mapping is clear
- Awkward fit: claim → ontology mapping feels forced
- Missing: claim cannot be mapped to ontology

**Target:** 80%+ perfect/good fit

#### C. Phase 2 Validation

**Focus on Phase 2 additions:**
- **Vulnerability**: Did claims mention vulnerabilities? How? (exposure, sensitivity, adaptive capacity)
- **Infrastructure vs UrbanSystem**: Can we distinguish IMPROVES vs OPERATES_ON from claims?
- **ExposureUnit**: Do claims quantify exposed populations/assets?
- **Temporal relationships**: Do claims reference planning cycles, policy windows?
- **Actor coordination**: Do claims describe multi-stakeholder governance?

**Example findings:**
- ✅ REDUCES relationship: Found in 5 claims, works well
- ⚠️ IMPROVES vs OPERATES_ON: Confusing in 1/3 cases - need clearer distinction
- ❌ ExposureUnit: Not found in claims - may need to extract from different source
- ❌ COORDINATES_WITH: Not found in claims - may be in planning docs, not solution descriptions

#### D. Integrated Gap Summary

Create prioritized list using both claim analysis AND document expansion:

1. **Critical ontology gaps (FIX IMMEDIATELY)**
   - Concepts in claims/docs that can't be expressed in ontology
   - Example: "Actor A funded Actor B" - no Actor→Actor funding relationship
   - Action: Add missing node/relationship to ontology

2. **Ontology design issues (REFINE)**
   - Concepts mappable but awkward or confusing
   - Example: IMPROVES vs OPERATES_ON confusion in 30% of cases, even in full docs
   - Action: Clarify distinction, merge, or split

3. **Extraction gaps (EXPAND CLAIM TAXONOMY)**
   - Ontology validates well in docs, but not in current claims
   - Example: Actor nodes appear 23 times in docs, 0 times in claims
   - Action: Add actor extraction to claim types

4. **Enrichment opportunities (ENHANCE EXISTING CLAIMS)**
   - Current claims are valid but docs contain more detail
   - Example: Claims say "reduces flood risk", docs specify "for 50k residents"
   - Action: Enhance claim extraction to capture quantification

5. **Validation success (KEEP AS-IS)**
   - Ontology works well in both claims and docs
   - Example: Hazard, MITIGATES - perfect fit in 95% of cases
   - Action: No changes needed

6. **Deferred/future validation (MONITOR)**
   - Ontology concepts that may appear in different doc types
   - Example: COORDINATES_WITH - might be in planning docs, not solution case studies
   - Action: Validate against planning docs in Sprint 3

---

### Step 4: Recommendations (15 min)

Based on claim analysis, recommend:

**Category 1: Quick Fixes (Sprint 1 - Apr 17)**
- Add missing properties revealed by claims
- Adjust vocabulary values
- Clarify relationship definitions (e.g., IMPROVES vs OPERATES_ON)

**Category 2: Small Refactors (Sprint 1-2)**
- Merge overly-granular nodes that don't appear in claims
- Split under-specified nodes that cause awkward mappings
- Add missing relationships found in claims

**Category 3: Data vs Ontology Issues**
- **Ontology over-designed**: Node/relationship never appears in claims → consider removing
- **Data gap**: Ontology concept is valid but not in current claims → keep for future data
  - Example: ExposureUnit may appear in planning docs, not solution descriptions

**Category 4: Design Validation (Sprint 1 - Based on Temporal Analysis)**
- **TimePoint node vs property vs Event**
  - If <10 temporal refs OR mostly simple dates → Convert to properties
  - If planning cycles reused → Keep as PlanningCycle node (rename from TimePoint)
  - If milestone events with sequences → Replace with Event node
  - If mixed → Hybrid approach (properties + PlanningCycle + Event)

**Category 5: Deferred (Sprint 4 - Corpus Analysis)**
- Vocabulary formalization from 129K claims
- Mechanism taxonomy clustering
- Property standardization

---

## Success Criteria

**Minimum viable validation:**
- ✅ Can map at least 80% of claims to ontology (perfect/good fit)
- ✅ Phase 2 additions appear in either claims OR source documents
- ✅ No more than 3 critical ontology gaps (unmappable concepts in docs)
- ✅ Clear understanding of: ontology issues vs extraction gaps vs data limitations
- ✅ Quantify claim coverage: what % of ontology-relevant content is in current claims?

**Strong validation:**
- ✅ Can map 90%+ of claims to ontology
- ✅ All Phase 2 additions validated with real examples (claims or docs)
- ✅ Zero critical ontology gaps
- ✅ Clear patterns for IMPROVES vs OPERATES_ON, REDUCES vs MITIGATES, etc.
- ✅ Actionable roadmap: which ontology concepts to prioritize for extraction expansion

---

## Deliverables

1. **Sample selection record:** Which solutions, claim counts, sources
2. **Phase 1: Claim analysis:** Claim mappings for each of 3-5 solutions
3. **Phase 2: Document expansion:** New findings from source documents
4. **Cross-solution synthesis:** Coverage analysis (claims vs docs), fit quality, Phase 2 validation
5. **Coverage metrics:** What % of ontology scope do current claims cover?
6. **Recommendations:** Categorized by ontology fixes, extraction expansion, enrichment opportunities
7. **Updated decisions-log.md:** Document validation findings and design changes

**File structure:**
```
packages/ontology/validation/
  sample-selection.md                    # Which solutions we tested
  
  # Phase 1: Claims
  solution-1-[name-slug]-claims.md       # Per-solution claim mappings
  solution-2-[name-slug]-claims.md
  ...
  llm-output-solution-1-claims.json      # Raw LLM claim analysis
  llm-output-solution-2-claims.json
  ...
  
  # Phase 2: Document Expansion
  doc-[id]-expansion.md                  # New findings from each source doc
  llm-output-doc-[id]-expansion.json     # Raw LLM expansion analysis
  ...
  
  # Synthesis
  synthesis.md                           # Coverage analysis: claims vs docs
  recommendations.md                     # Ontology fixes, extraction priorities, enrichment
```

---

## Tools & Resources

### Supabase Queries
Use Supabase MCP tool to query solutions, claims, and documents:
```
mcp__plugin_supabase_supabase__execute_sql
  project_id: "eqfvclhdbrtfyxggjxru"
  query: "[SELECT queries from Step 1 and Step 2.A]"
```

### Ontology Reference
- `packages/ontology/ontology/draft-v0.json` - Complete ontology (19 types, 30 relationships)
- `packages/ontology/decisions-log.md` - Design rationale and Phase 2 decisions
- `packages/ontology/viewer.html` - Visual reference (./start-viewer.sh)

### Claim Data Schema
Check `SCHEMA_CACHE.json` for actual claim table columns:
- `claim_text` - The extracted text
- `claim_type` - hazard_addressed, mechanism, outcome, etc.
- `confidence_score` - Extraction confidence
- `solution_id`, `document_id` - Foreign keys

---

## Time Budget Breakdown (Two-Phase LLM-Assisted)

| Activity | Time | Notes |
|----------|------|-------|
| **Phase 1: Claims** | | |
| Sample selection | 10 min | Query Supabase for solutions with claims |
| Fetch solution+claim data | 10 min | Get complete solution→claim→document chains |
| Script setup | 10 min | Configure LLM calls, test on 1 solution |
| LLM claim analysis | 30-40 min | 6-8 min per solution (parallel if possible) |
| Review claim outputs | 15 min | Spot-check claim mappings |
| **Phase 2: Document Expansion** | | |
| Fetch source documents | 10 min | Get unique docs for sampled solutions |
| LLM document expansion | 30-40 min | 6-8 min per doc (parallel if possible) |
| Review expansion outputs | 15 min | Spot-check new findings vs claims |
| **Synthesis & Analysis** | | |
| Coverage analysis | 15 min | Script generates claim vs doc coverage |
| Manual synthesis | 20 min | Review patterns, Phase 2 validation, coverage gaps |
| Recommendations | 15 min | Categorized action items (ontology vs extraction) |
| **Total** | **2.5-3 hours** | Two-phase reveals extraction gaps! |

---

## Follow-up Actions

After claim validation:

1. **If critical gaps found:** Schedule ontology refinement (Sprint 1)
2. **If minor issues only:** Make quick fixes, update decisions-log.md
3. **If data gaps found:** Note for future extraction improvements
4. **Document learnings:** Add "Decision 11: Validation Findings" to decisions-log.md
5. **Update extraction priorities:** Focus on claim types that validate well

---

## Notes

- **Claim-centric validation:** We're testing ontology against actual extracted claims, not random documents
- **Focus on Phase 2 additions:** Especially Vulnerability, Infrastructure, ExposureUnit, new relationships
- **Distinguish ontology vs data issues:** 
  - Ontology issue: Claims exist but can't be mapped → fix ontology
  - Data gap: Ontology concept valid but not in claims → OK for now, may appear in planning docs
- **Speed over perfection:** 6-8 min per solution is enough to spot major issues
- **Capture both successes and failures:** What works well validates our design decisions
