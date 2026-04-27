# Research Agent Prompt: Extraction Schema Population

## Purpose

This prompt directs the deep research agent to populate the extraction schema with sourced claims organized by ontology dimensions. It extends the existing autonomous research prompt by adding structured output to the extraction schema format.

This prompt is designed to work alongside the existing researcher pipeline — it does NOT replace the tool-calling agent architecture. Instead, it provides instructions for a new output stage that transforms validated claims into a populated extraction schema.

---

## Prompt Template

```
You are populating a structured extraction schema for an urban climate adaptation solution. The schema organizes research findings into seven ontology dimensions, with every value grounded in sourced claims.

## Solution Context

Solution topic: "{solution_topic}"
Initial description: "{quote}"
City: "{city}"
Existing claims: {claims_json}

## Your Task

Transform the validated claims into a populated extraction schema. For each claim:

1. Determine which schema dimension(s) it informs:
   - **identity**: What the solution IS (name, category, actor types, deployment year)
   - **hazards**: What climate threats it addresses
   - **urban_systems**: What part of the city it operates on
   - **mechanisms**: HOW it works (absorb, redirect, harden, monitor, govern, shift_risk, adapt_behavior, restore_regenerate)
   - **implementation**: Deployment context (cities, scale, status, timeline, cost, actors)
   - **evidence**: Outcomes, effectiveness, co-benefits, failure modes
   - **context**: Enabling conditions, barriers, replicability, governance relationships

2. Place the claim in the appropriate field(s) within that dimension

3. Match controlled vocabulary where available:
   - **Solution category**: Use IDs from the solution taxonomy (water, food, buildings, infrastructure, energy, transportation, nature, health, finance, planning_and_monitoring, communication_and_community) and their subcategories
   - **Hazards**: Use IDs from the hazards table (e.g., flash_surface_flood, heat_wave, coastal_flood, drought, cyclone_hurricane_typhoon)
   - **IPCC action type**: structural_physical, social, institutional, ecosystem_based
   - **Actor types**: municipal_government, regional_government, national_government, utility, private_sector, ngo, community, academic, multi_stakeholder, international_organization
   - **Scale**: neighborhood, district, city, regional, national, multi_city
   - **Status**: proposed, scoping, pilot, operational, scaling, completed
   - **Evidence level**: anecdotal, measured, rigorously_evaluated

4. For mechanism of action (free text field), describe HOW the solution works using the seed vocabulary as guidance but not constraint

5. Preserve the exact source text in each claim — do NOT paraphrase

## Claim Object Format

Every claim must include:
```json
{
  "text": "Exact source text — do not paraphrase",
  "source_url": "https://...",
  "source_title": "Document or page title",
  "source_type": "case_library|cdp|academic|government|news|ngo|other",
  "confidence": "measured|modeled|anecdotal|self_reported|expert_assessment",
  "extraction_date": "{current_date}",
  "agent_notes": "Optional: note ambiguity, conflicts, or classification difficulty"
}
```

## Confidence Assignment Rules

- **measured**: Quantitative data from direct measurement or monitoring systems
- **modeled**: Output from simulation, projection, or modeling
- **anecdotal**: Qualitative reports, case descriptions without systematic data
- **self_reported**: CDP data, self-disclosure, organizational claims about own programs
- **expert_assessment**: Professional judgment, consulting reports, expert panels

When a claim's confidence is unclear, default to **anecdotal** and note the ambiguity in agent_notes.

## Handling Multiple Cities

A solution may be deployed across multiple cities. Create separate entries in implementation.cities[] for each deployment, linking city-specific claims to the appropriate city entry.

## Handling Claim Conflicts

When multiple sources provide conflicting information:
1. Record ALL claims — do not discard conflicting evidence
2. Note the conflict in agent_notes on each conflicting claim
3. Do NOT resolve the conflict — that's for human review
4. Prefer measured > modeled > anecdotal > self_reported when assessing overall evidence_level

## Classification Difficulty

If a solution doesn't fit cleanly into the taxonomy:
- Assign the CLOSEST match for controlled vocab fields
- Record the difficulty in classification_difficulty_notes at the top level
- Include a note in agent_notes explaining why the match is imperfect
- These notes drive ontology refinement in Month 2

## Completeness Scoring

After populating all claims, compute completeness per dimension:

```
dimension_completeness = populated_fields / total_fields_in_dimension

Required fields count 2x in the calculation:
  identity: solution_name, solution_category (required)
  hazards: hazards_addressed (required, at least 1)
  urban_systems: systems_affected (required, at least 1)
  mechanisms: primary_mechanism (required)
  implementation: cities (required, at least 1)
  evidence: evidence_level (required)
  context: (no required fields)

overall = weighted_average(all_dimensions)
```

## Synthesis Trigger

After computing completeness:
- If overall ≥ 0.4 and this is the first pass: flag for synthesis attempt (gap identification)
- If overall ≥ 0.7: flag for near-publishable synthesis
- If overall < 0.4: identify the 3 dimensions with lowest completeness and generate research directives

## Research Directives

When gaps are identified, generate specific search queries:

```json
{
  "query": "specific search query text",
  "target_dimension": "evidence",
  "target_field": "outcome_indicators",
  "rationale": "No quantitative effectiveness data found in initial sources"
}
```

## Output Format

Return the complete extraction schema JSON as defined in extraction-schema-v1.json, with all applicable claims placed in their appropriate dimension/field locations.
```

---

## Integration Notes

This prompt is designed for a **post-processing stage** that runs after the existing claim extraction and validation pipeline. The input is the set of validated claims already extracted by the researcher. The output is a populated extraction schema.

In the existing pipeline flow:
```
web_search → scrape_content → extract_claims → validate_claims
                                                       ↓
                                          [NEW] populate_extraction_schema
                                                       ↓
                                          [NEW] assess_completeness
                                                       ↓
                                          [EXISTING] synthesize_narrative
                                          (now takes schema, not raw claims)
```

The synthesis step then uses the populated extraction schema as input instead of raw claims, enabling dimension-aware narrative generation.
