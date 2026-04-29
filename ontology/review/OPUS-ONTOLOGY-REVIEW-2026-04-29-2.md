---
  Clarifying questions (8)                                                                                                                               
                                                                                                                                                         
  GC-1 (Enums / outliers): For every new or tightened enum, I'd add an other value plus a companion free-text _other_description field. That way         
  extraction never fails on an outlier and you still get structured labels for ML training. Does this pattern work for you, or do you prefer a different 
  convention?     

  This is good.
                                                                                                                                                         
  GC-2 (Over-specification): Given extraction + retrieval + possible ML training — but no formal inference — I'd drop two items from my recommendations: 
  EnablingCondition.scale_required and UrbanSystem.is_instance. Both are primarily useful for formal reasoning, not for training labels or retrieval
  filtering. Confirm you want them removed from the punch list?
  
  Yes, remove.
                  
  1a (Governance relationships): You accepted GovernanceStructure. On the related relationships: I recommend restoring COORDINATES_WITH as Stakeholder → 
  Stakeholder (documents cross-agency coordination on specific initiatives) and extending PARTICIPATES_IN to also allow Stakeholder → GovernanceStructure
   (membership in a formal body). I do NOT recommend restoring REPORTS_TO — that's org-chart information that won't appear in plan text. Does this scope 
  work?       
  
  Yes.

  1b (Hazard scenarios): The SSP vocabulary (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5) is IPCC AR6 WGII. The older RCP labels (RCP 4.5, RCP 8.5) still     
  appear in many city plan documents because plans from 2015-2022 predate the SSP shift. Do you want both RCP and SSP values in the enum, or only SSP
  (with extractors mapping older RCP references to SSP equivalents)?                                                                                     
  
  I think we should use SSP, and provide a structured mapping/crosswalk for the extractor.

  Q3 (Action → Barrier direction): You asked whether Action FACES Barrier or Barrier BLOCKS Action. I recommend BLOCKS (Barrier → Action) — it's a richer
   verb, it reads naturally ("regulatory barrier blocks flood sensor deployment"), and it keeps directionality consistent with how barriers are
  encountered during plan execution. It's also a separate relationship ID from FACES (Solution → Barrier), which avoids overloading FACES with two source
   types. Confirm?

  Acutally, I think Barrier BLOCKS Solution and Action FACES Barrier is better because our use case is more focused on solutions, and we want to know when they are blocked. actions are going to be less specific than solutions so the fuzziness of FACES actually helps there. it suggests working around, whereas for blocked solutions, we need the focus to be on removing the block.

  Q5 (Does §1b fix the longitudinal query?): The climate_scenario + projection_year additions on Hazard fix the within-plan representation — you can now 
  store both current and 2050 characterizations of the same hazard. But Q5 asks to compare hazard assessments across two successive plans. For that to
  work, you'd need either (a) a RISK_ASSESSED_IN (Hazard → Plan) relationship, or (b) a convention where extractors create separate Hazard nodes per     
  plan-assessment context. Option (a) is cleaner for graph queries; option (b) has zero schema cost. Which do you prefer?

  i like a.

  3f (External crosswalks): My recommendation was purely a vocabulary metadata task — add a sdg_goals array field (e.g., ["SDG11", "SDG13"]) to entries  
  in solution-categories.json, the same way c40_action_categories is already there. No change to the main ontology JSON. Still want this, or skip it?

  yes, i like it.
                                                                                                                                                         
  Section 4/5 items needing an explicit decision (not addressed in your {responses}): Four items from my property recommendations are still open. Quick  
  yes/no on each:
  - Location comparability fields (climate_zone, population, coastal_status, income_classification) — add?       yes though we need enumerations for some, right? or are these all scalars?                                        
  - Action → Location direct link (currently Actions have no location node, only spatial_scale enum) — add?     yes, and we should probably use Location nodes now wherever we had previously used properties with geodata                                         
  - ResilienceGoal.goal_text (human-readable label on the node) — add?   yes                                  
  - Solution.deployment_count_range (count bucket alongside maturity_level) — add?   i dont understand what this is.                                                                    
                                                                                                                                                         
  ---                                                                                                                                                    
  Punch list — confirmed changes                                                                                                                         
                                                                                                                                                         
  Items you explicitly accepted, with no open questions. Ready to implement in the ontology JSON once the 8 questions above are resolved.                
                                                                                                                                                         
  New node types                                                                                                                                         
  - GovernanceStructure: structure_type (enum + other), authority_level (enum: advisory, regulatory, operational), mandate_description (string)          
                                                                                                                                                         
  New relationships
  - LOCATED_IN (ExposureUnit → Location)                                                                                                                 
  - SHIFTS_RISK_TO (Solution → ExposureUnit) — maladaptation spatial displacement                                                                        
  - GOVERNS (GovernanceStructure → Plan)                                         
  - COORDINATES_WITH (Stakeholder → Stakeholder) — restore, with explicit note: extract only when documented, not inferred from co-occurrence (pending   
  confirmation of scope from Q 1a)                                                                                                                       
  - BLOCKS (Barrier → Action) — direction pending confirmation from Q3                                                                                   
                                                                                                                                                         
  Property additions — confirmed                                                                                                                         
  - Hazard.climate_scenario (enum, optional) — values pending Q 1b                                                                                       
  - Hazard.projection_year (integer, optional)                                                                                                           
  - Indicator.measurement_period (string, optional)                                                                                                      
  - Plan.review_cycle_years (integer, optional)                                                                                                          
  - ResilienceGoal.goal_text (string) (pending Q8)
                                                                                                                                                         
  Property additions — enum changes                                                                                                                      
  - Outcome.outcome_type: add maladaptation value (distinct from failure_mode — define: solution worked as intended but transferred or increased risk)   
  - Outcome.co_benefit_type (enum, only populated when outcome_type = co_benefit): public_health, ecological, economic, social_cohesion,                 
  carbon_sequestration, aesthetic_recreational                                                                                                           
  - Plan.plan_type: convert free-text → enum: climate_action_plan, resilience_strategy, adaptation_plan, sectoral_adaptation_plan,                       
  disaster_risk_reduction_plan, heat_action_plan, coastal_adaptation_plan, nature_based_solutions_plan                            
  - DEMONSTRATES_PROGRESS_ON: add achieved (boolean) property                                                                                            
                  
  Property removals                                                                                                                                      
  - Remove UrbanSystem.infra_color from the UrbanSystem type and all references in the JSON
                                                                                                                                                         
  PlanningData — add all properties (currently zero)
  - data_name (string, required)                                                                                                                         
  - data_type (enum: hazard_map, vulnerability_assessment, climate_projection, demographic_dataset, land_use_map, monitoring_report)                     
  - data_source (string)                                                                                                                                 
  - data_source_url (string) — your addition                                                                                                             
  - publication_year (integer)                                                                                                                           
  - spatial_coverage (enum: city, regional, national, global)                                                                                            
  - temporal_coverage (string, free text)                                                                                                                
                                                                                                                                                         
  Vocabulary work                                                                                                                                        
  - Formalize Vulnerability.vuln_type controlled vocabulary from RCC crosswalk: economic_inequality, poverty, structural_racism, food_insecurity,        
  gender_inequality, housing_insecurity, poor_adaptive_capacity, low_social_cohesion, compound_social_vulnerability                                      
  - Add restore, relocate, buffer, insulate, regulate to mechanism vocabulary and change status from "guidance only" to authoritative                    
  - Fix vocabularies_count in metadata from 6 → correct count after Sendai removal is confirmed                                                          
  - Fix ResilienceGoal count inconsistency: definition says 22 (CRF 2024 v2), terms_count says 12 — verify which is correct against the CRF vocabulary   
  and update both                                                                                                                                        
                                                                                                                                                         
  CQ document cleanup (stale references)                                                                                                                 
  - Remove/update CQ-12 (references removed Policy node)                                                                                                 
  - Remove/update CQ-20 (references removed TimePoint/RECORDED_AT)                                                                                       
  - Update CQ-26 (references removed COORDINATES_WITH — may be restored, adjust accordingly)                                                             
  - Update CQ-11, CQ-21 (reference FUNDED_BY which was replaced by USES_INSTRUMENT/CHANNELS_THROUGH)                                                     
                                                                                                                                                         
  Deferred (not on the punch list)                                                                                                                       
  - NbS preconditions on Solution                                                                                                                        
  - COMPOUNDS_WITH (Hazard → Hazard)                                                                                                                     
  - CASCADES_TO (UrbanSystem → UrbanSystem)                                                                                                              
  - GovernanceStructure / AdaptationPathway as future work  