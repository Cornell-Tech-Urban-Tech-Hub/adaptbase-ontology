(function () {
  const el = () => document.getElementById('inspector');

  function esc(s) {
    return String(s ?? '').replace(/[&<>"]/g, c => ({
      '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;'
    }[c]));
  }

  function commentKey(target) {
    if (target.type === 'node') return target.id;
    return `${target.id}:${target._sourceId}:${target._targetId}`;
  }

  // Sort relationships clockwise from 12 o'clock by other node's angle,
  // grouping reciprocal pairs together (outgoing first)
  function sortRelationships(links, currentNode) {
    const sorted = links.slice();
    // Compute clockwise angle from 12 o'clock for each link's other node
    function angleOf(l) {
      const other = l.source.id === currentNode.id ? l.target : l.source;
      const dx = other.x - currentNode.x;
      const dy = other.y - currentNode.y;
      // atan2 from -π to π, convert to clockwise from north (0 to 2π)
      let a = Math.atan2(dx, -dy); // north=0, clockwise positive
      if (a < 0) a += 2 * Math.PI;
      return a;
    }
    function otherNode(l) {
      return l.source.id === currentNode.id ? l.target.id : l.source.id;
    }
    function isOutgoing(l) {
      return l.source.id === currentNode.id;
    }
    sorted.sort((a, b) => {
      const otherA = otherNode(a), otherB = otherNode(b);
      // Group by other node first (reciprocals stay together)
      if (otherA === otherB) {
        // Outgoing edges first within the same pair
        return isOutgoing(a) === isOutgoing(b) ? 0 : isOutgoing(a) ? -1 : 1;
      }
      return angleOf(a) - angleOf(b);
    });
    return sorted;
  }

  function showEmpty() {
    const featured = [
      { id: 'Solution', lede: 'The central hub — all other solution-domain entities connect to it, with additional relationships between them.' },
      { id: 'Hazard',   lede: 'Bound to the C40/Arup typology with 13 categories and 31 specific hazards.' },
      { id: 'Vulnerability', lede: 'IPCC AR6 framing — exposure × sensitivity × adaptive capacity.' },
      { id: 'Plan',     lede: 'New in v0.1.2; binds goals, prescribed solutions, and policy.' },
    ];

    el().innerHTML = `
      <div class="inspector-empty">
        <span class="mono-eyebrow">Inspector</span>
        <h3>Select a node or relationship to inspect it.</h3>
        <p class="small" style="color:var(--fg-3); font-size:13px; line-height:1.55; margin:0;">Or start with one of these:</p>
        <ul>
          ${featured.map((f, i) => {
            const n = window.Graph.getNodeById(f.id);
            if (!n) return '';
            const color = window.Graph.getClusterColor(n.cluster);
            return `
              <li data-featured="${f.id}">
                <span class="dot" style="width:8px; height:8px; border-radius:50%; background:${color}; display:inline-block; flex-shrink:0; margin-top:6px;"></span>
                <span style="display:flex; flex-direction:column; gap:4px; flex:1;">
                  <strong style="color:var(--fg-1);">${esc(n.label)}</strong>
                  <span style="color:var(--fg-3);">${esc(f.lede)}</span>
                </span>
              </li>
            `;
          }).join('')}
        </ul>
      </div>
    `;
    el().querySelectorAll('[data-featured]').forEach(li => {
      li.addEventListener('click', () => window.Graph.focusNode(li.dataset.featured));
    });
  }

  function renderHeader(opts) {
    return `
      <div class="inspector-header">
        <button class="close-btn" id="close-inspector" title="Close">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>
        <div class="kicker">
          <span class="kind-dot" style="background:${opts.clusterColor}"></span>
          <span class="kind-label">${esc(opts.kind)}</span>
          ${opts.cluster ? `<span class="cluster">· ${esc(opts.cluster)}</span>` : ''}
        </div>
        ${opts.title}
      </div>
    `;
  }

  function renderTabs(active, counts) {
    const tabs = [
      { id: 'detail',    label: 'Detail' },
      { id: 'neighbors', label: 'Neighbors', count: counts.neighbors },
      { id: 'comments',  label: 'Comments', count: counts.comments },
    ];
    return `
      <div class="inspector-tabs">
        ${tabs.map(t => `
          <button class="tab-btn ${t.id === active ? 'active' : ''}" data-tab="${t.id}">
            ${t.label}${t.count != null ? `<span class="badge">${t.count}</span>` : ''}
          </button>
        `).join('')}
      </div>
    `;
  }

  function renderProperties(properties) {
    if (!properties || !properties.length) {
      return '<p class="small" style="color:var(--fg-4);">No properties defined.</p>';
    }
    return `
      <ul class="prop-list">
        ${properties.map(p => {
          const isEnum = p.type && p.type.includes('enum');
          const enumValues = p.values && p.values.length
            ? p.values
            : (p.vocabulary_binding ? window.OntologyAdapter.resolveEnumValues(p.vocabulary_binding) : []);
          const vocabLabel = p.vocabulary_binding ? p.vocabulary_binding.field : p.vocabulary;
          return `
          <li class="prop-item">
            <span class="name">${esc(p.id)}</span>
            <span class="type-group">
              <span class="type">${esc(p.type)}${p.required ? '<span class="req">req</span>' : ''}</span>
              ${isEnum && enumValues.length ? `<span class="enum-hover">${enumValues.length}<span class="enum-tooltip">${enumValues.map(v => `<span class="enum-val">${esc(v)}</span>`).join('')}</span></span>` : ''}
            </span>
            ${p.note ? `<span class="note">${esc(p.note)}</span>` : ''}
            ${vocabLabel ? `<span class="vocab-tag" data-vocab="${esc(vocabLabel)}">${esc(vocabLabel)}</span>` : ''}
          </li>`;
        }).join('')}
      </ul>
    `;
  }

  function renderNeighborsList(node) {
    const links = window.Graph.getLinksForNode(node.id);
    if (!links.length) {
      return '<p class="small" style="color:var(--fg-4);">No connections.</p>';
    }
    return `
      <ul class="neighbors">
        ${links.map(l => {
          const isOutgoing = l.source.id === node.id;
          const other = isOutgoing ? l.target : l.source;
          if (!other) return '';
          const color = window.Graph.getClusterColor(other.cluster);
          return `
            <li class="neighbor" data-nid="${other.id}" data-eid="${l.id}" data-dir="${isOutgoing ? 'out' : 'in'}">
              <span class="dot" style="background:${color}"></span>
              <span class="label">
                <span class="dir">${isOutgoing ? '→ outgoing' : '← incoming'}</span>
                <span class="rel">${esc(l.label)}</span>
                <span class="name">${esc(other.label)}</span>
              </span>
              <span class="arrow">→</span>
            </li>
          `;
        }).join('')}
      </ul>
    `;
  }

  function renderCommentsPanel(key, label) {
    return `
      <div class="comments" data-comment-key="${esc(key)}" data-comment-label="${esc(label)}">
        <div class="comments-loading">Loading comments…</div>
      </div>
    `;
  }

  function showNode(n) {
    const color = window.Graph.getClusterColor(n.cluster);
    const links = window.Graph.getLinksForNode(n.id);
    const key = n.id;
    const counts = {
      neighbors: links.length,
      comments: null,
    };

    el().innerHTML = `
      <div class="inspector-detail">
        ${renderHeader({
          kind: 'Entity type',
          cluster: n.cluster,
          clusterColor: color,
          title: `<h2>${esc(n.label)}</h2>`,
        })}
        ${renderTabs('detail', counts)}
        <div class="inspector-body">
          <div data-panel="detail">
            <div class="section">
              <h4>Definition</h4>
              <p class="definition">${esc(n.definition)}</p>
            </div>

            <div class="section">
              <h4>Metadata</h4>
              <div class="chips">
                <span class="chip chip-hover">${n.properties.length} properties<span class="chip-tooltip">${n.properties.map(p => `<span>${esc(p.id)}</span>`).join('')}</span></span>
                ${n.vocabulary_bindings && n.vocabulary_bindings.length
                  ? n.vocabulary_bindings.map(vb =>
                      `<span class="chip chip-vocab" data-vocab="${esc(vb.vocab)}">${esc(vb.vocab)}</span>`
                    ).join('')
                  : ''}
              </div>
            </div>

            ${links.length ? `
            <div class="section">
              <h4>Relationships <span class="section-count">${links.length}</span></h4>
              <ul class="rel-list">
                ${sortRelationships(links, n).map(l => {
                  const out = l.source.id === n.id;
                  const other = out ? l.target : l.source;
                  if (!other) return '';
                  const color = window.Graph.getClusterColor(other.cluster);
                  const srcLabel = out ? n.label : other.label;
                  const tgtLabel = out ? other.label : n.label;
                  const selfIsSrc = out;
                  return `<li class="rel-item" data-nid="${esc(other.id)}" data-eid="${esc(l.id)}">
                    <span class="rel-sentence">
                      <span class="${selfIsSrc ? 'rel-self' : 'rel-other'}" ${!selfIsSrc ? `style="color:${color}"` : ''}>${esc(srcLabel)}</span>
                      <span class="rel-label">${esc(l.label)}</span>
                      <span class="${selfIsSrc ? 'rel-other' : 'rel-self'}" ${selfIsSrc ? `style="color:${color}"` : ''}>${esc(tgtLabel)}</span>
                    </span>
                  </li>`;
                }).join('')}
              </ul>
            </div>
            ` : ''}

            <div class="section">
              <h4>Properties</h4>
              ${renderProperties(n.properties)}
            </div>

            ${n.notes ? `
              <div class="section">
                <h4>Design notes</h4>
                <p class="definition" style="font-size:13px; color:var(--fg-3);">${esc(n.notes)}</p>
              </div>
            ` : ''}

            ${n.schema_source ? `
              <div class="section">
                <h4>Schema source</h4>
                <p class="definition" style="font-size:12px; font-family:var(--font-mono); color:var(--fg-3);">${esc(n.schema_source)}</p>
              </div>
            ` : ''}
          </div>

          <div data-panel="neighbors" hidden>
            <div class="section">
              <h4>${links.length} connection${links.length === 1 ? '' : 's'}</h4>
              ${renderNeighborsList(n)}
            </div>
          </div>

          <div data-panel="comments" hidden>
            ${renderCommentsPanel(key, n.label)}
          </div>
        </div>
      </div>
    `;

    wireTabs();
    wireClose();
    wireNeighbors();
    wireVocabTags();
  }

  function showEdge(l) {
    const sourceColor = window.Graph.getClusterColor(l.source.cluster);
    const targetColor = window.Graph.getClusterColor(l.target.cluster);
    const key = `${l.id}:${l.source.id}:${l.target.id}`;
    const counts = {
      neighbors: 2,
      comments: null,
    };

    const title = `
      <h2>
        <span class="rel-endpoint" data-ep="${l.source.id}" style="cursor:pointer; border-bottom:1px dotted var(--fg-4);">${esc(l.source.label)}</span>
        <span class="rel-arrow">→</span>
        <span class="rel-endpoint" data-ep="${l.target.id}" style="cursor:pointer; border-bottom:1px dotted var(--fg-4);">${esc(l.target.label)}</span>
        <span class="edge-label">${esc(l.label)}</span>
      </h2>
    `;

    el().innerHTML = `
      <div class="inspector-detail">
        ${renderHeader({
          kind: 'Relationship',
          cluster: l.id,
          clusterColor: '#B31B1B',
          title,
        })}
        ${renderTabs('detail', counts)}
        <div class="inspector-body">
          <div data-panel="detail">
            <div class="section">
              <h4>Definition</h4>
              <p class="definition">${esc(l.definition)}</p>
            </div>

            <div class="section">
              <h4>Metadata</h4>
              <div class="chips">
                <span class="chip chip-carn">${esc(l.id)}</span>
                <span class="chip">${l.properties.length} edge properties</span>
              </div>
              ${l.cardinality ? `
                <div class="meta-row" style="margin-top:8px">
                  <label class="meta-label">Cardinality:</label>
                  <span class="meta-value">${esc(l.cardinality)}</span>
                </div>
              ` : ''}
            </div>

            <div class="section">
              <h4>Endpoints</h4>
              <ul class="neighbors">
                <li class="neighbor" data-nid="${l.source.id}">
                  <span class="dot" style="background:${sourceColor}"></span>
                  <span class="label">
                    <span class="dir">source</span>
                    <span class="name">${esc(l.source.label)}</span>
                  </span>
                  <span class="arrow">→</span>
                </li>
                <li class="neighbor" data-nid="${l.target.id}">
                  <span class="dot" style="background:${targetColor}"></span>
                  <span class="label">
                    <span class="dir">target</span>
                    <span class="name">${esc(l.target.label)}</span>
                  </span>
                  <span class="arrow">→</span>
                </li>
              </ul>
            </div>

            ${l.properties.length ? `
              <div class="section">
                <h4>Edge properties</h4>
                ${renderProperties(l.properties)}
              </div>
            ` : ''}

            ${l.notes ? `
              <div class="section">
                <h4>Design notes</h4>
                <p class="definition" style="font-size:13px; color:var(--fg-3);">${esc(l.notes)}</p>
              </div>
            ` : ''}
          </div>

          <div data-panel="neighbors" hidden>
            <div class="section">
              <h4>Endpoints</h4>
              <ul class="neighbors">
                <li class="neighbor" data-nid="${l.source.id}">
                  <span class="dot" style="background:${sourceColor}"></span>
                  <span class="label">
                    <span class="dir">source</span>
                    <span class="name">${esc(l.source.label)}</span>
                  </span>
                  <span class="arrow">→</span>
                </li>
                <li class="neighbor" data-nid="${l.target.id}">
                  <span class="dot" style="background:${targetColor}"></span>
                  <span class="label">
                    <span class="dir">target</span>
                    <span class="name">${esc(l.target.label)}</span>
                  </span>
                  <span class="arrow">→</span>
                </li>
              </ul>
            </div>
          </div>

          <div data-panel="comments" hidden>
            ${renderCommentsPanel(key, `${l.label} (${l.source.label} → ${l.target.label})`)}
          </div>
        </div>
      </div>
    `;

    wireTabs();
    wireClose();
    wireNeighbors();
    wireVocabTags();
    el().querySelectorAll('[data-ep]').forEach(ep => {
      ep.addEventListener('click', () => window.Graph.focusNode(ep.dataset.ep));
    });
  }

  function wireTabs() {
    const tabs = el().querySelectorAll('.tab-btn');
    const panels = el().querySelectorAll('[data-panel]');
    tabs.forEach(t => {
      t.addEventListener('click', () => {
        tabs.forEach(x => x.classList.toggle('active', x === t));
        panels.forEach(p => p.hidden = (p.dataset.panel !== t.dataset.tab));

        if (t.dataset.tab === 'comments') {
          const commentsEl = el().querySelector('.comments[data-comment-key]');
          if (commentsEl && commentsEl.querySelector('.comments-loading')) {
            window.Comments.loadComments(commentsEl);
          }
        }
      });
    });
  }

  function wireClose() {
    const btn = el().querySelector('#close-inspector');
    if (btn) btn.addEventListener('click', () => window.Graph.deselect());
  }

  function wireNeighbors() {
    el().querySelectorAll('.neighbor').forEach(li => {
      li.addEventListener('click', () => window.Graph.focusNode(li.dataset.nid));
    });
    el().querySelectorAll('.rel-item').forEach(li => {
      li.addEventListener('click', () => window.Graph.focusNode(li.dataset.nid));
    });
  }

  function wireVocabTags() {
    el().querySelectorAll('[data-vocab]').forEach(tag => {
      tag.addEventListener('click', (e) => {
        e.stopPropagation();
        if (window.APP.showVocabulary) window.APP.showVocabulary(tag.dataset.vocab);
      });
    });
  }

  window.Inspector = { showNode, showEdge, showEmpty };
})();
