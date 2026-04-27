// Force-directed graph on canvas.
// Exposes window.Graph with init, focusNode(id), selectEdge(id), setPhysics(bool),
// getNodeById, getEdgesForNode, etc.

(function () {
  const CLUSTER_COLORS = {
    'Core':     '#B31B1B',  // carnelian (Solution only)
    'Threat':   '#6B4C9A',  // purple (hazard, vulnerability, exposure, barrier) - distinct from Planning grey
    'Place':    '#2E7D4F',  // chlorophyll (location, urban system)
    'Actors':   '#1E4DD8',  // blueprint
    'Outcomes': '#F4A02C',  // sodium
    'Finance':  '#4A4F57',  // graphite
    'Planning': '#8A8F98',  // concrete
  };

  // Hub-spoke layout configuration
  const LAYOUT_CONFIG = {
    hubRadius: 280,             // Distance from hub to 1st-degree neighbors
    singletonRadiusMult: 1.45,  // Singletons pushed further out to clear chord edges
    outerRadiusMult: 1.75,      // Outer nodes (Indicator, FinancingSource) further still
    chargeStrength: -520,       // Repulsion strength between nodes
    linkDistance: 100,          // Base link distance
    collisionRadius: 30,        // Padding around nodes for collision detection
    layoutIterations: 400,      // Number of simulation ticks before stopping
    randomSeed: 12345,          // Seed for deterministic positioning
  };

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
  let physicsOn = false;

  function colorFor(cluster) { return CLUSTER_COLORS[cluster] || '#4A4F57'; }

  function radiusFor(d) {
    // degree-based; min 14, max ~60 (2x previous)
    const deg = d.degree || 1;
    return 14 + Math.min(46, Math.sqrt(deg) * 9);
  }

  // Seeded random number generator for deterministic layout
  let rngSeed = LAYOUT_CONFIG.randomSeed;
  function seededRandom() {
    rngSeed = (rngSeed * 9301 + 49297) % 233280;
    return rngSeed / 233280;
  }

  function applyHubSpokeLayout() {
    // Reset seed for deterministic positioning
    rngSeed = LAYOUT_CONFIG.randomSeed;

    // Find hub node (Solution)
    const hub = nodes.find(n => n.id === 'Solution');
    if (!hub) {
      console.warn('Hub node "Solution" not found, applying random layout');
      for (const n of nodes) {
        n.x = (seededRandom() - 0.5) * 400;
        n.y = (seededRandom() - 0.5) * 400;
      }
      return;
    }

    // Position hub at center
    hub.x = 0;
    hub.y = 0;

    // Find spoke nodes (1st-degree neighbors of hub)
    const hubLinks = links.filter(l =>
      (l.source.id === hub.id || l.target.id === hub.id) &&
      l.source !== l.target
    );

    const spokes = new Set();
    for (const l of hubLinks) {
      if (l.source !== hub) spokes.add(l.source);
      if (l.target !== hub) spokes.add(l.target);
    }

    if (spokes.size === 0) {
      console.warn('No spokes found');
      return;
    }

    // Find secondary edges (spoke-to-spoke connections)
    const secondaryEdges = [];
    const spokeIds = new Set(Array.from(spokes).map(n => n.id));
    for (const l of links) {
      if (l.source !== hub && l.target !== hub &&
          spokeIds.has(l.source.id) && spokeIds.has(l.target.id)) {
        secondaryEdges.push(l);
      }
    }

    console.log(`Step 0: Found ${spokes.size} spokes, ${secondaryEdges.length} secondary edges`);

    // STEP 1: Decompose into connected components
    const allComponents = findConnectedComponents(Array.from(spokes), secondaryEdges);
    const multiComps = allComponents.filter(c => c.length > 1);
    const singletons = allComponents
      .filter(c => c.length === 1)
      .map(c => c[0])
      .sort((a, b) => a.id.localeCompare(b.id)); // deterministic

    console.log(`Step 1: ${multiComps.length} multi-node components + ${singletons.length} singletons`);
    multiComps.forEach((c, i) => console.log(`  Multi[${i}]: [${c.map(n => n.id).join(', ')}]`));

    // STEP 2: Order nodes within each multi-node component (DFS for trees, barycenter for cycles)
    const orderedMultiComps = multiComps.map(c => orderWithinComponent(c, secondaryEdges));
    orderedMultiComps.forEach((c, i) =>
      console.log(`Step 2: Multi[${i}] internal order: [${c.map(n => n.id).join(', ')}]`)
    );

    // STEP 3: Optimize multi-node component circular ordering (minimize cross-component crossings)
    const optimizedComps = optimizeMultiComponentOrder(orderedMultiComps, secondaryEdges);
    console.log(`Step 3: Component cyclic order:`,
      optimizedComps.map(c => `[${c.map(n => n.id).join(',')}]`));

    // STEP 4: Distribute singletons across gaps between multi-node components
    const numGaps = Math.max(1, optimizedComps.length);
    const gapSingletons = Array.from({ length: numGaps }, () => []);
    for (let i = 0; i < singletons.length; i++) {
      gapSingletons[i % numGaps].push(singletons[i]);
    }
    console.log(`Step 4: Singleton distribution per gap:`,
      gapSingletons.map(g => g.map(n => n.id)));

    // STEP 5: Build final spoke order (multi-comp + gap-singletons interleaved)
    const orderedSpokes = [];
    if (optimizedComps.length === 0) {
      orderedSpokes.push(...singletons);
    } else {
      for (let i = 0; i < optimizedComps.length; i++) {
        orderedSpokes.push(...optimizedComps[i]);
        orderedSpokes.push(...gapSingletons[i]);
      }
    }

    // STEP 6: Place spokes around circle
    const spokeAngles = placeSpokesAroundCircle(orderedSpokes, singletons);

    const crossings = countAllCrossings(orderedSpokes, secondaryEdges, hub, spokeAngles);
    console.log(`Step 6: Layout complete with ${crossings} crossings`);

    // STEP 7: Position outer nodes (non-spokes like Indicator, FinancingSource)
    positionOuterNodes(nodes, hub, spokes, links, spokeAngles);

    console.log(`Hub-spoke layout: ${spokes.size} spokes, ${crossings} crossings`);
  }

  // Place spokes evenly around circle, with singletons at slightly larger radius
  function placeSpokesAroundCircle(orderedSpokes, singletonsList) {
    const angles = new Map();
    const angleStep = (2 * Math.PI) / orderedSpokes.length;
    const singletonIds = new Set(singletonsList.map(n => n.id));

    orderedSpokes.forEach((n, i) => {
      const angle = i * angleStep - Math.PI / 2;
      const radius = singletonIds.has(n.id)
        ? LAYOUT_CONFIG.hubRadius * LAYOUT_CONFIG.singletonRadiusMult
        : LAYOUT_CONFIG.hubRadius;
      n.x = Math.cos(angle) * radius;
      n.y = Math.sin(angle) * radius;
      angles.set(n.id, angle);
    });

    return angles;
  }

  // Find optimal cyclic ordering of multi-node components to minimize crossings
  function optimizeMultiComponentOrder(orderedMultiComps, secondaryEdges) {
    if (orderedMultiComps.length <= 1) return orderedMultiComps;
    if (orderedMultiComps.length === 2) return orderedMultiComps; // 2 comps: only 1 cyclic order

    // For small numbers, try all permutations (fixing first component to break rotational symmetry)
    const n = orderedMultiComps.length;
    if (n <= 7) {
      let best = orderedMultiComps;
      let bestCrossings = countCrossingsForComponentOrder(orderedMultiComps, secondaryEdges);

      const fixed = orderedMultiComps[0];
      const rest = orderedMultiComps.slice(1);
      const perms = [];
      generatePermutations(rest, 0, [], perms);

      for (const perm of perms) {
        const candidate = [fixed, ...perm];
        const crossings = countCrossingsForComponentOrder(candidate, secondaryEdges);
        if (crossings < bestCrossings) {
          bestCrossings = crossings;
          best = candidate;
        }
      }
      return best;
    }

    // For larger numbers, use 2-opt
    let current = [...orderedMultiComps];
    let bestCrossings = countCrossingsForComponentOrder(current, secondaryEdges);
    let improved = true;
    while (improved) {
      improved = false;
      for (let i = 0; i < current.length - 1; i++) {
        for (let j = i + 1; j < current.length; j++) {
          // Try swapping i and j
          [current[i], current[j]] = [current[j], current[i]];
          const newCrossings = countCrossingsForComponentOrder(current, secondaryEdges);
          if (newCrossings < bestCrossings) {
            bestCrossings = newCrossings;
            improved = true;
          } else {
            [current[i], current[j]] = [current[j], current[i]]; // revert
          }
        }
      }
    }
    return current;
  }

  function countCrossingsForComponentOrder(orderedComps, secondaryEdges) {
    // Place components contiguously and count crossings
    const flat = orderedComps.flat();
    const angles = new Map();
    const step = (2 * Math.PI) / flat.length;
    flat.forEach((n, i) => angles.set(n.id, i * step - Math.PI / 2));
    return countAllCrossings(flat, secondaryEdges, null, angles);
  }

  // STEP 1: Find connected components in spoke subgraph
  function findConnectedComponents(spokes, secondaryEdges) {
    const adj = new Map();
    for (const n of spokes) adj.set(n.id, []);
    for (const e of secondaryEdges) {
      adj.get(e.source.id).push(e.target);
      adj.get(e.target.id).push(e.source);
    }

    const visited = new Set();
    const components = [];

    for (const start of spokes) {
      if (visited.has(start.id)) continue;

      const component = [];
      const queue = [start];
      visited.add(start.id);

      while (queue.length > 0) {
        const node = queue.shift();
        component.push(node);

        for (const neighbor of adj.get(node.id)) {
          if (!visited.has(neighbor.id)) {
            visited.add(neighbor.id);
            queue.push(neighbor);
          }
        }
      }

      components.push(component);
    }

    return components;
  }

  // Order nodes within a component (DFS for trees, barycenter for cycles)
  function orderWithinComponent(component, secondaryEdges) {
    if (component.length === 1) return component;

    // Build adjacency for this component
    const adj = new Map();
    const nodeIds = new Set(component.map(n => n.id));
    for (const n of component) adj.set(n.id, []);
    for (const e of secondaryEdges) {
      if (nodeIds.has(e.source.id) && nodeIds.has(e.target.id)) {
        adj.get(e.source.id).push(e.target);
        adj.get(e.target.id).push(e.source);
      }
    }

    // Find a leaf or endpoint (degree-1 node) for DFS start
    let start = component[0];
    for (const n of component) {
      if (adj.get(n.id).length === 1) {
        start = n;
        break;
      }
    }

    // DFS traversal
    const ordered = [];
    const visited = new Set();

    function dfs(node) {
      visited.add(node.id);
      ordered.push(node);
      for (const neighbor of adj.get(node.id)) {
        if (!visited.has(neighbor.id)) {
          dfs(neighbor);
        }
      }
    }

    dfs(start);

    // If component has cycles or wasn't fully connected, add remaining nodes
    for (const n of component) {
      if (!visited.has(n.id)) ordered.push(n);
    }

    return ordered;
  }

  function generatePermutations(arr, start, current, results) {
    if (current.length === arr.length) {
      results.push([...current]);
      return;
    }

    // Limit to prevent combinatorial explosion
    if (results.length > 720) return; // 6! = 720

    for (let i = 0; i < arr.length; i++) {
      if (!current.includes(arr[i])) {
        current.push(arr[i]);
        generatePermutations(arr, start, current, results);
        current.pop();
      }
    }
  }

  function countAllCrossings(orderedSpokes, secondaryEdges, hub, angles) {
    let crossings = 0;

    // Check all pairs of secondary edges
    for (let i = 0; i < secondaryEdges.length; i++) {
      for (let j = i + 1; j < secondaryEdges.length; j++) {
        const e1 = secondaryEdges[i];
        const e2 = secondaryEdges[j];

        // Skip if edges share a node
        if (e1.source === e2.source || e1.source === e2.target ||
            e1.target === e2.source || e1.target === e2.target) {
          continue;
        }

        // Get angles
        const a1 = angles.get(e1.source.id);
        const a2 = angles.get(e1.target.id);
        const b1 = angles.get(e2.source.id);
        const b2 = angles.get(e2.target.id);

        if (edgesCrossInCircularLayout(a1, a2, b1, b2)) {
          crossings++;
        }
      }
    }

    return crossings;
  }

  function edgesCrossInCircularLayout(a1, a2, b1, b2) {
    // Two chords in a circle cross iff their endpoints alternate around the circle
    // Normalize angles to [0, 2π)
    const normalize = (a) => ((a % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);

    let angles = [
      {a: normalize(a1), edge: 1},
      {a: normalize(a2), edge: 1},
      {a: normalize(b1), edge: 2},
      {a: normalize(b2), edge: 2}
    ];

    angles.sort((x, y) => x.a - y.a);

    // Edges cross iff pattern is 1,2,1,2 or 2,1,2,1
    const pattern = angles.map(x => x.edge).join('');
    return pattern === '1212' || pattern === '2121';
  }

  function positionOuterNodes(allNodes, hub, spokes, links, spokeAngles) {
    for (const n of allNodes) {
      if (n === hub || spokes.has(n)) continue;

      // Find connected spokes
      const connectedSpokes = [];
      for (const l of links) {
        if (l.source === n && spokes.has(l.target)) {
          connectedSpokes.push(l.target);
        } else if (l.target === n && spokes.has(l.source)) {
          connectedSpokes.push(l.source);
        }
      }

      if (connectedSpokes.length > 0) {
        // Position at average angle, outer ring
        let avgAngle = 0;
        for (const spoke of connectedSpokes) {
          avgAngle += spokeAngles.get(spoke.id);
        }
        avgAngle /= connectedSpokes.length;

        const outerRadius = LAYOUT_CONFIG.hubRadius * LAYOUT_CONFIG.outerRadiusMult;
        n.x = Math.cos(avgAngle) * outerRadius;
        n.y = Math.sin(avgAngle) * outerRadius;
      } else {
        // Orphaned node, place randomly
        const angle = seededRandom() * 2 * Math.PI;
        const distance = LAYOUT_CONFIG.hubRadius * LAYOUT_CONFIG.outerRadiusMult;
        n.x = Math.cos(angle) * distance;
        n.y = Math.sin(angle) * distance;
      }
    }
  }

  function setData(graphData) {
    // Accept data from OntologyAdapter instead of loading from file
    return Promise.resolve(graphData);
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

    // Apply hub-spoke layout algorithm for deterministic positioning
    applyHubSpokeLayout();

    // Build cluster counts for legend
    const counts = {};
    for (const n of nodes) counts[n.cluster] = (counts[n.cluster] || 0) + 1;

    // Populate legend
    const legend = document.getElementById('legend');
    Object.keys(CLUSTER_COLORS).forEach(c => {
      if (!counts[c]) return;
      const row = document.createElement('div');
      row.className = 'legend-row';
      row.dataset.cluster = c;
      const dotFill = c === 'Core' ? CLUSTER_COLORS[c] : hexToSoftFill(CLUSTER_COLORS[c]);
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

  function initSim() {
    // Initial pass: collision resolution only — preserves the deterministic layout
    // while gently resolving any node-node overlaps. Auto-stops and pins nodes.
    simulation = d3.forceSimulation(nodes)
      .force('collide', d3.forceCollide()
        .radius(d => radiusFor(d) + 6)
        .strength(0.9)
        .iterations(4)
      )
      .alpha(0.4)
      .alphaDecay(0.05)
      .on('tick', draw)
      .on('end', () => {
        for (const n of nodes) { n.fx = n.x; n.fy = n.y; }
        fitToView();
        draw();
        setPhysics(true);
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

    // selected edge label (if any)
    if (selectedEdge) drawEdgeLabel(selectedEdge);
    else if (hoverEdge) drawEdgeLabel(hoverEdge);

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

    // Arrow head
    const arrSize = isHighlight ? 7 : 5.5;
    const angle = Math.atan2(dy, dx);
    ctx.fillStyle = ctx.strokeStyle;
    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - arrSize * Math.cos(angle - Math.PI / 7),
               y2 - arrSize * Math.sin(angle - Math.PI / 7));
    ctx.lineTo(x2 - arrSize * Math.cos(angle + Math.PI / 7),
               y2 - arrSize * Math.sin(angle + Math.PI / 7));
    ctx.closePath();
    ctx.fill();

    ctx.restore();
  }

  function drawNode(n, isDim) {
    const r = radiusFor(n);
    const isSel = n === selectedNode;
    const isHov = n === hoverNode;
    const color = colorFor(n.cluster);

    ctx.save();

    if (isDim) {
      ctx.globalAlpha = 0.2;
    }

    // Outer selection ring
    if (isSel) {
      ctx.strokeStyle = '#B31B1B';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(n.x, n.y, r + 6, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Fill
    if (n.cluster === 'Core' || isSel) {
      ctx.fillStyle = color;
    } else {
      // paper-tinted fill
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
    ctx.font = `${isSel ? 600 : 500} ${isSel ? 18 : 16}px "Inter Tight", system-ui, sans-serif`;
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

    ctx.fillStyle = isSel || isHov ? '#121417' : '#2A2D33';
    ctx.fillText(label, n.x, ly);
    ctx.restore();
  }

  function drawEdgeLabel(l) {
    if (l.source === l.target) return;
    const mx = (l.source.x + l.target.x) / 2;
    const my = (l.source.y + l.target.y) / 2;

    ctx.save();
    ctx.font = `italic 500 13px "Instrument Serif", "Fraunces", Georgia, serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const metrics = ctx.measureText(l.label);
    const padX = 8, padY = 4;
    const w = metrics.width + padX * 2;
    const h = 18 + padY;

    ctx.fillStyle = 'rgba(251, 250, 246, 0.95)';
    ctx.strokeStyle = 'rgba(179,27,27,0.4)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.rect(mx - w/2, my - h/2, w, h);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#B31B1B';
    ctx.fillText(l.label, mx, my + 1);
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
      if (physicsOn && !moved) {
        dragNode.fx = null; dragNode.fy = null;
      }
      // If physics off, leave pinned. If moved and physics on, leave pinned (user pinned it).
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

  function setPhysics(on) {
    physicsOn = on;
    if (on) {
      // Full spring physics: unpin nodes, add link + charge + centering forces
      for (const n of nodes) { n.fx = null; n.fy = null; }
      simulation
        .force('link', d3.forceLink(links)
          .id(d => d.id)
          .distance(l => LAYOUT_CONFIG.linkDistance + radiusFor(l.source) + radiusFor(l.target))
          .strength(0.4)
        )
        .force('charge', d3.forceManyBody()
          .strength(d => LAYOUT_CONFIG.chargeStrength - radiusFor(d) * 10)
          .distanceMax(700)
        )
        .force('center', d3.forceCenter(0, 0).strength(0.06))
        .on('tick', draw)
        .on('end', null)
        .alpha(0.4).alphaDecay(0.01).restart();
    } else {
      // Pin all nodes at current positions; remove spring forces; keep collision
      for (const n of nodes) { n.fx = n.x; n.fy = n.y; }
      simulation
        .force('link', null)
        .force('charge', null)
        .force('center', null)
        .alphaTarget(0).alpha(0).stop();
      simulation.on('end', () => {
        for (const n of nodes) { n.fx = n.x; n.fy = n.y; }
      });
    }
  }

  function init() {
    canvas = document.getElementById('graph');

    // Set up event listeners once
    canvas.addEventListener('mousemove', onMouseMove);
    canvas.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mouseup', onMouseUp);
    canvas.addEventListener('wheel', onWheel, { passive: false });
    window.addEventListener('resize', resize);

    document.getElementById('zoom-in').onclick = () => zoomAt(W/2, H/2, 1.25);
    document.getElementById('zoom-out').onclick = () => zoomAt(W/2, H/2, 1/1.25);
    document.getElementById('zoom-reset').onclick = resetZoom;

    const toggle = document.getElementById('toggle-physics');
    toggle.addEventListener('click', () => {
      const on = !toggle.classList.contains('on');
      toggle.classList.toggle('on', on);
      toggle.setAttribute('aria-checked', on ? 'true' : 'false');
      setPhysics(on);
    });
  }

  function load(graphData) {
    window.ONTOLOGY = graphData;
    if (simulation) simulation.stop();
    transform = { x: 0, y: 0, k: 1 };
    physicsOn = false;
    const toggle = document.getElementById('toggle-physics');
    if (toggle) { toggle.classList.add('on'); toggle.setAttribute('aria-checked', 'true'); }
    setup(graphData);
    resize();
    fitToView();
    initSim();
    draw();
    window.Inspector && window.Inspector.showEmpty();
  }

  // Expose crossing counter for validation
  function countCrossings() {
    const hub = nodes.find(n => n.id === 'Solution');
    if (!hub) return 0;

    const spokes = new Set();
    for (const l of links) {
      if (l.source === hub && l.target !== hub) spokes.add(l.target);
      if (l.target === hub && l.source !== hub) spokes.add(l.source);
    }

    const secondaryEdges = [];
    const spokeIds = new Set(Array.from(spokes).map(n => n.id));
    for (const l of links) {
      if (l.source !== hub && l.target !== hub &&
          spokeIds.has(l.source.id) && spokeIds.has(l.target.id)) {
        secondaryEdges.push(l);
      }
    }

    const angles = new Map();
    for (const n of spokes) {
      const angle = Math.atan2(n.y - hub.y, n.x - hub.x);
      angles.set(n.id, angle);
    }

    return countAllCrossings(Array.from(spokes), secondaryEdges, hub, angles);
  }

  window.Graph = {
    init, load, focusNode, selectNode, selectEdge, deselect,
    getNodeById: id => nodeById[id],
    getNodes: () => nodes,
    getLinks: () => links,
    getLinksForNode: id => linksByNode[id] || [],
    getClusterColor: colorFor,
    layoutConfig: LAYOUT_CONFIG, // Expose for tuning
    countCrossings, // Expose for validation
  };
})();
