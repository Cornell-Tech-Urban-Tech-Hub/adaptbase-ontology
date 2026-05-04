# Synthesis Prompt: Extraction Schema → Narrative Report

## Purpose

Transform a populated extraction schema into a structured narrative markdown report. This replaces the existing narrative_synthesis_prompt.txt by taking a schema organized by ontology dimensions instead of a flat list of claims.

Supports three modes:
1. **Gap identification** (~40% completeness) — draft with explicit gap markers
2. **Near-publishable** (~70% completeness) — full draft, minor gaps flagged
3. **Final synthesis** — publishable report

---

## Prompt Template

```
You are synthesizing a research report about an urban climate adaptation solution from a structured extraction schema. The schema contains sourced claims organized by seven ontology dimensions.

**CURRENT YEAR: {current_year}**
**SYNTHESIS MODE: {mode}** (gap_identification | near_publishable | final)

## Extraction Schema

{schema_json}

## Dimension-to-Section Mapping

Transform the schema dimensions into narrative sections using this mapping:

### Section 1: Solution Overview
**Sources**: identity + hazards + mechanisms.primary_mechanism
**Content**: 2-3 sentences describing what this solution is, what climate hazards it addresses, and its primary mechanism of action. Use the solution_description claims and hazard claims.

### Section 2: Technical Components
**Sources**: mechanisms.technical_components + mechanisms.secondary_mechanisms
**Content**: Paragraph covering hardware, software, design standards, and data inputs. Each technical component should be described with its supporting claims.

### Section 3: Implementation Details
**Sources**: implementation (cities, key_actors, timeline, cost, scale_of_deployment, implementation_status)
**Content**: Paragraph covering where it's deployed, who implemented it, when, at what cost, and at what scale. Include all city-specific deployment details.

### Section 4: Benefits and Impacts
**Sources**: evidence (outcome_indicators, co_benefits, primary_beneficiaries)
**Content**: Paragraph covering quantitative outcomes, operational benefits, and co-benefits. Prioritize measured evidence over anecdotal.

### Section 5: Challenges and Limitations
**Sources**: context.barriers + evidence.failure_modes
**Content**: Paragraph covering known barriers and failure modes. If no claims exist for this section, OMIT it entirely (do not fabricate challenges).

### Section 6: Replicability and Scaling
**Sources**: context.replicability + context.enabling_conditions + implementation.scale_of_deployment
**Content**: Paragraph covering what conditions enable this solution, how transferable it is, and what governance arrangements support it. Include context.governance_relationships if populated.

## Citation Rules

1. Build a citation map from ALL claims across all dimensions:
   - Deduplicate by source_url — one citation number per unique URL
   - Number sequentially as they first appear in the narrative

2. Cite after the period at end of sentence: "statement.[^1]"
   - Maximum 3 citations per sentence
   - Distribute claims across multiple sentences

3. Generate a Sources section at the end:
   ```
   [^1]: [Source Title](url)
   [^2]: [Source Title](url)
   ```

## Gap Handling (by synthesis mode)

### gap_identification mode (completeness ~40%)
For dimensions below 0.3 completeness, insert explicit gap markers:

```
[GAP: {dimension}.{field} — {description}. Suggested search: "{query}"]
```

Example:
```
[GAP: evidence.outcome_indicators — No quantitative effectiveness metrics found. Suggested search: "solution_name effectiveness evaluation metrics"]
```

After the narrative, output a research directives section:

```
## Research Directives

The following gaps should be addressed in the next research iteration:

1. **evidence.outcome_indicators** (HIGH) — No quantitative effectiveness data found
   - Suggested query: "{solution_name} evaluation results metrics"
   - Suggested query: "{solution_name} impact assessment"

2. **implementation.cost** (MEDIUM) — No cost information found
   - Suggested query: "{solution_name} cost budget funding"
```

### near_publishable mode (completeness ~70%)
Insert softer gap markers only for critical missing fields:

```
Further research could strengthen this analysis with [specific missing information].
```

Do NOT include a research directives section.

### final mode
No gap markers. Omit sections with no supporting claims rather than flagging gaps.

## Anti-Fabrication Rules (CRITICAL)

1. **Claim-only content**: Every factual statement MUST trace to a specific claim in the schema
2. **No extrapolation**: Do NOT infer beyond what claims explicitly state
3. **No external knowledge**: Do NOT add information from training data
4. **Empty sections**: If no claims support a section, OMIT it (don't fabricate)
5. **Preserve specificity**: Include ALL numbers, dates, names, metrics from claims

## Temporal Awareness

- Use past tense for completed events with dates before {current_year}
- Use present tense for ongoing capabilities and current operations
- Check claim text for temporal markers before choosing tense

## Writing Style

- Flowing paragraphs, not bullet points
- 80%+ of narrative about the SPECIFIC solution (not generic climate context)
- Varied language — avoid repeating the solution name; use "this approach", "the system", "the initiative"
- Solution-focused: If you find yourself writing about a city's general climate plan, STOP and refocus

## Completeness Assessment Output

After the narrative, output a JSON block with:

```json
{
  "synthesis_mode": "gap_identification|near_publishable|final",
  "completeness_at_synthesis": {
    "identity": 0.0,
    "hazards": 0.0,
    "urban_systems": 0.0,
    "mechanisms": 0.0,
    "implementation": 0.0,
    "evidence": 0.0,
    "context": 0.0,
    "overall": 0.0
  },
  "total_claims_used": 0,
  "total_unique_sources": 0,
  "sections_populated": ["Solution Overview", "Technical Components", ...],
  "sections_omitted": ["Business Analysis"],
  "quality_assessment": "Brief assessment of whether this is publishable",
  "gaps_identified": [
    {
      "dimension": "evidence",
      "field": "outcome_indicators",
      "gap_description": "...",
      "priority": "high|medium|low"
    }
  ],
  "research_directives": [
    {
      "query": "...",
      "target_dimension": "...",
      "target_field": "..."
    }
  ]
}
```

## Output Format

Return:
1. The narrative markdown report (sections as defined above)
2. The completeness assessment JSON block
```

---

## Integration Notes

This prompt replaces the existing `narrative_synthesis_prompt.txt` for the ontology-aware pipeline. The key differences:

| Current Pipeline | Ontology Pipeline |
|---|---|
| Input: flat list of validated claims | Input: populated extraction schema (7 dimensions) |
| Output: narrative markdown only | Output: narrative + completeness assessment + gap directives |
| Single synthesis call | Multiple synthesis calls (gap_id → near_pub → final) |
| No gap tracking | Explicit gap markers and research directives |
| Sections hardcoded | Sections derived from dimension mapping |

The existing `narrative_synthesis_prompt.txt` continues to work for the current pipeline. This prompt is for the ontology-aware pipeline that will progressively replace it.
