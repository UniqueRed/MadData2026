import { useState, useEffect } from "react";
import { getStates, searchPlans, compareMarketplacePlans } from "../services/api";

const METAL_LEVELS = ["All", "Bronze", "Silver", "Gold", "Platinum", "Catastrophic"];

export default function ComparePlans({ profile }) {
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

  return (
    <div className="compare-plans">
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

      {/* Step 1: Search */}
      <div className="plan-search-bar">
        <select
          value={selectedState}
          onChange={(e) => setSelectedState(e.target.value)}
        >
          <option value="">Select state...</option>
          {states.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

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

        <button
          className="compare-btn"
          onClick={handleSearch}
          disabled={!selectedState || searchLoading}
        >
          {searchLoading ? "Searching..." : "Search Plans"}
        </button>
      </div>

      {error && <p className="compare-error">Error: {error}</p>}

      {/* Step 2: Select plans */}
      {step >= 2 && plans.length > 0 && (
        <>
          <p className="plan-count">{planCount} plans found — select up to 3 to compare</p>
          <div className="plan-list">
            {plans.map((p) => (
              <div
                key={p.plan_id}
                className={`plan-list-card${selectedPlanIds.includes(p.plan_id) ? " selected" : ""}`}
                onClick={() => togglePlan(p.plan_id)}
              >
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

          <button
            className="compare-btn"
            onClick={handleCompare}
            disabled={selectedPlanIds.length < 2 || compareLoading}
            style={{ marginTop: 20 }}
          >
            {compareLoading
              ? "Comparing..."
              : `Compare ${selectedPlanIds.length} Plan${selectedPlanIds.length !== 1 ? "s" : ""}`}
          </button>
        </>
      )}

      {step >= 2 && plans.length === 0 && !searchLoading && (
        <p className="plan-count">No plans found for this state and filter.</p>
      )}

      {/* Step 3: Results */}
      {results && (
        <div className="compare-results">
          <h3>5-Year Cost Breakdown</h3>
          <div className="result-cards">
            {results.map((r, i) => (
              <div
                key={i}
                className={`result-card ${i === cheapestIdx ? "cheapest" : ""}`}
              >
                {i === cheapestIdx && <span className="cheapest-badge">Best Value</span>}
                <h4>{r.plan.plan_name}</h4>
                <p className="result-issuer">{r.plan.issuer}</p>
                <div className="result-row">
                  <span>Out-of-Pocket</span>
                  <span className="result-value">
                    ${Math.round(r.graph.total_5yr_oop).toLocaleString()}
                  </span>
                </div>
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
              </div>
            ))}
          </div>
          <button
            className="compare-btn"
            onClick={() => { setStep(2); setResults(null); }}
            style={{ marginTop: 20 }}
          >
            Back to Plans
          </button>
        </div>
      )}
    </div>
  );
}
