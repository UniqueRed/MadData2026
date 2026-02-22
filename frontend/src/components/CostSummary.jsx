export default function CostSummary({ graph, comparisonGraph }) {
  if (!graph) return null;

  const savings =
    comparisonGraph && comparisonGraph.total_5yr_oop
      ? comparisonGraph.total_5yr_oop - graph.total_5yr_oop
      : null;

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
