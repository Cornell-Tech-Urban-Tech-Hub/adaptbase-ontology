// Bootstrap: orchestrates loading, version selection, edit mode, and UI wiring
document.addEventListener('DOMContentLoaded', async () => {
  let editMode = localStorage.getItem('editMode') === 'true';
  let currentGraphData = null;
  let isDirty = false; // Track unsaved changes

  // Initialize
  await init();

  async function init() {
    renderVersionSelector();
    updateEditModeUI();
    wireHeaderButtons();
    wireSearch();

    // Initialize graph FIRST (sets up canvas and event listeners)
    window.Graph.init();

    // Then load default version (latest)
    const versions = window.OntologyAdapter.getVersions();
    if (versions.length) {
      await loadVersion(versions[0].path);
    }
  }

  function renderVersionSelector() {
    const selector = document.getElementById('version-selector');
    const versions = window.OntologyAdapter.getVersions();

    selector.innerHTML = versions.map(v =>
      `<option value="${v.path}">${v.label}</option>`
    ).join('');

    selector.addEventListener('change', (e) => {
      if (isDirty && !confirm('You have unsaved changes. Switch version anyway?')) {
        // Revert selection
        const currentVersion = window.OntologyAdapter.getCurrentVersion();
        const versions = window.OntologyAdapter.getVersions();
        const current = versions.find(v => v.value === currentVersion);
        if (current) selector.value = current.path;
        return;
      }
      loadVersion(e.target.value);
      markClean();
    });
  }

  async function loadVersion(versionPath) {
    try {
      // Load ontology
      const ontology = await window.OntologyAdapter.loadOntology(versionPath);

      // Convert to graph format
      currentGraphData = window.OntologyAdapter.ontologyToGraph(ontology);

      // Load into graph
      window.Graph.load(currentGraphData);

      // Update UI
      updateStats(currentGraphData);
      updateMeta(currentGraphData.metadata);

      console.log('Loaded:', versionPath, currentGraphData);
    } catch (err) {
      console.error('Failed to load ontology:', err);
      alert(`Failed to load ontology: ${err.message}`);
    }
  }

  // Reload graph from current in-memory ontology (preserves edits)
  function reloadGraph() {
    const ontology = window.OntologyAdapter.getCurrentOntology();
    if (!ontology) return;

    currentGraphData = window.OntologyAdapter.ontologyToGraph(ontology);
    window.Graph.load(currentGraphData);
    updateStats(currentGraphData);
    updateMeta(currentGraphData.metadata);
  }

  function updateStats(graphData) {
    const numTypes = graphData.nodes.length;
    // Use relationship count from source ontology (not rendered edges)
    const ontology = window.OntologyAdapter.getCurrentOntology();
    const numRels = ontology?.relationships?.filter(r => r.source && r.target).length || graphData.edges.length;
    const numVocabs = graphData.metadata.vocabularies?.length || 0;

    // Update stat cards
    document.getElementById('stat-types').textContent = numTypes;
    document.getElementById('stat-rels').textContent = numRels;
    document.getElementById('stat-vocabs').textContent = numVocabs;

    // Update hero text with spelled-out numbers
    document.getElementById('hero-type-count').textContent = numberToWord(numTypes);
    document.getElementById('hero-rel-count').textContent = numberToWord(numRels);
  }

  function numberToWord(n) {
    const words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
      'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen'];
    const tens = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'];

    if (n < 20) return words[n] || n;
    if (n < 100) {
      const digit = n % 10;
      const ten = Math.floor(n / 10);
      return digit === 0 ? tens[ten] : `${tens[ten]}-${words[digit]}`;
    }
    return n; // For numbers >= 100, just use the numeral
  }

  function updateMeta(metadata) {
    const versionEl = document.getElementById('current-version');
    if (versionEl) versionEl.textContent = metadata.version || '—';
    const domainEl = document.getElementById('domain-label');
    if (domainEl) domainEl.textContent = metadata.domain || '—';

    if (metadata.updated) {
      const date = new Date(metadata.updated);
      const formatted = date.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
      document.getElementById('updated-date').textContent = formatted;
    }
  }

  function updateEditModeUI() {
    const btn = document.getElementById('btn-edit-mode');
    const addEntityBtn = document.getElementById('btn-add-entity');

    if (editMode) {
      btn.textContent = 'Exit Edit';
      btn.classList.remove('btn-primary');
      btn.classList.add('btn-secondary');
      if (addEntityBtn) addEntityBtn.style.display = 'inline-flex';
    } else {
      btn.textContent = 'Edit';
      btn.classList.remove('btn-secondary');
      btn.classList.add('btn-primary');
      if (addEntityBtn) addEntityBtn.style.display = 'none';
    }

    // Show/hide save/discard buttons
    updateSaveButtons();

    // Notify inspector if it exists
    if (window.Inspector && window.Inspector.setEditMode) {
      window.Inspector.setEditMode(editMode);
    }
  }

  function markDirty() {
    isDirty = true;
    updateSaveButtons();
  }

  function markClean() {
    isDirty = false;
    updateSaveButtons();
  }

  function updateSaveButtons() {
    const saveBtn = document.getElementById('btn-save');
    const discardBtn = document.getElementById('btn-discard');

    if (editMode && isDirty) {
      saveBtn.style.display = 'inline-flex';
      discardBtn.style.display = 'inline-flex';
    } else {
      saveBtn.style.display = 'none';
      discardBtn.style.display = 'none';
    }
  }

  function wireHeaderButtons() {
    // Edit mode toggle
    document.getElementById('btn-edit-mode').addEventListener('click', () => {
      if (isDirty && !confirm('You have unsaved changes. Switch modes anyway?')) {
        return;
      }
      editMode = !editMode;
      localStorage.setItem('editMode', editMode);
      updateEditModeUI();
    });

    // Save changes
    document.getElementById('btn-save').addEventListener('click', async () => {
      if (!confirm('Save changes as a new version? This will download a JSON file that you need to manually place in the ontology/ directory.')) {
        return;
      }
      await saveAsNewVersion();
    });

    // Discard changes
    document.getElementById('btn-discard').addEventListener('click', () => {
      if (!confirm('Discard all unsaved changes?')) return;
      const selector = document.getElementById('version-selector');
      loadVersion(selector.value);
      markClean();
    });

    // Reload
    document.getElementById('btn-reload').addEventListener('click', () => {
      if (isDirty && !confirm('You have unsaved changes. Reload anyway?')) {
        return;
      }
      const selector = document.getElementById('version-selector');
      loadVersion(selector.value);
      markClean();
    });

    // Export JSON
    document.getElementById('btn-download').addEventListener('click', () => {
      const json = window.OntologyAdapter.exportOntologyJSON();
      if (!json) {
        alert('No ontology loaded');
        return;
      }

      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const version = window.OntologyAdapter.getCurrentVersion() || 'ontology';
      a.download = `ontology-${version}-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    });

    // Add new entity
    document.getElementById('btn-add-entity').addEventListener('click', () => {
      showAddEntityDialog();
    });

    // Vocabularies (modal - to be implemented)
    document.getElementById('btn-vocabularies').addEventListener('click', () => {
      showVocabulariesModal();
    });

    // Sample data (to be implemented)
    document.getElementById('btn-sample').addEventListener('click', () => {
      alert('Sample data viewer coming soon!');
    });

    // Vocabulary modal close
    document.getElementById('vocab-modal-close').addEventListener('click', () => {
      document.getElementById('vocab-modal').classList.remove('show');
    });

    document.getElementById('vocab-modal').addEventListener('click', (e) => {
      if (e.target.id === 'vocab-modal') {
        document.getElementById('vocab-modal').classList.remove('show');
      }
    });
  }

  async function saveAsNewVersion() {
    const ontology = window.OntologyAdapter.getCurrentOntology();
    if (!ontology) {
      alert('No ontology loaded');
      return;
    }

    // Parse current version and increment patch
    const currentVersion = ontology.version || 'v0.1.0';
    const match = currentVersion.match(/v(\d+)\.(\d+)\.(\d+)/);
    if (!match) {
      alert(`Cannot parse version "${currentVersion}". Expected format: v0.1.0`);
      return;
    }

    const [, major, minor, patch] = match;
    const newPatch = parseInt(patch) + 1;
    const newVersion = `v${major}.${minor}.${newPatch}`;

    // Update version in ontology
    ontology.version = newVersion;
    ontology.updated = new Date().toISOString();

    // Export JSON
    const json = JSON.stringify(ontology, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ontology-${newVersion}.json`;
    a.click();
    URL.revokeObjectURL(url);

    // Show instructions
    const instructions = `
Version ${newVersion} has been downloaded.

To use this version:
1. Save the downloaded file to: packages/ontology/ontology/ontology-${newVersion}.json
2. Add this line to ONTOLOGY_VERSIONS in ontology-adapter.js:
   { path: 'ontology/ontology-${newVersion}.json', label: '${newVersion} — [description]', value: '${newVersion}' },
3. Reload this page
    `.trim();

    alert(instructions);
    markClean();
  }

  function showVocabulariesModal() {
    const ontology = window.OntologyAdapter.getCurrentOntology();
    if (!ontology || !ontology.vocabularies) {
      alert('No vocabularies loaded');
      return;
    }

    const modal = document.getElementById('vocab-modal');
    const content = document.getElementById('vocab-modal-content');

    const vocabs = ontology.vocabularies;
    const external = vocabs.filter(v => v.type === 'external');
    const internal = vocabs.filter(v => v.type === 'internal');

    const makeCard = (v) => {
      const isExt = v.type === 'external';
      return `
        <div style="background:var(--bg-1);border:1px solid ${isExt ? 'var(--carnelian)' : 'var(--border-soft)'};border-radius:var(--r-sm);padding:var(--sp-4);margin-bottom:var(--sp-2);cursor:pointer">
          <div style="font-weight:600;color:${isExt ? 'var(--carnelian)' : 'var(--fg-1)'};margin-bottom:4px;font-size:14px">${escapeHtml(v.label)}</div>
          <div style="font-size:12px;color:var(--fg-3);margin-bottom:8px;line-height:1.5">${escapeHtml(v.description)}</div>
          ${v.terms_count ? `<span style="font-family:var(--font-mono);font-size:10px;background:var(--bg-3);padding:3px 8px;border-radius:999px;color:var(--fg-3)">${v.terms_count} terms</span>` : ''}
          ${v.url ? `<span style="font-size:11px;color:var(--carnelian);margin-left:8px">↗ reference</span>` : ''}
        </div>`;
    };

    content.innerHTML = `
      ${external.length > 0 ? `
        <div style="font-family:var(--font-mono);font-size:10px;text-transform:uppercase;letter-spacing:.14em;color:var(--fg-3);font-weight:600;margin-bottom:var(--sp-2)">External (${external.length})</div>
        ${external.map(makeCard).join('')}
      ` : ''}
      ${internal.length > 0 ? `
        <div style="font-family:var(--font-mono);font-size:10px;text-transform:uppercase;letter-spacing:.14em;color:var(--fg-3);font-weight:600;margin:var(--sp-4) 0 var(--sp-2)">Internal (${internal.length})</div>
        ${internal.map(makeCard).join('')}
      ` : ''}
    `;

    modal.classList.add('show');
  }

  function escapeHtml(s) {
    return String(s || '').replace(/[&<>"']/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
    );
  }

  // Search
  function wireSearch() {
    const input = document.getElementById('search');
    const results = document.getElementById('search-results');

    function match(q) {
      q = q.trim().toLowerCase();
      if (!q) return [];
      const out = [];
      for (const n of window.Graph.getNodes()) {
        if (n.label.toLowerCase().includes(q) || n.id.toLowerCase().includes(q)) {
          out.push({ kind: 'node', n });
        }
      }
      for (const l of window.Graph.getLinks()) {
        if (l.label.toLowerCase().includes(q) || l.id.toLowerCase().includes(q)) {
          out.push({ kind: 'edge', l });
        }
      }
      return out.slice(0, 10);
    }

    function render(list) {
      if (!list.length) {
        results.classList.remove('open');
        results.innerHTML = '';
        return;
      }

      results.innerHTML = list.map((r, i) => {
        if (r.kind === 'node') {
          const color = window.Graph.getClusterColor(r.n.cluster);
          return `<div class="result" data-idx="${i}" data-kind="node" data-id="${r.n.id}">
            <span class="swatch" style="background:${color}"></span>
            <span>${escapeHtml(r.n.label)}</span>
            <span class="kind">${escapeHtml(r.n.cluster)}</span>
          </div>`;
        } else {
          return `<div class="result" data-idx="${i}" data-kind="edge" data-sid="${r.l.source.id}" data-tid="${r.l.target.id}" data-eid="${r.l.id}">
            <span class="swatch" style="background:#B31B1B"></span>
            <span><em style="font-family:'Instrument Serif',serif; font-style:italic; color:var(--carnelian);">${escapeHtml(r.l.label)}</em> <span style="color:var(--fg-4); font-size:11px;">${escapeHtml(r.l.source.label)} → ${escapeHtml(r.l.target.label)}</span></span>
            <span class="kind">rel</span>
          </div>`;
        }
      }).join('');

      results.classList.add('open');

      results.querySelectorAll('.result').forEach(el => {
        el.addEventListener('click', () => {
          if (el.dataset.kind === 'node') {
            window.Graph.focusNode(el.dataset.id);
          } else {
            // Focus edge by finding it
            const links = window.Graph.getLinks();
            const edge = links.find(l => l.id === el.dataset.eid);
            if (edge) window.Graph.selectEdge(edge);
          }
          results.classList.remove('open');
          input.value = '';
        });
      });
    }

    input.addEventListener('input', (e) => {
      const list = match(e.target.value);
      render(list);
    });

    input.addEventListener('blur', () => {
      setTimeout(() => results.classList.remove('open'), 200);
    });

    input.addEventListener('focus', (e) => {
      if (e.target.value) {
        const list = match(e.target.value);
        render(list);
      }
    });
  }

  // Expose for debugging and inter-module communication
  window.APP = {
    loadVersion,
    reloadGraph,
    getEditMode: () => editMode,
    getCurrentGraphData: () => currentGraphData,
    markDirty,
    showAddEntityDialog,
  };

  function showAddEntityDialog() {
    const ontology = window.OntologyAdapter.getCurrentOntology();
    if (!ontology) {
      alert('No ontology loaded');
      return;
    }

    const html = `
      <div class="modal show" id="add-entity-modal">
        <div class="modal-content">
          <h3>Create new entity type</h3>
          <div class="form-row">
            <label>ID (PascalCase, no spaces)</label>
            <input type="text" id="new-entity-id" placeholder="MyNewEntity" />
          </div>
          <div class="form-row">
            <label>Label (display name)</label>
            <input type="text" id="new-entity-label" placeholder="My New Entity" />
          </div>
          <div class="form-row">
            <label>Definition</label>
            <textarea id="new-entity-definition" placeholder="What does this entity represent?"></textarea>
          </div>
          <div class="form-row">
            <label>Connect to Solution as spoke?</label>
            <select id="new-entity-connect">
              <option value="yes" selected>Yes — create relationship to Solution</option>
              <option value="no">No — orphan entity (you can add relationships later)</option>
            </select>
          </div>
          <div class="form-row" id="new-entity-rel-row">
            <label>Relationship label (verb)</label>
            <input type="text" id="new-entity-rel-label" placeholder="relates to" />
          </div>
          <div class="modal-buttons">
            <button id="cancel-add-entity">Cancel</button>
            <button class="primary" id="confirm-add-entity">Create</button>
          </div>
        </div>
      </div>
    `;

    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    document.body.appendChild(tempDiv.firstElementChild);

    const modal = document.getElementById('add-entity-modal');

    document.getElementById('new-entity-connect').addEventListener('change', (e) => {
      document.getElementById('new-entity-rel-row').style.display =
        e.target.value === 'yes' ? '' : 'none';
    });

    document.getElementById('cancel-add-entity').addEventListener('click', () => modal.remove());
    document.getElementById('confirm-add-entity').addEventListener('click', () => {
      const id = document.getElementById('new-entity-id').value.trim();
      const label = document.getElementById('new-entity-label').value.trim();
      const definition = document.getElementById('new-entity-definition').value.trim();
      const connect = document.getElementById('new-entity-connect').value;
      const relLabel = document.getElementById('new-entity-rel-label').value.trim();

      if (!id || !label) {
        alert('ID and Label are required');
        return;
      }

      if (!/^[A-Z][a-zA-Z0-9]*$/.test(id)) {
        alert('ID must be PascalCase (e.g., MyEntity)');
        return;
      }

      const ont = window.OntologyAdapter.getCurrentOntology();
      if (ont.types.find(t => t.id === id)) {
        alert(`An entity with id "${id}" already exists`);
        return;
      }

      const newType = {
        id,
        label,
        definition,
        properties: [],
        vocabulary_bindings: [],
        evidence_cases: [],
        notes: '',
      };

      window.OntologyAdapter.addTypeToOntology(newType);

      // Optionally add a relationship to Solution
      if (connect === 'yes' && relLabel) {
        const relId = window.OntologyAdapter.generateRelationshipId(relLabel);
        if (!ont.relationships.find(r => r.id === relId)) {
          window.OntologyAdapter.addRelationshipToOntology({
            id: relId,
            label: relLabel,
            source: 'Solution',
            target: id,
            definition: '',
            properties: [],
          });
        }
      }

      markDirty();
      modal.remove();
      reloadGraph();

      // Focus the new node
      setTimeout(() => {
        if (window.Graph.focusNode) window.Graph.focusNode(id);
      }, 100);
    });
  }
});
