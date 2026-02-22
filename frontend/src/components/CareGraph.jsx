import { useMemo, useRef, useCallback } from "react";
import CytoscapeComponent from "react-cytoscapejs";

const NODE_COLORS = {
  root: "#111827",
  current: "#dc2626",
  future: "#f59e0b",
  high_cost: "#7f1d1d",
  intervention: "#16a34a",
};

const EDGE_COLORS = {
  root: "#b0b8c4",
  progression: "#cbd5e1",
  comorbidity: "#fca5a5",
  intervention: "#86efac",
  llm_progression: "#c4b5fd",
  cost: "#cbd5e1",
};

function toElements(graph) {
  if (!graph) return [];

  const nodes = [];
  const edges = [];

  const currentIds = [];
  const nodeMap = {};
  for (const n of graph.nodes) {
    nodeMap[n.id] = n;
    // Treat both confirmed ("current_") and suspected ("suspected_") as branch roots
    if (n.node_type === "current" || n.id.startsWith("suspected_")) currentIds.push(n.id);
  }

  // Build parent → children adjacency
  const childrenOf = {};
  for (const e of graph.edges) {
    if (!childrenOf[e.source]) childrenOf[e.source] = [];
    childrenOf[e.source].push(e.target);
  }

  // Walk the tree: assign every node to a branch (current condition)
  const branchOf = {};
  const branchChildren = {};
  for (const cid of currentIds) {
    branchChildren[cid] = { depth1: [], depth2: [] };
    for (const childId of childrenOf[cid] || []) {
      if (!branchOf[childId]) {
        branchOf[childId] = cid;
        branchChildren[cid].depth1.push(childId);
      }
      for (const gcId of childrenOf[childId] || []) {
        if (!branchOf[gcId] && gcId !== cid) {
          branchOf[gcId] = cid;
          branchChildren[cid].depth2.push(gcId);
        }
      }
    }
  }

  // --- Compute dynamic radii based on how many nodes we have ---
  const totalNodes = graph.nodes.length;
  const numBranches = currentIds.length || 1;
  // Scale up when there are many branches / children so nothing overlaps
  const scale = Math.max(1, Math.sqrt(totalNodes / 6));
  const R1 = 250 * scale;
  const R2 = 420 * scale;
  const R3 = 560 * scale;

  // --- Position every node ---
  const positions = {};
  positions["root"] = { x: 0, y: 0 };

  const sliceAngle = (2 * Math.PI) / numBranches;

  currentIds.forEach((cid, i) => {
    const angle = sliceAngle * i - Math.PI / 2;
    positions[cid] = {
      x: Math.cos(angle) * R1,
      y: Math.sin(angle) * R1,
    };

    const { depth1, depth2 } = branchChildren[cid];

    // Depth-1: fan children within their slice, with min angular gap
    const minGap1 = 0.18; // ~10 degrees minimum between siblings
    const need1 = Math.max((depth1.length - 1) * minGap1, 0);
    const fan1 = Math.min(Math.max(need1, sliceAngle * 0.4), sliceAngle * 0.85);
    depth1.forEach((childId, j) => {
      const n = depth1.length;
      const off = n === 1 ? 0 : (j / (n - 1) - 0.5) * fan1;
      const a = angle + off;
      positions[childId] = { x: Math.cos(a) * R2, y: Math.sin(a) * R2 };
    });

    // Depth-2: wider fan in outer ring
    const minGap2 = 0.15;
    const need2 = Math.max((depth2.length - 1) * minGap2, 0);
    const fan2 = Math.min(Math.max(need2, sliceAngle * 0.5), sliceAngle * 0.9);
    depth2.forEach((childId, j) => {
      const n = depth2.length;
      const off = n === 1 ? 0 : (j / (n - 1) - 0.5) * fan2;
      const a = angle + off;
      positions[childId] = { x: Math.cos(a) * R3, y: Math.sin(a) * R3 };
    });
  });

  // --- Build Cytoscape elements ---
  nodes.push({
    data: {
      id: "root", label: "Your Health", nodeType: "root",
      probability: 1, annualCost: 0, oopEstimate: 0, year: 0,
    },
    position: positions["root"],
  });

  for (const n of graph.nodes) {
    const depth = branchOf[n.id]
      ? (branchChildren[branchOf[n.id]].depth2.includes(n.id) ? 2 : 1)
      : 0;
    nodes.push({
      data: {
        id: n.id, label: n.is_llm_generated ? `${n.label}\n(AI estimate)` : n.label,
        nodeType: n.node_type,
        probability: n.probability, annualCost: n.annual_cost,
        oopEstimate: n.oop_estimate, year: n.year, depth,
        isLlmGenerated: n.is_llm_generated || false,
      },
      position: positions[n.id] || { x: 0, y: 0 },
    });

    if (n.node_type === "current" || n.id.startsWith("suspected_")) {
      edges.push({
        data: {
          id: `root-to-${n.id}`, source: "root", target: n.id,
          label: "", edgeType: "root", probability: n.probability,
        },
      });
    }
  }

  for (let i = 0; i < graph.edges.length; i++) {
    const e = graph.edges[i];
    edges.push({
      data: {
        id: `edge-${i}`, source: e.source, target: e.target,
        label: e.label, edgeType: e.edge_type, probability: e.probability,
      },
    });
  }

  return [...nodes, ...edges];
}

const stylesheet = [
  // --- Nodes ---
  {
    selector: "node",
    style: {
      shape: "ellipse",
      label: "data(label)",
      "text-wrap": "wrap",
      "text-valign": "center",
      "text-halign": "center",
      "font-size": "12px",
      "font-weight": "600",
      "font-family": "Inter, system-ui, sans-serif",
      color: "#ffffff",
      "text-max-width": "90px",
      "background-color": (ele) => NODE_COLORS[ele.data("nodeType")] || "#94a3b8",
      width: 140,
      height: 140,
      "border-width": 2,
      "border-color": "#ffffff",
      "border-opacity": 0.25,
      "background-opacity": 0.9,
      "text-outline-color": (ele) => NODE_COLORS[ele.data("nodeType")] || "#94a3b8",
      "text-outline-width": 1.5,
      "text-outline-opacity": 0.5,
      "overlay-padding": "8px",
      "shadow-blur": "12",
      "shadow-color": "#000000",
      "shadow-offset-x": "0",
      "shadow-offset-y": "2",
      "shadow-opacity": "0.08",
    },
  },
  {
    selector: "node[nodeType='root']",
    style: {
      width: 180,
      height: 180,
      "font-size": "15px",
      "font-weight": "700",
      "text-max-width": "110px",
      "background-opacity": 1,
      "border-width": 3,
      "border-color": "#374151",
      "border-opacity": 0.5,
      "shadow-blur": "20",
      "shadow-opacity": "0.12",
    },
  },
  {
    selector: "node[nodeType='current']",
    style: {
      width: 155,
      height: 155,
      "font-size": "13px",
      "font-weight": "700",
      "background-opacity": 0.95,
      "border-color": "#fca5a5",
      "border-opacity": 0.35,
    },
  },
  {
    selector: "node[nodeType='high_cost']",
    style: {
      width: 150,
      height: 150,
      "font-size": "13px",
      "border-color": "#f87171",
      "border-opacity": 0.35,
    },
  },
  {
    selector: "node[nodeType='intervention']",
    style: {
      width: 130,
      height: 130,
      "font-size": "11px",
      "border-color": "#86efac",
      "border-opacity": 0.35,
    },
  },
  // Depth-2 nodes are smaller and softer
  {
    selector: "node[depth = 2]",
    style: {
      width: 115,
      height: 115,
      "font-size": "10px",
      "background-opacity": 0.75,
      "border-opacity": 0.15,
      "shadow-opacity": "0.04",
    },
  },
  // --- Edges ---
  {
    selector: "edge",
    style: {
      "line-color": (ele) => EDGE_COLORS[ele.data("edgeType")] || "#cbd5e1",
      "target-arrow-color": (ele) => EDGE_COLORS[ele.data("edgeType")] || "#cbd5e1",
      "target-arrow-shape": "triangle",
      "target-arrow-fill": "filled",
      "arrow-scale": 5,
      "curve-style": "unbundled-bezier",
      "control-point-distances": "40",
      "control-point-weights": "0.5",
      width: 1.5,
      "line-opacity": 0.35,
      label: "data(label)",
      "font-size": "9px",
      "font-weight": "500",
      color: "#94a3b8",
      "text-rotation": "autorotate",
      "text-background-color": "#f9fafb",
      "text-background-opacity": 0.9,
      "text-background-padding": "4px",
      "text-background-shape": "roundrectangle",
    },
  },
  {
    selector: "edge[edgeType='root']",
    style: {
      width: 2,
      "line-opacity": 0.25,
      "line-color": "#9ca3af",
      "target-arrow-color": "#9ca3af",
      "line-style": "solid",
      "curve-style": "straight",
    },
  },
  {
    selector: "edge[edgeType='comorbidity']",
    style: {
      width: 1.5,
      "line-opacity": 0.4,
    },
  },
  {
    selector: "edge[edgeType='intervention']",
    style: {
      width: 1.5,
      "line-opacity": 0.45,
      "line-style": "dashed",
    },
  },
  {
    selector: "edge[edgeType='llm_progression']",
    style: {
      width: 1.5,
      "line-opacity": 0.4,
      "line-style": "dashed",
      "line-dash-pattern": [6, 4],
    },
  },
  {
    selector: "node[?isLlmGenerated]",
    style: {
      "border-style": "dashed",
      "border-width": 2.5,
      "border-color": "#a78bfa",
      "border-opacity": 0.6,
    },
  },
  // --- Selection ---
  {
    selector: "node:selected",
    style: {
      "border-width": 3,
      "border-color": "#111827",
      "border-opacity": 1,
      "background-opacity": 1,
      "shadow-blur": "24",
      "shadow-opacity": "0.18",
    },
  },
  // --- Focus mode: dimmed (everything not connected) ---
  {
    selector: "node.dimmed",
    style: {
      "background-opacity": 0.12,
      "border-opacity": 0.05,
      "text-opacity": 0.15,
      "shadow-opacity": "0",
    },
  },
  {
    selector: "edge.dimmed",
    style: {
      "line-opacity": 0.04,
      "text-opacity": 0,
    },
  },
  // --- Focus mode: highlighted (connected nodes + edges) ---
  {
    selector: "node.highlighted",
    style: {
      "background-opacity": 1,
      "border-opacity": 0.8,
      "border-width": 3,
      "shadow-blur": "20",
      "shadow-opacity": "0.15",
    },
  },
  {
    selector: "edge.highlighted",
    style: {
      width: 3,
      "line-opacity": 0.85,
      "text-opacity": 1,
    },
  },
  // --- The tapped node itself ---
  {
    selector: "node.focus-source",
    style: {
      "background-opacity": 1,
      "border-width": 4,
      "border-color": "#111827",
      "border-opacity": 1,
      "shadow-blur": "28",
      "shadow-opacity": "0.22",
    },
  },
];

const LEGEND = [
  { color: "#111827", label: "Your Profile" },
  { color: "#dc2626", label: "Current Condition" },
  { color: "#f59e0b", label: "Possible Future" },
  { color: "#7f1d1d", label: "High Cost Risk" },
  { color: "#16a34a", label: "Intervention" },
  { color: "#a78bfa", label: "AI Estimate", dashed: true },
];

export default function CareGraph({ graph, onNodeSelect }) {
  const cyRef = useRef(null);
  const onNodeSelectRef = useRef(onNodeSelect);
  onNodeSelectRef.current = onNodeSelect;

  const focusedRef = useRef(null);

  const clearFocus = useCallback((cy) => {
    cy.elements().removeClass("dimmed highlighted focus-source");
    focusedRef.current = null;
  }, []);

  const applyFocus = useCallback((cy, tapped) => {
    clearFocus(cy);
    focusedRef.current = tapped.id();

    // Collect tapped node + only its outgoing edges and child nodes
    const outgoing = tapped.outgoers();
    const childEdges = outgoing.edges();
    const childNodes = outgoing.nodes();
    const chain = cy.collection().union(tapped).union(childEdges).union(childNodes);

    // Dim everything, then highlight the chain
    cy.elements().addClass("dimmed");
    chain.removeClass("dimmed").addClass("highlighted");
    tapped.addClass("focus-source");
  }, [clearFocus]);

  const handleCy = useCallback((cy) => {
    cyRef.current = cy;
    cy.minZoom(0.15);
    cy.maxZoom(3);

    // Background tap → clear focus
    cy.on("tap", (e) => {
      if (e.target === cy) clearFocus(cy);
    });

    // Node tap → toggle focus + fire detail panel
    cy.on("tap", "node", (e) => {
      const tapped = e.target;
      if (onNodeSelectRef.current) onNodeSelectRef.current(tapped.data());

      if (focusedRef.current === tapped.id()) {
        clearFocus(cy);
      } else {
        applyFocus(cy, tapped);
      }
    });
  }, [clearFocus, applyFocus]);

  const elements = useMemo(() => toElements(graph), [graph]);

  const hasLlmNodes = useMemo(
    () => graph?.nodes?.some((n) => n.is_llm_generated) || false,
    [graph]
  );

  const layout = useMemo(
    () => ({ name: "preset", fit: true, padding: 60, animate: false }),
    []
  );

  const handleRecenter = useCallback(() => {
    if (cyRef.current) cyRef.current.fit(undefined, 60);
  }, []);

  const handleZoomIn = useCallback(() => {
    if (cyRef.current) {
      const cy = cyRef.current;
      cy.zoom({ level: cy.zoom() * 1.3, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
    }
  }, []);

  const handleZoomOut = useCallback(() => {
    if (cyRef.current) {
      const cy = cyRef.current;
      cy.zoom({ level: cy.zoom() / 1.3, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
    }
  }, []);

  if (elements.length === 0) {
    return (
      <div className="graph-placeholder">
        <p>Speak or type your health profile to generate your care pathway.</p>
      </div>
    );
  }

  return (
    <>
      {hasLlmNodes && (
        <div className="llm-fallback-note">
          Dashed nodes use a fallback algorithm (AI estimate) — not from the clinical dataset.
        </div>
      )}
      <div className="graph-controls">
        <button className="graph-ctrl-btn" onClick={handleZoomIn} title="Zoom in">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /><line x1="11" y1="8" x2="11" y2="14" /><line x1="8" y1="11" x2="14" y2="11" />
          </svg>
        </button>
        <button className="graph-ctrl-btn" onClick={handleZoomOut} title="Zoom out">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /><line x1="8" y1="11" x2="14" y2="11" />
          </svg>
        </button>
        <button className="graph-ctrl-btn" onClick={handleRecenter} title="Recenter">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="5 9 2 12 5 15" /><polyline points="9 5 12 2 15 5" /><polyline points="15 19 12 22 9 19" /><polyline points="19 9 22 12 19 15" /><line x1="2" y1="12" x2="22" y2="12" /><line x1="12" y1="2" x2="12" y2="22" />
          </svg>
        </button>
      </div>

      <div className="graph-legend">
        {LEGEND.map((item) => (
          <div key={item.label} className="legend-item">
            <span
              className="legend-dot"
              style={{
                background: item.dashed ? "transparent" : item.color,
                border: item.dashed ? `2px dashed ${item.color}` : "none",
              }}
            />
            <span className="legend-label">{item.label}</span>
          </div>
        ))}
      </div>

      <CytoscapeComponent
        key={graph ? graph.total_5yr_cost : "empty"}
        elements={elements}
        stylesheet={stylesheet}
        layout={layout}
        cy={handleCy}
        style={{ width: "100%", height: "100%", background: "#f9fafb" }}
      />
    </>
  );
}
