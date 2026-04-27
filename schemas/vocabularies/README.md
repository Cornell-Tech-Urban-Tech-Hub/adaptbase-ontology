# Vocabulary Integration Strategy

## Overview

Vocabulary files in this directory are the **authoritative source** for controlled terms used in the extraction schema. The extraction schema references these vocabularies rather than duplicating them as inline enums.

## Philosophy: Vocabularies as Reference, Not Constraints

**Design Decision**: We use external vocabulary files as **guidance** rather than rigid schema constraints, for several reasons:

1. **Rich Taxonomies**: Full vocabularies contain detailed hierarchies (e.g., 30+ specific hazards organized into 13 categories) that would be verbose as inline enums
2. **Flexibility**: Vocabularies can evolve independently from the schema structure
3. **LLM-Friendly**: Agents can select the most appropriate terms from rich vocabularies rather than being limited to simplified enums
4. **Standards Integration**: Vocabularies reference external standards (IPCC, CityGML) that may be updated
5. **Domain Expertise**: Domain experts can update vocabularies without modifying schema

## Vocabulary Files

### Table-Backed Vocabularies

These vocabularies sync with Supabase database tables:

- **`hazards.json`**: Climate hazards taxonomy
  - Source: `hazards` table (is_active = true)
  - Structure: 13 categories, 30+ specific hazards
  - Usage: `hazards.hazards_addressed[].hazard_id` and `hazard_category`

- **`solution-categories.json`**: Solution taxonomy
  - Source: `solution_taxonomy` table (is_active = true)
  - Structure: 7 categories (Water, Food, Buildings, etc.), 80+ subcategories
  - Usage: `identity.solution_category.category_id` and `subcategory_id`

### Enum-Based Vocabularies

Controlled vocabularies not backed by database tables:

- **`crf-goals.json`**: City Resilience Framework 2024 goals taxonomy
  - Source: City Resilience Framework 2024 v2 (Resilient Cities Network)
  - Structure: 4 dimensions, 22 resilience goals
  - Usage: `outcomes.resilience_goals[].goal_id`
  - Dimensions: Health & Wellbeing, Economy & Society, Infrastructure & Environment, Leadership & Planning

- **`urban-systems.json`**: Hierarchical urban sectors taxonomy
  - Source: Advanced urban systems classification for climate adaptation
  - Structure: 7 sectors, 20+ subsectors, 50+ granular systems
  - Usage: `urban_systems.systems_affected[].system_id`, `sector`, `subsector`
  - Hierarchy: Sector → Subsector → System (e.g., Hydrological Water → Stormwater Management → Bioswales)
  - Enables interdependency analysis and critical bottleneck identification

- **`enums.json`**: Various controlled vocabularies
  - IPCC action types
  - Actor types (municipal_government, utility, ngo, etc.)
  - Deployment scales (site, building, neighborhood, city, etc.)
  - Implementation status
  - Evidence levels
  - Enabling condition types
  - Co-benefit categories
  - Financing models (grants, PPP, green bonds, climate funds, etc.)
  - Financing status (fully funded, seeking funding, feasibility stage, etc.)
  - Claim source types
  - Mechanism seed vocabulary (guidance, not constraint)

## Integration Pattern

### 1. Schema References Vocabularies

The extraction schema includes **descriptions** that point to vocabulary files:

```json
{
  "hazard_id": {
    "type": "string",
    "description": "Specific hazard ID from vocabularies/hazards.json (e.g., 'coastal_flood', 'heat_wave')"
  },
  "hazard_category": {
    "type": "string",
    "description": "Hazard category from vocabularies/hazards.json. Valid values: chemical_change, extreme_temperature_cold, ..."
  }
}
```

### 2. Agents Use Vocabularies for Selection

**Crawler** (discovery phase):
- References vocabularies when initially classifying solutions
- Selects best-matching category and subcategory
- Stores in `crawler.category` and `crawler.subcategory`

**Researcher** (enrichment phase):
- Loads vocabulary files at initialization
- Uses vocabularies to tag claims with appropriate terms
- Places claims into extraction schema dimensions using controlled vocab IDs

### 3. Post-Extraction Validation

After extraction is complete, validation checks:

1. **Term Exists**: Does the extracted term exist in the vocabulary?
2. **Correct Hierarchy**: If using hierarchical vocab (hazards, solutions), is the parent-child relationship valid?
3. **Consistent Usage**: Are terms used consistently across the extraction?

**Important**: Validation is **advisory**, not blocking. Invalid terms are flagged for review, but extraction proceeds. This allows handling of:
- Edge cases not yet in vocabularies
- New terms that need to be added
- Genuine classification ambiguity

## Validation Rules

### Strict Validation (Must Pass)

These fields must match vocabulary exactly:

- `solution_category.category_id` → must exist in `solution-categories.json`
- `solution_category.subcategory_id` → must be valid child of category
- `ipcc_action_type.values[]` → must match `enums.json` values
- `implementing_actor_types.values[]` → must match `enums.json` values

### Advisory Validation (Flag But Don't Block)

These fields should match vocabulary but mismatches are flagged:

- `hazards_addressed[].hazard_id` → should exist in `hazards.json`
- `hazards_addressed[].hazard_category` → should match hazard's category
- `urban_systems.systems_affected[].system_category` → should match category list

### Free Text (No Validation)

These fields use seed vocabularies as guidance only:

- `mechanisms.primary_mechanism.value` → seed vocab suggests terms but accepts free text
- `mechanisms.secondary_mechanisms[].value` → guidance, not constraint

## Updating Vocabularies

### When Vocabularies Change

1. **Update vocabulary file** (hazards.json, solution-categories.json, enums.json)
2. **Update corresponding database table** if table-backed (hazards, solution_taxonomy)
3. **No schema change required** - vocabularies are referenced, not embedded
4. **Agents automatically use new terms** on next extraction

### Adding New Terms

1. Add to vocabulary file with proper structure:
   ```json
   {
     "id": "new_term_id",
     "name": "Human Readable Name",
     "description": "Optional explanation"
   }
   ```
2. If table-backed, also add to database
3. Document in vocabulary file's `_source` or `_note` fields

### Deprecating Terms

1. Mark as `"deprecated": true` in vocabulary file
2. Add `"deprecated_reason"` and `"use_instead"` fields
3. Keep in vocabulary for backwards compatibility
4. Validation warns but doesn't fail

## Syncing with Database Tables

For table-backed vocabularies (`hazards.json`, `solution-categories.json`):

**Source of Truth**: Database tables (`hazards`, `solution_taxonomy`)

**Sync Process**:
1. Vocabulary files are exports from database
2. Update database via migrations or admin tools
3. Re-export vocabulary files after database changes
4. Vocabulary files used by agents for local reference (avoid DB round-trips)

**Export Command** (to be implemented):
```bash
uv run python scripts/export_vocabularies.py
```

## Examples

### Example 1: Hazard Selection

Vocabulary has rich hierarchy:
```json
{
  "id": "flood",
  "name": "Flood",
  "hazards": [
    { "id": "coastal_flood", "name": "Coastal flood" },
    { "id": "flash_surface_flood", "name": "Flash/surface flood" },
    { "id": "groundwater_flood", "name": "Groundwater flood" },
    { "id": "river_flood", "name": "River flood" }
  ]
}
```

Agent extracts specific hazard:
```json
{
  "hazard_id": "coastal_flood",
  "hazard_name": "Coastal flood",
  "hazard_category": "flood",
  "is_primary": true
}
```

Validation: ✅ `coastal_flood` exists in vocabulary, `flood` is correct parent

### Example 2: Mechanism (Free Text)

Vocabulary provides guidance:
```json
{
  "id": "absorb",
  "name": "Absorb",
  "description": "Buffer, attenuate, or absorb the impact"
}
```

Agent uses vocabulary term:
```json
{
  "primary_mechanism": {
    "value": "absorb",
    "claim_ids": ["claim-uuid"]
  }
}
```

Or agent uses descriptive text:
```json
{
  "primary_mechanism": {
    "value": "Bioswales capture and filter stormwater runoff through engineered soil media",
    "claim_ids": ["claim-uuid"]
  }
}
```

Validation: ✅ Both are valid - mechanism is free text guided by seed vocabulary

## Integration with Crawler and Researcher

### Crawler Integration

**Initialization**:
```python
# Load vocabularies at startup
hazards_vocab = load_json('packages/ontology/schemas/vocabularies/hazards.json')
categories_vocab = load_json('packages/ontology/schemas/vocabularies/solution-categories.json')
```

**Classification**:
```python
# Use vocabulary to classify discovered solution
category, subcategory = classify_solution(
    quote=seed.quote,
    categories_vocab=categories_vocab
)

# Validate classification
if not validate_category(category, subcategory, categories_vocab):
    log.warning(f"Classification mismatch: {category}/{subcategory}")
```

**Storage**:
```python
# Store in crawler bundle with initial classification
solutions.crawler = {
    "category": category,
    "subcategory": subcategory,
    # ... other discovery metadata
}
```

### Researcher Integration

**Initialization**:
```python
# Load vocabularies for claim tagging
vocab_loader = VocabularyLoader('packages/ontology/schemas/vocabularies/')
hazards_vocab = vocab_loader.load('hazards')
categories_vocab = vocab_loader.load('solution-categories')
enums_vocab = vocab_loader.load('enums')
```

**Claim Placement**:
```python
# When placing claim in extraction schema, use vocabulary
def place_hazard_claim(claim, extraction_schema):
    # Extract hazard mention from claim
    hazard_mention = extract_hazard(claim.text)

    # Find best match in vocabulary
    hazard = find_best_match(hazard_mention, hazards_vocab)

    if hazard:
        extraction_schema['hazards']['hazards_addressed'].append({
            'hazard_id': hazard['id'],
            'hazard_name': hazard['name'],
            'hazard_category': hazard['category'],
            'claim_ids': [claim.id]
        })
    else:
        log.warning(f"Hazard not found in vocabulary: {hazard_mention}")
```

**Validation**:
```python
# Post-synthesis validation
def validate_extraction(extraction_schema, vocabularies):
    errors = []
    warnings = []

    # Validate hazards
    for hazard in extraction_schema['hazards']['hazards_addressed']:
        if not hazard_exists(hazard['hazard_id'], vocabularies['hazards']):
            warnings.append(f"Unknown hazard: {hazard['hazard_id']}")

        if not category_matches(hazard['hazard_id'], hazard['hazard_category'], vocabularies['hazards']):
            errors.append(f"Category mismatch: {hazard['hazard_id']} -> {hazard['hazard_category']}")

    return errors, warnings
```

## Benefits

1. **Flexibility**: Vocabularies evolve without schema changes
2. **Richness**: Full taxonomies available to agents (30+ hazards, not just 13 categories)
3. **Standards Alignment**: Easy to sync with external standards (IPCC, CityGML)
4. **Domain Expert Friendly**: Non-technical experts can update vocabularies
5. **Quality Control**: Validation flags mismatches without blocking extraction
6. **Interoperability**: Vocabulary files can be shared across systems

## Trade-offs

**Strengths**:
- Rich vocabularies for agent selection
- Flexible evolution of terms
- Standards integration

**Weaknesses**:
- Validation is post-extraction, not schema-enforced
- Agents can select invalid terms (caught in validation)
- Requires loading external files

**Decision**: We chose flexibility and richness over rigid enforcement, with advisory validation to maintain quality.

---

## Vocabulary Sources & Provenance

This section documents the authoritative sources for each controlled vocabulary, ensuring traceability and scientific rigor.

### Table-Backed Vocabularies

#### hazards.json
- **Source**: C40/Arup Climate Hazard Typology for urban climate adaptation
- **Document**: https://www.c40.org/wp-content/static/researches/images/33_C40_Arup_Climate_Hazard_Typology.original.pdf
- **Structure**: 13 hazard categories, 30+ specific hazards
- **Sync**: Synced from Supabase `hazards` table (is_active = true)
- **Updates**: Table is canonical; vocabulary file syncs from it
- **Rationale**: C40 typology is the authoritative standard for urban climate hazards, developed specifically for city-level adaptation planning

#### solution-categories.json
- **Source**: Supabase `solution_taxonomy` table
- **Structure**: 7 main categories, ~100 subcategories
- **Sync**: Synced from `solution_taxonomy` table (is_active = true)
- **Updates**: Table is canonical; vocabulary file syncs from it
- **Categories**: Water, Food, Buildings, Infrastructure, Energy, Transportation, Nature-based Solutions
- **Rationale**: Organizes solutions by what they ARE (identity), not what they do (expressed via hazard/mechanism relationships)

### External Standard Vocabularies

#### crf-goals.json
- **Source**: City Resilience Framework 2024 v2 (Resilient Cities Network)
- **Document**: `packages/ontology/resources/city-resilience-framework-2024v2.pdf`
- **Structure**: 4 dimensions, 22 resilience goals
- **Dimensions**:
  - Health & Wellbeing (6 goals)
  - Economy & Society (5 goals)
  - Infrastructure & Environment (5 goals)
  - Leadership & Planning (6 goals)
- **Sync**: External reference standard; no database table
- **Updates**: Updated when CRF releases new versions
- **Rationale**: CRF is the leading global framework for urban resilience assessment, used by 100+ cities worldwide

#### resilience-attributes.json
- **Source**: ARUP City Resilience Index / CDP Cities Adaptation Disclosure
- **Structure**: Flat list of 19 resilience attributes
- **Sync**: External reference standard; no database table
- **Usage**: `mechanisms.resilience_attributes[].attribute_id`
- **Added**: Schema v1.1 (2026-03-28)
- **Rationale**: CDP `action_resilience_attributes` field is a closed enum of 19 values from the ARUP City Resilience Index, describing capacity-building approaches. 80% populated on CDP actions (4,419/5,552). Orthogonal to mechanism seed vocabulary (which describes physical function like absorb/redirect/harden).

### Custom Analytical Vocabularies

#### urban-systems.json
- **Source**: Custom hierarchical taxonomy for climate adaptation interdependency analysis
- **Construction**: Generated using Google AI Studio (anthony@starcitygroup.us account) on March 3, 2026 around 6:00 PM EST
  - **Note**: Original chat history is currently missing from Google AI Studio for unknown reasons. Anthony will attempt to recover it if it appears in the account's chat history log.
  - Prompt requested sophisticated, multi-tiered breakdown of urban sectors as interconnected physical, ecological, and socio-economic systems
- **Structure**: 7 sectors → 20+ subsectors → 50+ granular systems
- **Sectors**:
  1. Built Environment & Land Use
  2. Mobility & Transport Networks
  3. Hydrological & Water Infrastructure
  4. Energy & Telecommunications
  5. Urban Ecology & Natural Capital
  6. Socio-Economic & Public Health Systems
  7. Governance, Policy & Finance
- **Sync**: Custom taxonomy (no external standard)
- **Updates**: Evolved through ontology research
- **NOT from CityGML**: CityGML (OGC standard) is a 3D geometric model for city visualization (buildings, bridges, terrain). Our taxonomy classifies **functional urban systems** for adaptation analysis, not physical geometry.
- **Rationale**: Enables precise classification of where solutions operate and what they protect. Example: "Elevated transformer pads" → Energy & Telecom > Energy Transmission > Substations. This specificity enables interdependency queries ("Which solutions protect substations during floods?") that would be impossible with flat categorization.
- **Design Philosophy**: Views urban sectors as interconnected physical, ecological, and socio-economic systems rather than spatial silos. Supports cascading failure analysis (e.g., flooded substations affecting hospital power and cellular networks).

#### enums.json
- **Sources**: Multiple (compilation from various standards and databases)
- **Content**:
  - **IPCC AR6 action types**: From IPCC AR6 Chapter 14 adaptation action typology (structural/physical, social, institutional, ecosystem-based)
  - **Actor types**: Derived from case library and CDP data analysis (municipal_government, utility, ngo, etc.)
  - **Deployment scales**: Standard spatial scales (site, building, neighborhood, district, city, regional, national, multi_city)
  - **Implementation status**: Common project lifecycle stages (proposed, scoping, pilot, operational, scaling, completed)
  - **Evidence levels**: Epistemological hierarchy (anecdotal, measured, rigorously_evaluated)
  - **Financing models**: From CDP project_financing_model field (grants, PPP, green bonds, climate funds, etc.)
  - **Financing status**: From CDP project_financing_status field (fully_funded, seeking_funding, feasibility_stage, etc.)
  - **Co-benefit categories**: Aligned with CDP action_cobenefits (economic, public_health, environmental, social, governance, mitigation)
  - **Enabling condition types**: Common barrier/enabler categories (regulatory, financial, technical, social, institutional, political)
  - **Mechanism seed vocabulary**: Conceptual framework for adaptation mechanisms (absorb, redirect, harden, monitor, govern, shift_risk, adapt_behavior, restore_regenerate) - guidance for free text, not constraint
  - **Governance relationships**: From student ontology schema (MANDATES, FACILITATED_BY, ISSUED_BY, IMPLEMENTS, HINDERED_BY, CONSTRAINED_BY)
- **Sync**: Multi-source; updated as standards evolve
- **Rationale**: Consolidates commonly-used controlled terms that don't warrant separate vocabulary files

### Maintenance & Updates

**Syncing from Database Tables**:
```bash
# Hazards and solution categories sync from Supabase
# Run after table updates:
cd packages/admin-cms
uv run python ../../scripts/sync_vocabularies.py
```

**External Standard Updates**:
- Monitor CRF releases for new goal versions
- Check C40/Arup for hazard typology updates
- Review IPCC reports for action typology refinements

**Custom Taxonomy Evolution**:
- Urban systems taxonomy evolves through ontology research
- Changes should be documented in git commit messages
- Major revisions require updating this documentation

**Version Control**:
- All vocabulary files are version-controlled
- Breaking changes require schema version bump
- Non-breaking additions (new terms) can be made without version change

---

## Schema Changelog

### v1.1 (2026-03-28)
- **Added** `resilience-attributes.json` vocabulary (19 ARUP City Resilience Index attributes from CDP data)
- **Added** `mechanisms.resilience_attributes` array to extraction schema
- **Fixed** CDP importer: use EN fields for `action_cobenefits` and `project_area`
- **Fixed** CDP importer: quote truncation extended from 200 to 1000 characters
- **Added** CDP importer harvesting: region, financing_status, investment_needed, local currency cost
