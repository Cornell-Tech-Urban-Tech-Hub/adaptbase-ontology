// Inspector panel. Renders empty/landing state, node detail, and edge detail.
(function () {
  const el = () => document.getElementById('inspector');
  let editMode = false;
  let currentTarget = null; // Track currently displayed node/edge for re-render

  function esc(s) {
    return String(s ?? '').replace(/[&<>"]/g, c => ({
      '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;'
    }[c]));
  }

  function markDirty() {
    if (window.APP && window.APP.markDirty) {
      window.APP.markDirty();
    }
  }

  function makeEditable(content, field, target, opts = {}) {
    if (!editMode) {
      return `<span class="field-content">${esc(content)}</span>`;
    }

    const placeholder = opts.placeholder || `Enter ${field}...`;
    const multiline = opts.multiline !== false;
    const className = opts.className || '';

    if (multiline) {
      return `<div class="field-editable ${className}"
                   contenteditable="true"
                   data-field="${field}"
                   data-target-type="${target.type}"
                   data-target-id="${target.id}"
                   data-placeholder="${esc(placeholder)}">${esc(content)}</div>`;
    } else {
      return `<input type="text"
                     class="field-editable ${className}"
                     data-field="${field}"
                     data-target-type="${target.type}"
                     data-target-id="${target.id}"
                     value="${esc(content)}"
                     placeholder="${esc(placeholder)}" />`;
    }
  }

  function commentKey(target) {
    if (target.type === 'node') return target.id;
    return `${target.id}:${target._sourceId}:${target._targetId}`;
  }

  function commentCount(key) {
    const t = window.THREADS[key];
    if (!t) return 0;
    let c = t.length;
    for (const m of t) c += (m.replies ? m.replies.length : 0);
    return c;
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
        <h3>Click a node or relationship in the graph to inspect its definition, properties, neighbors, and reviewer comments.</h3>
        <p class="small" style="color:var(--fg-3); font-size:13px; line-height:1.55; margin:0;">Or start with one of the central entity types:</p>
        <ul>
          ${featured.map((f, i) => {
            const n = window.Graph.getNodeById(f.id);
            if (!n) return '';
            const color = window.Graph.getClusterColor(n.cluster);
            return `
              <li data-featured="${f.id}">
                <span class="num">${String(i+1).padStart(2,'0')}</span>
                <span style="display:flex; flex-direction:column; gap:4px; flex:1;">
                  <span style="display:flex; align-items:center; gap:8px;">
                    <span class="dot" style="width:8px; height:8px; border-radius:50%; background:${color}; display:inline-block;"></span>
                    <strong style="color:var(--fg-1);">${esc(n.label)}</strong>
                  </span>
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
    // opts: { kind ('node'|'edge'), title (html), eyebrow, cluster, clusterColor, tags[] }
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

  function renderProperties(properties, target) {
    if (editMode) {
      return renderEditableProperties(properties || [], target);
    }
    if (!properties || !properties.length) {
      return '<p class="small" style="color:var(--fg-4);">No properties defined.</p>';
    }
    return `
      <ul class="prop-list">
        ${properties.map(p => `
          <li class="prop-item">
            <span class="name">${esc(p.id)}</span>
            <span class="type">${esc(p.type)}${p.required ? '<span class="req">required</span>' : ''}</span>
            ${p.note ? `<span class="note">${esc(p.note)}</span>` : ''}
            ${p.values ? `<span class="values">${p.values.map(v => `<span class="v">${esc(v)}</span>`).join('')}</span>` : ''}
            ${p.vocabulary ? `<span class="note">Bound to vocabulary <code>${esc(p.vocabulary)}</code></span>` : ''}
          </li>
        `).join('')}
      </ul>
    `;
  }

  const PROPERTY_TYPES = [
    'string', 'integer', 'number', 'boolean', 'enum',
    'array<string>', 'array<integer>', 'array<enum>',
    'object', 'date', 'datetime'
  ];

  function renderEditableProperties(properties, target) {
    return `
      <ul class="prop-list prop-list-editable">
        ${properties.map((p, i) => renderEditableProperty(p, i, target)).join('')}
        <li class="prop-add-row">
          <button class="btn-add-prop" data-action="add-property"
                  data-target-type="${target.type}" data-target-id="${target.id}">
            + Add property
          </button>
        </li>
      </ul>
    `;
  }

  function renderEditableProperty(p, index, target) {
    const dataAttrs = `data-prop-index="${index}" data-target-type="${target.type}" data-target-id="${target.id}"`;
    return `
      <li class="prop-item prop-editable" ${dataAttrs}>
        <div class="prop-row-1">
          <input type="text"
                 class="prop-field prop-field-id"
                 ${dataAttrs}
                 data-prop-field="id"
                 value="${esc(p.id || '')}"
                 placeholder="property_id" />
          <select class="prop-field prop-field-type"
                  ${dataAttrs}
                  data-prop-field="type">
            ${PROPERTY_TYPES.map(t => `
              <option value="${t}" ${p.type === t ? 'selected' : ''}>${t}</option>
            `).join('')}
            ${p.type && !PROPERTY_TYPES.includes(p.type) ?
              `<option value="${esc(p.type)}" selected>${esc(p.type)}</option>` : ''}
          </select>
          <label class="prop-required-toggle">
            <input type="checkbox"
                   class="prop-field"
                   ${dataAttrs}
                   data-prop-field="required"
                   ${p.required ? 'checked' : ''} />
            <span>required</span>
          </label>
          <button class="prop-delete-btn"
                  data-action="delete-property"
                  ${dataAttrs}
                  title="Delete property">×</button>
        </div>
        <textarea class="prop-field prop-field-note"
                  ${dataAttrs}
                  data-prop-field="note"
                  placeholder="Note about this property (optional)">${esc(p.note || '')}</textarea>
        ${(p.type === 'enum' || p.type === 'array<enum>') ? `
          <div class="prop-values">
            <label class="prop-values-label">Allowed values (one per line):</label>
            <textarea class="prop-field prop-field-values"
                      ${dataAttrs}
                      data-prop-field="values"
                      placeholder="value_one&#10;value_two">${esc((p.values || []).join('\n'))}</textarea>
          </div>
        ` : ''}
        ${p.vocabulary ? `
          <div class="prop-vocab">
            <label class="prop-vocab-label">Vocabulary binding:</label>
            <input type="text" class="prop-field prop-field-vocab"
                   ${dataAttrs}
                   data-prop-field="vocabulary"
                   value="${esc(p.vocabulary)}" />
          </div>
        ` : ''}
      </li>
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

  function renderCommentsPanel(key) {
    const thread = window.THREADS[key] || [];
    const body = thread.length ? `
      <div class="comment-thread">
        ${thread.map(c => renderComment(c, false)).join('')}
      </div>
    ` : `
      <div class="empty-comments">
        No comments yet on this ${key.includes(':') ? 'relationship' : 'entity'}.<br>
        Be the first — your feedback shapes v0.2.
      </div>
    `;

    return `
      <div class="comments">
        ${body}
        ${renderComposer()}
      </div>
    `;
  }

  function renderComment(c, isReply) {
    const reviewer = window.REVIEWERS[c.by] || { name: 'Anonymous', affil: '', color: 'slate' };
    const ini = window.initialsOf(reviewer.name);
    return `
      <div class="comment ${isReply ? 'comment-reply' : ''} c-${reviewer.color}">
        <div class="avatar">${ini}</div>
        <div class="bubble">
          <div class="byline">
            <span class="name">${esc(reviewer.name)}</span>
            <span class="affil">· ${esc(reviewer.affil)}</span>
            <span class="time">${esc(c.when)}</span>
          </div>
          <div class="body">${c.body}</div>
          ${!isReply ? `
            <div class="actions">
              <a>Reply</a>
              <a>Resolve</a>
              <a class="resolved">↑ Support</a>
            </div>
          ` : ''}
        </div>
      </div>
      ${(c.replies || []).map(r => renderComment(r, true)).join('')}
    `;
  }

  function renderComposer() {
    return `
      <div class="composer">
        <div class="avatar">yo</div>
        <div class="box">
          <textarea placeholder="Add a review comment — suggest a property, flag an ambiguity, or propose a rename…"></textarea>
          <div class="bar">
            <span class="hint">Markdown supported · Posting as You</span>
            <button class="btn btn-primary" style="padding:8px 12px; font-size:12px;">Post comment</button>
          </div>
        </div>
      </div>
    `;
  }

  // ------ node detail ------
  function showNode(n) {
    currentTarget = { type: 'node', ...n };
    const color = window.Graph.getClusterColor(n.cluster);
    const links = window.Graph.getLinksForNode(n.id);
    const key = n.id;
    const counts = {
      neighbors: links.length,
      comments: commentCount(key),
    };

    const labelField = editMode
      ? `<h2>${makeEditable(n.label, 'label', currentTarget, { multiline: false, className: 'editable-title' })}</h2>`
      : `<h2>${esc(n.label)}</h2>`;

    el().innerHTML = `
      <div class="inspector-detail">
        ${renderHeader({
          kind: 'Entity type',
          cluster: n.cluster,
          clusterColor: color,
          title: labelField,
        })}
        ${renderTabs('detail', counts)}
        <div class="inspector-body">
          <div data-panel="detail">
            <div class="section">
              <h4>Definition</h4>
              ${editMode
                ? makeEditable(n.definition, 'definition', currentTarget, { className: 'definition' })
                : `<p class="definition">${esc(n.definition)}</p>`
              }
            </div>

            <div class="section">
              <h4>Metadata</h4>
              <div class="chips">
                <span class="chip">${n.properties.length} properties</span>
                <span class="chip">${links.length} connections</span>
                ${n.vocabulary_bindings && n.vocabulary_bindings.length ? `<span class="chip chip-carn">${n.vocabulary_bindings.length} vocab bindings</span>` : ''}
              </div>
            </div>

            <div class="section">
              <h4>Properties</h4>
              ${renderProperties(n.properties, currentTarget)}
            </div>

            ${n.notes || editMode ? `
              <div class="section">
                <h4>Design notes</h4>
                ${editMode
                  ? makeEditable(n.notes || '', 'notes', currentTarget, { className: 'definition', placeholder: 'Add design notes...' })
                  : `<p class="definition" style="font-size:13px; color:var(--fg-3);">${esc(n.notes)}</p>`
                }
              </div>
            ` : ''}

            ${n.schema_source ? `
              <div class="section">
                <h4>Schema source</h4>
                <p class="definition" style="font-size:12px; font-family:var(--font-mono); color:var(--fg-3);">${esc(n.schema_source)}</p>
              </div>
            ` : ''}

            ${editMode ? `
              <div class="section danger-zone">
                <h4>Danger zone</h4>
                <button class="btn-delete-entity" data-action="delete-node" data-target-id="${n.id}">
                  Delete entity "${esc(n.label)}"
                </button>
                <p class="small" style="color:var(--fg-4); margin-top:6px;">
                  This will remove the entity and all relationships connecting to it.
                </p>
              </div>
            ` : ''}
          </div>

          <div data-panel="neighbors" hidden>
            <div class="section">
              <h4>${links.length} connection${links.length === 1 ? '' : 's'}</h4>
              ${renderNeighborsList(n)}
              ${editMode ? `
                <button class="btn-add-edge" data-action="add-edge" data-from-id="${n.id}" style="margin-top:12px">
                  + Add new relationship from this entity
                </button>
              ` : ''}
            </div>
          </div>

          <div data-panel="comments" hidden>
            ${renderCommentsPanel(key)}
          </div>
        </div>
      </div>
    `;

    wireTabs();
    wireClose();
    wireNeighbors();
    wireEditableFields();
  }

  // ------ edge detail ------
  function showEdge(l) {
    currentTarget = { type: 'edge', ...l };
    const sourceColor = window.Graph.getClusterColor(l.source.cluster);
    const targetColor = window.Graph.getClusterColor(l.target.cluster);
    const key = `${l.id}:${l.source.id}:${l.target.id}`;
    const counts = {
      neighbors: 2,
      comments: commentCount(key),
    };

    const labelField = editMode
      ? makeEditable(l.label, 'label', currentTarget, { multiline: false, className: 'editable-edge-label' })
      : esc(l.label);

    const title = `
      <h2>
        <span class="rel-endpoint" data-ep="${l.source.id}" style="cursor:pointer; border-bottom:1px dotted var(--fg-4);">${esc(l.source.label)}</span>
        <span class="rel-arrow">→</span>
        <span class="rel-endpoint" data-ep="${l.target.id}" style="cursor:pointer; border-bottom:1px dotted var(--fg-4);">${esc(l.target.label)}</span>
        <span class="edge-label">${labelField}</span>
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
              ${editMode
                ? makeEditable(l.definition, 'definition', currentTarget, { className: 'definition' })
                : `<p class="definition">${esc(l.definition)}</p>`
              }
            </div>

            <div class="section">
              <h4>Metadata</h4>
              <div class="chips">
                <span class="chip chip-carn">${esc(l.id)}</span>
                <span class="chip">${l.properties.length} edge properties</span>
              </div>
              <div class="meta-row" style="margin-top:8px">
                <label class="meta-label">Cardinality:</label>
                ${editMode ? `
                  <select class="field-editable cardinality-select"
                          data-field="cardinality"
                          data-target-type="edge"
                          data-target-id="${l.id}">
                    <option value="" ${!l.cardinality ? 'selected' : ''}>—</option>
                    <option value="one-to-one" ${l.cardinality === 'one-to-one' ? 'selected' : ''}>one-to-one</option>
                    <option value="one-to-many" ${l.cardinality === 'one-to-many' ? 'selected' : ''}>one-to-many</option>
                    <option value="many-to-one" ${l.cardinality === 'many-to-one' ? 'selected' : ''}>many-to-one</option>
                    <option value="many-to-many" ${l.cardinality === 'many-to-many' ? 'selected' : ''}>many-to-many</option>
                  </select>
                ` : `<span class="meta-value">${l.cardinality ? esc(l.cardinality) : '—'}</span>`}
              </div>
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

            ${l.properties.length || editMode ? `
              <div class="section">
                <h4>Edge properties</h4>
                ${renderProperties(l.properties, currentTarget)}
              </div>
            ` : ''}

            ${l.notes || editMode ? `
              <div class="section">
                <h4>Design notes</h4>
                ${editMode
                  ? makeEditable(l.notes || '', 'notes', currentTarget, { className: 'definition', placeholder: 'Add design notes...' })
                  : `<p class="definition" style="font-size:13px; color:var(--fg-3);">${esc(l.notes)}</p>`
                }
              </div>
            ` : ''}

            ${editMode ? `
              <div class="section danger-zone">
                <h4>Danger zone</h4>
                <button class="btn-delete-entity" data-action="delete-edge" data-target-id="${l.id}">
                  Delete relationship "${esc(l.label)}"
                </button>
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
            ${renderCommentsPanel(key)}
          </div>
        </div>
      </div>
    `;

    wireTabs();
    wireClose();
    wireNeighbors();
    wireEditableFields();
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
  }

  function wireEditableFields() {
    if (!editMode) return;

    // Top-level fields (label, definition, notes, cardinality)
    el().querySelectorAll('.field-editable').forEach(field => {
      const isContentEditable = field.hasAttribute('contenteditable');
      const isSelect = field.tagName === 'SELECT';

      function saveValue() {
        const fieldName = field.dataset.field;
        const targetType = field.dataset.targetType;
        const targetId = field.dataset.targetId;
        let newValue;
        if (isContentEditable) newValue = field.textContent.trim();
        else if (isSelect) newValue = field.value;
        else newValue = field.value.trim();

        console.log(`Saving ${targetType}.${fieldName} = "${newValue}"`);

        if (targetType === 'node') {
          window.OntologyAdapter.updateNodeInOntology(targetId, { [fieldName]: newValue });
          if (fieldName === 'label') {
            const node = window.Graph.getNodeById(targetId);
            if (node) {
              node.label = newValue;
            }
          }
        } else if (targetType === 'edge') {
          window.OntologyAdapter.updateEdgeInOntology(targetId, { [fieldName]: newValue });
          if (fieldName === 'label') {
            const edge = window.Graph.getLinks().find(e => e.id === targetId);
            if (edge) edge.label = newValue;
          }
        }

        markDirty();
      }

      if (isSelect) {
        field.addEventListener('change', saveValue);
      } else if (isContentEditable) {
        field.addEventListener('blur', saveValue);
        field.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            field.blur();
          }
        });
      } else {
        field.addEventListener('blur', saveValue);
        field.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            field.blur();
          }
        });
      }
    });

    wireProperties();
    wireActions();
  }

  function wireProperties() {
    // Property field changes
    el().querySelectorAll('.prop-field').forEach(field => {
      const isCheckbox = field.type === 'checkbox';
      const isSelect = field.tagName === 'SELECT';
      const isTextarea = field.tagName === 'TEXTAREA';

      function saveProperty() {
        const propIndex = parseInt(field.dataset.propIndex);
        const propField = field.dataset.propField;
        const targetType = field.dataset.targetType;
        const targetId = field.dataset.targetId;

        let newValue;
        if (isCheckbox) {
          newValue = field.checked;
        } else if (propField === 'values') {
          // Split by newlines and filter empty
          newValue = field.value.split('\n').map(v => v.trim()).filter(v => v);
        } else {
          newValue = field.value.trim();
        }

        console.log(`Saving ${targetType} ${targetId} prop[${propIndex}].${propField} =`, newValue);

        if (targetType === 'node') {
          window.OntologyAdapter.updateNodeProperty(targetId, propIndex, propField, newValue);
          // Update graph node properties
          const node = window.Graph.getNodeById(targetId);
          if (node && node.properties && node.properties[propIndex]) {
            node.properties[propIndex][propField] = newValue;
          }
        } else if (targetType === 'edge') {
          window.OntologyAdapter.updateEdgeProperty(targetId, propIndex, propField, newValue);
          const edge = window.Graph.getLinks().find(e => e.id === targetId);
          if (edge && edge.properties && edge.properties[propIndex]) {
            edge.properties[propIndex][propField] = newValue;
          }
        }

        markDirty();

        // If type changed, re-render to show/hide enum values field
        if (propField === 'type') {
          rerenderCurrentTarget();
        }
      }

      if (isCheckbox || isSelect) {
        field.addEventListener('change', saveProperty);
      } else if (isTextarea) {
        field.addEventListener('blur', saveProperty);
      } else {
        field.addEventListener('blur', saveProperty);
        field.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            field.blur();
          }
        });
      }
    });
  }

  function wireActions() {
    // Property add/delete
    el().querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const action = btn.dataset.action;

        if (action === 'add-property') {
          handleAddProperty(btn);
        } else if (action === 'delete-property') {
          handleDeleteProperty(btn);
        } else if (action === 'delete-node') {
          handleDeleteNode(btn);
        } else if (action === 'delete-edge') {
          handleDeleteEdge(btn);
        } else if (action === 'add-edge') {
          handleAddEdge(btn);
        }
      });
    });
  }

  function handleAddProperty(btn) {
    const targetType = btn.dataset.targetType;
    const targetId = btn.dataset.targetId;

    const newProp = {
      id: 'new_property',
      type: 'string',
      required: false,
      note: '',
    };

    if (targetType === 'node') {
      window.OntologyAdapter.addNodeProperty(targetId, newProp);
      const node = window.Graph.getNodeById(targetId);
      if (node) {
        if (!node.properties) node.properties = [];
        node.properties.push(newProp);
      }
    } else if (targetType === 'edge') {
      window.OntologyAdapter.addEdgeProperty(targetId, newProp);
      const edge = window.Graph.getLinks().find(e => e.id === targetId);
      if (edge) {
        if (!edge.properties) edge.properties = [];
        edge.properties.push(newProp);
      }
    }

    markDirty();
    rerenderCurrentTarget();
  }

  function handleDeleteProperty(btn) {
    const propIndex = parseInt(btn.dataset.propIndex);
    const targetType = btn.dataset.targetType;
    const targetId = btn.dataset.targetId;

    if (!confirm('Delete this property?')) return;

    if (targetType === 'node') {
      window.OntologyAdapter.deleteNodeProperty(targetId, propIndex);
      const node = window.Graph.getNodeById(targetId);
      if (node && node.properties) {
        node.properties.splice(propIndex, 1);
      }
    } else if (targetType === 'edge') {
      window.OntologyAdapter.deleteEdgeProperty(targetId, propIndex);
      const edge = window.Graph.getLinks().find(e => e.id === targetId);
      if (edge && edge.properties) {
        edge.properties.splice(propIndex, 1);
      }
    }

    markDirty();
    rerenderCurrentTarget();
  }

  function handleDeleteNode(btn) {
    const nodeId = btn.dataset.targetId;
    const node = window.Graph.getNodeById(nodeId);
    if (!node) return;

    const links = window.Graph.getLinksForNode(nodeId);
    const msg = links.length > 0
      ? `Delete entity "${node.label}" and ${links.length} associated relationship${links.length === 1 ? '' : 's'}?`
      : `Delete entity "${node.label}"?`;

    if (!confirm(msg)) return;

    window.OntologyAdapter.deleteTypeFromOntology(nodeId);
    markDirty();

    // Reload graph from updated ontology
    if (window.APP && window.APP.reloadGraph) {
      window.APP.reloadGraph();
    }
  }

  function handleDeleteEdge(btn) {
    const edgeId = btn.dataset.targetId;
    const edge = window.Graph.getLinks().find(e => e.id === edgeId);
    if (!edge) return;

    if (!confirm(`Delete relationship "${edge.label}"?`)) return;

    window.OntologyAdapter.deleteRelationshipFromOntology(edgeId);
    markDirty();

    if (window.APP && window.APP.reloadGraph) {
      window.APP.reloadGraph();
    }
  }

  function handleAddEdge(btn) {
    const fromId = btn.dataset.fromId;
    showAddEdgeDialog(fromId);
  }

  function rerenderCurrentTarget() {
    if (!currentTarget) return;
    if (currentTarget.type === 'node') {
      const node = window.Graph.getNodeById(currentTarget.id);
      if (node) showNode(node);
    } else if (currentTarget.type === 'edge') {
      const edge = window.Graph.getLinks().find(e => e.id === currentTarget.id);
      if (edge) showEdge(edge);
    }
  }

  function showAddEdgeDialog(fromId) {
    // Get all entity types as potential targets
    const allNodes = window.Graph.getNodes();
    const targets = allNodes
      .filter(n => n.id !== fromId)
      .map(n => `<option value="${esc(n.id)}">${esc(n.label)}</option>`)
      .join('');

    const html = `
      <div class="modal show" id="add-edge-modal">
        <div class="modal-content">
          <h3>Create new relationship</h3>
          <div class="form-row">
            <label>From</label>
            <input type="text" value="${esc(fromId)}" disabled />
          </div>
          <div class="form-row">
            <label>To</label>
            <select id="new-edge-target">
              ${targets}
            </select>
          </div>
          <div class="form-row">
            <label>Label (verb phrase)</label>
            <input type="text" id="new-edge-label" placeholder="produces, depends on, ..." />
          </div>
          <div class="form-row">
            <label>Definition</label>
            <textarea id="new-edge-definition" placeholder="What does this relationship mean?"></textarea>
          </div>
          <div class="form-row">
            <label>Cardinality</label>
            <select id="new-edge-cardinality">
              <option value="">—</option>
              <option value="one-to-one">one-to-one</option>
              <option value="one-to-many" selected>one-to-many</option>
              <option value="many-to-one">many-to-one</option>
              <option value="many-to-many">many-to-many</option>
            </select>
          </div>
          <div class="modal-buttons">
            <button id="cancel-add-edge">Cancel</button>
            <button class="primary" id="confirm-add-edge">Create</button>
          </div>
        </div>
      </div>
    `;

    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    document.body.appendChild(tempDiv.firstElementChild);

    const modal = document.getElementById('add-edge-modal');
    document.getElementById('cancel-add-edge').addEventListener('click', () => modal.remove());
    document.getElementById('confirm-add-edge').addEventListener('click', () => {
      const targetId = document.getElementById('new-edge-target').value;
      const label = document.getElementById('new-edge-label').value.trim();
      const definition = document.getElementById('new-edge-definition').value.trim();
      const cardinality = document.getElementById('new-edge-cardinality').value;

      if (!label) {
        alert('Label is required');
        return;
      }

      const id = window.OntologyAdapter.generateRelationshipId(label);

      // Check for duplicate
      const ontology = window.OntologyAdapter.getCurrentOntology();
      if (ontology.relationships.find(r => r.id === id)) {
        alert(`A relationship with id "${id}" already exists`);
        return;
      }

      const newRel = {
        id,
        label,
        source: fromId,
        target: targetId,
        definition,
        cardinality,
        properties: [],
      };

      window.OntologyAdapter.addRelationshipToOntology(newRel);
      markDirty();
      modal.remove();

      if (window.APP && window.APP.reloadGraph) {
        window.APP.reloadGraph();
      }
    });
  }

  function setEditMode(enabled) {
    editMode = enabled;
    rerenderCurrentTarget();
  }

  window.Inspector = { showNode, showEdge, showEmpty, setEditMode };
})();
