(function() {
  const CLUSTER_ASSIGNMENTS = {
    'Solution': 'Core',
    'Hazard': 'Threat',
    'Vulnerability': 'Threat',
    'ExposureUnit': 'Threat',
    'Barrier': 'Threat',
    'Location': 'Place',
    'UrbanSystem': 'Place',
    'Stakeholder': 'Actors',
    'Supplier': 'Actors',
    'Outcome': 'Outcomes',
    'Indicator': 'Outcomes',
    'ResilienceGoal': 'Outcomes',
    'FinancingSource': 'Finance',
    'FinancialInstrument': 'Finance',
    'Plan': 'Planning',
    'Action': 'Planning',
    'EnablingCondition': 'Planning',
    'Mechanism': 'Planning',
  };

  let ONTOLOGY_VERSIONS = [];
  let currentOntology = null;
  let currentVersion = null;

  async function loadVersions() {
    const res = await fetch('ontology/versions.json?t=' + Date.now());
    if (!res.ok) throw new Error('Failed to load ontology/versions.json');
    ONTOLOGY_VERSIONS = await res.json();
    return ONTOLOGY_VERSIONS;
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
      }
    };
  }

  window.OntologyAdapter = {
    loadOntology,
    loadVersions,
    ontologyToGraph,
    getCurrentOntology: () => currentOntology,
    getCurrentVersion: () => currentVersion,
    getVersions: () => ONTOLOGY_VERSIONS,
  };
})();
