// Seed reviewers + comments. Keyed by node id or edge id.
// Deterministic for mock; could be swapped for a backend.

window.REVIEWERS = {
  ML:  { name: "Maya Leclerc",     affil: "Urban Tech Hub, Cornell Tech",      color: "carn" },
  RP:  { name: "Ruowen Pan",       affil: "Cornell CRP · Student co-author",   color: "blue" },
  JK:  { name: "Jordan Okafor",    affil: "NYC Mayor's Office of Climate",     color: "green" },
  AT:  { name: "Aditi Tiwari",     affil: "Arup Advisory, NYC",                color: "slate" },
  HB:  { name: "Henrik Bech",      affil: "C40 Cities, Knowledge Hub",         color: "amber" },
  SG:  { name: "Sofía G. Ortega",  affil: "Environmental Defense Fund",        color: "blue" },
};
window.ME = { id: "ME", initials: "yo", name: "You", affil: "reviewer" };

function initials(name) {
  return name.split(/\s+/).map(w => w[0]).slice(0,2).join("").toUpperCase();
}
window.initialsOf = initials;

// Comment threads. Each key is either a node id or an edge id (e.g. "MITIGATES:Solution:Hazard")
window.THREADS = {
  "Solution": [
    { id:"c1", by:"ML", when:"2 days ago", body:"The <strong>maturity_level</strong> property is doing real work here — but I'm worried we'll never be able to populate it reliably from public reporting. Can we flag CQ-36 as a v0.2 falsifiability test rather than keeping the property?", replies:[
      { id:"c1r1", by:"HB", when:"1 day ago", body:"Agree. C40 doesn't publish maturity at the solution class level, only deployment stage. Would vote to drop if evidence-level is duplicative." },
      { id:"c1r2", by:"RP", when:"1 day ago", body:"Keep it. Planners ask \"is this a proven technique?\" all the time and evidence-level is per-outcome, not per-class." }
    ]},
    { id:"c2", by:"SG", when:"4 days ago", body:"Big +1 on adding <strong>equity_focus</strong> and <strong>target_populations</strong>. This is exactly what the EDF equity impact study needs to query." }
  ],
  "Hazard": [
    { id:"c3", by:"HB", when:"yesterday", body:"Consider adding a <strong>time_horizon</strong> property (near / mid / long term). The C40 typology separates acute from chronic, and we lose that here.", replies:[
      { id:"c3r1", by:"ML", when:"yesterday", body:"Could live on the MITIGATES edge instead — it's really a property of the claim, not the hazard itself. Thinking." }
    ]}
  ],
  "Vulnerability": [
    { id:"c4", by:"AT", when:"3 days ago", body:"The three IPCC AR6 components (exposure, sensitivity, adaptive capacity) are modeled as separate scores — makes sense — but we should note somewhere that these are meant to be relative/normalized, not absolute." }
  ],
  "UrbanSystem": [
    { id:"c5", by:"JK", when:"6 hours ago", body:"Merging Infrastructure into UrbanSystem was the right call. For NYC data the distinction was impossible to maintain at extraction time." }
  ],
  "Plan": [
    { id:"c6", by:"ML", when:"5 days ago", body:"Plan properties are placeholder — flagging this for the ontology WG. We need a vocabulary for plan_type (C40 has one; ICLEI diverges)." }
  ],
  "FinancialInstrument": [
    { id:"c7", by:"AT", when:"2 days ago", body:"Adding <strong>grant</strong> and <strong>direct_allocation</strong> to instrument_type was pragmatic but it blurs the theoretical line. Worth a footnote in the schema doc." }
  ],

  // Edges keyed by "RELATIONSHIP_ID:source:target"
  "MITIGATES:Solution:Hazard": [
    { id:"e1", by:"HB", when:"2 days ago", body:"This is doing a lot of heavy lifting. I'd want to see <strong>mitigation_type</strong> on the edge — does the solution reduce intensity, frequency, or duration of the hazard? These have different policy implications." }
  ],
  "DEPENDS_ON:Solution:Solution": [
    { id:"e2", by:"RP", when:"1 day ago", body:"Self-referential edges are going to be hell to extract cleanly from text. Do we have a plan for cycle detection in the pipeline?", replies:[
      { id:"e2r1", by:"ML", when:"20 hours ago", body:"Weeks 7–8 corpus mining has a topological-sort sanity pass. Cycles get flagged, not silently accepted." }
    ]}
  ],
  "CHANNELS_THROUGH:FinancingSource:FinancialInstrument": [
    { id:"e3", by:"AT", when:"3 days ago", body:"Love that this is finally explicit. Blended finance queries were impossible before." }
  ],
  "CONTRIBUTES_TO:Solution:ResilienceGoal": [
    { id:"e4", by:"SG", when:"yesterday", body:"Should this be renamed <strong>CLAIMS_TO_CONTRIBUTE</strong>? The naming hides that this is assertion-based, not evidence-based. DEMONSTRATES_PROGRESS_ON is the evidence edge." }
  ],
  "SHAPES:UrbanSystem:Vulnerability": [
    { id:"e5", by:"JK", when:"4 hours ago", body:"This is my favorite new edge. Captures the \"aging infrastructure creates vulnerability\" story that AR6 keeps insisting on." }
  ],
};
