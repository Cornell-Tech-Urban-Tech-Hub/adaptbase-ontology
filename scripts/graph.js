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
    ring1Radius: 180,           // Inner ring (structural connectors)
    ring2Radius: 300,           // Middle ring (hub neighbors)
    ring3Radius: 400,           // Outer ring (leaves)
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
  let simulation;
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

  function applyConcentricLayout() {
    const hub = nodes.find(n => n.id === 'Solution');
    if (!hub) return;
    hub.x = 0;
    hub.y = 0;

    nodeSectorBounds = new Map();

    // Group non-hub nodes by cluster, assign ring per node
    const clusterBuckets = new Map();
    for (const n of nodes) {
      if (n === hub) continue;
      if (!clusterBuckets.has(n.cluster)) clusterBuckets.set(n.cluster, []);
      clusterBuckets.get(n.cluster).push(n);
    }

    // Each cluster gets a sector wedge; place nodes within that wedge at their ring radius
    const sectorNames = Object.keys(SECTOR_ANGLES);
    const sectorArc = (2 * Math.PI) / sectorNames.length;
    const gapArc = sectorArc * 0.12;
    const usableArc = sectorArc - gapArc;

    for (const cluster of sectorNames) {
      const arr = clusterBuckets.get(cluster);
      if (!arr || arr.length === 0) continue;

      arr.sort((a, b) => {
        const ringA = RING1_NODES.has(a.id) ? 1 : RING3_NODES.has(a.id) ? 3 : 2;
        const ringB = RING1_NODES.has(b.id) ? 1 : RING3_NODES.has(b.id) ? 3 : 2;
        if (ringA !== ringB) return ringA - ringB;
        return (b.degree || 0) - (a.degree || 0);
      });

      const centerAngle = SECTOR_ANGLES[cluster];
      const startAngle = centerAngle - usableArc / 2;
      const endAngle = centerAngle + usableArc / 2;

      for (let i = 0; i < arr.length; i++) {
        const n = arr[i];
        const ring = RING1_NODES.has(n.id) ? 1 : RING3_NODES.has(n.id) ? 3 : 2;
        const radius = ring === 1 ? LAYOUT_CONFIG.ring1Radius
                     : ring === 2 ? LAYOUT_CONFIG.ring2Radius
                     : LAYOUT_CONFIG.ring3Radius;

        const angle = arr.length === 1
          ? centerAngle
          : startAngle + (usableArc / (arr.length - 1)) * i;

        n.x = Math.cos(angle) * radius;
        n.y = Math.sin(angle) * radius;

        // Store sector bounds for collision clamping
        nodeSectorBounds.set(n.id, { minAngle: startAngle, maxAngle: endAngle, minR: radius * 0.7, maxR: radius * 1.4 });
      }
    }
  }

  function clampToSector() {
    for (const n of nodes) {
      const bounds = nodeSectorBounds.get(n.id);
      if (!bounds) continue;

      let angle = Math.atan2(n.y, n.x);
      let r = Math.sqrt(n.x * n.x + n.y * n.y);

      // Clamp angle to sector
      // Handle wrap-around for sectors crossing the -π/π boundary
      let min = bounds.minAngle, max = bounds.maxAngle;
      if (min > max) {
        // Sector wraps around ±π
        if (angle < min && angle > max) {
          angle = (Math.abs(angle - min) < Math.abs(angle - max)) ? min : max;
        }
      } else {
        angle = Math.max(min, Math.min(max, angle));
      }

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
        if (!counts[c]) return;
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

  function initSim() {
    simulation = d3.forceSimulation(nodes)
      .force('collide', d3.forceCollide()
        .radius(d => radiusFor(d) + 32)
        .strength(0.9)
        .iterations(4)
      )
      .alpha(0.5)
      .alphaDecay(0.05)
      .on('tick', () => { clampToSector(); draw(); })
      .on('end', () => {
        for (const n of nodes) { n.fx = n.x; n.fy = n.y; }
        fitToView();
        draw();
      });
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

    // Edge labels: all connected edges when a node is selected, otherwise hover/selected edge
    if (selectedNode) {
      const edgesToDraw = (linksByNode[selectedNode.id] || []).filter(l => l.source !== l.target);
      // Detect reciprocal pairs (same two nodes, opposite directions)
      const pairKey = (l) => [l.source.id, l.target.id].sort().join('::');
      const pairCounts = {};
      const pairIndex = {};
      for (const l of edgesToDraw) {
        const k = pairKey(l);
        pairCounts[k] = (pairCounts[k] || 0) + 1;
        pairIndex[k] = 0;
      }
      for (const l of edgesToDraw) {
        const k = pairKey(l);
        let offset = 0;
        if (pairCounts[k] > 1) {
          offset = pairIndex[k] === 0 ? -1 : 1;
          pairIndex[k]++;
        }
        drawEdgeLabel(l, offset);
      }
    } else if (selectedEdge) {
      drawEdgeLabel(selectedEdge, 0);
    } else if (hoverEdge) {
      drawEdgeLabel(hoverEdge, 0);
    }

    ctx.restore();
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

    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();

    // Arrow heads — one at each end, both pointing source→target
    const arrSize = isHighlight ? 13 : 10;
    const angle = Math.atan2(dy, dx);
    ctx.fillStyle = ctx.strokeStyle;

    function drawArrow(px, py) {
      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.lineTo(px - arrSize * Math.cos(angle - Math.PI / 7),
                 py - arrSize * Math.sin(angle - Math.PI / 7));
      ctx.lineTo(px - arrSize * Math.cos(angle + Math.PI / 7),
                 py - arrSize * Math.sin(angle + Math.PI / 7));
      ctx.closePath();
      ctx.fill();
    }

    // target-end arrow
    drawArrow(x2, y2);
    // source-end arrow — placed arrSize*2 along the line from x1,y1
    const srcOffset = arrSize * 2;
    drawArrow(x1 + ux * srcOffset, y1 + uy * srcOffset);

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

  function drawEdgeLabel(l, offsetIndex) {
    if (l.source === l.target) return;

    const mx = (l.source.x + l.target.x) / 2;
    const my = (l.source.y + l.target.y) / 2;

    // Offset perpendicular to the edge for reciprocal pairs
    const dx = l.target.x - l.source.x;
    const dy = l.target.y - l.source.y;
    const len = Math.sqrt(dx * dx + dy * dy) || 1;
    const perpX = -dy / len;
    const perpY = dx / len;
    const offset = (offsetIndex || 0) * 26;

    const lx = mx + perpX * offset;
    const ly = my + perpY * offset;

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
      const d = distToSegment(wx, wy, l.source.x, l.source.y, l.target.x, l.target.y);
      if (d < bestDist) { bestDist = d; best = l; }
    }
    return best;
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
      dragNode.fx = wx; dragNode.fy = wy;
      simulation.alphaTarget(0.3).restart();
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
      simulation.alphaTarget(0.3).restart();
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
      simulation.alphaTarget(0);
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
    initSim();
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
