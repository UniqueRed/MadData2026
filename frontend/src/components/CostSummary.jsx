export default function CostSummary({ graph, comparisonGraph }) {
  if (!graph) return null;

  const savings =
    comparisonGraph && comparisonGraph.total_5yr_oop
      ? comparisonGraph.total_5yr_oop - graph.total_5yr_oop
      : null;

  return (
    <div className="cost-summary">
      <h3>5-Year Cost Projection</h3>
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
