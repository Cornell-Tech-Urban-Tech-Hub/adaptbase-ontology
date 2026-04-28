document.addEventListener('DOMContentLoaded', async () => {
  let currentGraphData = null;

  await init();

  async function init() {
    await window.OntologyAdapter.loadVersions();
    renderVersionSelector();
    wireHeaderButtons();
    wireSearch();

    window.Graph.init();

    const versions = window.OntologyAdapter.getVersions();
    if (versions.length) {
      await loadVersion(versions[0].path);
    }
  }

  async function renderVersionSelector() {
    const selector = document.getElementById('version-selector');
    const versions = window.OntologyAdapter.getVersions();

    const entries = await Promise.all(versions.map(async (v) => {
      try {
        const res = await fetch(v.path);
        const data = await res.json();
        const dateStr = data.updated
          ? new Date(data.updated).toLocaleDateString('en-US', { day: 'numeric', month: 'short' })
          : '';
        return { ...v, dateStr };
      } catch {
        return { ...v, dateStr: '' };
      }
    }));

    selector.innerHTML = entries.map(v =>
      `<option value="${v.path}">${v.label}${v.dateStr ? ' · ' + v.dateStr : ''}</option>`
    ).join('');

    selector.addEventListener('change', (e) => {
      loadVersion(e.target.value);
    });
  }

  async function loadVersion(versionPath) {
    try {
      const ontology = await window.OntologyAdapter.loadOntology(versionPath);
      currentGraphData = window.OntologyAdapter.ontologyToGraph(ontology);
      window.Graph.load(currentGraphData);
      updateStats(currentGraphData);
      updateMeta(currentGraphData.metadata);
    } catch (err) {
      console.error('Failed to load ontology:', err);
    }
  }

  function updateStats(graphData) {
    const numTypes = graphData.nodes.length;
    const ontology = window.OntologyAdapter.getCurrentOntology();
    const numRels = ontology?.relationships?.filter(r => r.source && r.target).length || graphData.edges.length;
    const numVocabs = graphData.metadata.vocabularies?.length || 0;

    document.getElementById('stat-types').textContent = numTypes;
    document.getElementById('stat-rels').textContent = numRels;
    document.getElementById('stat-vocabs').textContent = numVocabs;

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
    return n;
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

  function wireHeaderButtons() {
    document.getElementById('btn-vocabularies').addEventListener('click', () => {
      showVocabulariesModal();
    });

    document.getElementById('vocab-modal-close').addEventListener('click', () => {
      document.getElementById('vocab-modal').classList.remove('show');
    });

    document.getElementById('vocab-modal').addEventListener('click', (e) => {
      if (e.target.id === 'vocab-modal') {
        document.getElementById('vocab-modal').classList.remove('show');
      }
    });
  }

  const vocabFileMap = {
    'hazards': 'schemas/vocabularies/hazards.json',
    'urban-systems': 'schemas/vocabularies/urban-systems.json',
    'solution-categories': 'schemas/vocabularies/solution-categories.json',
    'crf-goals': 'schemas/vocabularies/crf-goals.json',
    'enums': 'schemas/vocabularies/enums.json',
    'vulnerable-populations': 'schemas/vocabularies/vulnerable-populations.json',
    'resilience-attributes': 'schemas/vocabularies/resilience-attributes.json',
  };
  const vocabCache = {};

  async function fetchVocabData(vocabId) {
    if (vocabCache[vocabId]) return vocabCache[vocabId];
    const path = vocabFileMap[vocabId];
    if (!path) return null;
    try {
      const res = await fetch(path);
      if (!res.ok) return null;
      const data = await res.json();
      vocabCache[vocabId] = data;
      return data;
    } catch { return null; }
  }

  function showVocabulariesModal() {
    const ontology = window.OntologyAdapter.getCurrentOntology();
    if (!ontology || !ontology.vocabularies) return;

    const modal = document.getElementById('vocab-modal');
    const content = document.getElementById('vocab-modal-content');
    const vocabs = [...ontology.vocabularies].sort((a, b) => {
      if (a.type === 'external' && b.type !== 'external') return -1;
      if (a.type !== 'external' && b.type === 'external') return 1;
      return 0;
    });

    content.innerHTML = vocabs.map(v => {
      const isExt = v.type === 'external';
      const bindings = (v.bound_to || []).filter(b => b !== 'various');
      return `
        <div class="vocab-card ${isExt ? 'vocab-external' : ''}" data-vocab-id="${escapeHtml(v.id)}">
          <div class="vocab-header">
            <span class="vocab-chevron">▶</span>
            <div class="vocab-summary">
              <div class="vocab-label">${escapeHtml(v.label)}</div>
              <div class="vocab-desc">${escapeHtml(v.description)}</div>
              <div class="vocab-meta">
                <span class="vocab-badge vocab-badge-type">${isExt ? 'external' : 'internal'}</span>
                ${v.terms_count ? `<span class="vocab-badge">${v.terms_count} terms</span>` : ''}
                ${v.url ? `<a href="${escapeHtml(v.url)}" target="_blank" rel="noopener" class="vocab-ref" onclick="event.stopPropagation()">↗ source</a>` : ''}
              </div>
              ${bindings.length ? `<div class="vocab-bindings">Binds to: ${bindings.map(b => `<code>${escapeHtml(b)}</code>`).join(', ')}</div>` : ''}
            </div>
          </div>
          <div class="vocab-body" hidden>
            <div class="vocab-loading">Loading…</div>
          </div>
        </div>`;
    }).join('');

    content.querySelectorAll('.vocab-card').forEach(card => {
      const header = card.querySelector('.vocab-header');
      const body = card.querySelector('.vocab-body');
      const chevron = card.querySelector('.vocab-chevron');
      let loaded = false;

      header.addEventListener('click', async () => {
        const isOpen = !body.hidden;
        if (isOpen) {
          body.hidden = true;
          chevron.textContent = '▶';
          card.classList.remove('vocab-open');
          return;
        }

        body.hidden = false;
        chevron.textContent = '▼';
        card.classList.add('vocab-open');

        if (!loaded) {
          loaded = true;
          const vocabId = card.dataset.vocabId;
          const data = await fetchVocabData(vocabId);
          if (!data) {
            body.innerHTML = '<div class="vocab-empty">No detailed data available for this vocabulary.</div>';
            return;
          }
          body.innerHTML = renderVocabData(vocabId, data);
          wireVocabExpanders(body);
        }
      });
    });

    modal.classList.add('show');
  }

  function renderVocabData(vocabId, data) {
    if (vocabId === 'hazards') return renderHierarchy(data.categories, 'hazards');
    if (vocabId === 'solution-categories') return renderHierarchy(data.categories, 'subcategories');
    if (vocabId === 'urban-systems') return renderSectors(data.sectors);
    if (vocabId === 'crf-goals') return renderCrfGoals(data.dimensions);
    if (vocabId === 'enums') return renderEnums(data);
    if (vocabId === 'vulnerable-populations') return renderFlatList(data.populations);
    if (vocabId === 'resilience-attributes') return renderFlatList(data.attributes, 'cdp_label');
    return '<div class="vocab-empty">Unknown vocabulary format.</div>';
  }

  function renderHierarchy(categories, childKey) {
    if (!categories || !categories.length) return '<div class="vocab-empty">Empty.</div>';
    return `<ul class="vocab-tree">${categories.map(cat => {
      const children = cat[childKey] || cat.hazards || cat.subcategories || [];
      return `
        <li class="vocab-tree-node ${children.length ? 'has-children' : ''}">
          <div class="vocab-tree-header" ${children.length ? 'data-expandable' : ''}>
            ${children.length ? '<span class="vocab-tree-chevron">▶</span>' : '<span class="vocab-tree-leaf">·</span>'}
            <span class="vocab-tree-name">${escapeHtml(cat.name)}</span>
            ${children.length ? `<span class="vocab-tree-count">${children.length}</span>` : ''}
          </div>
          ${children.length ? `
            <ul class="vocab-tree-children" hidden>
              ${children.map(child => `
                <li class="vocab-tree-node">
                  <div class="vocab-tree-header">
                    <span class="vocab-tree-leaf">·</span>
                    <span class="vocab-tree-name">${escapeHtml(child.name)}</span>
                    ${child.description ? `<span class="vocab-tree-note">${escapeHtml(child.description)}</span>` : ''}
                  </div>
                </li>
              `).join('')}
            </ul>
          ` : ''}
        </li>`;
    }).join('')}</ul>`;
  }

  function renderSectors(sectors) {
    if (!sectors || !sectors.length) return '<div class="vocab-empty">Empty.</div>';
    return `<ul class="vocab-tree">${sectors.map(sector => {
      const subs = sector.subsectors || [];
      return `
        <li class="vocab-tree-node ${subs.length ? 'has-children' : ''}">
          <div class="vocab-tree-header" ${subs.length ? 'data-expandable' : ''}>
            ${subs.length ? '<span class="vocab-tree-chevron">▶</span>' : '<span class="vocab-tree-leaf">·</span>'}
            <span class="vocab-tree-name">${escapeHtml(sector.name)}</span>
            ${sector.description ? `<span class="vocab-tree-note">${escapeHtml(sector.description)}</span>` : ''}
            ${subs.length ? `<span class="vocab-tree-count">${subs.length}</span>` : ''}
          </div>
          ${subs.length ? `
            <ul class="vocab-tree-children" hidden>
              ${subs.map(sub => `
                <li class="vocab-tree-node">
                  <div class="vocab-tree-header">
                    <span class="vocab-tree-leaf">·</span>
                    <span class="vocab-tree-name">${escapeHtml(sub.name)}</span>
                  </div>
                </li>
              `).join('')}
            </ul>
          ` : ''}
        </li>`;
    }).join('')}</ul>`;
  }

  function renderCrfGoals(dimensions) {
    if (!dimensions || !dimensions.length) return '<div class="vocab-empty">Empty.</div>';
    return `<ul class="vocab-tree">${dimensions.map(dim => {
      const goals = dim.goals || [];
      return `
        <li class="vocab-tree-node ${goals.length ? 'has-children' : ''}">
          <div class="vocab-tree-header" ${goals.length ? 'data-expandable' : ''}>
            ${goals.length ? '<span class="vocab-tree-chevron">▶</span>' : '<span class="vocab-tree-leaf">·</span>'}
            <span class="vocab-tree-name">${escapeHtml(dim.name)}</span>
            ${dim.description ? `<span class="vocab-tree-note">${escapeHtml(dim.description)}</span>` : ''}
            ${goals.length ? `<span class="vocab-tree-count">${goals.length}</span>` : ''}
          </div>
          ${goals.length ? `
            <ul class="vocab-tree-children" hidden>
              ${goals.map(g => `
                <li class="vocab-tree-node">
                  <div class="vocab-tree-header">
                    <span class="vocab-tree-leaf">·</span>
                    <span class="vocab-tree-name">${escapeHtml(g.name || g.id)}</span>
                    ${g.description ? `<span class="vocab-tree-note">${escapeHtml(g.description)}</span>` : ''}
                  </div>
                </li>
              `).join('')}
            </ul>
          ` : ''}
        </li>`;
    }).join('')}</ul>`;
  }

  function renderEnums(data) {
    const skip = new Set(['_description']);
    const keys = Object.keys(data).filter(k => !k.startsWith('_'));
    if (!keys.length) return '<div class="vocab-empty">Empty.</div>';
    return `<ul class="vocab-tree">${keys.map(key => {
      const entry = data[key];
      const values = entry.values || [];
      const label = key.replace(/_/g, ' ');
      return `
        <li class="vocab-tree-node ${values.length ? 'has-children' : ''}">
          <div class="vocab-tree-header" ${values.length ? 'data-expandable' : ''}>
            ${values.length ? '<span class="vocab-tree-chevron">▶</span>' : '<span class="vocab-tree-leaf">·</span>'}
            <span class="vocab-tree-name">${escapeHtml(label)}</span>
            ${values.length ? `<span class="vocab-tree-count">${values.length}</span>` : ''}
          </div>
          ${values.length ? `
            <ul class="vocab-tree-children" hidden>
              ${values.map(v => `
                <li class="vocab-tree-node">
                  <div class="vocab-tree-header">
                    <span class="vocab-tree-leaf">·</span>
                    <span class="vocab-tree-name">${escapeHtml(v.name || v.id)}</span>
                    ${v.description ? `<span class="vocab-tree-note">${escapeHtml(v.description)}</span>` : ''}
                  </div>
                </li>
              `).join('')}
            </ul>
          ` : ''}
        </li>`;
    }).join('')}</ul>`;
  }

  function renderFlatList(items, nameKey) {
    if (!items || !items.length) return '<div class="vocab-empty">Empty.</div>';
    return `<ul class="vocab-tree">${items.map(item => `
      <li class="vocab-tree-node">
        <div class="vocab-tree-header">
          <span class="vocab-tree-leaf">·</span>
          <span class="vocab-tree-name">${escapeHtml(item[nameKey || 'name'] || item.name || item.id)}</span>
          ${item.description ? `<span class="vocab-tree-note">${escapeHtml(item.description)}</span>` : ''}
        </div>
      </li>
    `).join('')}</ul>`;
  }

  function wireVocabExpanders(container) {
    container.querySelectorAll('[data-expandable]').forEach(header => {
      header.addEventListener('click', () => {
        const li = header.closest('.vocab-tree-node');
        const children = li.querySelector('.vocab-tree-children');
        const chevron = header.querySelector('.vocab-tree-chevron');
        if (!children) return;
        const open = !children.hidden;
        children.hidden = open;
        chevron.textContent = open ? '▶' : '▼';
      });
    });
  }

  function escapeHtml(s) {
    return String(s || '').replace(/[&<>"']/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
    );
  }

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

  window.APP = {
    loadVersion,
    getCurrentGraphData: () => currentGraphData,
  };
});
