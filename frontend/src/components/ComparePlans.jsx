import { useState, useEffect } from "react";
import { getStates, searchPlans, compareMarketplacePlans } from "../services/api";

const METAL_LEVELS = ["All", "Bronze", "Silver", "Gold", "Platinum", "Catastrophic"];

function getConditionBreakdown(graph) {
  if (!graph?.nodes) return [];
  return graph.nodes
    .filter((n) => n.node_type === "current")
    .map((n) => ({
      label: n.label,
      annual_oop: n.oop_estimate || 0,
      five_yr_oop: (n.oop_estimate || 0) * 5,
    }))
    .sort((a, b) => b.five_yr_oop - a.five_yr_oop);
}

function computeBestValueReason(results, cheapestIdx) {
  if (!results || results.length < 2) return null;
  const cheapest = results[cheapestIdx];
  const others = results.filter((_, i) => i !== cheapestIdx);
  const minOtherTotal = Math.min(...others.map((r) => r.total_with_premium));
  const savings = Math.round(minOtherTotal - cheapest.total_with_premium);

  // Find the condition where this plan saves the most vs next best
  const cheapestNodes = getConditionBreakdown(cheapest.graph);
  let bestCondition = null;
  let bestSaving = 0;
  for (const node of cheapestNodes) {
    for (const other of others) {
      const otherNode = getConditionBreakdown(other.graph).find((n) => n.label === node.label);
      if (otherNode) {
        const diff = Math.round(otherNode.five_yr_oop - node.five_yr_oop);
        if (diff > bestSaving) {
          bestSaving = diff;
          bestCondition = node.label;
        }
      }
    }
  }

  const parts = [];
  if (savings > 0) parts.push(`Saves $${savings.toLocaleString()} overall`);
  if (bestCondition && bestSaving > 100)
    parts.push(`$${bestSaving.toLocaleString()} cheaper for ${bestCondition}`);
  return parts.length ? parts.join(" · ") : "Lowest total cost";
}

function getConditionBestPlan(results, conditionLabel) {
  let bestIdx = 0;
  let bestOop = Infinity;
  results.forEach((r, i) => {
    const node = getConditionBreakdown(r.graph).find((n) => n.label === conditionLabel);
    if (node && node.five_yr_oop < bestOop) {
      bestOop = node.five_yr_oop;
      bestIdx = i;
    }
  });
  return bestIdx;
}

export default function ComparePlans({ profile, onSelectPlan }) {
  const [step, setStep] = useState(1);

  // Step 1: Search
  const [states, setStates] = useState([]);
  const [selectedState, setSelectedState] = useState("");
  const [metalFilter, setMetalFilter] = useState("All");
  const [searchAge, setSearchAge] = useState(profile?.age ?? 45);
  const [searchLoading, setSearchLoading] = useState(false);

  // Step 2: Select
  const [plans, setPlans] = useState([]);
  const [planCount, setPlanCount] = useState(0);
  const [selectedPlanIds, setSelectedPlanIds] = useState([]);

  // Step 3: Results
  const [results, setResults] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [expandedCard, setExpandedCard] = useState(null);

  const [error, setError] = useState(null);

  useEffect(() => {
    getStates()
      .then((s) => setStates(s))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (profile?.age) setSearchAge(profile.age);
  }, [profile?.age]);

  const handleSearch = async () => {
    if (!selectedState) return;
    setSearchLoading(true);
    setError(null);
    setResults(null);
    setSelectedPlanIds([]);
    try {
      const data = await searchPlans(selectedState, metalFilter, searchAge);
      setPlans(data.plans);
      setPlanCount(data.count);
      setStep(2);
    } catch (err) {
      setError(err.message);
    }
    setSearchLoading(false);
  };

  const togglePlan = (planId) => {
    setSelectedPlanIds((prev) => {
      if (prev.includes(planId)) return prev.filter((id) => id !== planId);
      if (prev.length >= 3) return prev;
      return [...prev, planId];
    });
  };

  const handleCompare = async () => {
    if (selectedPlanIds.length < 2) return;
    setCompareLoading(true);
    setError(null);
    try {
      const data = await compareMarketplacePlans({
        age: profile?.age ?? searchAge,
        sex: profile?.sex ?? "M",
        conditions: profile?.conditions ?? [],
        interventions: [],
        state: selectedState,
        plan_ids: selectedPlanIds,
        time_horizon_years: 5,
      });
      setResults(data.plan_comparisons);
      setStep(3);
    } catch (err) {
      setError(err.message);
    }
    setCompareLoading(false);
  };

  const cheapestIdx =
    results &&
    results.reduce(
      (best, r, i) => (r.total_with_premium < results[best].total_with_premium ? i : best),
      0
    );

  const bestValueReason = results ? computeBestValueReason(results, cheapestIdx) : null;

  return (
    <div className="compare-layout">
      {/* Main area — fills screen */}
      <div className="compare-main">
        <div className="compare-main-inner">
          <h2 className="compare-title">Marketplace Plan Comparison</h2>
          <p className="compare-subtitle">
            {profile
              ? `Comparing for your profile: ${profile.age}yo, ${profile.conditions?.join(", ") || "no conditions"}`
              : "Using defaults (age 45). Run a simulation first for personalized results."}
          </p>
          {!profile && (
            <p className="no-profile-note">
              No patient profile loaded — results will use default demographics.
            </p>
          )}

          {/* Step Indicator */}
          <div className="compare-steps">
            <div className={`compare-step${step >= 1 ? " active" : ""}`}>
              <span className="compare-step-num">1</span>
              <span className="compare-step-label">Search</span>
            </div>
            <div className="compare-step-line" />
            <div className={`compare-step${step >= 2 ? " active" : ""}`}>
              <span className="compare-step-num">2</span>
              <span className="compare-step-label">Select Plans</span>
            </div>
            <div className="compare-step-line" />
            <div className={`compare-step${step >= 3 ? " active" : ""}`}>
              <span className="compare-step-num">3</span>
              <span className="compare-step-label">Results</span>
            </div>
          </div>

          {/* Step 1: Search */}
          <div className="plan-search-section">
            <div className="plan-search-field">
              <label className="plan-search-label">State</label>
              <select
                value={selectedState}
                onChange={(e) => setSelectedState(e.target.value)}
              >
                <option value="">Select state...</option>
                {states.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div className="plan-search-field">
              <label className="plan-search-label">Coverage Level</label>
              <div className="metal-filters">
                {METAL_LEVELS.map((ml) => (
                  <button
                    key={ml}
                    className={`metal-filter-btn${metalFilter === ml ? " active" : ""}`}
                    onClick={() => setMetalFilter(ml)}
                  >
                    {ml}
                  </button>
                ))}
              </div>
            </div>

            <button
              className="compare-btn"
              onClick={handleSearch}
              disabled={!selectedState || searchLoading}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              {searchLoading ? "Searching..." : "Search Plans"}
            </button>
          </div>

          {error && <p className="compare-error">Error: {error}</p>}

          {step >= 2 && plans.length === 0 && !searchLoading && (
            <p className="plan-count">No plans found for this state and filter.</p>
          )}

          {/* Step 2: Plan cards */}
          {step >= 2 && plans.length > 0 && (
            <>
              <div className="compare-split-header">
                <p className="plan-count">
                  <strong>{planCount}</strong> plans found — select up to 3 to compare
                </p>
                <div className="compare-split-header-actions">
                  <button
                    className="compare-btn compare-btn-secondary compare-btn-sm"
                    onClick={() => { setStep(1); setPlans([]); setSelectedPlanIds([]); setResults(null); }}
                  >
                    New Search
                  </button>
                  <button
                    className="compare-btn compare-btn-sm"
                    onClick={handleCompare}
                    disabled={selectedPlanIds.length < 2 || compareLoading}
                  >
                    {compareLoading
                      ? "Comparing..."
                      : `Compare ${selectedPlanIds.length} Plan${selectedPlanIds.length !== 1 ? "s" : ""}`}
                  </button>
                </div>
              </div>
              <div className="plan-list">
                {plans.map((p) => (
                  <div
                    key={p.plan_id}
                    className={`plan-list-card${selectedPlanIds.includes(p.plan_id) ? " selected" : ""}`}
                    onClick={() => togglePlan(p.plan_id)}
                  >
                    {selectedPlanIds.includes(p.plan_id) && (
                      <div className="plan-list-check">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      </div>
                    )}
                    <div className="plan-list-card-header">
                      <span className={`metal-badge ${p.metal_level.toLowerCase()}`}>
                        {p.metal_level}
                      </span>
                      <span className="plan-list-type">{p.plan_type}</span>
                      {p.is_hsa_eligible && <span className="plan-list-hsa">HSA</span>}
                    </div>
                    <h4 className="plan-list-name">{p.plan_name}</h4>
                    <p className="plan-list-issuer">{p.issuer}</p>
                    <div className="plan-list-stats">
                      <span>Ded: ${Math.round(p.deductible).toLocaleString()}</span>
                      <span>OOP: ${Math.round(p.oop_max).toLocaleString()}</span>
                      <span className="plan-list-premium">
                        ${Math.round(p.monthly_premium)}/mo
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Right sidebar — same width as chatbot panel */}
      {results && (
        <div className="compare-sidebar">
          <div className="compare-sidebar-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />
            </svg>
            <span>5-Year Cost Breakdown</span>
          </div>
          <div className="compare-sidebar-content">
            {results.map((r, i) => {
              const conditions = getConditionBreakdown(r.graph);
              const isExpanded = expandedCard === i;
              const drugOop = r.graph.total_5yr_drug_oop || 0;
              const medicalOop = r.graph.total_5yr_oop - drugOop;

              return (
                <div
                  key={i}
                  className={`result-card ${i === cheapestIdx ? "cheapest" : ""}`}
                >
                  {i === cheapestIdx && (
                    <div className="cheapest-badge-wrap">
                      <span className="cheapest-badge">Best Value</span>
                      {bestValueReason && (
                        <span className="cheapest-reason">{bestValueReason}</span>
                      )}
                    </div>
                  )}
                  <h4>{r.plan.plan_name}</h4>
                  <p className="result-issuer">{r.plan.issuer}</p>

                  <div className="result-row">
                    <span>Medical OOP</span>
                    <span className="result-value">
                      ${Math.round(medicalOop).toLocaleString()}
                    </span>
                  </div>
                  {drugOop > 0 && (
                    <div className="result-row">
                      <span>Drug OOP</span>
                      <span className="result-value drug">
                        ${Math.round(drugOop).toLocaleString()}
                      </span>
                    </div>
                  )}
                  <div className="result-row">
                    <span>Premiums (5yr)</span>
                    <span className="result-value">
                      ${Math.round(r.plan.monthly_premium * 60).toLocaleString()}
                    </span>
                  </div>
                  <div className="result-row total">
                    <span>Total Cost</span>
                    <span className="result-value">
                      ${Math.round(r.total_with_premium).toLocaleString()}
                    </span>
                  </div>

                  {/* Condition breakdown toggle */}
                  {conditions.length > 0 && (
                    <>
                      <button
                        className="condition-toggle"
                        onClick={() => setExpandedCard(isExpanded ? null : i)}
                      >
                        <span>Condition breakdown</span>
                        <svg
                          width="12" height="12" viewBox="0 0 24 24" fill="none"
                          stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                          className={isExpanded ? "chevron-open" : ""}
                        >
                          <polyline points="6 9 12 15 18 9" />
                        </svg>
                      </button>
                      {isExpanded && (
                        <div className="condition-breakdown">
                          {conditions.map((c) => {
                            const isBestForThis = getConditionBestPlan(results, c.label) === i;
                            return (
                              <div key={c.label} className="condition-row">
                                <span className="condition-name">
                                  {c.label}
                                  {isBestForThis && results.length > 1 && (
                                    <span className="condition-best-tag">Best</span>
                                  )}
                                </span>
                                <span className="condition-cost">
                                  ${Math.round(c.five_yr_oop).toLocaleString()}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </>
                  )}

                  {/* Use This Plan button */}
                  {onSelectPlan && (
                    <button
                      className="compare-btn compare-btn-sm use-plan-btn"
                      onClick={() => onSelectPlan(r)}
                    >
                      Use This Plan
                    </button>
                  )}
                </div>
              );
            })}
          </div>
          <div className="compare-sidebar-footer">
            <button
              className="compare-btn compare-btn-secondary"
              onClick={() => { setStep(2); setResults(null); setExpandedCard(null); }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
              </svg>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
