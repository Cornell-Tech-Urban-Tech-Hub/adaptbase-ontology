# Resilience Ontology Build — Working Brief for Claude Code

## Context

I'm building a unified ontology for the **Resilience Scanner** knowledge graph. The ontology needs to cover two linked domains:

1. **Adaptation planning** — the process, actors, governance, plans, commitments, timelines
2. **Adaptation solutions** — the interventions themselves: what they do, where, against which hazards, at what cost, with what evidence

## What I'm starting with

- **~200 deep-researched case studies** of adaptation solutions (curated, with source documents behind every claim)
- **Climate adaptation plans** that reference those cases
- **Source documents** used as evidence in the cases
- **An existing planning-domain ontology** built by a graduate student (covers planning but not solutions in depth)
- **Several controlled vocabularies** I want to bind to (e.g., UNDRR hazard taxonomy, IPCC AR6 WG2 terms, whichever intervention typology we settle on)

## What I want from you (Claude Code)

Work with me as an **extraction-and-proposal partner**, not an autonomous agent. I make the ontology decisions; you do the tedious transcription, clustering, and alignment work fast enough that I can make more decisions per day. Every output should be saved to a file, version-controlled, and re-runnable.

## Repository layout

Please set up this structure in the working directory:

```
resilience-ontology/
├── cases/                      # Source case studies (markdown or JSON, as I provide them)
│   └── raw/                    # Original files
├── sources/                    # Source documents referenced by cases
├── extractions/                # Per-case structured extractions (one JSON file per case)
│   ├── v0/                     # First pass with template v0
│   ├── v1/                     # After template revision
│   └── ...
├── templates/                  # Extraction prompt templates (versioned)
│   ├── extraction-template-v0.md
│   ├── extraction-template-v1.md
│   └── ...
├── ontology/                   # The ontology itself
│   ├── draft-v0.json           # Machine-readable ontology
│   ├── draft-v0.md             # Human-readable documentation
│   ├── types.json              # Node/entity types
│   ├── relationships.json      # Edge types
│   ├── vocabularies.json       # Bound controlled vocabularies
│   └── decisions-log.md        # Why we made each call
├── alignment/                  # Mappings to student ontology and external vocabs
│   ├── student-ontology-map.md
│   ├── undrr-hazard-map.json
│   └── ...
├── holdout/                    # Cases held out for stress testing
│   └── extraction-results/
└── README.md
```

The ontology JSON files should use a simple, viewer-friendly schema (see "Ontology JSON schema" below) so I can load them into an HTML ontology viewer.

---

## The process — five phases

### Phase 1: Build the extraction template (Day 1)

**Goal:** a prompt template that, given one case + its source documents, produces a structured JSON extraction capturing every entity, claim, relationship, property, and provenance link.

**Steps:**

1. Ask me to paste or point you at **one representative case** I know well.
2. Draft `templates/extraction-template-v0.md` — a prompt that instructs Claude (the model) to extract:
   - **Entities**: with type guess, canonical name, aliases, source span
   - **Claims**: subject, predicate, object, qualifiers (time, place, conditions), confidence, source span
   - **Relationships**: between extracted entities, typed
   - **Properties**: attached to entities (cost, timeframe, scale, etc.)
   - **Provenance**: every claim and property must cite a source document + span
3. Run the template against the one case and show me the JSON.
4. Iterate with me on the template until the output matches what I'd have written by hand. Expect 3–6 iterations. **This is the most important prompt in the project — do not rush it.**
5. Save the final version as `templates/extraction-template-v1.md` and commit.

**Do not proceed to Phase 2 until I explicitly approve the template.**

### Phase 2: Batch extraction on 15–20 cases (Day 2)

**Goal:** get a stable batch of extracted cases to use as evidence for type induction.

**Steps:**

1. Ask me which 15–20 cases to use. Favor diversity across hazard types, intervention categories, geographies, and plan sources.
2. Run the Phase 1 template against each case. Save results to `extractions/v1/<case-id>.json`.
3. Generate a **batch review report** at `extractions/v1/REVIEW.md` that lists, per case:
   - Entity count by guessed type
   - Any extraction failures or warnings
   - Any entities the model flagged as uncertain
   - Any claims that lacked source spans (these should be flagged, not silently dropped)
4. We review the batch together. Where the template broke, we revise it and re-run. Do not fix individual extractions by hand — fix the template and rerun the batch. Bump version to v2 if we revise.

### Phase 3: Type induction and clustering (Day 3)

**Goal:** propose a draft type system grounded in the actual extracted evidence.

**Steps:**

1. Load all extractions from `extractions/v<latest>/`.
2. Cluster entities across cases. Propose **canonical types** with:
   - Suggested name
   - Definition (1–2 sentences)
   - Observed properties (which showed up, how often)
   - Evidence (list of case IDs + entity names that justify the type)
   - Open questions / ambiguities for me to resolve
3. Do the same for **relationships** (edges): propose edge types with source/target constraints and evidence.
4. Flag entities that could be modeled either as a property of another type OR as a type in their own right. These are the most important decisions — surface them explicitly.
5. Write the draft to `ontology/draft-v0.json` (machine-readable, see schema below) and `ontology/draft-v0.md` (human-readable).
6. Log every non-obvious call in `ontology/decisions-log.md` with: the question, the options considered, the call made, the reasoning. **This log is as important as the ontology itself.**

**I make the final calls on all type decisions. Your job is to propose with evidence, not decide.**

### Phase 4: Alignment with student ontology and external vocabularies (Day 4)

**Goal:** reconcile the draft with existing work and bind to standard vocabularies.

**Steps:**

1. Ask me to provide the student's planning ontology and the controlled vocabularies I want to bind to.
2. Produce `alignment/student-ontology-map.md` with:
   - Types in both (aligned, with any naming differences)
   - Types only in the student ontology (evaluate for inclusion)
   - Types only in our draft (evaluate for inclusion in the unified ontology)
   - Conflicts in definition or scope (flag for my decision)
3. For each external vocabulary (UNDRR, IPCC, etc.), produce a mapping file in `alignment/` that binds our draft types/properties to the canonical terms. Where we need a term that doesn't exist in any vocabulary, flag it for my decision and note whether to invent or defer.
4. **Be ruthless about reuse.** Prefer binding to an existing term over inventing a new one. Flag any case where you had to invent.
5. Update `ontology/draft-v0.json` to include vocabulary bindings on relevant types/properties.

### Phase 5: Stress test against held-out cases (Day 5)

**Goal:** validate the ontology by extracting cases it wasn't built from.

**Steps:**

1. Ask me to pick **5 cases** we didn't use in Phases 2–4. Copy them to `holdout/`.
2. Extract each held-out case against the current ontology (not free-form — constrained to our types).
3. For each case, produce a report at `holdout/extraction-results/<case-id>.md` covering:
   - What extracted cleanly
   - What required stretching a type or inventing a new one
   - What couldn't be represented at all
   - Proposed ontology changes (if any)
4. Aggregate findings into `holdout/STRESS-TEST-SUMMARY.md`.
5. We decide together: accept the ontology as v1.0, or loop back to Phase 3/4 for revisions.

---

## Ontology JSON schema (viewer-compatible)

Use this shape for `ontology/draft-v*.json` so I can load it into the HTML ontology viewer:

```json
{
  "version": "0.1",
  "updated": "ISO-8601 timestamp",
  "domains": ["adaptation-planning", "adaptation-solutions"],
  "types": [
    {
      "id": "Intervention",
      "label": "Intervention",
      "domain": "adaptation-solutions",
      "definition": "A specific action or project undertaken to reduce vulnerability or increase adaptive capacity against a climate hazard.",
      "properties": [
        {"id": "name", "type": "string", "required": true},
        {"id": "category", "type": "enum", "vocabulary": "intervention-typology"},
        {"id": "cost_estimate", "type": "money-range", "required": false},
        {"id": "timeframe", "type": "duration", "required": false}
      ],
      "vocabulary_bindings": [
        {"vocab": "UNEP-adaptation-taxonomy", "term": "..."}
      ],
      "evidence_cases": ["case-001", "case-014", "case-037"],
      "notes": "Free-text notes / open questions"
    }
  ],
  "relationships": [
    {
      "id": "mitigates",
      "label": "mitigates",
      "source": "Intervention",
      "target": "Hazard",
      "definition": "The intervention is intended to reduce the impact or likelihood of the hazard.",
      "properties": [
        {"id": "evidence_strength", "type": "enum", "values": ["strong", "moderate", "weak", "asserted"]}
      ],
      "evidence_cases": ["case-001", "case-014"]
    }
  ],
  "vocabularies": [
    {
      "id": "UNDRR-hazards",
      "label": "UNDRR Hazard Taxonomy",
      "url": "https://...",
      "bound_to": ["Hazard.type"]
    }
  ]
}
```

Keep the schema **loose** — typed nodes and edges, light constraints, controlled vocabularies only where they matter. We can tighten later; we can't loosen later without migration pain.

---

## Rules of engagement

1. **Save everything to files.** Never produce output only in chat. Every extraction, proposal, and decision goes to a versioned file.
2. **Version the templates.** When we revise the extraction template, bump the version and keep the old one. Same for the ontology drafts.
3. **Propose with evidence.** Every type, relationship, and property you propose should cite the cases that justify it. No evidence, no proposal.
4. **Surface decisions, don't hide them.** When you face a judgment call (property vs. relationship, split vs. merge, invent vs. defer to vocabulary), stop and ask me. Log the decision and its reasoning.
5. **Prefer reuse over invention.** Always check the student ontology and controlled vocabularies before proposing a new term.
6. **Do not auto-proceed between phases.** At the end of each phase, summarize what we did, what's open, and wait for my go-ahead.
7. **Use Sonnet for extraction, not Haiku.** We're doing this once per case, quality matters more than cost. Reserve cost discipline for the runtime researcher we'll build later.
8. **Stop if confused.** If a case doesn't fit cleanly, if two of my decisions contradict, if an external vocabulary seems wrong — stop and ask. Don't paper over ambiguity.

## First action

When I start the session, your first action is to:
1. Set up the repository structure above.
2. Ask me to provide the first representative case for Phase 1.
3. Confirm which model you'll use for extraction (should be Sonnet).

Do not begin extraction until I confirm the case and the setup.
