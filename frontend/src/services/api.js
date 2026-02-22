import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000/api",
});

export async function generatePathway(profile, interventions = [], timeHorizon = 5, symptomConditions = [], unmappedConditions = [], symptomScores = {}) {
  const { data } = await api.post("/simulation/pathway", {
    profile,
    interventions,
    time_horizon_years: timeHorizon,
    symptom_conditions: symptomConditions,
    unmapped_conditions: unmappedConditions,
    symptom_scores: symptomScores,
  });
  return data;
}

export async function compareScenarios(profile, scenarios, timeHorizon = 5) {
  const { data } = await api.post("/simulation/compare", null, {
    params: { time_horizon_years: timeHorizon },
    data: { profile, scenarios },
  });
  return data;
}

export async function comparePlans(request) {
  const { data } = await api.post("/plans/compare", request);
  return data;
}

export async function getStates() {
  const { data } = await api.get("/plans/states");
  return data.states;
}

export async function searchPlans(state, metalLevel, age) {
  const params = { state, age };
  if (metalLevel && metalLevel !== "All") params.metal_level = metalLevel;
  const { data } = await api.get("/plans/search", { params });
  return data;
}

export async function compareMarketplacePlans(request) {
  const { data } = await api.post("/plans/marketplace-compare", request);
  return data;
}

export async function parseProfile(text) {
  const { data } = await api.post("/voice/parse-profile", { text });
  return data;
}

export async function parseScenario(text, currentConditions = []) {
  const { data } = await api.post("/voice/parse-scenario", {
    text,
    current_conditions: currentConditions,
  });
  return data;
}

export async function getExplanation(graphData, question) {
  const { data } = await api.post("/voice/explain", {
    graph_data: graphData,
    question,
  });
  return data.explanation;
}

export default api;
