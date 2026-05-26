(function() {
  const CLUSTER_ASSIGNMENTS = {
    // Core — the central hub
    'Solution': 'Solution',
    // Risk — the full hazard/exposure/vulnerability chain + barriers
    'Hazard': 'Risk',
    'Vulnerability': 'Risk',
    'ExposureUnit': 'Risk',
    'Barrier': 'Risk',
    // Context — where solutions operate and who governs them
    'Jurisdiction': 'Context',
    'Place': 'Context',
    'UrbanSystem': 'Context',
    'Stakeholder': 'Context',
    'Supplier': 'Finance',
    'GovernanceStructure': 'Context',
    // Programs — how solutions are planned and delivered
    'Plan': 'Programs',
    'Action': 'Programs',
    'PlanningData': 'Programs',
    'Mechanism': 'Programs',
    'EnablingCondition': 'Programs',
    // Finance — capital flows and instruments
    'FinancingSource': 'Finance',
    'FinancialInstrument': 'Finance',
    'CapitalProject': 'Finance',
    // Outcomes — goals, results, measurement
    'Outcome': 'Outcomes',
    'Indicator': 'Outcomes',
    'ResilienceGoal': 'Outcomes',
  };

  let ONTOLOGY_VERSIONS = [];
  let currentOntology = null;
  let currentVersion = null;
  let loadedEnums = null;

  async function loadVersions() {
    const res = await fetch('../ontology/versions.json?t=' + Date.now());
    if (!res.ok) throw new Error('Failed to load ontology/versions.json');
    ONTOLOGY_VERSIONS = await res.json();
    return ONTOLOGY_VERSIONS;
  }

  async function loadEnums() {
    if (loadedEnums) return loadedEnums;
    const res = await fetch('../ontology/vocabularies/enums.json?t=' + Date.now());
    if (!res.ok) throw new Error('Failed to load ontology/vocabularies/enums.json');
    loadedEnums = await res.json();
    return loadedEnums;
  }

  function resolveEnumValues(binding) {
    if (!loadedEnums || !binding) return [];
    const vocab = loadedEnums[binding.field];
    if (!vocab || !vocab.values) return [];
    return vocab.values.map(v => v.id);
  }

  async function loadOntology(versionPath) {
    const response = await fetch(versionPath + '?t=' + Date.now());
    if (!response.ok) throw new Error(`Failed to load ${versionPath}: ${response.status}`);
    const ontology = await response.json();
    currentOntology = ontology;
    currentVersion = ontology.version || versionPath.match(/v\d+\.\d+(\.\d+)?/)?.[0] || 'unknown';
    return ontology;
  }

  function ontologyToGraph(ontology) {
    const nodes = ontology.types.map(type => {
      const cluster = CLUSTER_ASSIGNMENTS[type.id] || 'Planning';
      const outgoing = ontology.relationships.filter(r => r.source === type.id).length;
      const incoming = ontology.relationships.filter(r => r.target === type.id).length;

      return {
        id: type.id,
        label: type.label,
        cluster,
        degree: outgoing + incoming,
        definition: type.definition || '',
        properties: type.properties || [],
        vocabulary_bindings: type.vocabulary_bindings || [],
        evidence_cases: type.evidence_cases || [],
        notes: type.notes || '',
        schema_source: type.schema_source || '',
      };
    });

    const edges = ontology.relationships.map(rel => ({
      id: rel.id,
      label: rel.label,
      source: rel.source,
      target: rel.target,
      definition: rel.definition || '',
      properties: rel.properties || [],
      cardinality: rel.cardinality || '',
      evidence_cases: rel.evidence_cases || [],
      notes: rel.notes || '',
      _sourceId: rel.source,
      _targetId: rel.target,
    }));

    return {
      nodes,
      edges,
      metadata: {
        version: ontology.version,
        updated: ontology.updated,
        domain: ontology.domain,
        domain_label: ontology.domain_label,
        vocabularies: ontology.vocabularies || [],
        version_notes: ontology.version_notes || [],
      }
    };
  }

  const vocabCache = {};
  const VOCAB_PATHS = {
    'hazards': '../ontology/vocabularies/hazards.json',
    'urban-systems': '../ontology/vocabularies/urban-systems.json',
    'solution-categories': '../ontology/vocabularies/solution-categories.json',
    'crf-goals': '../ontology/vocabularies/crf-goals.json',
    'vulnerable-populations': '../ontology/vocabularies/vulnerable-populations.json',
  };

  async function loadVocab(vocabId) {
    if (vocabCache[vocabId]) return vocabCache[vocabId];
    const path = VOCAB_PATHS[vocabId];
    if (!path) return null;
    try {
      const res = await fetch(path + '?t=' + Date.now());
      if (!res.ok) return null;
      const data = await res.json();
      vocabCache[vocabId] = data;
      return data;
    } catch { return null; }
  }

  function resolveLabel(vocabId, id) {
    const data = vocabCache[vocabId];
    if (!data) return id;
    if (vocabId === 'hazards') {
      for (const cat of (data.categories || [])) {
        const h = (cat.hazards || []).find(h => h.id === id);
        if (h) return h.name;
      }
    } else if (vocabId === 'crf-goals') {
      for (const dim of (data.dimensions || [])) {
        const g = (dim.goals || []).find(g => g.id === id);
        if (g) return g.text || g.name || id;
      }
    } else if (vocabId === 'urban-systems') {
      for (const sec of (data.sectors || [])) {
        if (sec.id === id) return sec.name;
        for (const sys of (sec.systems || [])) {
          if (sys.id === id) return sys.name;
        }
      }
    } else if (vocabId === 'solution-categories') {
      for (const cat of (data.categories || [])) {
        if (cat.id === id) return cat.name;
        for (const sub of (cat.subcategories || [])) {
          if (sub.id === id) return sub.name;
        }
      }
    } else if (vocabId === 'vulnerable-populations') {
      const pop = (data.populations || data.items || []).find(p => p.id === id);
      if (pop) return pop.name || pop.label || id;
    }
    return id;
  }

  window.OntologyAdapter = {
    loadOntology,
    loadVersions,
    loadEnums,
    loadVocab,
    resolveEnumValues,
    resolveLabel,
    ontologyToGraph,
    getCurrentOntology: () => currentOntology,
    getCurrentVersion: () => currentVersion,
    getVersions: () => ONTOLOGY_VERSIONS,
    getEnums: () => loadedEnums,
  };
})();
