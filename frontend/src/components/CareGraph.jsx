import { useEffect, useRef } from "react";
import CytoscapeComponent from "react-cytoscapejs";

const NODE_COLORS = {
  current: "#22c55e",
  future: "#eab308",
  high_cost: "#ef4444",
  intervention: "#8b5cf6",
};

const EDGE_COLORS = {
  progression: "#94a3b8",
  comorbidity: "#f97316",
  intervention: "#8b5cf6",
  cost: "#64748b",
};

function toElements(graph) {
  if (!graph) return [];

  const nodes = graph.nodes.map((n) => ({
    data: {
      id: n.id,
      label: `${n.label}\n$${Math.round(n.annual_cost).toLocaleString()}/yr`,
      nodeType: n.node_type,
      probability: n.probability,
      annualCost: n.annual_cost,
      oopEstimate: n.oop_estimate,
      year: n.year,
    },
  }));

  const edges = graph.edges.map((e, i) => ({
    data: {
      id: `edge-${i}`,
      source: e.source,
      target: e.target,
      label: e.label,
      edgeType: e.edge_type,
      probability: e.probability,
    },
  }));

  return [...nodes, ...edges];
}

const stylesheet = [
  {
    selector: "node",
    style: {
      label: "data(label)",
      "text-wrap": "wrap",
      "text-valign": "center",
      "text-halign": "center",
      "font-size": "11px",
      "font-family": "Inter, system-ui, sans-serif",
      color: "#fff",
      "background-color": (ele) => NODE_COLORS[ele.data("nodeType")] || "#64748b",
      width: (ele) => Math.max(60, Math.sqrt(ele.data("annualCost") || 100) * 3),
      height: (ele) => Math.max(60, Math.sqrt(ele.data("annualCost") || 100) * 3),
      "border-width": 2,
      "border-color": "#1e293b",
      padding: "12px",
    },
  },
  {
    selector: "edge",
    style: {
      "line-color": (ele) => EDGE_COLORS[ele.data("edgeType")] || "#94a3b8",
      "target-arrow-color": (ele) => EDGE_COLORS[ele.data("edgeType")] || "#94a3b8",
      "target-arrow-shape": "triangle",
      "curve-style": "bezier",
      width: (ele) => Math.max(1, (ele.data("probability") || 0.1) * 8),
      label: "data(label)",
      "font-size": "9px",
      color: "#94a3b8",
      "text-rotation": "autorotate",
    },
  },
  {
    selector: "node:selected",
    style: {
      "border-color": "#fff",
      "border-width": 4,
    },
  },
];

export default function CareGraph({ graph, onNodeSelect }) {
  const cyRef = useRef(null);

  useEffect(() => {
    if (cyRef.current) {
      const cy = cyRef.current;
      cy.layout({
        name: "breadthfirst",
        directed: true,
        spacingFactor: 1.5,
        animate: true,
        animationDuration: 600,
      }).run();

      cy.on("tap", "node", (e) => {
        const node = e.target.data();
        if (onNodeSelect) onNodeSelect(node);
      });
    }
  }, [graph, onNodeSelect]);

  const elements = toElements(graph);

  if (elements.length === 0) {
    return (
      <div className="graph-placeholder">
        <p>Speak or type your health profile to generate your care pathway.</p>
      </div>
    );
  }

  return (
    <CytoscapeComponent
      elements={elements}
      stylesheet={stylesheet}
      layout={{ name: "breadthfirst", directed: true, spacingFactor: 1.5 }}
      cy={(cy) => {
        cyRef.current = cy;
      }}
      style={{ width: "100%", height: "100%", background: "#0f172a" }}
    />
  );
}
