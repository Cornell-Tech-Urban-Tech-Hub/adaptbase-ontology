MY RESPONSES TO CLAUDE's QUERIES AND RECOMMENDATIONS ARE AFTER EACH SUBSECTION CONTAINED IN BRACES {}
ALSO GENERAL CONSIDERATIONS AT THE TOP
PARSE THESE AND RETURN A LIST OF CLARIFYING QUESTIONS AND PUNCH LIST OF ONTOLOGY CHANGES

{
    General considerations:
    1. You recommend a lot of enumerated fields which seems somewhat premature given we have not done the discovery yet. I like the detail and it will help AI agents to focus during extraction, but what do we do with outliers?

    2. Some of these suggestions feel like we are over-specifying the ontology for what is largely meant to assist extraction, retrieval, and some very limited LLM-based reasoning across the graph. We aren't doing formal semantic inference, though we may do some ML model training on the graph. Does that change any of your recommendations?

}


  Domain Adequacy Review: AdaptBase Ontology v0.2                                                                                    
                                                                                                                                     
  Reviewer role: Senior researcher, urban climate adaptation                                                                         
  Scope: ontology-v0.2.json, decisions-log.md, all vocabulary files, competency questions, framework crosswalk
  Date: 2026-04-29                                                                                                                   
                                                                                                                                     
  ---                                                                                                                                
  Summary judgment                                                                                                                   
                  
  This is a serious ontology. The IPCC AR6 three-pathway risk model, the Shi (2024) justice rubric, the four-tier epistemic hierarchy
   for ResilienceGoal, and the claim provenance architecture all signal that the schema was designed by people who know the          
  literature. An expert panel will take it seriously.
                                                                                                                                     
  That said, there are five issues that would generate immediate pushback: temporal modeling is stripped down to the point where you 
  can't answer forward-looking planning questions, the governance layer is nearly absent, PlanningData is a skeleton, the
  compound/cascading hazard problem is unmodeled, and the CQ document has multiple stale references to removed entities. Fix these   
  before sending to reviewers.

  ---
  1. Coverage Completeness
                                                                                                                                     
  1a. Governance and institutional arrangements — major gap
                                                                                                                                     
  The Stakeholder type captures individual actors and their types but there is no structure for modeling governance arrangements:    
  formal bodies (multi-stakeholder committees, technical working groups, inter-agency coordination panels), mandated authorities,    
  accountability chains, or public-private partnership structures.                                                                   
                  
  Decision 18 removed COORDINATES_WITH and REPORTS_TO as "not extractable" from adaptation plans. That rationale is questionable.    
  These patterns appear in plan preambles, implementation chapters, and governance annexes with meaningful frequency. Their removal
  leaves a blind spot that practitioners will notice.                                                                                
                  
  Current state: you can say "City Water Authority" and "Parks Department" are both Stakeholders. You cannot say they are coordinated
   under a "Climate Resilience Steering Committee" with defined authority, nor that the Parks Department reports to the Deputy Mayor
  on green infrastructure targets. The governance structure IS the enabling condition for many adaptation decisions.                 
                  
  Recommended addition: A GovernanceStructure node type (id: GovernanceStructure) — a formal coordinating body, working group, or    
  institutional arrangement. Properties: structure_type (enum: inter_agency_committee, public_private_partnership, community_board,
  technical_working_group, regional_authority), authority_level (advisory, regulatory, operational), mandate_description (string).   
  Relationships needed: PARTICIPATES_IN extended to allow Stakeholder → GovernanceStructure, and GOVERNS (GovernanceStructure →
  Plan).

  {

    Accept, with my caveats about the likely need to expand the enumerated properties as we collect data.

    Do you recommend restoring the COORDINATES_WITH and REPORTS_TO relationsips? What node types would they connect?

  }

  1b. Temporal dynamics — major gap

  Decision 20 removed TimePoint, converting temporal data to year properties. The consequence is that the ontology has no structured 
  representation of:
  - Climate scenario time horizons (2030, 2050, 2100 projections)                                                                    
  - Multi-period monitoring (year 1 baseline, year 3 midpoint, year 5 evaluation)                                                    
  - Policy cycles and planning windows                                           
  - The gap between a plan's adoption year and the start of implementation                                                           
                                                                                                                                     
  What's present is adequate for the solution-evidence use case (point-in-time Indicator readings, Action start/end years). But for  
  planning-domain use cases — "how did the city's flood risk assessment change between the 2015 and 2024 plan?" or "which targets set
   for 2025 have been met?" — the current model cannot answer.                                                                       
                                                                                                                                     
  Most critically, the Hazard type has trend and return_period properties but no way to anchor hazard projections to specific climate
   scenarios or time horizons. This is a real problem: a hazard can simultaneously be a 1-in-50-year event under current climate and
  a 1-in-10-year event under RCP 8.5 by 2050. Both facts matter, but the current schema can only hold one value.                     
                  
  Recommended additions:                                                                                                             
  - Hazard.climate_scenario (enum: current, ssp1_2.6, ssp2_4.5, ssp3_7.0, ssp5_8.5) — which scenario the hazard characterization
  applies to                                                                                                                         
  - Hazard.projection_year (integer) — horizon year for projections (e.g., 2050, 2100)
  - Indicator.measurement_period (string) — a free-text period descriptor for multi-year monitoring windows (e.g., "2021-2023        
  average")                                                                                                                          
  - Plan.review_cycle_years (integer) — structured temporal governance field                                                         
                                                                                                                                     
  I am not arguing for restoring the full TimePoint node, which added extraction complexity. Targeted properties on Hazard and       
  Indicator cover the most critical gaps.   

  {
    Where are these hazard scenarios from? IPCC? If so, we'll need a controlled vocabulary for it
    I assume all of these will be optional fields?
     
  }                                                                                         
                                                                                                                                     
  1c. Monitoring and evaluation — moderate gap                                                                                       
                  
  The Indicator type captures the measurement artifact but has no structure for the monitoring process. PlanningData is the most     
  underdeveloped type in the entire ontology: zero properties. This will be flagged immediately by any evaluator who asks "how do you
   know a plan is evidence-based?"                                                                                                   
                  
  The ICLEI Milestone E (Monitor) crosswalk in the framework document rates monitoring as "Good" — this is too generous. You can     
  record an indicator value, but there is no way to represent:
  - Who is responsible for monitoring                                                                                                
  - How often measurements are scheduled                                                                                             
  - What data quality standards apply   
  - Whether a monitoring indicator is required by an external framework (GCoM, Sendai)                                               
  - The distinction between a monitoring indicator and a performance target           
                                                                                                                                     
  Recommended additions to PlanningData:                                                                                             
  data_name (string, required)                                                                                                       
  data_type (enum: hazard_map, vulnerability_assessment, climate_projection, demographic_dataset, land_use_map, monitoring_report)   
  data_source (string)                                                                                                               
  publication_year (integer)                                                                                                         
  spatial_coverage (enum: city, regional, national, global)                                                                          
  temporal_coverage (string — free text; too variable for enum)                                                                      
  methodology_url (string)                                                                                                           
                                                                                                                                     
  This turns PlanningData from a placeholder into something worth populating during extraction.     

  { Lets add data source url also}                                 
                                                                                                                                     
  1d. Nature-based solutions specifics — moderate gap                                                                                
                                                                                                                                     
  The "nature" solution category is present and has reasonable subcategories. However, NbS have properties that distinguish them from
   grey infrastructure that the current schema cannot capture:
                                                                                                                                     
  - Ecological preconditions: soil quality, hydrology, climate suitability (a mangrove restoration solution that works in Rotterdam  
  may fail in Dubai)
  - Co-species and biodiversity effects: whether native vs. non-native species are used, whether the solution increases or decreases 
  habitat connectivity                                                                                                               
  - Maintenance intensity: NbS typically have significant ongoing maintenance requirements that affect lifecycle costs and long-term
  effectiveness — not captured anywhere                                                                                              
  - Ecosystem service valuation: carbon sequestration, biodiversity value, recreational value as distinct from adaptation co-benefits
                                                                                                                                     
  None of these require new node types. They could be captured as optional properties on Solution (conditioned on category_id =      
  "nature") or via the EnablingCondition structure, but the latter is too generic to surface them cleanly in queries.                
                                                                                                                                     
  Recommended addition: Solution.nbs_preconditions (array<string>, vocabulary-bound) — a controlled vocabulary of ecological site    
  conditions required for NbS deployment.

  {
    This is needless complexity at this stage. I get where you are coming from but we need to defer this to the future.    
  }
                                                                                                                                     
  1e. Compound and cascading hazards — significant gap                                                                               
   
  The hazard model is currently atomic: each Hazard node is a single hazard type. There is no way to represent:                      
  - Simultaneous compound hazard events (e.g., heat + drought)
  - Cascading sequences (flood → substation failure → hospital loss of power)                                                        
  - Cumulative effects of multiple moderate hazards                          
                                                                                                                                     
  This is not an edge case. Compound climate events are driving the frontier of risk assessment literature (IPCC AR6 Chapter 11), and
   practitioners in coastal cities increasingly plan for compound flood/storm surge/heat events.                                     
                                                                                                                                     
  Recommended addition: COMPOUNDS_WITH (Hazard → Hazard) relationship, with properties:                                              
  - compound_type (enum: simultaneous, cascading, cumulative)
  - frequency_amplification (number) — how much more frequent the compound event is than each individual hazard                      
                                                                                                               
  This also enables the most important infrastructure interdependency queries: which urban systems are exposed to cascading failures 
  when a primary system fails? Currently DEPENDS_ON exists only for Solution→Solution. An analogous CASCADES_TO (UrbanSystem →       
  UrbanSystem) would complete the picture.                                                                                           

{
Lets defer this. We are not trying to model the entire hazard system, but the subset of hazards that specific solutions target. I also don't think the properties you identify will be quantitatively documented in the plans and other documents so the extraction LLM would be guessing.

}


  1f. Maladaptation risks — absent                                                                                                   
   
  Maladaptation — adaptation that increases long-run vulnerability, creates path dependencies, or transfers risk to other populations
   — is a prominent concern in the literature (IPCC AR6 Chapter 17, section 17.4.3) and is absent from the ontology.
                                                                                                                                     
  The current schema conflates maladaptation with failure_mode in the Outcome type. These are distinct: a failure mode is a solution 
  that didn't work as intended; maladaptation is a solution that worked as intended but created negative second-order effects (e.g.,
  a seawall that protects one neighborhood but accelerates erosion in adjacent areas, locking in development in a flood-prone zone). 
                  
  Recommended addition: Add maladaptation to the outcome_type enum values in Outcome, with a definition that distinguishes it from   
  failure_mode. Alternatively, add a SHIFTS_RISK_TO (Solution → ExposureUnit) relationship to capture spatial risk displacement.

  {
    Would both make sense? I like both, they are important.
  }
                                                                                                                                     
  ---             
  2. Relationship Adequacy
                                                                                                                                     
  Walking through six domain questions against the actual relationship set:
                                                                                                                                     
  Q1: "What solutions address heat in low-income neighborhoods?"                                                                     
                                                                                                                                     
  Result: Partially answerable, with gaps.                                                                                           
  - Solution MITIGATES Hazard (extreme_temperature_hot) ✓
  - Solution.target_populations contains low_income_households ✓                                                                     
  - Solution.equity_focus = primary_target ✓                    
                                                                                                                                     
  But: "low-income neighborhoods" as a place is not queryable. Location has no income or socioeconomic attributes. ExposureUnit has  
  affected_group but ExposureUnit has no direct link to Location — there is no ExposureUnit LOCATED_IN Location relationship. You can
   find solutions that target low-income populations generally, but not solutions deployed in low-income neighborhoods in a given    
  city.                                                                                                                              
                  
  Missing: LOCATED_IN (ExposureUnit → Location) relationship. Without this, spatial equity analysis is broken.       

  {add the LOCATED_IN relationship}                
   
  Q2: "Which financing mechanisms support nature-based solutions?"                                                                   
                  
  Result: Well-supported.                                                                                                            
  - Solution.category_id = "nature" → USES_INSTRUMENT → FinancialInstrument ✓
  - FinancingSource CHANNELS_THROUGH FinancialInstrument ✓                                                                           
                                                          
  Solid. The financing graph is one of the better-constructed parts of the schema.                                                   

   {good to hear, as this is a primary use case}   

  Q3: "What barriers prevent implementation of proven solutions?"                                                                    
                                                                                                                                     
  Result: Partially answerable.                                                                                                      
  - Solution FACES Barrier ✓
  - Solution.maturity_level = established (as proxy for "proven") ✓                                                                  
  - Barrier.is_structural ✓                                        
                                                                                                                                     
  But "proven" in practice means high-evidence outcomes, not just maturity. CQ-36 is designed to test whether maturity correlates    
  with evidence quality, but you can't currently answer "barriers that affect solutions with rigorously_evaluated outcomes" without a
   multi-hop join: Solution → Outcome (evidence_level) + Solution → Barrier.                                                         
                                                                                                                                     
  Also: Action has no path to Barrier. If a specific committed action is blocked, there is no Action FACES Barrier relationship —    
  you'd have to resolve the Action to a Solution first.
                                                                                                                                     
  Missing: Action FACES Barrier relationship, consistent with the Action → solution class resolution being optional. 

  {
  add the Action FACES Barrier, or would a Barrier BLOCKS Action be more active?
  
  }                
   
  Q4: "Which cities have met their adaptation targets?"                                                                              
                  
  Result: Not fully answerable.                                                                                                      
  - Plan SETS_GOAL ResilienceGoal with target_year ✓
  - Outcome DEMONSTRATES_PROGRESS_ON ResilienceGoal ✓                                                                                
                                                     
  But there is no status flag on ResilienceGoal or DEMONSTRATES_PROGRESS_ON indicating whether a goal was achieved vs. merely        
  progressed toward. You can accumulate evidence but can't say "Goal X was reached in 2024 as specified in the 2019 plan." The       
  SETS_GOAL.target_year is present but there's no way to close the loop: was the target met?                                         
                                                                                                                                     
  Missing: achieved boolean on DEMONSTRATES_PROGRESS_ON relationship, or a goal_status property on ResilienceGoal.   

  {
    please add
  }                
   
  Q5: "How has climate risk changed between two planning cycles?"                                                                    
                  
  Result: Not answerable.                                                                                                            
  The Plan SUPERSEDES Plan relationship captures plan succession but Hazard nodes have no temporal anchoring to specific plans. You
  can't compare "flood risk as assessed in Plan A (2015)" vs. "flood risk as assessed in Plan B (2024)." The removal of TimePoint    
  means hazard assessments float free of their temporal context.
                                                                                                                                     
  This is the most serious gap for longitudinal analysis.                                                                            
   
  Missing: As noted in §1b, Hazard.climate_scenario and Hazard.projection_year are needed. More structurally, a RISK_ASSESSED_IN     
  (Hazard → Plan) relationship would capture when and in what context a hazard characterization was made.

{
    do the changes in §1b fix this, or is more needed?
  }                
   
                                                                                                                                     
  Q6: "What are the equity outcomes of grey vs. green infrastructure?"                                                               
   
  Result: Partially answerable with a multi-hop join.                                                                                
  - Solution.category_id = "nature" or UrbanSystem.infra_color = green (for green)
  - Solution PRODUCES Outcome with justice_dimension ✓                                                                               
                                                      
  The join works but is awkward because "grey vs. green" is coded at the UrbanSystem level (infra_color) while solutions are         
  classified at the solution-categories level. For a clean query you'd want Solution.infra_color directly, or a direct relationship  
  between solution and infrastructure type.

  {
    I'm actually not a big fan of the infra_color property. these classifications are vague and not particularly useful for anyone. i'd say we remove it.

  }                                                                             
                                                                                                                                     
  ---             
  Missing relationships summary
                                                                                                                                     
  ┌──────────────────┬───────────────────────────┬──────────┬─────────────────────────────────────────────────────────────┐
  │   Proposed ID    │      Source → Target      │ Priority │                          Rationale                          │          
  ├──────────────────┼───────────────────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ LOCATED_IN       │ ExposureUnit → Location   │ High     │ Spatial equity queries broken without this                  │
  ├──────────────────┼───────────────────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ COMPOUNDS_WITH   │ Hazard → Hazard           │ High     │ Compound hazard modeling absent                             │          
  ├──────────────────┼───────────────────────────┼──────────┼─────────────────────────────────────────────────────────────┤          
  │ CASCADES_TO      │ UrbanSystem → UrbanSystem │ Medium   │ Infrastructure interdependency modeling                     │          
  ├──────────────────┼───────────────────────────┼──────────┼─────────────────────────────────────────────────────────────┤          
  │ COORDINATES_WITH │ Stakeholder → Stakeholder │ Medium   │ Multi-actor governance — Decision 18 should be reconsidered │
  ├──────────────────┼───────────────────────────┼──────────┼─────────────────────────────────────────────────────────────┤          
  │ Action FACES     │ Action → Barrier          │ Medium   │ Actions can be blocked independent of solution resolution   │
  ├──────────────────┼───────────────────────────┼──────────┼─────────────────────────────────────────────────────────────┤          
  │ RISK_ASSESSED_IN │ Hazard → Plan             │ Medium   │ Temporal anchoring for hazard characterizations             │
  ├──────────────────┼───────────────────────────┼──────────┼─────────────────────────────────────────────────────────────┤          
  │ COMPLEMENTS      │ Solution → Solution       │ Low      │ Solution synergies distinct from DEPENDS_ON                 │
  ├──────────────────┼───────────────────────────┼──────────┼─────────────────────────────────────────────────────────────┤          
  │ EVALUATES        │ Stakeholder → Outcome     │ Low      │ Who conducted monitoring/evaluation                         │
  └──────────────────┴───────────────────────────┴──────────┴─────────────────────────────────────────────────────────────┘          
                  
  ---                                                                                                                                
  3. Vocabulary Gaps
                    
  3a. Vulnerability type — formalize this now
                                                                                                                                     
  Vulnerability.vuln_type has been "free-text, formalize later" since the beginning. The framework crosswalk has a detailed list of  
  socioeconomic stress types that map to this field. This vocabulary needs to be built before publication: it's the linchpin for CQ-5
   and the equity CQ cluster, and "free-text" will yield inconsistent extractions that can't be aggregated.                          
                  
  At minimum, formalize these categories from the RCC crosswalk: economic_inequality, poverty, structural_racism, food_insecurity,   
  gender_inequality, housing_insecurity, poor_adaptive_capacity, low_social_cohesion, plus a catch-all compound_social_vulnerability.

  {ok}
                                                                                                                                     
  3b. Mechanism type vocabulary — incomplete                                                                                         
   
  The mechanism vocabulary is still labeled "seed vocabulary, guidance only, not constraint" from Decision 15. The current seed      
  values are:     
  - From original: absorb, redirect, harden, monitor, govern, cool, filter, store                                                    
  - From Sprint 4: sense_and_detect, forecast_and_model, automate_and_control, inform_and_alert                                      
                                                                                               
  These 12 are reasonable but incomplete. Missing functional mechanisms that recur in the corpus:                                    
  - restore — ecological restoration processes                                                                                       
  - relocate — managed retreat, displacement of assets                                                                               
  - buffer — creating protective spatial buffer zones                                                                                
  - insulate — thermal or acoustic insulation processes                                                                              
  - regulate — pricing, standards-setting, permitting                                                                                
                                                                                                                                     
  The vocabulary note says this will be "formalized via corpus clustering in Weeks 7-8." If publication is May 14, this work needs to
   happen before then or reviewers will flag it as incomplete.

    {ok, can you compelte it}                                                                       
                                                                                                                                     
  3c. Plan type vocabulary — low-hanging fruit                                                                                       
                  
  Plan.plan_type is free-text despite the ICLEI crosswalk recommending an enum since Sprint 3. This is an easy fix:                  
  climate_action_plan, resilience_strategy, adaptation_plan,
  sectoral_adaptation_plan, disaster_risk_reduction_plan,                                                                            
  heat_action_plan, coastal_adaptation_plan, nature_based_solutions_plan                                                             
  Free-text plan_type prevents CQ-13 ("which actor types prescribe which solution types") from working properly when filtered by plan
   type.

    {ok}                                                                                                                             
                                                                                                                                     
  3d. Sendai indicators — inconsistency                                                                                              
                                                                                                                                     
  The CLAUDE.md prompt lists "Sendai indicators" as one of the 7 controlled vocabularies. The ontology JSON metadata says            
  vocabularies_count: 6 and lists only 6 vocabularies. The Sendai indicators vocabulary is referenced in the repository directory    
  (resilience-attributes.json exists in schemas/vocabularies/) but is not wired into the ontology JSON. This is a consistency error —
   fix the count or the wiring before publication.

{you fix, we removed it}  

  3e. Co-benefits classification — no taxonomy                                                                                       
   
  Outcome nodes with outcome_type = co_benefit have free-text descriptions but no taxonomy of co-benefit types. The climate          
  adaptation co-benefits literature consistently uses a small set of categories: public health, biodiversity/ecosystem services,
  economic productivity, social cohesion, carbon sequestration, aesthetic/recreational value. Without this, CQ-17 ("which solutions  
  deliver co-benefits beyond their primary hazard target, and what categories recur?") returns unstructured text.

  Recommended addition: Outcome.co_benefit_type (enum, only applicable when outcome_type = co_benefit): public_health, ecological,   
  economic, social_cohesion, carbon_sequestration, aesthetic_recreational.

  {ok}
                                                                                                                                     
  3f. Missing external crosswalks                                                                                                    
   
  The solution-categories vocabulary has C40, GCoM, and IPCC mappings (added Sprint 3). Missing:                                     
  - SDG crosswalk: many cities frame adaptation in SDG language. A sdg_indicators field on solution-categories would enable
  "solutions that contribute to SDG 11 (Sustainable Cities)" queries.                                                                
  - Sendai Framework targets: the ExposureUnit node explicitly references Sendai but the vocabulary isn't connected.

  {im not sure i understand your recomendations}
                                                                                                                                     
  ---                                                                                                                                
  4. Property Completeness
                                                                                                                                     
  Calling out underdeveloped entity types specifically:
                                                                                                                                     
  PlanningData — critically underdeveloped                                                                                           
                                                                                                                                     
  Zero properties. Extract hint says "look for referenced datasets, models, or studies." But extractors can't produce structured     
  PlanningData nodes with nothing to populate. Minimum required: data_name, data_type, publication_year, data_source. See §1c above.
                                                                                                                                     
  Mechanism — underdeveloped

  Two properties: mechanism_type (uncontrolled string) and description. If the mechanism vocabulary is going to remain informative   
  rather than authoritative, the type is effectively free-text with a hint. This limits the value of WORKS_BY as a relationship.
  Mechanism nodes are potentially the highest-value analytical bridge in the ontology (they enable CQ-2 and CQ-29 — mechanism vs.    
  evidence quality cross-analysis) but only if the vocabulary is controlled.

  Location — missing key comparability attributes                                                                                    
   
  The CQ document notes that "comparable city" is a query-time filter spanning all city characteristics. But Location has no city    
  characteristics beyond name, country, region, and geometry. For cross-city comparability (CQ-1, CQ-3, CQ-24), you need at minimum:
  - climate_zone (string, Koppen-Geiger classification — e.g., "Cfb", "BSk")                                                         
  - population (integer)                                                                                                             
  - coastal_status (boolean)
  - income_classification (enum: low_income, lower_middle, upper_middle, high — World Bank classification)                           
                                                                                                                                     
  These are data that would be joined from an external cities database (the loc_id foreign key points to one), but having these as   
  optional properties would allow the Location node to be self-contained for cities that don't have a loc_id match.                  
                                                                                                                                     
  ResilienceGoal — inconsistent counts                                                                                               
                  
  The definition says "22 goals across 4 dimensions" (CRF 2024 v2). The vocabulary metadata in the JSON says terms_count: 12 (the old
   CRF had 12 goals). One of these is wrong. Fix before publication.
                                                                                                                                     
  Also: ResilienceGoal has no description or label_text property. The goal_id and dimension are present for query purposes but       
  there's no way to display a human-readable goal name in the viewer without joining to the external CRF vocabulary. Add goal_text
  (string) at minimum.                                                                                                               
                  
  Action — no direct location link                                                                                                   
   
  Action has spatial_scale (city/district/neighborhood/site) but no link to a specific Location node. CQ-40 asks for solutions with  
  equity benefits in "comparable cities" but Actions don't carry their own Location — you'd trace back through Plan → COVERS_LOCATION
   → Location, which only gets you to the plan's jurisdiction, not the specific neighborhood where an action is deployed.            
                  
  EnablingCondition — too sparse for use in gap analysis                                                                             
   
  The condition is a free-text string with a type enum. For enabling condition gap analysis (CQ-4, CQ-16, CQ-24), practitioners need 
  to know:        
  - Whether a condition is currently present or absent in a given context                                                            
  - Whether the condition is at the city level or requires national-level action                                                     
  - How long it typically takes to establish                                    
                                                                                                                                     
  Recommend adding: scale_required (enum: building, city, national, international) and typical_establishment_years (integer,         
  optional).

  {which of these were not addressed in section 1 and my resopnses?}                                                                                                                         
                                                                                                                                     
  ---                                                                                                                                
  5. Modeling Choices

    {which of these were not addressed in section 1 and my resopnses?}  
                                                                                                                                     
  5a. Decision 20: TimePoint removal — revisit partially
                                                                                                                                     
  The decision to remove TimePoint and use year properties was correct in principle — a full TimePoint node added extraction overhead
   for limited gain. But the implementation went too far: Hazard now has no mechanism to carry forward-looking scenario-based        
  characterizations.                                                                                                                 
                  
  The specific problem: Hazard.trend (enum: increasing/stable/decreasing/uncertain) and Hazard.frequency (free text) are both        
  present-tense properties. They cannot hold scenario-conditional values like "frequency doubles under SSP5-8.5 by 2050." This is not
   a rare edge case — it's how every risk assessment in the corpus frames hazard trends.                                             
                  
  The fix is minimal: add climate_scenario and projection_year to Hazard. You do not need TimePoint back.                            
   
  5b. Decision 20: Infrastructure merged into UrbanSystem — tension worth acknowledging                                              
                  
  The merger is defensible for extraction simplicity. The practical issue is that UrbanSystem is now doing two different jobs:       
                  
  1. Sector classification (sector, subsector, system_id): what domain/sector does this solution operate in?                         
  2. Physical infrastructure entity (condition, capacity, service_coverage, infra_color): what is the state of specific
  infrastructure?                                                                                                                    
                  
  When the same node type is used for "stormwater management sector" and "the specific stormwater network in Rotterdam with capacity 
  X," queries get ambiguous. Solution OPERATES_ON stormwater_management (sector) vs. Solution IMPROVES stormwater_network (physical
  entity) should ideally be distinguishable.                                                                                         
                  
  This can be partially resolved without re-splitting by adding a boolean is_instance property to UrbanSystem — flagging whether a   
  node is a generic sector classification (is_instance = false) or a specific city-infrastructure entity (is_instance = true). This
  preserves the merger while making the distinction queryable.                                                                       
                  
  5c. Decision 3/14: maturity_level — provisional is right, test it                                                                  
   
  The three-level maturity scale (emerging/demonstrated/established) is a reasonable practical choice — the rejection of full TRL    
  scale was correct. The falsifiability condition on CQ-36 is the right intellectual disposition.
                                                                                                                                     
  One concern: "demonstrated" is doing a lot of work. The gap between a solution with 3 reference deployments and one with 100       
  deployments is large, but both would be "demonstrated." Consider whether deployment_count_range (enum: 1, 2-5, 6-20, >20) would add
   analytical value alongside maturity_level.                                                                                        
                  
  5d. Identity vs. function classification — defensible but flag extraction risk                                                     
   
  The core design decision (solutions classified by what they ARE, not what they DO) is principled and aligns with how solutions     
  appear in practitioner literature ("urban heat island mitigation program" identifies a solution type independently of its
  functions).                                                                                                                        
                  
  However, the IPCC action type classification (ipcc_action_types: structural_physical, social, institutional, ecosystem_based) is   
  itself a functional classification embedded on the Solution node. A green roof is simultaneously structural_physical (the built
  fabric) and ecosystem_based (the NbS function). This creates ambiguity: is ipcc_action_types a property of the solution identity or
   of what it does?

  The bigger extraction risk: the extract_hint on Solution says to look for "named interventions, technologies, programs, or         
  projects." But 30-40% of CDP city actions are described in purely functional terms without a solution name. How extractors should
  handle "we are implementing actions to increase urban greenery" (function, no solution name) vs. "we are installing bioswales in 5 
  districts" (named solution) is not documented in the schema.

  This is an implementation concern rather than a schema flaw, but it should be addressed in extraction guidance before the pipeline 
  runs at scale.
                                                                                                                                     
  5e. COORDINATES_WITH removal — wrong call                                                                                          
   
  Decision 18 removed COORDINATES_WITH as "not extractable." The rationale was that actor-actor coordination hierarchies are rarely  
  documented at individual-actor granularity in adaptation plans.
                                                                                                                                     
  This conflates two different things: (1) org-chart-style REPORTS_TO hierarchies (correctly removed) and (2) documented coordination
   on specific initiatives (COORDINATES_WITH, incorrectly removed). The former is genuinely rare in plan documents; the latter
  appears in governance sections, implementation chapters, and partnership descriptions with real frequency. Plans routinely name    
  which departments coordinate on which initiatives.

  The absence of COORDINATES_WITH means you cannot model "the Rotterdam Water Authority coordinates with the Parks Department and    
  three NGOs on the green corridor program" — a governance fact that appears directly in plan text.
                                                                                                                                     
  Recommend restoring COORDINATES_WITH with a note that it should only be extracted when explicitly documented (not inferred from    
  co-occurrence in the same plan section).
                                                                                                                                     
  ---             
  6. Publication Readiness
                                                                                                                                     
  What an expert panel would flag in the first hour
                                                                                                                                     
  Immediate flags (would cause credibility concerns):                                                                                
                                                                                                                                     
  1. Stale competency questions document. CQ-12 references Policy node (removed in Decision 20). CQ-20 references                    
  TimePoint/RECORDED_AT (removed in Decision 20). CQ-26 references COORDINATES_WITH (removed in Decision 18). CQ-11 and CQ-21
  reference FUNDED_BY which was replaced by USES_INSTRUMENT and CHANNELS_THROUGH. Sending this to external reviewers with stale CQs  
  signals lack of internal coherence.
  2. ResilienceGoal count inconsistency. The definition says "22 goals" (CRF 2024 v2). The vocabulary metadata says terms_count: 12
  (old CRF). One is wrong. Reviewers who use the CRF will catch this immediately.                                                    
  3. PlanningData has zero properties. For an ontology that centers data-informed planning, a node type with no extractable
  properties signals incompleteness.                                                                                                 
  4. Vulnerability.vuln_type is still free-text. The decisions log flags this as "formalize later" across multiple sprints. Later is
  now.                                                                                                                               
                  
  Questions panel would ask:                                                                                                         
                  
  5. "How do I represent a compound event — simultaneous heat and drought?" — currently unanswerable.                                
  6. "Can I see which solutions were deployed before vs. after a specific climate event?" — temporal modeling insufficient for this.
  7. "How does the schema represent the difference between what a plan aims for and what actually happened?" — the SETS_GOAL /       
  DEMONSTRATES_PROGRESS_ON distinction is good conceptually, but there's no goal_status closing the loop.                            
  8. "Where are the mechanism types defined?" — the answer ("seed vocabulary, guidance only") will not satisfy a methodologically    
  rigorous reviewer.                                                                                                                 
                  
  What would make them take it seriously                                                                                             
                  
  The following design choices are genuinely strong and practitioners will notice them:                                              
                  
  - The IPCC AR6 three-pathway structure (MITIGATES Hazard / REDUCES_EXPOSURE ExposureUnit / REDUCES Vulnerability) is analytically  
  precise and directly grounded in the authoritative risk framework. This is better than most practitioner ontologies which conflate
  these.                                                                                                                             
  - The four-tier epistemic hierarchy for ResilienceGoal (SETS_GOAL → TARGETS_GOAL → CONTRIBUTES_TO → DEMONSTRATES_PROGRESS_ON) is
  the right architecture for distinguishing aspiration from evidence. Reviewers who work in M&E will immediately understand its      
  value.
  - The Shi (2024) justice dimensions (distributive, procedural, recognitional, epistemic) on Outcome.justice_dimension is a         
  principled choice that reflects current equity scholarship — it goes beyond the simpler "equity as co-benefit" framing used in most
   comparable tools.
  - The claim provenance architecture (claim_ids on every relationship) is unusual in practitioner-facing ontologies and signals     
  methodological rigor. Anyone who has worked with contradictory evidence across city reports will understand its value.             
  - The FinancingSource / FinancialInstrument distinction is correct and practitioners will recognize it: the World Bank (source) and
   a green bond (instrument) are different things that need to be tracked separately.                                                
                  
  Pre-publication checklist                                                                                                          
                  
  ┌─────────────────────────────────────────────────────────────────────────────────────────┬──────────────────────────┬─────────┐   
  │                                           Fix                                           │         Urgency          │ Effort  │
  ├─────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────┼─────────┤   
  │ Update CQ document to remove references to Policy, TimePoint/RECORDED_AT,               │ Before any external      │ Low     │
  │ COORDINATES_WITH, FUNDED_BY                                                             │ sharing                  │         │
  ├─────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────┼─────────┤   
  │ Fix ResilienceGoal count: 22 goals or 12? Update metadata to match definition           │ Before publication       │ Trivial │
  ├─────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────┼─────────┤   
  │ Add properties to PlanningData (at minimum: data_name, data_type, data_source,          │ Before publication       │ Low     │
  │ publication_year)                                                                       │                          │         │   
  ├─────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────┼─────────┤
  │ Formalize Vulnerability.vuln_type vocabulary                                            │ Before publication       │ Medium  │   
  ├─────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────┼─────────┤   
  │ Add Hazard.climate_scenario and Hazard.projection_year                                  │ Before publication       │ Low     │
  ├─────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────┼─────────┤   
  │ Add LOCATED_IN (ExposureUnit → Location)                                                │ Before publication       │ Low     │
  ├─────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────┼─────────┤   
  │ Formalize mechanism type vocabulary (constrain it, stop calling it guidance-only)       │ Before publication       │ Medium  │
  ├─────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────┼─────────┤   
  │ Add COMPOUNDS_WITH (Hazard → Hazard)                                                    │ Can defer to v0.3        │ Medium  │
  ├─────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────┼─────────┤   
  │ Reconsider COORDINATES_WITH removal                                                     │ Can defer to v0.3        │ Low     │
  ├─────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────┼─────────┤   
  │ Add co_benefit_type enum to Outcome                                                     │ Can defer to v0.3        │ Low     │
  ├─────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────┼─────────┤   
  │ Add GovernanceStructure node                                                            │ Future work              │ High    │
  ├─────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────┼─────────┤   
  │ Add AdaptationPathway node                                                              │ Future work              │ High    │
  └─────────────────────────────────────────────────────────────────────────────────────────┴──────────────────────────┴─────────┘   
                  
  ---                                                                                                                                
  Specific additions with proposed IDs
                                                                                                                                     
  Entity additions:
  - GovernanceStructure (node): structure_type, authority_level, mandate_description                                                 
    Relationships: Stakeholder PARTICIPATES_IN GovernanceStructure, GovernanceStructure GOVERNS Plan                                 
                                                                                                                                     
  Property additions:                                                                                                                
  - Hazard.climate_scenario (enum: current, ssp1_2.6, ssp2_4.5, ssp3_7.0, ssp5_8.5)                                                  
  - Hazard.projection_year (integer)                                                                                                 
  - Location.climate_zone (string, Koppen-Geiger)                                                                                    
  - Location.population (integer)                                                                                                    
  - Location.coastal_status (boolean)                                                                                                
  - Location.income_classification (enum: low_income, lower_middle, upper_middle, high)                                              
  - ResilienceGoal.goal_text (string)                                                                                                
  - Outcome.co_benefit_type (enum: public_health, ecological, economic, social_cohesion, carbon_sequestration,
  aesthetic_recreational)                                                                                                            
  - Outcome.time_to_effectiveness (integer, years)
  - Solution.scale_applicability (enum: building, neighborhood, district, city, regional)                                            
  - PlanningData: data_name, data_type, data_source, publication_year, spatial_coverage, temporal_coverage                           
  - EnablingCondition.scale_required (enum: building, city, national, international)                                                 
  - UrbanSystem.is_instance (boolean — distinguishes sector classification from specific infrastructure entity)                      
                                                                                                                                     
  Relationship additions:                                                                                                            
  - LOCATED_IN: ExposureUnit → Location (high priority)                                                                              
  - COMPOUNDS_WITH: Hazard → Hazard, compound_type property                                                                          
  - CASCADES_TO: UrbanSystem → UrbanSystem
  - COORDINATES_WITH: Stakeholder → Stakeholder (restore)                                                                            
  - RISK_ASSESSED_IN: Hazard → Plan (temporal anchoring)                                                                             
  - Action FACES: Action → Barrier (extend FACES source)                                                                             
                                                                                                                                     
  Vocabulary additions:                                                                                                              
  - Vulnerability.vuln_type: formalize controlled vocabulary from RCC crosswalk                                                      
  - Outcome.co_benefit_type: as above                                                                                                
  - Plan.plan_type: convert free-text to enum
  - Mechanism.mechanism_type: constrain from guidance-only to required vocabulary                                                    
                                                                                                                                     
  ---                                                                                                                                
  The ontology has the right bones. The gaps are concentrated in governance, temporal modeling, and a handful of underdeveloped nodes
   — addressable before publication. The epistemic architecture and equity framework are strong enough to differentiate this from the
   generic schema work in this space.
                                       