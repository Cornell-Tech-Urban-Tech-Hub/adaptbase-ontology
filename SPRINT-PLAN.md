# Ontology Sprint Plan: Apr 17 - May 15, 2026

**Goal:** Expand, pressure-test, and refine adaptation planning & solution ontologies by incorporating taxonomies and customizing for technology-enabled solutions.

**Cadence:** 4-6 Thursday work sessions through May 15

---

## Existing Knowledge Graph Todos (15 tasks)

### Validation & Quality (4 tasks)
- [ ] Validate ontology v0.3 against real published documents (Wed Apr 16)
- [ ] Validate ontology v0.1 against held-out cases
- [ ] ask LLM to review/rationalize
- [ ] fix C40 hazard taxonomy — heat wave vs extreme hot weather conflict

### Technology Focus (2 tasks)
- [ ] special tech solution extensions? Corpus mining: cluster mechanism free-text into formal taxonomy
- [ ] special tech solution extensions? Extract emergent entities and relationships from 129K claims

### Taxonomy Integration (3 tasks)
- [ ] Map vocabulary bindings to external frameworks
- [ ] how to integrate RCC shocks + stresses taxonomy?
- [ ] indicators: create vocabulary from UAE-Belem adaptation indicators

### Schema & Standardization (2 tasks)
- [ ] Update extraction schema with Phase 2 ontology additions (May 15)
- [ ] review parts of the Adaptation Planning domain that could be standardized

### Implementation/Tooling (4 tasks - DEFER)
- [ ] Ontology Viewer — Design Supabase storage with versioning
- [ ] merge ontology viewer / editor into the admin-cms site
- [ ] ontology viewer — Add vocab viewer functionality (store taxonomies in supabase and manage them there?)
- [ ] Populate Neo4j graph with ontology v1.0

---

## Proposed Sprint Organization

### Sprint 0: Apr 16 (Wed) - **Validation Baseline**
**Not a Thursday, but scheduled**

- [x] Validate ontology v0.3 against real published documents (LLM-assisted script)
  - Run validation script on 5 diverse docs
  - Generate reports on coverage, gaps, Phase 2 validation
  - Identify quick fixes vs. major issues

**Outcome:** Validation report with recommendations

---

### Sprint 1: Apr 17 (Thu) - **Quality & Quick Fixes**
**Theme:** Address validation findings and rationalize design

**Tasks:**
1. Review validation results from Apr 16 test
2. **ask LLM to review/rationalize** - systematic consistency check
3. **fix C40 hazard taxonomy** — heat wave vs extreme hot weather conflict
4. Implement quick fixes from validation (properties, vocabularies)
5. Update decisions-log.md with validation learnings

**Outcome:** Cleaned-up ontology v0.3.1 with validation-driven fixes

---

### Sprint 2: Apr 24 (Thu) - **Technology Solutions Extension**
**Theme:** Customize for technology-enabled solutions

**Tasks:**
1. **special tech solution extensions?** - Design tech classification
   - Technology taxonomy (IoT, sensors, AI/ML, digital twins, automation, data platforms)
   - Technology properties (maturity level, deployment model, data requirements)
   - Tech-specific relationships (POWERED_BY, INTEGRATES_WITH, MONITORS_VIA)
2. **Corpus mining: cluster mechanism free-text** into formal taxonomy
   - Extract mechanism patterns from 129K claims
   - Focus on tech-enabled mechanisms (monitor, predict, automate, optimize)
   - Create controlled mechanism vocabulary
3. Document tech ontology extensions in decisions-log.md

**Outcome:** Technology-extended ontology v0.4

---

### Sprint 3: May 1 (Thu) - **Taxonomy Integration**
**Theme:** Align with major adaptation frameworks

**Tasks:**
1. **review parts of Adaptation Planning domain that could be standardized**
   - ICLEI 5-Milestones (planning process workflow)
   - C40 Impacts Taxonomy (intervention logic, co-benefits)
   - GCoM CRF Common Data Core (city disclosure compatibility)
2. **Map vocabulary bindings to external frameworks**
   - Document mappings in ontology metadata
   - Create crosswalks where needed
3. **how to integrate RCC shocks + stresses taxonomy?**
   - Review RCC taxonomy structure
   - Map to Hazard/Barrier nodes
   - Extend controlled vocabularies
4. **indicators: create vocabulary from UAE-Belem adaptation indicators**
   - Extract indicator taxonomy
   - Map to Indicator node properties
   - Create controlled vocabulary

**Outcome:** Framework-aligned ontology v0.5

---

### Sprint 4: May 8 (Thu) - **Emergence & Validation**
**Theme:** Learn from corpus, validate refinements

**Tasks:**
1. **Extract emergent entities and relationships from 129K claims**
   - What node types appear frequently but aren't in ontology?
   - What relationships are implicit but common?
   - What properties are mentioned repeatedly?
2. **Validate ontology v0.1 against held-out cases**
   - Use cases NOT used in design
   - Test coverage of refined ontology
   - Identify remaining gaps
3. Synthesize all learnings (validation + corpus + held-out)
4. Propose final refinements for v1.0

**Outcome:** Evidence-based refinement proposals

---

### Sprint 5: May 15 (Thu) - **Finalization**
**Theme:** Lock down v1.0 and prepare for implementation

**Tasks:**
1. **Update extraction schema with Phase 2 ontology additions**
   - All Phase 2 nodes (Vulnerability, TimePoint, Infrastructure, ExposureUnit)
   - All Phase 2 relationships (14 new relationships)
   - Tech extensions from Sprint 2
   - Framework alignments from Sprint 3
2. Finalize ontology v1.0
   - Merge all sprint additions
   - Final consistency check
   - Version bump to v1.0
3. Documentation
   - Update decisions-log.md with all sprint decisions
   - Create v0.3 → v1.0 migration guide
   - Update TYPES-EXTRACTION-SUMMARY.md
   - Update RELATIONSHIPS-EXTRACTION-SUMMARY.md
4. Prepare for Neo4j (design graph schema document)

**Outcome:** Production-ready ontology v1.0, updated extraction schema

---

## Deferred to Post-May 15 / Summer

**Viewer/Tooling (4 tasks):**
- Ontology Viewer — Design Supabase storage with versioning
- merge ontology viewer / editor into the admin-cms site
- ontology viewer — Add vocab viewer functionality
- Populate Neo4j graph with ontology v1.0

**Rationale:** Focus sprints on ontology DESIGN, defer implementation tools to summer when you have help.

---

## Success Metrics

**By May 15, we will have:**
- ✅ Validated ontology against real docs + held-out cases
- ✅ Technology-focused extensions for tech-enabled solutions
- ✅ Integration with major frameworks (C40, ICLEI, GCoM, RCC, UAE-Belem)
- ✅ Data-driven mechanism taxonomy from corpus mining
- ✅ Extraction schema updated with all additions
- ✅ Production-ready v1.0 with full documentation

**Quality indicators:**
- 90%+ coverage of diverse document types
- All Phase 2 additions validated in real examples
- Clear tech solution classification
- Framework crosswalks documented

---

## Dependencies

**External resources needed:**
- C40 Impacts Taxonomy (public)
- ICLEI 5-Milestones framework (public)
- GCoM CRF data structure (public via CDP)
- RCC shocks + stresses taxonomy (need to locate)
- UAE-Belem indicators (need to locate)

**Technical:**
- Access to 129K claims in Supabase
- LLM API for corpus mining
- Validation script results from Apr 16

---

## Risk Mitigation

**Risk:** Corpus mining reveals major ontology gaps  
**Mitigation:** Plan for this in Sprint 4, have 2-week buffer before May 15

**Risk:** Framework integration conflicts with existing design  
**Mitigation:** Document as mappings/crosswalks first, only modify ontology if critical

**Risk:** Tech extensions conflict with general solutions ontology  
**Mitigation:** Use inheritance/specialization pattern (TechSolution extends Solution)

---

## Notes

- Sprint plan assumes ~4-6 hours per Thursday session
- Each sprint builds on previous (sequential dependencies)
- Validation (Sprint 0) informs all subsequent work
- May 15 is hard deadline (matches strategic plan milestone)
