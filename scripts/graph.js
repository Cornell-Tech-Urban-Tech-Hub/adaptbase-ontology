// Force-directed graph on canvas.
// Exposes window.Graph with init, focusNode(id), selectEdge(id), setPhysics(bool),
// getNodeById, getEdgesForNode, etc.

(function () {
  // Cluster colors used by the inspector (node dots, kicker line) — not for graph node fill
  const CLUSTER_COLORS = {
    'Solution': '#B31B1B',  // carnelian
    'Risk':     '#6B4C9A',  // purple
    'Context':  '#2E7D4F',  // chlorophyll
    'Programs': '#1E4DD8',  // blueprint
    'Finance':  '#4A4F57',  // graphite
    'Outcomes': '#D4900A',  // warm amber
  };

  // Multi-ring concentric layout
  const LAYOUT_CONFIG = {
    ring1Radius: 240,           // Inner ring (structural connectors)
    ring2Radius: 360,           // Middle ring (hub neighbors)
    ring3Radius: 470,           // Outer ring (leaves)
  };

  // Sector angles per cluster (radians, starting from top going clockwise)
  // Order: Risk, Programs, Outcomes, Finance, Context
  const SECTOR_ANGLES = {
    'Risk':     -Math.PI / 2,                    // top (12 o'clock)
    'Programs':  -Math.PI / 2 + 2*Math.PI/5,    // top-right
    'Outcomes':  -Math.PI / 2 + 4*Math.PI/5,    // bottom-right
    'Finance':   -Math.PI / 2 + 6*Math.PI/5,    // bottom-left
    'Context':   -Math.PI / 2 + 8*Math.PI/5,    // top-left
  };

  // Ring assignments: which nodes go on which ring
  // Ring 1: high cross-connectivity (degree > 4, excluding Solution)
  // Ring 3: not connected to hub directly
  // Ring 2: everything else
  const RING1_NODES = new Set(['Plan', 'Action', 'Stakeholder', 'ExposureUnit', 'Location']);
  const RING3_NODES = new Set(['Indicator', 'FinancingSource', 'GovernanceStructure', 'Mechanism', 'EnablingCondition', 'Supplier']);

  let canvas, ctx, dpr;
  let W = 0, H = 0;
  let nodes = [], links = [], nodeById = {}, linksByNode = {};
  let simulation = null;
  let transform = { x: 0, y: 0, k: 1 };
  let hoverNode = null, hoverEdge = null;
  let selectedNode = null, selectedEdge = null;
  let dimmed = new Set(); // cluster ids that are off
  let dragNode = null, dragStart = null;
  let isPanning = false, panStart = null;

  function colorFor(cluster) { return CLUSTER_COLORS[cluster] || '#4A4F57'; }

  function radiusFor(d) {
    const deg = d.degree || 1;
    return 22 + Math.min(58, Math.sqrt(deg) * 13);
  }

  // Per-node sector constraints (populated during layout)
  let nodeSectorBounds = new Map();
  // Sector geometry for drawing separators
  let sectorBoundaries = [];

  function applyConcentricLayout() {
    const hub = nodes.find(n => n.id === 'Solution');
    if (!hub) return;
    hub.x = 0;
    hub.y = 0;

    nodeSectorBounds = new Map();
    sectorBoundaries = [];

    // Group non-hub nodes by cluster, assign ring per node
    const clusterBuckets = new Map();
    for (const n of nodes) {
      if (n === hub) continue;
      if (!clusterBuckets.has(n.cluster)) clusterBuckets.set(n.cluster, []);
      clusterBuckets.get(n.cluster).push(n);
    }

    // Determine optimal sector order to minimize inter-cluster edge length
    const clusterNames = Object.keys(SECTOR_ANGLES);

    // Count inter-cluster edges (excluding hub)
    const interClusterEdges = {};
    for (const a of clusterNames) for (const b of clusterNames) {
      interClusterEdges[a + '::' + b] = 0;
    }
    for (const l of links) {
      const ca = l.source.cluster, cb = l.target.cluster;
      if (ca === 'Solution' || cb === 'Solution') continue;
      if (ca !== cb) {
        interClusterEdges[ca + '::' + cb]++;
        interClusterEdges[cb + '::' + ca]++;
      }
    }

    // Try all permutations (5! = 120) and score by adjacency
    function permutations(arr) {
      if (arr.length <= 1) return [arr];
      const result = [];
      for (let i = 0; i < arr.length; i++) {
        const rest = [...arr.slice(0, i), ...arr.slice(i + 1)];
        for (const p of permutations(rest)) result.push([arr[i], ...p]);
      }
      return result;
    }

    function scorePerm(perm) {
      let cost = 0;
      for (let i = 0; i < perm.length; i++) {
        for (let j = i + 1; j < perm.length; j++) {
          const dist = Math.min(j - i, perm.length - (j - i)); // circular distance
          const edges = interClusterEdges[perm[i] + '::' + perm[j]];
          cost += edges * dist;
        }
      }
      return cost;
    }

    let bestOrder = clusterNames;
    let bestCost = Infinity;
    for (const perm of permutations(clusterNames)) {
      const c = scorePerm(perm);
      if (c < bestCost) { bestCost = c; bestOrder = perm; }
    }

    const sectorNames = bestOrder;
    const totalGap = sectorNames.length * 0.04; // minimal gaps between sectors
    const availableArc = 2 * Math.PI - totalGap;
    const gapArc = totalGap / sectorNames.length;

    // Weight = nodes + intra-cluster edges (gives denser clusters more room)
    const weights = sectorNames.map(cluster => {
      const arr = clusterBuckets.get(cluster) || [];
      const nodeIds = new Set(arr.map(n => n.id));
      let intraLinks = 0;
      for (const l of links) {
        if (nodeIds.has(l.source.id) && nodeIds.has(l.target.id)) intraLinks++;
      }
      return arr.length + intraLinks * 0.5;
    });
    const totalWeight = weights.reduce((s, w) => s + w, 0);
    const sectorArcs = weights.map(w => (w / totalWeight) * availableArc);

    // Place sectors sequentially starting from top (-π/2)
    let cursor = -Math.PI / 2 - sectorArcs[0] / 2;

    for (let si = 0; si < sectorNames.length; si++) {
      const cluster = sectorNames[si];
      const usableArc = sectorArcs[si];
      const arr = clusterBuckets.get(cluster);
      if (!arr || arr.length === 0) { cursor += usableArc + gapArc; continue; }

      const startAngle = cursor;
      const endAngle = cursor + usableArc;

      // Sort by degree descending — highest-degree nodes get center positions
      arr.sort((a, b) => (b.degree || 0) - (a.degree || 0));
      // Reorder to place highest-degree at center of arc (interleave from center out)
      const ordered = new Array(arr.length);
      for (let i = 0; i < arr.length; i++) {
        if (i % 2 === 0) ordered[Math.floor(arr.length / 2) + Math.floor(i / 2)] = arr[i];
        else ordered[Math.floor(arr.length / 2) - Math.ceil(i / 2)] = arr[i];
      }

      for (let i = 0; i < ordered.length; i++) {
        const n = ordered[i];
        const ring = RING1_NODES.has(n.id) ? 1 : RING3_NODES.has(n.id) ? 3 : 2;
        const radius = ring === 1 ? LAYOUT_CONFIG.ring1Radius
                     : ring === 2 ? LAYOUT_CONFIG.ring2Radius
                     : LAYOUT_CONFIG.ring3Radius;

        const angle = ordered.length === 1
          ? (startAngle + endAngle) / 2
          : startAngle + (usableArc / (ordered.length + 1)) * (i + 1);

        n.x = Math.cos(angle) * radius;
        n.y = Math.sin(angle) * radius;

        nodeSectorBounds.set(n.id, { minAngle: startAngle, maxAngle: endAngle, minR: radius * 0.7, maxR: radius * 1.4 });
      }

      sectorBoundaries.push({ cluster, startAngle, endAngle, color: CLUSTER_COLORS[cluster] });
      cursor = endAngle + gapArc;
    }
  }

  function clampToSector() {
    for (const n of nodes) {
      const bounds = nodeSectorBounds.get(n.id);
      if (!bounds) continue;

      let angle = Math.atan2(n.y, n.x);
      let r = Math.sqrt(n.x * n.x + n.y * n.y);

      // Normalize angle to match sector range (sectors can exceed π)
      let min = bounds.minAngle, max = bounds.maxAngle;
      // Shift angle into the same revolution as the sector
      while (angle < min - Math.PI) angle += 2 * Math.PI;
      while (angle > max + Math.PI) angle -= 2 * Math.PI;
      angle = Math.max(min, Math.min(max, angle));

      // Clamp radius
      r = Math.max(bounds.minR, Math.min(bounds.maxR, r));

      n.x = Math.cos(angle) * r;
      n.y = Math.sin(angle) * r;
    }
  }

  function setup(data) {
    // Nodes - initial positions will be set by layout algorithm
    nodes = data.nodes.map(n => ({
      ...n,
      x: 0,
      y: 0,
    }));
    nodeById = {};
    for (const n of nodes) nodeById[n.id] = n;

    // Links — drop self-loops; they add visual noise and don't help layout
    links = data.edges.map(e => ({
      ...e,
      source: nodeById[e.source],
      target: nodeById[e.target],
      _sourceId: e.source,
      _targetId: e.target,
    })).filter(l => l.source && l.target && l.source !== l.target);

    linksByNode = {};
    for (const n of nodes) linksByNode[n.id] = [];
    for (const l of links) {
      linksByNode[l.source.id].push(l);
      if (l.source.id !== l.target.id) linksByNode[l.target.id].push(l);
    }

    // Detect reciprocal pairs and assign curve directions
    const pairMap = {};
    for (const l of links) {
      const k = [l.source.id, l.target.id].sort().join('::');
      if (!pairMap[k]) pairMap[k] = [];
      pairMap[k].push(l);
    }
    for (const k in pairMap) {
      if (pairMap[k].length > 1) {
        pairMap[k][0]._curveDir = 1;
        pairMap[k][1]._curveDir = -1;
      }
    }

    // Deterministic concentric ring layout
    applyConcentricLayout();

    // Build cluster counts and populate legend
    const counts = {};
    for (const n of nodes) counts[n.cluster] = (counts[n.cluster] || 0) + 1;

    const legend = document.getElementById('legend');
    if (legend) {
      // Clear any rows from a previous load
      legend.querySelectorAll('.legend-row').forEach(r => r.remove());
      Object.keys(CLUSTER_COLORS).forEach(c => {
        if (!counts[c] || c === 'Solution') return;
        const row = document.createElement('div');
        row.className = 'legend-row';
        row.dataset.cluster = c;
        const dotFill = c === 'Solution' ? CLUSTER_COLORS[c] : hexToSoftFill(CLUSTER_COLORS[c]);
        row.innerHTML = `
          <span class="dot" style="background:${dotFill}; border-color:${CLUSTER_COLORS[c]}"></span>
          <span>${c}</span>
          <span class="count">${counts[c]}</span>
        `;
        row.addEventListener('click', () => {
          if (dimmed.has(c)) dimmed.delete(c); else dimmed.add(c);
          row.classList.toggle('off');
          draw();
        });
        legend.appendChild(row);
      });
    }
  }

  // Preferred radius per node (soft target for radial force)
  let nodeTargetRadius = new Map();

  function initDiffusionSim() {
    // Build target radii
    nodeTargetRadius = new Map();
    for (const n of nodes) {
      if (n.id === 'Solution') { nodeTargetRadius.set(n.id, 0); continue; }
      const ring = RING1_NODES.has(n.id) ? 1 : RING3_NODES.has(n.id) ? 3 : 2;
      const r = ring === 1 ? LAYOUT_CONFIG.ring1Radius
              : ring === 2 ? LAYOUT_CONFIG.ring2Radius
              : LAYOUT_CONFIG.ring3Radius;
      nodeTargetRadius.set(n.id, r);
    }

    const sim = d3.forceSimulation(nodes)
      .force('charge', d3.forceManyBody().strength(-300).distanceMax(500))
      .force('collide', d3.forceCollide().radius(d => radiusFor(d) + 14).strength(1).iterations(2))
      .force('radial', d3.forceRadial(
        d => nodeTargetRadius.get(d.id) || 0,
        0, 0
      ).strength(0.3))
      .alpha(1)
      .alphaDecay(0.04)
      .on('tick', () => {
        // Pin hub at center
        const hub = nodes.find(n => n.id === 'Solution');
        if (hub) { hub.x = 0; hub.y = 0; }
        clampToSector();
        draw();
      })
      .on('end', () => {
        for (const n of nodes) { n.fx = n.x; n.fy = n.y; }
        fitToView();
        draw();
      });

    return sim;
  }

  function resize() {
    const pane = document.getElementById('graph-pane');
    const rect = pane.getBoundingClientRect();
    W = rect.width; H = rect.height;
    dpr = window.devicePixelRatio || 1;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (transform.x === 0 && transform.y === 0 && transform.k === 1) {
      fitToView();
    }
    draw();
  }

  function fitToView() {
    if (!nodes.length || !W || !H) {
      transform = { x: W / 2, y: H / 2, k: 1 };
      return;
    }

    // Compute bounding box including node radii and labels
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const n of nodes) {
      const r = radiusFor(n);
      const labelHeight = 28; // approx height of label below node
      minX = Math.min(minX, n.x - r);
      maxX = Math.max(maxX, n.x + r);
      minY = Math.min(minY, n.y - r);
      maxY = Math.max(maxY, n.y + r + labelHeight);
    }

    const graphW = maxX - minX;
    const graphH = maxY - minY;
    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;

    // Padding around graph (10% on each side)
    const padding = 0.92;
    const scaleX = (W * padding) / graphW;
    const scaleY = (H * padding) / graphH;
    const k = Math.min(scaleX, scaleY, 1.5); // cap at 1.5x to avoid over-zooming small graphs

    transform = {
      k: k,
      x: W / 2 - cx * k,
      y: H / 2 - cy * k,
    };
  }

  // screen → world coordinates
  function toWorld(sx, sy) {
    return { x: (sx - transform.x) / transform.k, y: (sy - transform.y) / transform.k };
  }
  function toScreen(wx, wy) {
    return { x: wx * transform.k + transform.x, y: wy * transform.k + transform.y };
  }

  function isClusterOn(c) { return !dimmed.has(c); }

  function nodeIsDim(n) {
    if (!isClusterOn(n.cluster)) return true;
    if (selectedNode) {
      if (n === selectedNode) return false;
      const neighbors = new Set();
      for (const l of linksByNode[selectedNode.id]) {
        neighbors.add(l.source.id); neighbors.add(l.target.id);
      }
      if (!neighbors.has(n.id)) return true;
    } else if (hoverNode) {
      if (n === hoverNode) return false;
      const neighbors = new Set();
      for (const l of linksByNode[hoverNode.id]) {
        neighbors.add(l.source.id); neighbors.add(l.target.id);
      }
      if (!neighbors.has(n.id)) return true;
    } else if (selectedEdge) {
      if (n === selectedEdge.source || n === selectedEdge.target) return false;
      return true;
    }
    return false;
  }

  function linkIsDim(l) {
    if (!isClusterOn(l.source.cluster) || !isClusterOn(l.target.cluster)) return true;
    if (selectedNode) {
      return l.source !== selectedNode && l.target !== selectedNode;
    } else if (hoverNode) {
      return l.source !== hoverNode && l.target !== hoverNode;
    } else if (selectedEdge) {
      return l !== selectedEdge;
    }
    return false;
  }

  function draw() {
    if (!ctx) return;
    ctx.clearRect(0, 0, W, H);

    ctx.save();
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.k, transform.k);

    // --- draw sector wedge fills and separators ---
    const sepRadius = LAYOUT_CONFIG.ring3Radius + 80;
    for (const sec of sectorBoundaries) {
      ctx.save();
      // Subtle wedge fill
      const c = sec.color;
      const r = parseInt(c.slice(1,3),16), g = parseInt(c.slice(3,5),16), b = parseInt(c.slice(5,7),16);
      ctx.fillStyle = `rgba(${r},${g},${b},0.03)`;
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.arc(0, 0, sepRadius, sec.startAngle, sec.endAngle);
      ctx.closePath();
      ctx.fill();
      // Separator line at startAngle
      ctx.strokeStyle = 'rgba(18,20,23,0.12)';
      ctx.lineWidth = 0.8;
      ctx.setLineDash([6, 4]);
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(Math.cos(sec.startAngle) * sepRadius, Math.sin(sec.startAngle) * sepRadius);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.restore();
    }

    // --- draw links ---
    // Two passes: dim first, then bright
    for (const pass of ['dim', 'bright']) {
      for (const l of links) {
        const isDim = linkIsDim(l);
        if (pass === 'dim' && !isDim) continue;
        if (pass === 'bright' && isDim) continue;
        drawLink(l, isDim);
      }
    }

    // --- draw nodes ---
    for (const pass of ['dim', 'bright']) {
      for (const n of nodes) {
        const isDim = nodeIsDim(n);
        if (pass === 'dim' && !isDim) continue;
        if (pass === 'bright' && isDim) continue;
        drawNode(n, isDim);
      }
    }

    // --- labels (on top) ---
    for (const n of nodes) {
      if (nodeIsDim(n)) continue;
      drawLabel(n);
    }

    // Edge labels: show on hover OR select of a node, otherwise hover/selected edge
    const activeNode = selectedNode || hoverNode;
    if (activeNode) {
      const edgesToDraw = (linksByNode[activeNode.id] || []).filter(l => l.source !== l.target);
      for (const l of edgesToDraw) drawEdgeLabel(l);
    } else if (selectedEdge) {
      drawEdgeLabel(selectedEdge);
    } else if (hoverEdge) {
      drawEdgeLabel(hoverEdge);
    }

    ctx.restore();
  }

  // Compute quadratic bezier control point for curved reciprocal edges
  // Only curves when the edge is connected to the active (hovered/selected) node
  function getCurveControl(l) {
    if (!l._curveDir) return null;
    const activeNode = selectedNode || hoverNode;
    if (!activeNode) return null;
    if (l.source !== activeNode && l.target !== activeNode) return null;
    const mx = (l.source.x + l.target.x) / 2;
    const my = (l.source.y + l.target.y) / 2;
    // Use canonical direction (sorted node IDs) so reciprocal pairs get genuinely opposite curves
    const [id1, id2] = [l.source.id, l.target.id].sort();
    const n1 = nodeById[id1], n2 = nodeById[id2];
    const dx = n2.x - n1.x;
    const dy = n2.y - n1.y;
    const len = Math.sqrt(dx * dx + dy * dy) || 1;
    const perpX = -dy / len;
    const perpY = dx / len;
    const bow = Math.min(len * 0.25, 60);
    return { x: mx + perpX * bow * l._curveDir, y: my + perpY * bow * l._curveDir };
  }

  function drawLink(l, isDim) {
    const sx = l.source.x, sy = l.source.y;
    const tx = l.target.x, ty = l.target.y;

    ctx.save();

    const dx = tx - sx, dy = ty - sy;
    const len = Math.sqrt(dx*dx + dy*dy) || 1;
    const ux = dx / len, uy = dy / len;
    const rs = radiusFor(l.source), rt = radiusFor(l.target);
    const x1 = sx + ux * rs, y1 = sy + uy * rs;
    const x2 = tx - ux * rt, y2 = ty - uy * rt;

    const isHighlight = l === selectedEdge || l === hoverEdge ||
      (selectedNode && (l.source === selectedNode || l.target === selectedNode)) ||
      (hoverNode && (l.source === hoverNode || l.target === hoverNode));

    if (isDim) {
      ctx.strokeStyle = 'rgba(18,20,23,0.05)';
      ctx.lineWidth = 0.8;
    } else if (isHighlight) {
      ctx.strokeStyle = '#B31B1B';
      ctx.lineWidth = 1.6;
    } else {
      ctx.strokeStyle = 'rgba(18,20,23,0.18)';
      ctx.lineWidth = 1;
    }

    const cp = getCurveControl(l);

    ctx.beginPath();
    ctx.moveTo(x1, y1);
    if (cp) {
      ctx.quadraticCurveTo(cp.x, cp.y, x2, y2);
    } else {
      ctx.lineTo(x2, y2);
    }
    ctx.stroke();

    // Arrowheads at both ends
    const arrSize = isHighlight ? 13 : 8;
    ctx.fillStyle = isHighlight ? ctx.strokeStyle : 'rgba(18,20,23,0.10)';

    // Target-end arrow — angle matches curve tangent at endpoint
    let targetAngle;
    if (cp) {
      targetAngle = Math.atan2(y2 - cp.y, x2 - cp.x);
    } else {
      targetAngle = Math.atan2(dy, dx);
    }
    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - arrSize * Math.cos(targetAngle - Math.PI / 7),
               y2 - arrSize * Math.sin(targetAngle - Math.PI / 7));
    ctx.lineTo(x2 - arrSize * Math.cos(targetAngle + Math.PI / 7),
               y2 - arrSize * Math.sin(targetAngle + Math.PI / 7));
    ctx.closePath();
    ctx.fill();

    // Source-end arrow — tangent at start, offset inward along curve
    let sourceAngle;
    if (cp) {
      sourceAngle = Math.atan2(cp.y - y1, cp.x - x1);
    } else {
      sourceAngle = Math.atan2(dy, dx);
    }
    const srcOffset = arrSize * 2;
    const srcAx = x1 + Math.cos(sourceAngle) * srcOffset;
    const srcAy = y1 + Math.sin(sourceAngle) * srcOffset;
    ctx.beginPath();
    ctx.moveTo(srcAx, srcAy);
    ctx.lineTo(srcAx - arrSize * Math.cos(sourceAngle - Math.PI / 7),
               srcAy - arrSize * Math.sin(sourceAngle - Math.PI / 7));
    ctx.lineTo(srcAx - arrSize * Math.cos(sourceAngle + Math.PI / 7),
               srcAy - arrSize * Math.sin(sourceAngle + Math.PI / 7));
    ctx.closePath();
    ctx.fill();

    ctx.restore();
  }

  function drawNode(n, isDim) {
    const r = radiusFor(n);
    const isSel = n === selectedNode;
    const isHov = n === hoverNode;

    ctx.save();

    if (isDim) {
      ctx.globalAlpha = 0.15;
    }

    const color = colorFor(n.cluster);

    // Outer selection ring
    if (isSel) {
      ctx.strokeStyle = '#B31B1B';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(n.x, n.y, r + 6, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Fill
    if (n.cluster === 'Solution' || isSel) {
      ctx.fillStyle = color;
    } else {
      ctx.fillStyle = hexToSoftFill(color);
    }
    ctx.beginPath();
    ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
    ctx.fill();

    // Stroke
    ctx.strokeStyle = color;
    ctx.lineWidth = isSel ? 2 : (isHov ? 1.6 : 1.2);
    ctx.stroke();

    ctx.restore();
  }

  function hexToSoftFill(hex) {
    // render the color at ~10% over paper
    const r = parseInt(hex.slice(1,3),16);
    const g = parseInt(hex.slice(3,5),16);
    const b = parseInt(hex.slice(5,7),16);
    // blend with paper #FBFAF6
    const a = 0.14;
    const pr = 251, pg = 250, pb = 246;
    const rr = Math.round(r*a + pr*(1-a));
    const gg = Math.round(g*a + pg*(1-a));
    const bb = Math.round(b*a + pb*(1-a));
    return `rgb(${rr},${gg},${bb})`;
  }

  function drawLabel(n) {
    const r = radiusFor(n);
    const isSel = n === selectedNode;
    const isHov = n === hoverNode;

    ctx.save();
    ctx.font = `${isSel ? 600 : 500} ${isSel ? 22 : 20}px "Inter Tight", system-ui, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';

    const label = n.label;
    const metrics = ctx.measureText(label);
    const padX = 7, padY = 4;
    const lw = metrics.width + padX * 2;
    const lh = 19 + padY * 2;
    const ly = n.y + r + 6;

    // paper backdrop for label legibility
    ctx.fillStyle = 'rgba(251, 250, 246, 0.88)';
    ctx.fillRect(n.x - lw / 2, ly - padY, lw, lh);

    ctx.fillStyle = '#121417';
    ctx.fillText(label, n.x, ly);
    ctx.restore();
  }

  function drawEdgeLabel(l) {
    if (l.source === l.target) return;

    // Position at curve midpoint (t=0.5 on quadratic bezier) or line midpoint
    const cp = getCurveControl(l);
    let lx, ly;
    if (cp) {
      lx = 0.25 * l.source.x + 0.5 * cp.x + 0.25 * l.target.x;
      ly = 0.25 * l.source.y + 0.5 * cp.y + 0.25 * l.target.y;
    } else {
      lx = (l.source.x + l.target.x) / 2;
      ly = (l.source.y + l.target.y) / 2;
    }

    ctx.save();
    ctx.font = `italic 700 18px "Instrument Serif", "Fraunces", Georgia, serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    const metrics = ctx.measureText(l.label);
    const padX = 10, padY = 5;
    const w = metrics.width + padX * 2;
    const h = 24 + padY;

    ctx.fillStyle = 'rgba(251, 250, 246, 0.95)';
    ctx.strokeStyle = 'rgba(179,27,27,0.4)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.rect(lx - w / 2, ly - h / 2, w, h);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#B31B1B';
    ctx.fillText(l.label, lx, ly + 1);
    ctx.restore();
  }

  // --- hit testing ---
  function nodeAt(wx, wy) {
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i];
      if (!isClusterOn(n.cluster)) continue;
      const r = radiusFor(n);
      const dx = wx - n.x, dy = wy - n.y;
      if (dx*dx + dy*dy <= (r + 2) * (r + 2)) return n;
    }
    return null;
  }

  function edgeAt(wx, wy) {
    let best = null, bestDist = 6; // world-space tolerance
    for (const l of links) {
      if (l.source === l.target) continue;
      if (!isClusterOn(l.source.cluster) || !isClusterOn(l.target.cluster)) continue;
      const cp = getCurveControl(l);
      let d;
      if (cp) {
        d = distToBezier(wx, wy, l.source.x, l.source.y, cp.x, cp.y, l.target.x, l.target.y);
      } else {
        d = distToSegment(wx, wy, l.source.x, l.source.y, l.target.x, l.target.y);
      }
      if (d < bestDist) { bestDist = d; best = l; }
    }
    return best;
  }

  function distToBezier(px, py, x0, y0, cx, cy, x1, y1) {
    // Sample the quadratic bezier at intervals and find closest point
    let minD = Infinity;
    for (let t = 0; t <= 1; t += 0.05) {
      const it = 1 - t;
      const bx = it * it * x0 + 2 * it * t * cx + t * t * x1;
      const by = it * it * y0 + 2 * it * t * cy + t * t * y1;
      const d = Math.hypot(px - bx, py - by);
      if (d < minD) minD = d;
    }
    return minD;
  }

  function distToSegment(px, py, x1, y1, x2, y2) {
    const dx = x2 - x1, dy = y2 - y1;
    const l2 = dx*dx + dy*dy;
    if (l2 === 0) return Math.hypot(px - x1, py - y1);
    let t = ((px - x1) * dx + (py - y1) * dy) / l2;
    t = Math.max(0, Math.min(1, t));
    const x = x1 + t * dx, y = y1 + t * dy;
    return Math.hypot(px - x, py - y);
  }

  // --- interaction ---
  function onMouseMove(e) {
    const rect = canvas.getBoundingClientRect();
    const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
    const { x: wx, y: wy } = toWorld(sx, sy);

    if (dragNode) {
      dragNode.x = wx; dragNode.y = wy;
      dragNode.fx = wx; dragNode.fy = wy;
      if (simulation) simulation.alphaTarget(0.1).restart();
      draw();
      return;
    }
    if (isPanning) {
      transform.x = panStart.tx + (e.clientX - panStart.mx);
      transform.y = panStart.ty + (e.clientY - panStart.my);
      draw();
      return;
    }

    const prevHover = hoverNode, prevEdge = hoverEdge;
    hoverNode = nodeAt(wx, wy);
    hoverEdge = hoverNode ? null : edgeAt(wx, wy);

    canvas.style.cursor = hoverNode ? 'pointer' : (hoverEdge ? 'pointer' : 'grab');
    if (prevHover !== hoverNode || prevEdge !== hoverEdge) draw();
  }

  function onMouseDown(e) {
    const rect = canvas.getBoundingClientRect();
    const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
    const { x: wx, y: wy } = toWorld(sx, sy);
    const hit = nodeAt(wx, wy);
    if (hit) {
      dragNode = hit;
      dragStart = { mx: e.clientX, my: e.clientY, moved: false };
      hit.fx = hit.x; hit.fy = hit.y;
      if (simulation) simulation.alphaTarget(0.1).restart();
    } else {
      isPanning = true;
      panStart = { mx: e.clientX, my: e.clientY, tx: transform.x, ty: transform.y };
    }
  }

  function onMouseUp(e) {
    if (dragNode) {
      const moved = dragStart && (Math.abs(e.clientX - dragStart.mx) + Math.abs(e.clientY - dragStart.my) > 3);
      if (!moved) {
        // treat as click
        selectNode(dragNode);
      }
      if (simulation) simulation.alphaTarget(0);
      dragNode.fx = dragNode.x; dragNode.fy = dragNode.y;
      dragNode = null;
      draw();
      return;
    }
    if (isPanning) {
      const moved = Math.abs(e.clientX - panStart.mx) + Math.abs(e.clientY - panStart.my) > 3;
      isPanning = false;
      if (!moved) {
        // clicked empty: try edge, else deselect
        const rect = canvas.getBoundingClientRect();
        const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
        const { x: wx, y: wy } = toWorld(sx, sy);
        const edge = edgeAt(wx, wy);
        if (edge) selectEdge(edge);
        else deselect();
      }
    }
  }

  function onWheel(e) {
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
    const factor = e.deltaY < 0 ? 1.1 : 1/1.1;
    zoomAt(sx, sy, factor);
  }

  function zoomAt(sx, sy, factor) {
    const before = toWorld(sx, sy);
    transform.k = Math.max(0.3, Math.min(3, transform.k * factor));
    const after = toWorld(sx, sy);
    transform.x += (after.x - before.x) * transform.k;
    transform.y += (after.y - before.y) * transform.k;
    draw();
  }

  function resetZoom() {
    fitToView();
    draw();
  }

  function selectNode(n) {
    selectedNode = n;
    selectedEdge = null;
    draw();
    window.Inspector && window.Inspector.showNode(n);
  }
  function selectEdge(l) {
    selectedEdge = l;
    selectedNode = null;
    draw();
    window.Inspector && window.Inspector.showEdge(l);
  }
  function deselect() {
    selectedNode = null;
    selectedEdge = null;
    draw();
    window.Inspector && window.Inspector.showEmpty();
  }

  function focusNode(id) {
    const n = nodeById[id];
    if (n) selectNode(n);
  }


  function init() {
    canvas = document.getElementById('graph');

    canvas.addEventListener('mousemove', onMouseMove);
    canvas.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mouseup', onMouseUp);
    canvas.addEventListener('wheel', onWheel, { passive: false });
    window.addEventListener('resize', resize);

    document.getElementById('zoom-in').onclick = () => zoomAt(W/2, H/2, 1.25);
    document.getElementById('zoom-out').onclick = () => zoomAt(W/2, H/2, 1/1.25);
    document.getElementById('zoom-reset').onclick = resetZoom;
  }

  function load(graphData) {
    window.ONTOLOGY = graphData;
    if (simulation) simulation.stop();
    transform = { x: 0, y: 0, k: 1 };
    setup(graphData);
    resize();
    fitToView();
    simulation = initDiffusionSim();
    draw();
    window.Inspector && window.Inspector.showEmpty();
  }

  window.Graph = {
    init, load, focusNode, selectNode, selectEdge, deselect,
    getNodeById: id => nodeById[id],
    getNodes: () => nodes,
    getLinks: () => links,
    getLinksForNode: id => linksByNode[id] || [],
    getClusterColor: colorFor,
    layoutConfig: LAYOUT_CONFIG,
  };
})();
