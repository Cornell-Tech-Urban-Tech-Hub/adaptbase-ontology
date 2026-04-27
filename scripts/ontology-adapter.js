// Ontology Adapter: Converts ontology JSON → D3 graph format
// Auto-assigns clusters based on semantic analysis

(function() {
  const CLUSTER_ASSIGNMENTS = {
    // Core
    'Solution': 'Core',

    // Threat
    'Hazard': 'Threat',
    'Vulnerability': 'Threat',
    'ExposureUnit': 'Threat',
    'Barrier': 'Threat',

    // Place
    'Location': 'Place',
    'UrbanSystem': 'Place',

    // Actors
    'Stakeholder': 'Actors',
    'Supplier': 'Actors',

    // Outcomes
    'Outcome': 'Outcomes',
    'Indicator': 'Outcomes',
    'ResilienceGoal': 'Outcomes',

    // Finance
    'FinancingSource': 'Finance',
    'FinancialInstrument': 'Finance',

    // Planning
    'Plan': 'Planning',
    'EnablingCondition': 'Planning',
    'Mechanism': 'Planning',
  };

  const ONTOLOGY_VERSIONS = [
    { path: 'ontology/ontology-v0.1.1.json', label: 'v0.1.1', value: 'v0.1.1' },
    { path: 'ontology/ontology-v0.1.json', label: 'v0.1', value: 'v0.1' },
  ];

  let currentOntology = null;
  let currentVersion = null;

  async function loadOntology(versionPath) {
    const response = await fetch(versionPath + '?t=' + Date.now());
    if (!response.ok) throw new Error(`Failed to load ${versionPath}: ${response.status}`);
    const ontology = await response.json();
    currentOntology = ontology;

    // Extract version from path or ontology
    currentVersion = ontology.version || versionPath.match(/v\d+\.\d+(\.\d+)?/)?.[0] || 'unknown';

    return ontology;
  }

  function ontologyToGraph(ontology) {
    // Build nodes from types
    const nodes = ontology.types.map(type => {
      const cluster = CLUSTER_ASSIGNMENTS[type.id] || 'Planning';

      // Calculate degree (for sizing)
      const outgoing = ontology.relationships.filter(r => r.source === type.id).length;
      const incoming = ontology.relationships.filter(r => r.target === type.id).length;
      const degree = outgoing + incoming;

      return {
        id: type.id,
        label: type.label,
        cluster: cluster,
        degree: degree,
        definition: type.definition || '',
        properties: type.properties || [],
        vocabulary_bindings: type.vocabulary_bindings || [],
        evidence_cases: type.evidence_cases || [],
        notes: type.notes || '',
        schema_source: type.schema_source || '',
        // Raw type data for editing
        _raw: type,
      };
    });

    // Build edges from relationships
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
      // Store original source/target IDs for comments key
      _sourceId: rel.source,
      _targetId: rel.target,
      // Raw relationship data for editing
      _raw: rel,
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

  function getCurrentOntology() {
    return currentOntology;
  }

  function getCurrentVersion() {
    return currentVersion;
  }

  function getVersions() {
    return ONTOLOGY_VERSIONS;
  }

  function updateNodeInOntology(nodeId, updates) {
    if (!currentOntology) return;
    const type = currentOntology.types.find(t => t.id === nodeId);
    if (!type) return;

    // Apply updates
    Object.keys(updates).forEach(key => {
      type[key] = updates[key];
    });

    // Update timestamp
    currentOntology.updated = new Date().toISOString();
  }

  function updateEdgeInOntology(edgeId, updates) {
    if (!currentOntology) return;
    const rel = currentOntology.relationships.find(r => r.id === edgeId);
    if (!rel) return;

    // Apply updates
    Object.keys(updates).forEach(key => {
      rel[key] = updates[key];
    });

    // Update timestamp
    currentOntology.updated = new Date().toISOString();
  }

  function addTypeToOntology(typeData) {
    if (!currentOntology) return;
    currentOntology.types.push(typeData);
    currentOntology.updated = new Date().toISOString();
  }

  function addRelationshipToOntology(relData) {
    if (!currentOntology) return;
    currentOntology.relationships.push(relData);
    currentOntology.updated = new Date().toISOString();
  }

  function deleteTypeFromOntology(typeId) {
    if (!currentOntology) return;
    currentOntology.types = currentOntology.types.filter(t => t.id !== typeId);
    currentOntology.relationships = currentOntology.relationships.filter(
      r => r.source !== typeId && r.target !== typeId
    );
    currentOntology.updated = new Date().toISOString();
  }

  function deleteRelationshipFromOntology(relId) {
    if (!currentOntology) return;
    currentOntology.relationships = currentOntology.relationships.filter(r => r.id !== relId);
    currentOntology.updated = new Date().toISOString();
  }

  // ---- Property helpers ----
  function updateNodeProperty(nodeId, propIndex, field, value) {
    if (!currentOntology) return;
    const type = currentOntology.types.find(t => t.id === nodeId);
    if (!type || !type.properties || !type.properties[propIndex]) return;
    type.properties[propIndex][field] = value;
    currentOntology.updated = new Date().toISOString();
  }

  function addNodeProperty(nodeId, propData) {
    if (!currentOntology) return;
    const type = currentOntology.types.find(t => t.id === nodeId);
    if (!type) return;
    if (!type.properties) type.properties = [];
    type.properties.push(propData);
    currentOntology.updated = new Date().toISOString();
  }

  function deleteNodeProperty(nodeId, propIndex) {
    if (!currentOntology) return;
    const type = currentOntology.types.find(t => t.id === nodeId);
    if (!type || !type.properties) return;
    type.properties.splice(propIndex, 1);
    currentOntology.updated = new Date().toISOString();
  }

  function updateEdgeProperty(edgeId, propIndex, field, value) {
    if (!currentOntology) return;
    const rel = currentOntology.relationships.find(r => r.id === edgeId);
    if (!rel || !rel.properties || !rel.properties[propIndex]) return;
    rel.properties[propIndex][field] = value;
    currentOntology.updated = new Date().toISOString();
  }

  function addEdgeProperty(edgeId, propData) {
    if (!currentOntology) return;
    const rel = currentOntology.relationships.find(r => r.id === edgeId);
    if (!rel) return;
    if (!rel.properties) rel.properties = [];
    rel.properties.push(propData);
    currentOntology.updated = new Date().toISOString();
  }

  function deleteEdgeProperty(edgeId, propIndex) {
    if (!currentOntology) return;
    const rel = currentOntology.relationships.find(r => r.id === edgeId);
    if (!rel || !rel.properties) return;
    rel.properties.splice(propIndex, 1);
    currentOntology.updated = new Date().toISOString();
  }

  function getOntologyTypes() {
    if (!currentOntology) return [];
    return currentOntology.types || [];
  }

  function generateRelationshipId(label) {
    // Convert "produces" to "PRODUCES", "is contributing to" to "IS_CONTRIBUTING_TO"
    return label
      .toUpperCase()
      .replace(/[^A-Z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '');
  }

  function exportOntologyJSON() {
    if (!currentOntology) return null;
    return JSON.stringify(currentOntology, null, 2);
  }

  // Expose API
  window.OntologyAdapter = {
    loadOntology,
    ontologyToGraph,
    getCurrentOntology,
    getCurrentVersion,
    getVersions,
    getOntologyTypes,
    generateRelationshipId,
    updateNodeInOntology,
    updateEdgeInOntology,
    addTypeToOntology,
    addRelationshipToOntology,
    deleteTypeFromOntology,
    deleteRelationshipFromOntology,
    updateNodeProperty,
    addNodeProperty,
    deleteNodeProperty,
    updateEdgeProperty,
    addEdgeProperty,
    deleteEdgeProperty,
    exportOntologyJSON,
  };
})();
