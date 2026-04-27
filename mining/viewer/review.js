// Ontology mining review viewer

const state = {
  phase: "distribution",
  proposals: [],
  decisionsById: {},   // proposal_id → decision record
  supportingById: {},  // action_id → action row (for distribution proposals)
  mechanismSeedVocab: [],  // existing mechanism seed vocabulary
  index: 0,
};

const el = (id) => document.getElementById(id);

async function fetchJSON(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function loadPhase(phase) {
  state.phase = phase;
  state.index = 0;
  try {
    state.proposals = await fetchJSON(`/api/proposals/${phase}`);
  } catch (e) {
    state.proposals = [];
  }
  try {
    const decisions = await fetchJSON(`/api/decisions/${phase}`);
    state.decisionsById = Object.fromEntries(decisions.map(d => [d.proposal_id, d]));
  } catch (e) {
    state.decisionsById = {};
  }
  // Load mechanism seed vocab if we're on the mechanisms phase
  if (phase === 'mechanisms') {
    try {
      state.mechanismSeedVocab = await fetchJSON('/api/vocab/mechanism-seed');
      console.log('Loaded mechanism vocab:', state.mechanismSeedVocab.length, 'items');
    } catch (e) {
      console.error('Failed to load mechanism vocab:', e);
      state.mechanismSeedVocab = [];
    }
  } else {
    state.mechanismSeedVocab = [];
  }
  // Jump to first unreviewed, else stay at 0
  const firstUnreviewed = state.proposals.findIndex(p => !state.decisionsById[p.proposal_id]);
  if (firstUnreviewed >= 0) state.index = firstUnreviewed;
  render();
}

function render() {
  if (state.proposals.length === 0) {
    el("main").innerHTML = `<div class="empty-state">No proposals for this phase yet.<br>Run the mining script to generate them.</div>`;
    el("progress").textContent = "0 / 0";
    el("evidence").innerHTML = "";
    el("meta").innerHTML = "";
    el("alt").innerHTML = "";
    el("ext").innerHTML = "";
    return;
  }
  const p = state.proposals[state.index];
  el("progress").textContent = `${state.index + 1} / ${state.proposals.length}`;

  // Prior decision banner
  const prior = state.decisionsById[p.proposal_id];
  const priorBanner = prior
    ? `<div class="prior-decision ${prior.status}">
         Previous decision: <strong>${prior.status}</strong>
         ${prior.rationale ? "— " + escapeHtml(prior.rationale) : ""}
         <button onclick="clearPriorDecision()" style="margin-left:8px;padding:2px 8px;font-size:11px;">Clear</button>
       </div>`
    : "";

  // Main pane — editable name + definition
  el("main").innerHTML = `
    ${priorBanner}
    <div><span class="chip">${escapeHtml(p.dimension || "proposal")}</span></div>
    <div class="field">
      <label>Proposed ID <span class="proposed-id">${escapeHtml(p.proposed_id || "")}</span></label>
      <input id="f-name" value="${escapeAttr(prior?.name ?? p.proposed_name ?? "")}" />
    </div>
    <div class="field">
      <label>Definition</label>
      <textarea id="f-definition">${escapeHtml(prior?.definition ?? p.definition ?? "")}</textarea>
    </div>
    <div class="field">
      <label>Rationale (required for reject / defer)</label>
      <textarea id="f-rationale" placeholder="Why reject/defer? What would change your mind?">${escapeHtml(prior?.rationale ?? "")}</textarea>
    </div>
  `;

  // Evidence pane — supporting actions / examples
  renderEvidence(p);

  // Right pane — metadata / alt / external vocab
  renderMeta(p);
}

function renderEvidence(p) {
  const items = [];
  if (Array.isArray(p.supporting_action_ids) && p.supporting_action_ids.length) {
    // For distribution proposals we only have action ids; render compactly.
    items.push(`<div class="example"><div class="ex-title">Supporting CDP action IDs (${p.supporting_action_ids.length})</div><div class="ex-snippet">${p.supporting_action_ids.map(i => `<code>${i}</code>`).join(", ")}</div></div>`);
  }
  if (Array.isArray(p.examples) && p.examples.length) {
    for (const ex of p.examples.slice(0, 12)) {
      const title = ex.text || ex.description || ex.canonical_name || "example";
      const meta = [ex.solution_id, ex.source_type, ex.source_domain].filter(Boolean).join(" · ");
      const quote = ex.supporting_quote || ex.snippet || "";
      items.push(`<div class="example">
        <div class="ex-title">${escapeHtml(String(title).slice(0, 180))}</div>
        ${meta ? `<div class="ex-meta">${escapeHtml(meta)}</div>` : ""}
        ${quote ? `<div class="ex-snippet">${escapeHtml(String(quote).slice(0, 320))}</div>` : ""}
      </div>`);
    }
  }
  if (!items.length && p.raw?.notes) {
    items.push(`<div class="example"><div class="ex-snippet">${escapeHtml(p.raw.notes)}</div></div>`);
  }
  el("evidence").innerHTML = items.join("") || '<div style="color:var(--text-dim);font-size:12px">No evidence attached.</div>';
}

function renderMeta(p) {
  // Existing mechanism seed vocabulary (for mechanisms phase only)
  if (state.phase === 'mechanisms' && state.mechanismSeedVocab.length > 0) {
    console.log('Rendering', state.mechanismSeedVocab.length, 'mechanism vocab items');
    const seedItems = state.mechanismSeedVocab.map(m =>
      `<div class="seed-mech"><div class="seed-id">${escapeHtml(m.id)}</div><div class="seed-name">${escapeHtml(m.name)}</div><div class="seed-desc">${escapeHtml(m.description)}</div></div>`
    ).join('');
    el("existing-vocab").innerHTML = seedItems;
  } else {
    console.log('Not rendering vocab: phase=', state.phase, 'vocab.length=', state.mechanismSeedVocab.length);
    el("existing-vocab").innerHTML = '<div style="color:var(--text-dim);font-size:12px">—</div>';
  }

  const metaRows = [];
  if (p.cluster_size != null) metaRows.push(row("cluster size", p.cluster_size));
  if (Array.isArray(p.supporting_action_ids)) metaRows.push(row("supporting actions", p.supporting_action_ids.length));
  if (Array.isArray(p.ambiguities) && p.ambiguities.length) metaRows.push(row("ambiguities", p.ambiguities.length));
  el("meta").innerHTML = metaRows.join("") || '<div style="color:var(--text-dim);font-size:12px">—</div>';

  el("alt").innerHTML = p.alternative
    ? `<div class="example"><div class="ex-title"><code>${escapeHtml(p.alternative)}</code></div><div class="ex-meta">Could plausibly map to this existing entry instead of being a new one.</div></div>`
    : '<div style="color:var(--text-dim);font-size:12px">None suggested.</div>';

  let ext = "";
  if (typeof p.external_vocab_match === "string" && p.external_vocab_match && p.external_vocab_match !== "null") {
    ext = `<div class="example"><div class="ex-title">${escapeHtml(p.external_vocab_match)}</div></div>`;
  } else if (p.external_vocab_match && typeof p.external_vocab_match === "object") {
    const pairs = Object.entries(p.external_vocab_match).filter(([, v]) => v);
    ext = pairs.length
      ? `<div class="example"><div class="ex-snippet">${pairs.map(([k, v]) => `<div><strong>${escapeHtml(k)}:</strong> ${escapeHtml(String(v))}</div>`).join("")}</div></div>`
      : "";
  }
  el("ext").innerHTML = ext || '<div style="color:var(--text-dim);font-size:12px">None.</div>';
}

function row(k, v) {
  return `<div class="meta-row"><span class="mk">${escapeHtml(k)}</span><span class="mv">${escapeHtml(String(v))}</span></div>`;
}

async function submit(status) {
  const p = state.proposals[state.index];
  if (!p) return;
  const name = el("f-name")?.value?.trim() || p.proposed_name;
  const definition = el("f-definition")?.value?.trim() || p.definition;
  const rationale = el("f-rationale")?.value?.trim() || null;
  if ((status === "rejected" || status === "deferred") && !rationale) {
    alert(`Please provide a rationale for ${status}.`);
    return;
  }
  // Detect "edited" vs "approved"
  let effective = status;
  if (status === "approved") {
    const edited = (name !== (p.proposed_name || "")) || (definition !== (p.definition || ""));
    if (edited) effective = "edited";
  }
  const payload = {
    proposal_id: p.proposal_id,
    dimension: p.dimension,
    status: effective,
    name,
    definition,
    rationale,
  };
  const rec = await fetchJSON(`/api/decisions/${state.phase}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  state.decisionsById[p.proposal_id] = rec;
  // Advance to next unreviewed
  const next = findNextUnreviewed(state.index + 1);
  state.index = next != null ? next : Math.min(state.index + 1, state.proposals.length - 1);
  render();
}

function findNextUnreviewed(from) {
  for (let i = from; i < state.proposals.length; i++) {
    if (!state.decisionsById[state.proposals[i].proposal_id]) return i;
  }
  return null;
}

async function clearPriorDecision() {
  const p = state.proposals[state.index];
  if (!p) return;
  await fetch(`/api/decisions/${state.phase}/${encodeURIComponent(p.proposal_id)}`, { method: "DELETE" });
  delete state.decisionsById[p.proposal_id];
  render();
}
window.clearPriorDecision = clearPriorDecision;

function nav(delta) {
  const ni = state.index + delta;
  if (ni < 0 || ni >= state.proposals.length) return;
  state.index = ni;
  render();
}

function escapeHtml(s) {
  if (s == null) return "";
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}
function escapeAttr(s) { return escapeHtml(s); }

// Wire up
el("phase").addEventListener("change", (e) => loadPhase(e.target.value));
el("prev").addEventListener("click", () => nav(-1));
el("next").addEventListener("click", () => nav(+1));
el("btn-approve").addEventListener("click", () => submit("approved"));
el("btn-reject").addEventListener("click", () => submit("rejected"));
el("btn-defer").addEventListener("click", () => submit("deferred"));

document.addEventListener("keydown", (e) => {
  if (["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) return;
  if (e.key === "ArrowLeft") nav(-1);
  else if (e.key === "ArrowRight") nav(+1);
  else if (e.key === "a") submit("approved");
  else if (e.key === "r") submit("rejected");
  else if (e.key === "d") submit("deferred");
});

// Kick off
loadPhase(el("phase").value);
