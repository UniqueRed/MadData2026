export default function NodeDetail({ node }) {
  if (!node) return null;

  return (
    <div className="node-detail">
      <h3>{node.label?.split("\n")[0]}</h3>
      <div className="detail-grid">
        <div className="detail-item">
          <span className="detail-label">Annual Cost</span>
          <span className="detail-value">${Math.round(node.annualCost).toLocaleString()}</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Out-of-Pocket</span>
          <span className="detail-value">${Math.round(node.oopEstimate).toLocaleString()}</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Probability</span>
          <span className="detail-value">{(node.probability * 100).toFixed(1)}%</span>
        </div>
        {node.year > 0 && (
          <div className="detail-item">
            <span className="detail-label">Year</span>
            <span className="detail-value">Year {node.year}</span>
          </div>
        )}
      </div>
    </div>
  );
}
