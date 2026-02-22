import { useMemo } from "react";

/**
 * Compute the cumulative pathway cost from root to a selected node.
 * Walks backwards through edges to find all ancestor nodes, then sums
 * their costs over the 5-year horizon (actual cost, not probability-weighted).
 */
function computePathwayCost(graph, selectedNodeId, timeHorizon = 5) {
  if (!graph || !selectedNodeId) return null;

  // Build lookup maps
  const nodeMap = {};
  for (const n of graph.nodes) {
    nodeMap[n.id] = n;
  }

  // Build reverse edge map: target → set of sources
  const parentOf = {};
  for (const e of graph.edges) {
    if (!parentOf[e.target]) parentOf[e.target] = [];
    parentOf[e.target].push(e.source);
  }

  // Walk backwards from selected node to collect all ancestors in the path
  const pathNodeIds = new Set();
  const queue = [selectedNodeId];
  while (queue.length > 0) {
    const id = queue.pop();
    if (pathNodeIds.has(id)) continue;
    pathNodeIds.add(id);
    for (const parentId of parentOf[id] || []) {
      queue.push(parentId);
    }
  }

  // Sum costs for all nodes in the path (unweighted — "if this happens" cost)
  let totalCost = 0;
  let totalOop = 0;
  for (const id of pathNodeIds) {
    const node = nodeMap[id];
    if (!node) continue;
    const yearsActive = Math.max(1, timeHorizon - node.year + 1);
    totalCost += node.annual_cost * yearsActive;
    totalOop += node.oop_estimate * yearsActive;
  }

  return { totalCost, totalOop, nodeCount: pathNodeIds.size };
}

export default function CostSummary({ graph, comparisonGraph, selectedNode }) {
  if (!graph) return null;

  const pathwayCost = useMemo(
    () => computePathwayCost(graph, selectedNode?.id),
    [graph, selectedNode]
  );

  const savings =
    comparisonGraph && comparisonGraph.total_5yr_oop
      ? comparisonGraph.total_5yr_oop - graph.total_5yr_oop
      : null;

  // When a node is selected, show the pathway cost to that node
  if (selectedNode && pathwayCost && selectedNode.nodeType !== "root") {
    return (
      <div className="cost-summary">
        <div className="section-header">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="1" x2="12" y2="23" />
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
          </svg>
          <span>Pathway Cost</span>
        </div>
        <div className="cost-pathway-label">{selectedNode.label}</div>
        <div className="cost-row">
          <span>Total if this occurs</span>
          <span className="cost-value">${Math.round(pathwayCost.totalCost).toLocaleString()}</span>
        </div>
        <div className="cost-row">
          <span>Out-of-Pocket</span>
          <span className="cost-value oop">${Math.round(pathwayCost.totalOop).toLocaleString()}</span>
        </div>
        {selectedNode.probability != null && selectedNode.probability < 1 && (
          <div className="cost-row">
            <span>Associated Risk Probability</span>
            <span className="cost-value">{(selectedNode.probability * 100).toFixed(1)}%</span>
          </div>
        )}
        {/* <div className="cost-row cost-row-muted">
          <span>Full 5-Year Projection</span>
          <span className="cost-value">${Math.round(graph.total_5yr_oop).toLocaleString()}</span>
        </div> */}
      </div>
    );
  }

  // Default: show full 5-year projection
  return (
    <div className="cost-summary">
      <div className="section-header">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="12" y1="1" x2="12" y2="23" />
          <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
        </svg>
        <span>5-Year Cost Projection</span>
      </div>
      <div className="cost-row">
        <span>Total Expected Cost</span>
        <span className="cost-value">${Math.round(graph.total_5yr_cost).toLocaleString()}</span>
      </div>
      <div className="cost-row">
        <span>Out-of-Pocket</span>
        <span className="cost-value oop">${Math.round(graph.total_5yr_oop).toLocaleString()}</span>
      </div>
      {savings !== null && savings > 0 && (
        <div className="cost-row savings">
          <span>Estimated Savings</span>
          <span className="cost-value">${Math.round(savings).toLocaleString()}</span>
        </div>
      )}
    </div>
  );
}
