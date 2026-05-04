(function () {
  'use strict';

  let ontology = null;
  let baseline = null;
  let vocabFiles = {};
  let vocabBaseline = {};
  let vocabFileList = [];
  let activeTab = 'types';
  let selectedId = null;
  let changeCount = 0;

  // ── Bootstrap ────────────────────────────────────────────────

  async function init() {
    const versions = await fetchJSON('../ontology/versions.json');
    if (!versions.length) { alert('No ontology versions found'); return; }

    ontology = await fetchJSON(versions[0].path);
    baseline = structuredClone(ontology);

    const vfRes = await fetchJSON('/api/vocab-files');
    vocabFileList = vfRes.files || [];
    for (const f of vocabFileList) {
      vocabFiles[f] = await fetchJSON(`../ontology/vocabularies/${f}`);
    }
    vocabBaseline = structuredClone(vocabFiles);

    document.getElementById('version-badge').textContent = ontology.version;
    wireUI();
    renderTab();
  }

  function wireUI() {
    document.querySelectorAll('#tabs button').forEach(btn => {
      btn.addEventListener('click', () => {
        activeTab = btn.dataset.tab;
        selectedId = null;
        document.querySelectorAll('#tabs button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        renderTab();
      });
    });
    document.getElementById('save-btn').addEventListener('click', openSaveModal);
    window.addEventListener('beforeunload', e => {
      if (changeCount > 0) { e.preventDefault(); e.returnValue = ''; }
    });
  }

  // ── Tab routing ──────────────────────────────────────────────

  function renderTab() {
    const sidebar = document.getElementById('sidebar');
    const detail = document.getElementById('detail');

    switch (activeTab) {
      case 'types': renderTypesSidebar(sidebar); break;
      case 'relationships': renderRelsSidebar(sidebar); break;
      case 'vocabularies': renderVocabsSidebar(sidebar); break;
      case 'vocab-files': sidebar.innerHTML = ''; renderVocabFilesTab(detail); break;
      case 'version': sidebar.innerHTML = ''; renderVersionTab(detail); break;
    }

    if (['types', 'relationships', 'vocabularies'].includes(activeTab) && !selectedId) {
      detail.innerHTML = '<div class="empty">Select an item to edit</div>';
    }
  }

  // ── Types tab ────────────────────────────────────────────────

  function renderTypesSidebar(el) {
    const clusters = {};
    for (const t of ontology.types) {
      const c = clusterOf(t.id);
      (clusters[c] = clusters[c] || []).push(t);
    }
    let html = '';
    for (const [cluster, types] of Object.entries(clusters)) {
      html += `<div class="section-header">${esc(cluster)}</div>`;
      for (const t of types) {
        const active = selectedId === t.id ? ' active' : '';
        html += `<div class="item${active}" data-id="${esc(t.id)}">${esc(t.label)}</div>`;
      }
    }
    html += `<div style="padding:10px"><button class="btn-sm primary" id="add-type-btn">+ Add Type</button></div>`;
    el.innerHTML = html;
    el.querySelectorAll('.item').forEach(item => {
      item.addEventListener('click', () => { selectedId = item.dataset.id; renderTab(); });
    });
    el.querySelector('#add-type-btn').addEventListener('click', () => {
      const newType = { id: 'NewType', label: 'New Type', definition: '', properties: [], vocabulary_bindings: [], evidence_cases: [], notes: '' };
      ontology.types.push(newType);
      selectedId = 'NewType';
      updateChangeCount();
      renderTab();
    });
    if (selectedId) renderTypeDetail(selectedId);
  }

  function renderTypeDetail(typeId) {
    const t = ontology.types.find(x => x.id === typeId);
    if (!t) return;
    const detail = document.getElementById('detail');

    const outRels = ontology.relationships.filter(r => r.source === t.id);
    const inRels = ontology.relationships.filter(r => r.target === t.id);

    let relLinksHtml = '';
    if (outRels.length || inRels.length) {
      relLinksHtml = '<div class="section"><div class="section-toggle open" data-toggle="rels"><h4>Relationships</h4><span class="badge">' + (outRels.length + inRels.length) + '</span></div><div class="section-body">';
      if (outRels.length) {
        relLinksHtml += '<div style="margin-bottom:6px;font-size:11px;color:var(--fg-muted);font-weight:600">Outgoing</div><div class="rel-links">';
        for (const r of outRels) {
          relLinksHtml += `<span class="rel-link outgoing" data-nav-rel="${esc(r.id)}">${esc(r.id)} <span class="arrow">&rarr;</span> ${esc(r.target)}</span>`;
        }
        relLinksHtml += '</div>';
      }
      if (inRels.length) {
        relLinksHtml += '<div style="margin-bottom:6px;margin-top:8px;font-size:11px;color:var(--fg-muted);font-weight:600">Incoming</div><div class="rel-links">';
        for (const r of inRels) {
          relLinksHtml += `<span class="rel-link incoming" data-nav-rel="${esc(r.id)}">${esc(r.source)} <span class="arrow">&rarr;</span> ${esc(r.id)}</span>`;
        }
        relLinksHtml += '</div>';
      }
      relLinksHtml += '</div></div>';
    }

    detail.innerHTML = `
      <h3>Type: ${esc(t.label)}</h3>
      <div class="form-row">
        <div class="form-group"><label>ID</label><input data-field="id" value="${esc(t.id)}"></div>
        <div class="form-group"><label>Label</label><input data-field="label" value="${esc(t.label)}"></div>
      </div>
      <div class="form-group"><label>Definition</label><textarea data-field="definition">${esc(t.definition || '')}</textarea></div>
      <div class="form-group"><label>Schema Source</label><input data-field="schema_source" value="${esc(t.schema_source || '')}"></div>
      <div class="form-group"><label>Notes</label><textarea data-field="notes">${esc(t.notes || '')}</textarea></div>

      ${relLinksHtml}

      <div class="section">
        <div class="section-toggle open" data-toggle="props"><h4>Properties</h4><span class="badge">${(t.properties || []).length}</span></div>
        <div class="section-body">
          <div id="props-container"></div>
          <button class="btn-sm primary btn-add" id="add-prop-btn">+ Add Property</button>
        </div>
      </div>

      <div class="section">
        <div class="section-toggle open" data-toggle="bindings"><h4>Vocabulary Bindings</h4><span class="badge">${(t.vocabulary_bindings || []).length}</span></div>
        <div class="section-body">
          <div id="bindings-container"></div>
          <button class="btn-sm primary btn-add" id="add-binding-btn">+ Add Binding</button>
        </div>
      </div>

      <div class="danger-zone">
        <button class="btn-sm danger" id="delete-type-btn">Delete Type</button>
      </div>
    `;

    wireToggles(detail);
    wireRelLinks(detail);

    detail.querySelectorAll('input[data-field], textarea[data-field]').forEach(inp => {
      inp.addEventListener('input', () => {
        t[inp.dataset.field] = inp.value;
        updateChangeCount();
      });
    });

    renderPropsTable(t);
    renderBindingsTable(t);

    detail.querySelector('#add-prop-btn').addEventListener('click', () => {
      t.properties = t.properties || [];
      t.properties.push({ id: '', type: 'string', required: false });
      renderPropsTable(t);
      updateChangeCount();
    });

    detail.querySelector('#add-binding-btn').addEventListener('click', () => {
      t.vocabulary_bindings = t.vocabulary_bindings || [];
      t.vocabulary_bindings.push({ vocab: '', field: '' });
      renderBindingsTable(t);
      updateChangeCount();
    });

    detail.querySelector('#delete-type-btn').addEventListener('click', () => {
      if (confirm(`Delete type "${t.label || t.id}"? This cannot be undone.`)) {
        const idx = ontology.types.indexOf(t);
        if (idx >= 0) ontology.types.splice(idx, 1);
        selectedId = null;
        updateChangeCount();
        renderTab();
      }
    });
  }

  function renderPropsTable(t) {
    const container = document.getElementById('props-container');
    const props = t.properties || [];
    if (!props.length) { container.innerHTML = '<div style="color:#999;font-size:12px">No properties</div>'; return; }

    let html = `<table class="prop-table">
      <tr><th>ID</th><th>Type</th><th>Req</th><th>Vocabulary</th><th>Values</th><th>Note</th><th></th></tr>`;
    props.forEach((p, i) => {
      html += `<tr>
        <td><input value="${esc(p.id || '')}" data-pi="${i}" data-pk="id"></td>
        <td><input value="${esc(p.type || '')}" data-pi="${i}" data-pk="type" style="width:90px"></td>
        <td><select data-pi="${i}" data-pk="required"><option value="true"${p.required ? ' selected' : ''}>Yes</option><option value="false"${!p.required ? ' selected' : ''}>No</option></select></td>
        <td><input value="${esc(p.vocabulary || '')}" data-pi="${i}" data-pk="vocabulary"></td>
        <td><textarea data-pi="${i}" data-pk="values">${esc(Array.isArray(p.values) ? p.values.join(', ') : '')}</textarea></td>
        <td><textarea data-pi="${i}" data-pk="note">${esc(p.note || '')}</textarea></td>
        <td><button class="btn-sm danger" data-remove="${i}">&times;</button></td>
      </tr>`;
    });
    html += '</table>';
    container.innerHTML = html;

    container.querySelectorAll('input[data-pi], textarea[data-pi], select[data-pi]').forEach(inp => {
      inp.addEventListener('input', () => {
        const idx = parseInt(inp.dataset.pi);
        const key = inp.dataset.pk;
        if (key === 'required') {
          props[idx][key] = inp.value === 'true';
        } else if (key === 'values') {
          const raw = inp.value.trim();
          props[idx][key] = raw ? raw.split(',').map(s => s.trim()).filter(Boolean) : undefined;
          if (!props[idx][key] || !props[idx][key].length) delete props[idx][key];
        } else if (key === 'vocabulary') {
          props[idx][key] = inp.value || undefined;
          if (!props[idx][key]) delete props[idx][key];
        } else if (key === 'note') {
          props[idx][key] = inp.value || undefined;
          if (!props[idx][key]) delete props[idx][key];
        } else {
          props[idx][key] = inp.value;
        }
        updateChangeCount();
      });
    });

    container.querySelectorAll('[data-remove]').forEach(btn => {
      btn.addEventListener('click', () => {
        props.splice(parseInt(btn.dataset.remove), 1);
        renderPropsTable(t);
        updateChangeCount();
      });
    });
  }

  function renderBindingsTable(t) {
    const container = document.getElementById('bindings-container');
    const bindings = t.vocabulary_bindings || [];
    if (!bindings.length) { container.innerHTML = '<div style="color:#999;font-size:12px">No bindings</div>'; return; }

    let html = `<table class="prop-table">
      <tr><th>Vocabulary</th><th>Field(s)</th><th>Note</th><th></th></tr>`;
    bindings.forEach((b, i) => {
      html += `<tr>
        <td><input value="${esc(b.vocab || '')}" data-bi="${i}" data-bk="vocab"></td>
        <td><input value="${esc(b.field || '')}" data-bi="${i}" data-bk="field"></td>
        <td><input value="${esc(b.note || '')}" data-bi="${i}" data-bk="note"></td>
        <td><button class="btn-sm danger" data-bremove="${i}">&times;</button></td>
      </tr>`;
    });
    html += '</table>';
    container.innerHTML = html;

    container.querySelectorAll('input[data-bi]').forEach(inp => {
      inp.addEventListener('input', () => {
        const idx = parseInt(inp.dataset.bi);
        bindings[idx][inp.dataset.bk] = inp.value || undefined;
        if (!bindings[idx][inp.dataset.bk]) delete bindings[idx][inp.dataset.bk];
        updateChangeCount();
      });
    });

    container.querySelectorAll('[data-bremove]').forEach(btn => {
      btn.addEventListener('click', () => {
        bindings.splice(parseInt(btn.dataset.bremove), 1);
        renderBindingsTable(t);
        updateChangeCount();
      });
    });
  }

  // ── Relationships tab ────────────────────────────────────────

  function renderRelsSidebar(el) {
    let html = '';
    for (const r of ontology.relationships) {
      const active = selectedId === r.id ? ' active' : '';
      html += `<div class="item${active}" data-id="${esc(r.id)}">
        ${esc(r.id)}
        <div class="sub">${esc(r.source)} &rarr; ${esc(r.target)}</div>
      </div>`;
    }
    html += `<div style="padding:10px"><button class="btn-sm primary" id="add-rel-btn">+ Add Relationship</button></div>`;
    el.innerHTML = html;
    el.querySelectorAll('.item').forEach(item => {
      item.addEventListener('click', () => { selectedId = item.dataset.id; renderTab(); });
    });
    el.querySelector('#add-rel-btn').addEventListener('click', () => {
      const firstType = ontology.types[0]?.id || '';
      const newRel = { id: 'NEW_RELATIONSHIP', label: 'new_relationship', source: firstType, target: firstType, definition: '', properties: [], cardinality: 'many-to-many', evidence_cases: [], notes: '' };
      ontology.relationships.push(newRel);
      selectedId = 'NEW_RELATIONSHIP';
      updateChangeCount();
      renderTab();
    });
    if (selectedId) renderRelDetail(selectedId);
  }

  function renderRelDetail(relId) {
    const r = ontology.relationships.find(x => x.id === relId);
    if (!r) return;
    const detail = document.getElementById('detail');
    const sourceOpts = ontology.types.map(t => `<option value="${esc(t.id)}"${t.id === r.source ? ' selected' : ''}>${esc(t.id)}</option>`).join('');
    const targetOpts = ontology.types.map(t => `<option value="${esc(t.id)}"${t.id === r.target ? ' selected' : ''}>${esc(t.id)}</option>`).join('');

    detail.innerHTML = `
      <h3>Relationship: ${esc(r.id)}</h3>
      <div style="margin-bottom:12px">
        <span class="backlink" data-nav-type="${esc(r.source)}">${esc(r.source)}</span>
        <span style="color:var(--fg-faint);margin:0 6px">&rarr;</span>
        <span style="font-family:var(--mono);font-weight:600;font-size:12px">${esc(r.id)}</span>
        <span style="color:var(--fg-faint);margin:0 6px">&rarr;</span>
        <span class="backlink" data-nav-type="${esc(r.target)}">${esc(r.target)}</span>
      </div>
      <div class="form-row">
        <div class="form-group"><label>ID</label><input data-field="id" value="${esc(r.id)}"></div>
        <div class="form-group"><label>Label</label><input data-field="label" value="${esc(r.label || '')}"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>Source</label><select data-field="source">${sourceOpts}</select></div>
        <div class="form-group"><label>Target</label><select data-field="target">${targetOpts}</select></div>
      </div>
      <div class="form-group"><label>Definition</label><textarea data-field="definition">${esc(r.definition || '')}</textarea></div>
      <div class="form-row">
        <div class="form-group"><label>Cardinality</label><input data-field="cardinality" value="${esc(r.cardinality || '')}"></div>
        <div class="form-group"><label>Schema Source</label><input data-field="schema_source" value="${esc(r.schema_source || '')}"></div>
      </div>
      <div class="form-group"><label>Notes</label><textarea data-field="notes">${esc(r.notes || '')}</textarea></div>

      <div class="section">
        <div class="section-toggle open" data-toggle="rel-props"><h4>Properties</h4><span class="badge">${(r.properties || []).length}</span></div>
        <div class="section-body">
          <div id="rel-props-container"></div>
          <button class="btn-sm primary btn-add" id="add-rel-prop-btn">+ Add Property</button>
        </div>
      </div>

      <div class="danger-zone">
        <button class="btn-sm danger" id="delete-rel-btn">Delete Relationship</button>
      </div>
    `;

    wireToggles(detail);
    wireTypeBacklinks(detail);

    detail.querySelectorAll('input[data-field], textarea[data-field], select[data-field]').forEach(inp => {
      inp.addEventListener('input', () => {
        r[inp.dataset.field] = inp.value;
        updateChangeCount();
      });
      inp.addEventListener('change', () => {
        r[inp.dataset.field] = inp.value;
        updateChangeCount();
      });
    });

    renderRelPropsTable(r);

    detail.querySelector('#add-rel-prop-btn').addEventListener('click', () => {
      r.properties = r.properties || [];
      r.properties.push({ id: '', type: 'string', required: false });
      renderRelPropsTable(r);
      updateChangeCount();
    });

    detail.querySelector('#delete-rel-btn').addEventListener('click', () => {
      if (confirm(`Delete relationship "${r.id}"? This cannot be undone.`)) {
        const idx = ontology.relationships.indexOf(r);
        if (idx >= 0) ontology.relationships.splice(idx, 1);
        selectedId = null;
        updateChangeCount();
        renderTab();
      }
    });
  }

  function renderRelPropsTable(r) {
    const container = document.getElementById('rel-props-container');
    const props = r.properties || [];
    if (!props.length) { container.innerHTML = '<div style="color:#999;font-size:12px">No properties</div>'; return; }

    let html = `<table class="prop-table">
      <tr><th>ID</th><th>Type</th><th>Req</th><th>Values</th><th>Note</th><th></th></tr>`;
    props.forEach((p, i) => {
      html += `<tr>
        <td><input value="${esc(p.id || '')}" data-rpi="${i}" data-rpk="id"></td>
        <td><input value="${esc(p.type || '')}" data-rpi="${i}" data-rpk="type" style="width:90px"></td>
        <td><select data-rpi="${i}" data-rpk="required"><option value="true"${p.required ? ' selected' : ''}>Yes</option><option value="false"${!p.required ? ' selected' : ''}>No</option></select></td>
        <td><textarea data-rpi="${i}" data-rpk="values">${esc(Array.isArray(p.values) ? p.values.join(', ') : '')}</textarea></td>
        <td><textarea data-rpi="${i}" data-rpk="note">${esc(p.note || '')}</textarea></td>
        <td><button class="btn-sm danger" data-rp-remove="${i}">&times;</button></td>
      </tr>`;
    });
    html += '</table>';
    container.innerHTML = html;

    container.querySelectorAll('input[data-rpi], textarea[data-rpi], select[data-rpi]').forEach(inp => {
      inp.addEventListener('input', () => {
        const idx = parseInt(inp.dataset.rpi);
        const key = inp.dataset.rpk;
        if (key === 'required') props[idx][key] = inp.value === 'true';
        else if (key === 'values') {
          const raw = inp.value.trim();
          props[idx][key] = raw ? raw.split(',').map(s => s.trim()).filter(Boolean) : undefined;
          if (!props[idx][key] || !props[idx][key].length) delete props[idx][key];
        } else {
          props[idx][key] = inp.value || undefined;
          if (!props[idx][key]) delete props[idx][key];
        }
        updateChangeCount();
      });
    });

    container.querySelectorAll('[data-rp-remove]').forEach(btn => {
      btn.addEventListener('click', () => {
        props.splice(parseInt(btn.dataset.rpRemove), 1);
        renderRelPropsTable(r);
        updateChangeCount();
      });
    });
  }

  // ── Vocabularies tab (ontology-embedded vocab references) ───

  function renderVocabsSidebar(el) {
    const vocabs = ontology.vocabularies || [];
    let html = '';
    for (const v of vocabs) {
      const active = selectedId === v.id ? ' active' : '';
      html += `<div class="item${active}" data-id="${esc(v.id)}">
        ${esc(v.label || v.id)}
        <div class="sub">${esc(v.type || '')}${v.terms_count ? ` (${v.terms_count} terms)` : ''}</div>
      </div>`;
    }
    html += `<div style="padding:10px"><button class="btn-sm primary" id="add-vocab-btn">+ Add Vocabulary</button></div>`;
    el.innerHTML = html;

    el.querySelectorAll('.item').forEach(item => {
      item.addEventListener('click', () => { selectedId = item.dataset.id; renderTab(); });
    });

    const addBtn = el.querySelector('#add-vocab-btn');
    if (addBtn) addBtn.addEventListener('click', () => {
      ontology.vocabularies = ontology.vocabularies || [];
      const newV = { id: 'new-vocab', label: 'New Vocabulary', type: 'internal', description: '' };
      ontology.vocabularies.push(newV);
      selectedId = newV.id;
      updateChangeCount();
      renderTab();
    });

    if (selectedId) renderVocabDetail(selectedId);
  }

  function renderVocabDetail(vocabId) {
    const vocabs = ontology.vocabularies || [];
    const v = vocabs.find(x => x.id === vocabId);
    if (!v) return;
    const detail = document.getElementById('detail');
    const idx = vocabs.indexOf(v);

    detail.innerHTML = `
      <h3>Vocabulary: ${esc(v.label || v.id)}</h3>
      <div class="form-row">
        <div class="form-group"><label>ID</label><input data-field="id" value="${esc(v.id || '')}"></div>
        <div class="form-group"><label>Label</label><input data-field="label" value="${esc(v.label || '')}"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>Type</label><select data-field="type">
          <option value="internal"${v.type === 'internal' ? ' selected' : ''}>Internal</option>
          <option value="external"${v.type === 'external' ? ' selected' : ''}>External</option>
        </select></div>
        <div class="form-group"><label>Terms Count</label><input data-field="terms_count" type="number" value="${v.terms_count || ''}"></div>
      </div>
      <div class="form-group"><label>URL</label><input data-field="url" value="${esc(v.url || '')}"></div>
      <div class="form-group"><label>Description</label><textarea data-field="description">${esc(v.description || '')}</textarea></div>
      <div class="form-group"><label>Bound To (comma-separated)</label><input data-field="bound_to" value="${esc(Array.isArray(v.bound_to) ? v.bound_to.join(', ') : '')}"></div>
      <div class="form-group"><label>Note</label><textarea data-field="note">${esc(v.note || '')}</textarea></div>
      <div style="margin-top:12px"><button class="btn-sm danger" id="remove-vocab-btn">Remove Vocabulary</button></div>
    `;

    detail.querySelectorAll('input[data-field], textarea[data-field], select[data-field]').forEach(inp => {
      const handler = () => {
        const key = inp.dataset.field;
        if (key === 'bound_to') {
          v[key] = inp.value.split(',').map(s => s.trim()).filter(Boolean);
        } else if (key === 'terms_count') {
          v[key] = inp.value ? parseInt(inp.value) : null;
        } else {
          v[key] = inp.value || undefined;
          if (!v[key]) delete v[key];
        }
        updateChangeCount();
      };
      inp.addEventListener('input', handler);
      inp.addEventListener('change', handler);
    });

    detail.querySelector('#remove-vocab-btn').addEventListener('click', () => {
      if (confirm(`Remove vocabulary "${v.label || v.id}"?`)) {
        vocabs.splice(idx, 1);
        selectedId = null;
        updateChangeCount();
        renderTab();
      }
    });
  }

  // ── Vocab Files tab ──────────────────────────────────────────

  let currentVocabFile = null;

  function renderVocabFilesTab(detail) {
    if (!currentVocabFile && vocabFileList.length) currentVocabFile = vocabFileList[0];

    const opts = vocabFileList.map(f =>
      `<option value="${esc(f)}"${f === currentVocabFile ? ' selected' : ''}>${esc(f)}</option>`
    ).join('');

    detail.innerHTML = `
      <h3>Vocabulary Files</h3>
      <select id="vocab-file-select">${opts}</select>
      <div id="vocab-tree"></div>
    `;

    detail.querySelector('#vocab-file-select').addEventListener('change', e => {
      currentVocabFile = e.target.value;
      renderVocabTree();
    });

    renderVocabTree();
  }

  function renderVocabTree() {
    const container = document.getElementById('vocab-tree');
    if (!currentVocabFile || !vocabFiles[currentVocabFile]) {
      container.innerHTML = '<div class="empty">No file selected</div>';
      return;
    }
    container.innerHTML = '';
    const data = vocabFiles[currentVocabFile];
    container.appendChild(buildTreeNode(data, [], currentVocabFile));
  }

  function buildTreeNode(obj, path, fileKey) {
    const frag = document.createDocumentFragment();

    if (Array.isArray(obj)) {
      obj.forEach((item, i) => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'tree-array-item';

        if (typeof item === 'object' && item !== null) {
          const label = item.id || item.name || `[${i}]`;
          const key = document.createElement('div');
          key.className = 'tree-key open';
          key.textContent = label;
          key.addEventListener('click', () => key.classList.toggle('open'));
          itemDiv.appendChild(key);

          const children = document.createElement('div');
          children.className = 'tree-node';
          children.appendChild(buildTreeNode(item, [...path, i], fileKey));
          itemDiv.appendChild(children);

          key.addEventListener('click', () => {
            children.style.display = children.style.display === 'none' ? '' : 'none';
          });
        } else {
          const leaf = makeLeaf(`[${i}]`, item, val => { obj[i] = val; vocabFileChanged(fileKey); });
          itemDiv.appendChild(leaf);
        }

        const removeBtn = document.createElement('button');
        removeBtn.className = 'btn-sm danger';
        removeBtn.textContent = '×';
        removeBtn.style.marginTop = '2px';
        removeBtn.addEventListener('click', () => {
          obj.splice(i, 1);
          vocabFileChanged(fileKey);
          renderVocabTree();
        });
        itemDiv.appendChild(removeBtn);

        frag.appendChild(itemDiv);
      });

      const addBtn = document.createElement('button');
      addBtn.className = 'btn-sm primary';
      addBtn.textContent = '+ Add Item';
      addBtn.style.marginTop = '4px';
      addBtn.addEventListener('click', () => {
        if (obj.length > 0 && typeof obj[0] === 'object') {
          const template = {};
          for (const k of Object.keys(obj[0])) {
            if (k.startsWith('_')) continue;
            template[k] = typeof obj[0][k] === 'string' ? '' : Array.isArray(obj[0][k]) ? [] : '';
          }
          obj.push(template);
        } else {
          obj.push('');
        }
        vocabFileChanged(fileKey);
        renderVocabTree();
      });
      frag.appendChild(document.createElement('div')).appendChild(addBtn);

    } else if (typeof obj === 'object' && obj !== null) {
      for (const [k, v] of Object.entries(obj)) {
        if (typeof v === 'object' && v !== null) {
          const wrapper = document.createElement('div');
          const key = document.createElement('div');
          key.className = 'tree-key open';
          key.textContent = k;
          wrapper.appendChild(key);

          const children = document.createElement('div');
          children.className = 'tree-node';
          children.appendChild(buildTreeNode(v, [...path, k], fileKey));
          wrapper.appendChild(children);

          key.addEventListener('click', () => {
            key.classList.toggle('open');
            children.style.display = children.style.display === 'none' ? '' : 'none';
          });

          frag.appendChild(wrapper);
        } else {
          frag.appendChild(makeLeaf(k, v, val => { obj[k] = val; vocabFileChanged(fileKey); }));
        }
      }
    }

    return frag;
  }

  function makeLeaf(label, value, onChange) {
    const div = document.createElement('div');
    div.className = 'tree-leaf';
    const lbl = document.createElement('label');
    lbl.textContent = label;
    div.appendChild(lbl);

    if (typeof value === 'boolean') {
      const sel = document.createElement('select');
      sel.innerHTML = `<option value="true"${value ? ' selected' : ''}>true</option><option value="false"${!value ? ' selected' : ''}>false</option>`;
      sel.addEventListener('change', () => onChange(sel.value === 'true'));
      div.appendChild(sel);
    } else if (typeof value === 'number') {
      const inp = document.createElement('input');
      inp.type = 'number';
      inp.value = value;
      inp.addEventListener('input', () => onChange(parseFloat(inp.value) || 0));
      div.appendChild(inp);
    } else {
      const str = String(value ?? '');
      if (str.length > 60) {
        const ta = document.createElement('textarea');
        ta.value = str;
        ta.addEventListener('input', () => onChange(ta.value));
        div.appendChild(ta);
      } else {
        const inp = document.createElement('input');
        inp.value = str;
        inp.addEventListener('input', () => onChange(inp.value));
        div.appendChild(inp);
      }
    }
    return div;
  }

  function vocabFileChanged(_fileKey) {
    updateChangeCount();
  }

  // ── Version tab ──────────────────────────────────────────────

  function renderVersionTab(detail) {
    const vn = ontology.version_notes || [];
    let historyHtml = '';
    for (const note of vn) {
      historyHtml += `<div style="margin-bottom:8px"><strong>${esc(note.version)}</strong> (${esc(note.date || '')})<ul style="margin:4px 0 0 20px;font-size:12px">`;
      for (const c of (note.changes || [])) historyHtml += `<li>${esc(c)}</li>`;
      historyHtml += '</ul></div>';
    }

    detail.innerHTML = `
      <h3>Version Information</h3>
      <div class="version-card">
        <div class="form-row">
          <div class="form-group"><label>Current Version</label><input value="${esc(ontology.version)}" disabled></div>
          <div class="form-group"><label>Last Updated</label><input value="${esc(ontology.updated || '')}" disabled></div>
        </div>
        <div class="form-group"><label>Domain</label><input value="${esc(ontology.domain_label || ontology.domain || '')}" disabled></div>
        <div class="form-group"><label>Update Note</label><textarea disabled>${esc(ontology.update_note || '')}</textarea></div>
      </div>
      <h4>Version History</h4>
      <div class="version-card" style="max-height:300px;overflow-y:auto">${historyHtml || '<div style="color:#999">No version history</div>'}</div>
    `;
  }

  // ── Change tracking ──────────────────────────────────────────

  function updateChangeCount() {
    const ontologyChanged = JSON.stringify(ontology) !== JSON.stringify(baseline);
    const vocabChanged = JSON.stringify(vocabFiles) !== JSON.stringify(vocabBaseline);

    let count = 0;
    const details = [];

    if (ontologyChanged) {
      const typeDiffs = countArrayDiffs(baseline.types, ontology.types, 'id');
      const relDiffs = countArrayDiffs(baseline.relationships, ontology.relationships, 'id');
      const vocDiffs = countArrayDiffs(baseline.vocabularies || [], ontology.vocabularies || [], 'id');
      if (typeDiffs) { count += typeDiffs; details.push(`${typeDiffs} type change${typeDiffs > 1 ? 's' : ''}`); }
      if (relDiffs) { count += relDiffs; details.push(`${relDiffs} relationship change${relDiffs > 1 ? 's' : ''}`); }
      if (vocDiffs) { count += vocDiffs; details.push(`${vocDiffs} vocabulary ref change${vocDiffs > 1 ? 's' : ''}`); }
      if (!count && ontologyChanged) { count = 1; details.push('metadata changes'); }
    }

    if (vocabChanged) {
      let vfCount = 0;
      for (const f of vocabFileList) {
        if (JSON.stringify(vocabFiles[f]) !== JSON.stringify(vocabBaseline[f])) vfCount++;
      }
      if (vfCount) { count += vfCount; details.push(`${vfCount} vocab file${vfCount > 1 ? 's' : ''} modified`); }
    }

    changeCount = count;

    const el = document.getElementById('change-status');
    const btn = document.getElementById('save-btn');
    if (count > 0) {
      el.className = 'changes dirty';
      el.textContent = `Unsaved changes: ${count} (${details.join(', ')})`;
      el.title = details.join('\n');
      btn.disabled = false;
    } else {
      el.className = 'changes clean';
      el.textContent = 'No unsaved changes';
      el.title = '';
      btn.disabled = true;
    }
  }

  function countArrayDiffs(a, b, key) {
    let diffs = 0;
    const aMap = new Map(a.map(x => [x[key], JSON.stringify(x)]));
    const bMap = new Map(b.map(x => [x[key], JSON.stringify(x)]));

    for (const [k, v] of bMap) {
      if (!aMap.has(k)) diffs++;
      else if (aMap.get(k) !== v) diffs++;
    }
    for (const k of aMap.keys()) {
      if (!bMap.has(k)) diffs++;
    }
    return diffs;
  }

  // ── Save modal ───────────────────────────────────────────────

  function openSaveModal() {
    const cur = ontology.version;
    const parts = parseVersion(cur);
    const patch = `v${parts.major}.${parts.minor}.${parts.patch + 1}`;
    const minor = `v${parts.major}.${parts.minor + 1}.0`;
    const major = `v${parts.major + 1}.0.0`;

    const recommendation = recommendBump();

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
      <div class="modal">
        <h3>Save New Version</h3>
        <p style="font-size:13px;color:#666;margin-bottom:12px">Current version: <strong>${esc(cur)}</strong></p>

        <div class="bump-options">
          <div class="bump-option${recommendation === 'patch' ? ' recommended' : ''}" data-bump="patch">
            <div class="bump-label">Patch</div>
            <div class="bump-version">${esc(patch)}</div>
            <div class="bump-desc">Fixes, typos, notes</div>
          </div>
          <div class="bump-option${recommendation === 'minor' ? ' recommended' : ''}" data-bump="minor">
            <div class="bump-label">Minor</div>
            <div class="bump-version">${esc(minor)}</div>
            <div class="bump-desc">New types, relationships, vocab changes</div>
          </div>
          <div class="bump-option${recommendation === 'major' ? ' recommended' : ''}" data-bump="major">
            <div class="bump-label">Major</div>
            <div class="bump-version">${esc(major)}</div>
            <div class="bump-desc">Breaking schema changes</div>
          </div>
        </div>

        <div class="form-group">
          <label>Update Note</label>
          <textarea id="save-note" placeholder="Describe what changed...">${esc(generateChangeNote())}</textarea>
        </div>

        <div class="modal-actions">
          <button id="cancel-save" style="background:#eee">Cancel</button>
          <button id="confirm-save" style="background:#1a73e8;color:#fff" disabled>Save</button>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);

    let selectedBump = null;
    const versions = { patch, minor, major };

    overlay.querySelectorAll('.bump-option').forEach(opt => {
      if (opt.classList.contains('recommended')) {
        opt.classList.add('selected');
        selectedBump = opt.dataset.bump;
        overlay.querySelector('#confirm-save').disabled = false;
      }
      opt.addEventListener('click', () => {
        overlay.querySelectorAll('.bump-option').forEach(o => o.classList.remove('selected'));
        opt.classList.add('selected');
        selectedBump = opt.dataset.bump;
        overlay.querySelector('#confirm-save').disabled = false;
      });
    });

    overlay.querySelector('#cancel-save').addEventListener('click', () => overlay.remove());
    overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });

    overlay.querySelector('#confirm-save').addEventListener('click', async () => {
      const newVersion = versions[selectedBump];
      const note = overlay.querySelector('#save-note').value;
      overlay.remove();
      await doSave(newVersion, note);
    });
  }

  function parseVersion(v) {
    const m = (v || '').match(/^v?(\d+)\.(\d+)(?:\.(\d+))?$/);
    return m ? { major: parseInt(m[1]), minor: parseInt(m[2]), patch: parseInt(m[3] || '0') } : { major: 0, minor: 1, patch: 0 };
  }

  function recommendBump() {
    const typesAdded = ontology.types.some(t => !baseline.types.find(bt => bt.id === t.id));
    const typesRemoved = baseline.types.some(t => !ontology.types.find(ot => ot.id === t.id));
    const relsAdded = ontology.relationships.some(r => !baseline.relationships.find(br => br.id === r.id));
    const relsRemoved = baseline.relationships.some(r => !ontology.relationships.find(or => or.id === r.id));

    if (typesRemoved || relsRemoved) return 'minor';
    if (typesAdded || relsAdded) return 'minor';
    return 'patch';
  }

  function generateChangeNote() {
    const parts = [];
    const statusEl = document.getElementById('change-status');
    if (statusEl) {
      const match = statusEl.textContent.match(/\((.+)\)/);
      if (match) parts.push(match[1]);
    }
    return parts.join('. ') || '';
  }

  async function doSave(newVersion, note) {
    ontology.version = newVersion;
    ontology.updated = new Date().toISOString();
    ontology.update_note = note;

    const versionNotes = ontology.version_notes || [];
    versionNotes.unshift({
      version: newVersion,
      date: new Date().toISOString().slice(0, 10),
      changes: [note]
    });
    ontology.version_notes = versionNotes;

    const versionsEntry = {
      path: `../ontology/ontology-${newVersion}.json`,
      label: newVersion,
      value: newVersion
    };

    try {
      const res = await fetch('/api/save-ontology', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ version: newVersion, data: ontology, versions_entry: versionsEntry })
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.error || 'Save failed');

      for (const f of vocabFileList) {
        if (JSON.stringify(vocabFiles[f]) !== JSON.stringify(vocabBaseline[f])) {
          const vRes = await fetch('/api/save-vocab', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: f, data: vocabFiles[f] })
          });
          const vResult = await vRes.json();
          if (!vRes.ok) throw new Error(vResult.error || `Failed to save ${f}`);
        }
      }

      baseline = structuredClone(ontology);
      vocabBaseline = structuredClone(vocabFiles);
      document.getElementById('version-badge').textContent = newVersion;
      updateChangeCount();
      alert(`Saved ${newVersion} successfully!`);
    } catch (err) {
      alert(`Save error: ${err.message}`);
    }
  }

  // ── Navigation helpers ────────────────────────────────────────

  function wireToggles(container) {
    container.querySelectorAll('.section-toggle').forEach(toggle => {
      toggle.addEventListener('click', () => {
        toggle.classList.toggle('open');
        toggle.closest('.section').classList.toggle('collapsed');
      });
    });
  }

  function wireRelLinks(container) {
    container.querySelectorAll('[data-nav-rel]').forEach(el => {
      el.addEventListener('click', () => {
        activeTab = 'relationships';
        selectedId = el.dataset.navRel;
        document.querySelectorAll('#tabs button').forEach(b => b.classList.remove('active'));
        document.querySelector('#tabs button[data-tab="relationships"]').classList.add('active');
        renderTab();
      });
    });
  }

  function wireTypeBacklinks(container) {
    container.querySelectorAll('[data-nav-type]').forEach(el => {
      el.addEventListener('click', () => {
        activeTab = 'types';
        selectedId = el.dataset.navType;
        document.querySelectorAll('#tabs button').forEach(b => b.classList.remove('active'));
        document.querySelector('#tabs button[data-tab="types"]').classList.add('active');
        renderTab();
      });
    });
  }

  // ── Utilities ────────────────────────────────────────────────

  async function fetchJSON(url) {
    const res = await fetch(url + '?t=' + Date.now());
    if (!res.ok) throw new Error(`Failed to load ${url}: ${res.status}`);
    return res.json();
  }

  function esc(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  const CLUSTER_ASSIGNMENTS = {
    'Solution': 'Core', 'Hazard': 'Threat', 'Vulnerability': 'Threat', 'ExposureUnit': 'Threat', 'Barrier': 'Threat',
    'Location': 'Place', 'UrbanSystem': 'Place',
    'Stakeholder': 'Actors', 'Supplier': 'Actors',
    'Outcome': 'Outcomes', 'Indicator': 'Outcomes', 'ResilienceGoal': 'Outcomes',
    'FinancingSource': 'Finance', 'FinancialInstrument': 'Finance',
    'Plan': 'Planning', 'EnablingCondition': 'Planning', 'Mechanism': 'Planning', 'PlanningData': 'Planning',
  };
  function clusterOf(id) { return CLUSTER_ASSIGNMENTS[id] || 'Other'; }

  // ── Go ───────────────────────────────────────────────────────

  init().catch(err => {
    document.getElementById('detail').innerHTML = `<div class="empty" style="color:red">Error: ${esc(err.message)}</div>`;
    console.error(err);
  });
})();
