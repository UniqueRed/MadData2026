"""
CareGraph Simulation Engine

Generates multi-year probabilistic care pathways using comorbidity network
data from 16 GEXF files (8 age groups x 2 sexes, 46 chronic conditions).
Costs are sourced from MEPS HC-233 (28,336 person survey) with fallback
to literature-based estimates for conditions MEPS doesn't track.

For conditions outside the 46, an LLM fallback generates minimal
standalone progression nodes (last resort only).
"""

import json
from groq import AsyncGroq
from app.config import GROQ_API_KEY
from app.models.patient import PatientProfile
from app.models.graph import GraphNode, GraphEdge, CarePathwayGraph
from app.data.meps_loader import query_cost, get_condition_summary, query_drug_cost, query_intervention_cost
from app.data.comorbidity_loader import get_comorbid_conditions, get_condition_label

_groq_client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Minimum edge weight to include (filters noise from weak associations)
_MIN_WEIGHT = 1.5

# Weight threshold for depth-2 expansion (strong associations)
_STRONG_WEIGHT = 3.0

# US adult prevalence by condition for OR → probability conversion.
# Sources: MEPS HC-233 (28,336 persons) for 12 flagship conditions,
# CDC/NIDDK/AHA/NIMH published prevalence for the remaining 34.
# Used as p0 in the epidemiological formula:
#   P(cond | exposure) = (OR * p0) / (1 - p0 + OR * p0)
CONDITION_PREVALENCE: dict[str, float] = {
    # ── From MEPS HC-233 (directly computed from diagnosis flags) ──
    "hypertension":       0.30,
    "high_cholesterol":   0.28,
    "arthritis":          0.24,
    "asthma_copd":        0.14,
    "diabetes":           0.12,
    "cancer":             0.10,
    "heart_failure":      0.10,
    "cad":                0.05,
    "stroke":             0.04,
    # ── From CDC / national registries / clinical literature ──
    "obesity":            0.42,
    "pre-diabetes":       0.38,
    "allergy":            0.30,
    "back_pain":          0.25,
    "gerd":               0.20,
    "anxiety":            0.19,
    "arthrosis":          0.15,
    "ckd":                0.15,
    "varicosis":          0.15,
    "hearing_loss":       0.15,
    "dizziness":          0.15,
    "vision_loss":        0.12,
    "thyroid_disease":    0.12,
    "migraine":           0.12,
    "tobacco_use":        0.12,
    "kidney_stones":      0.11,
    "insomnia":           0.10,
    "osteoporosis":       0.10,
    "diverticulosis":     0.10,
    "gallstones":         0.10,
    "urinary_incontinence": 0.10,
    "sexual_dysfunction": 0.10,
    "depression":         0.08,
    "neuropathy":         0.08,
    "gynecological":      0.08,
    "prostatic_hyperplasia": 0.08,
    "anemia":             0.06,
    "hypotension":        0.05,
    "hemorrhoids":        0.05,
    "liver_disease":      0.04,
    "gout":               0.04,
    "atherosclerosis":    0.03,
    "arrhythmia":         0.03,
    "psoriasis":          0.03,
    "dementia":           0.07,
    "valve_disorder":     0.025,
    "somatoform":         0.02,
    "parkinsons":         0.01,
}

# Fallback prevalence for conditions not in the table above
_DEFAULT_PREVALENCE = 0.05

# Maximum annual transition probability cap (no edge can exceed 15%)
_MAX_PROB = 0.15

# Fallback costs for conditions MEPS doesn't track as individual diagnosis flags.
# Used only when query_cost() returns None.
FALLBACK_ANNUAL_COSTS = {
    "pre-diabetes": 1200.0,
    "ckd_stage_2": 4200.0,
    "ckd_stage_3": 8400.0,
    "retinopathy": 2800.0,
    "neuropathy": 1900.0,
    "dialysis": 72000.0,
    "diabetic_foot": 5600.0,
    "back_pain": 3500.0,
    "vision_loss": 4000.0,
    "arthrosis": 3200.0,
    "thyroid_disease": 2400.0,
    "arrhythmia": 6500.0,
    "obesity": 2500.0,
    "gout": 2800.0,
    "prostatic_hyperplasia": 2200.0,
    "varicosis": 1800.0,
    "liver_disease": 5500.0,
    "depression": 3800.0,
    "asthma_copd": 4200.0,
    "gynecological": 2000.0,
    "atherosclerosis": 5200.0,
    "osteoporosis": 3000.0,
    "ckd": 6000.0,
    "hearing_loss": 1500.0,
    "gallstones": 3500.0,
    "somatoform": 2800.0,
    "hemorrhoids": 1200.0,
    "diverticulosis": 2500.0,
    "valve_disorder": 5800.0,
    "dizziness": 1800.0,
    "dementia": 12000.0,
    "urinary_incontinence": 2200.0,
    "kidney_stones": 3000.0,
    "anemia": 2600.0,
    "anxiety": 3200.0,
    "psoriasis": 2800.0,
    "migraine": 2400.0,
    "parkinsons": 10000.0,
    "allergy": 1500.0,
    "gerd": 2200.0,
    "sexual_dysfunction": 1800.0,
    "insomnia": 2000.0,
    "tobacco_use": 1500.0,
    "hypotension": 1200.0,
}

# Map engine condition names → MEPS condition names where they differ
ENGINE_TO_MEPS_CONDITION = {
    "cad": "coronary_heart_disease",
    "heart_failure": "other_heart_disease",
    "high_cholesterol": "high_cholesterol",
    "diabetes": "type_2_diabetes",
    "asthma_copd": "asthma",
    "arthritis": "arthritis",
    "cancer": "cancer",
    "depression": "depression",
    "anxiety": "anxiety",
    "stroke": "stroke",
    "obesity": "obesity",
    "ckd": "ckd_stage_2",
    "back_pain": "back_pain",
    "osteoporosis": "osteoporosis",
}

# Intervention effects: intervention -> {(source, target): multiplier}
# multiplier < 1.0 means the intervention reduces progression probability
INTERVENTION_EFFECTS = {
    "metformin": {
        ("pre-diabetes", "type_2_diabetes"): 0.42,
        ("pre-diabetes", "diabetes"): 0.42,
        ("diabetes", "ckd"): 0.60,
        ("diabetes", "neuropathy"): 0.70,
    },
    "sglt2_inhibitor": {
        ("diabetes", "ckd"): 0.52,
        ("diabetes", "heart_failure"): 0.65,
        ("type_2_diabetes", "ckd_stage_2"): 0.52,
        ("type_2_diabetes", "heart_failure"): 0.65,
    },
    "statin": {
        ("high_cholesterol", "cad"): 0.50,
        ("high_cholesterol", "atherosclerosis"): 0.50,
        ("cad", "heart_failure"): 0.70,
    },
    "ace_inhibitor": {
        ("hypertension", "ckd"): 0.55,
        ("hypertension", "stroke"): 0.60,
        ("hypertension", "heart_failure"): 0.65,
    },
    "lifestyle_change": {
        ("pre-diabetes", "diabetes"): 0.42,
        ("pre-diabetes", "type_2_diabetes"): 0.42,
        ("hypertension", "stroke"): 0.75,
        ("obesity", "diabetes"): 0.50,
        ("obesity", "hypertension"): 0.65,
    },
}

# Display labels for all conditions (engine key → label)
# Populated from comorbidity network + legacy conditions
CONDITION_LABELS = {
    # Legacy conditions kept for backward compatibility
    "pre-diabetes": "Pre-Diabetes",
    "type_2_diabetes": "Type 2 Diabetes",
    "ckd_stage_2": "CKD Stage 2",
    "ckd_stage_3": "CKD Stage 3",
    "retinopathy": "Retinopathy",
    "diabetic_foot": "Diabetic Foot",
    "heart_attack": "Heart Attack",
    "angina": "Angina",
    "emphysema": "Emphysema",
    "coronary_heart_disease": "Coronary Heart Disease",
    "other_heart_disease": "Other Heart Disease",
    # All 46 comorbidity network conditions
    "hypertension": "Hypertension",
    "high_cholesterol": "High Cholesterol",
    "back_pain": "Chronic Low Back Pain",
    "vision_loss": "Severe Vision Loss",
    "arthrosis": "Joint Arthrosis",
    "diabetes": "Diabetes Mellitus",
    "cad": "Coronary Artery Disease",
    "thyroid_disease": "Thyroid Disease",
    "arrhythmia": "Cardiac Arrhythmia",
    "obesity": "Obesity",
    "gout": "Gout",
    "prostatic_hyperplasia": "Prostatic Hyperplasia",
    "varicosis": "Varicose Veins",
    "liver_disease": "Liver Disease",
    "depression": "Depression",
    "asthma_copd": "Asthma / COPD",
    "gynecological": "Gynecological Problems",
    "atherosclerosis": "Atherosclerosis / PAOD",
    "osteoporosis": "Osteoporosis",
    "ckd": "Chronic Kidney Disease",
    "stroke": "Stroke",
    "heart_failure": "Heart Failure",
    "hearing_loss": "Hearing Loss",
    "gallstones": "Gallstones",
    "somatoform": "Somatoform Disorder",
    "hemorrhoids": "Hemorrhoids",
    "diverticulosis": "Diverticulosis",
    "arthritis": "Rheumatoid Arthritis",
    "valve_disorder": "Cardiac Valve Disorder",
    "neuropathy": "Neuropathy",
    "dizziness": "Dizziness / Vertigo",
    "dementia": "Dementia",
    "urinary_incontinence": "Urinary Incontinence",
    "kidney_stones": "Kidney Stones",
    "anemia": "Anemia",
    "anxiety": "Anxiety",
    "psoriasis": "Psoriasis",
    "migraine": "Migraine",
    "parkinsons": "Parkinson's Disease",
    "cancer": "Cancer",
    "allergy": "Allergy",
    "gerd": "GERD / Gastritis",
    "sexual_dysfunction": "Sexual Dysfunction",
    "insomnia": "Insomnia",
    "tobacco_use": "Tobacco Use Disorder",
    "hypotension": "Hypotension",
    "dialysis": "Dialysis",
}


# Drug-to-total cost multiplier: drug costs alone underestimate total care
# (doesn't include visits, labs, imaging, procedures). This ratio is derived
# from conditions with both HC-233 total expenditure and H239 drug cost data.
# Typical ratio for chronic conditions is ~2.0-2.5x (drugs are ~40-50% of total).
_DRUG_TO_TOTAL_RATIO = 2.1


def _get_condition_cost(condition: str, profile: PatientProfile) -> float:
    """
    Get the annual cost for a condition using a 4-tier lookup:

    1. MEPS HC-233 stratified by age/sex/insurance (12 conditions)
    2. MEPS HC-233 unstratified summary (same 12 conditions)
    3. H239 drug cost × multiplier (~25 more conditions from prescription data)
    4. Hardcoded FALLBACK_ANNUAL_COSTS (remaining conditions)

    Uses incremental cost (cost above baseline for that demographic).

    When a stratified cell returns a negative or zero incremental cost
    (common in thin age/sex strata), we fall back to the unstratified
    population-level summary so conditions like Cancer don't appear free.
    """
    meps_name = ENGINE_TO_MEPS_CONDITION.get(condition, condition)

    # Tier 1: MEPS HC-233 stratified
    result = query_cost(
        condition=meps_name,
        age=profile.age,
        sex=profile.sex,
        insurance_type=profile.insurance_type,
    )

    if result is not None and result["incremental_cost"] > 0:
        return result["incremental_cost"]

    # Tier 2: MEPS HC-233 unstratified summary
    summary = get_condition_summary(meps_name)
    if summary is not None and summary["incremental_cost"] > 0:
        return summary["incremental_cost"]

    # Tier 3: H239 drug cost × multiplier
    drug_data = query_drug_cost(condition)
    if drug_data is not None and drug_data["mean_drug_cost"] > 0:
        return round(drug_data["mean_drug_cost"] * _DRUG_TO_TOTAL_RATIO, 2)

    # Tier 4: Hardcoded fallback
    return FALLBACK_ANNUAL_COSTS.get(condition, 2000.0)


def _weight_to_prob(weight: float, target_condition: str = "") -> float:
    """
    Convert an odds-ratio weight to an annual transition probability.

    Uses the epidemiological formula:
        P(condition | exposure) = (OR * p0) / (1 - p0 + OR * p0)
    where p0 is the condition-specific population prevalence from MEPS/CDC data.

    The co-occurrence probability spans years, so we divide by a typical
    disease development window (~10 years) to get an annual rate.
    """
    p0 = CONDITION_PREVALENCE.get(target_condition, _DEFAULT_PREVALENCE)
    conditional = (weight * p0) / (1.0 - p0 + weight * p0)
    # Co-occurrence probability spans years; convert to annual incidence
    annual = conditional / 10.0
    return min(annual, _MAX_PROB)


def _get_effective_prob(
    source: str,
    target: str,
    base_prob: float,
    interventions: list[str],
) -> float:
    """Get the transition probability after applying intervention effects."""
    prob = base_prob
    for intervention in interventions:
        effects = INTERVENTION_EFFECTS.get(intervention, {})
        multiplier = effects.get((source, target))
        if multiplier is not None:
            prob *= multiplier
    return prob


def _estimate_oop(total_cost: float, profile: PatientProfile) -> float:
    """Estimate out-of-pocket cost given insurance parameters."""
    if total_cost <= profile.deductible:
        oop = total_cost
    else:
        oop = profile.deductible + (total_cost - profile.deductible) * profile.coinsurance
    return min(oop, profile.oop_max)


async def _generate_llm_progression(
    condition_text: str, profile: PatientProfile
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """
    Last-resort LLM fallback: generate a small set of progression nodes
    for a condition that doesn't exist in our 46-condition adjacency matrix.

    Returns (nodes, edges). Returns empty lists if the condition is terminal
    or has no meaningful progression.
    """
    if _groq_client is None:
        return [], []

    try:
        response = await _groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": """You are a medical progression modeler. Given a condition, generate a small set of likely disease progressions (max 3-4).

For each progression, provide:
- "name": short condition name
- "probability": annual probability (0-1, be conservative)
- "annual_cost": estimated US annual treatment cost in dollars

Rules:
- If the condition is terminal or has no meaningful progression, return {"progressions": []}
- Be medically accurate and conservative with probabilities
- Costs should reflect typical US healthcare costs
- Return ONLY valid JSON

Return JSON: {"progressions": [{"name": "...", "probability": 0.05, "annual_cost": 3000}, ...]}"""},
                {"role": "user", "content": f"Condition: {condition_text}\nPatient: {profile.age}yo {profile.sex}"},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        progressions = result.get("progressions", [])

        nodes = []
        edges = []
        source_id = f"current_{condition_text.lower().replace(' ', '_')}"

        for i, prog in enumerate(progressions[:4]):
            name = prog.get("name", f"progression_{i}")
            prob = min(float(prog.get("probability", 0.05)), _MAX_PROB)
            cost = float(prog.get("annual_cost", 2000))
            node_id = f"llm_{condition_text.lower().replace(' ', '_')}_{i}_y1"

            is_high_cost = cost > 10000
            nodes.append(GraphNode(
                id=node_id,
                label=name,
                node_type="high_cost" if is_high_cost else "future",
                probability=round(prob, 4),
                annual_cost=cost,
                oop_estimate=_estimate_oop(cost, profile),
                year=1,
                is_llm_generated=True,
            ))
            edges.append(GraphEdge(
                source=source_id,
                target=node_id,
                edge_type="llm_progression",
                probability=round(prob, 4),
                label=f"{prob:.0%} / yr",
            ))

        return nodes, edges
    except Exception:
        return [], []


def _compute_symptom_probability(
    condition: str,
    llm_score: float,
    confirmed_conditions: list[str],
    age: int,
    sex: str,
) -> float:
    """
    Two-signal probability for symptom-derived conditions.

    Signal 1 — LLM relevance score (capped at 0.85).
    Signal 2 — Comorbidity prior: for each confirmed condition, check how
    strongly it predicts the suspected condition via the adjacency matrix.
    Uses condition-specific prevalence from MEPS/CDC as p0 in:
        P(cond | exposure) = (OR * p0) / (1 - p0 + OR * p0)
    Capped at 0.50.

    Returns max(signal_1, signal_2), floored at 0.05.
    """
    # Signal 1: LLM relevance
    sig1 = min(llm_score, 0.85)

    # Signal 2: best comorbidity prior from any confirmed condition
    p0 = CONDITION_PREVALENCE.get(condition, _DEFAULT_PREVALENCE)
    sig2 = 0.0
    for confirmed in confirmed_conditions:
        neighbors = get_comorbid_conditions(
            condition=confirmed,
            age=age,
            sex=sex,
        )
        for neighbor in neighbors:
            if neighbor["condition"] == condition:
                odds_ratio = neighbor["weight"]
                prob = (odds_ratio * p0) / (1.0 - p0 + odds_ratio * p0)
                sig2 = max(sig2, min(prob, 0.50))
                break

    final = max(sig1, sig2)
    return max(final, 0.05)


async def simulate_pathway(
    profile: PatientProfile,
    interventions: list[str] | None = None,
    time_horizon_years: int = 5,
    symptom_conditions: list[str] | None = None,
    unmapped_conditions: list[str] | None = None,
    symptom_scores: dict[str, float] | None = None,
) -> CarePathwayGraph:
    """
    Generate a care pathway graph for the given patient profile.

    Uses comorbidity network data (46 conditions, age/sex stratified) to
    build a DAG of possible future health states. Costs are sourced from
    MEPS HC-233 data stratified by age, sex, and insurance type.

    symptom_conditions are shown as "possible future" (not confirmed diagnoses).
    For unmapped conditions (not in the 46), uses LLM to generate minimal
    standalone progression nodes as a last resort.
    """
    if interventions is None:
        interventions = []
    if symptom_conditions is None:
        symptom_conditions = []
    if unmapped_conditions is None:
        unmapped_conditions = []
    if symptom_scores is None:
        symptom_scores = {}

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    seen_nodes: set[str] = set()

    # Add current condition nodes
    for condition in profile.conditions:
        node_id = f"current_{condition}"
        cost = _get_condition_cost(condition, profile)
        nodes.append(GraphNode(
            id=node_id,
            label=CONDITION_LABELS.get(condition, condition),
            node_type="current",
            probability=1.0,
            annual_cost=cost,
            oop_estimate=_estimate_oop(cost, profile),
            year=0,
        ))
        seen_nodes.add(node_id)

    # Add intervention nodes with real drug pricing from H239
    for intervention in interventions:
        node_id = f"intervention_{intervention}"
        intervention_data = query_intervention_cost(intervention)
        if intervention_data is not None:
            rx_cost = intervention_data["mean_annual_cost"]
            rx_oop = intervention_data["mean_annual_oop"]
        else:
            rx_cost = 600.0
            rx_oop = _estimate_oop(rx_cost, profile)
        nodes.append(GraphNode(
            id=node_id,
            label=intervention.replace("_", " ").title(),
            node_type="intervention",
            annual_cost=rx_cost,
            oop_estimate=rx_oop,
            year=0,
        ))
        seen_nodes.add(node_id)

    # Add symptom-derived conditions as "suspected" (possible future, not confirmed)
    # Per-condition probability via two-signal approach (LLM relevance + comorbidity prior)
    # Skip any that duplicate a confirmed condition
    _confirmed_set = set(profile.conditions)
    _symptom_probs: dict[str, float] = {}
    for condition in symptom_conditions:
        if condition in _confirmed_set:
            continue
        llm_score = symptom_scores.get(condition, 0.4)  # fallback to 0.4 if no score
        prob = _compute_symptom_probability(
            condition=condition,
            llm_score=llm_score,
            confirmed_conditions=profile.conditions,
            age=profile.age,
            sex=profile.sex,
        )
        _symptom_probs[condition] = prob

        node_id = f"suspected_{condition}"
        cost = _get_condition_cost(condition, profile)
        nodes.append(GraphNode(
            id=node_id,
            label=CONDITION_LABELS.get(condition, condition),
            node_type="future",
            probability=round(prob, 4),
            annual_cost=cost,
            oop_estimate=_estimate_oop(cost, profile),
            year=0,
            is_llm_generated=True,
        ))
        seen_nodes.add(node_id)

    # Build future state nodes from comorbidity network
    def _expand(source_condition: str, source_id: str, year: int, cum_prob: float, depth: int):
        if year > time_horizon_years:
            return

        neighbors = get_comorbid_conditions(
            condition=source_condition,
            age=profile.age,
            sex=profile.sex,
        )

        for neighbor in neighbors:
            tgt = neighbor["condition"]
            weight = neighbor["weight"]

            # Skip weak associations
            if weight < _MIN_WEIGHT:
                continue

            # Skip if target is already a current condition
            if f"current_{tgt}" in seen_nodes:
                continue

            base_prob = _weight_to_prob(weight, tgt)
            prob = _get_effective_prob(source_condition, tgt, base_prob, interventions)
            joint_prob = cum_prob * prob

            if joint_prob < 0.001:
                continue

            node_id = f"future_{tgt}_y{year}"
            cost = _get_condition_cost(tgt, profile)

            is_high_cost = cost > 10000
            node_type = "high_cost" if is_high_cost else "future"

            if node_id not in seen_nodes:
                label = CONDITION_LABELS.get(tgt, neighbor.get("label", tgt))
                nodes.append(GraphNode(
                    id=node_id,
                    label=label,
                    node_type=node_type,
                    probability=round(joint_prob, 4),
                    annual_cost=cost,
                    oop_estimate=_estimate_oop(cost, profile),
                    year=year,
                ))
                seen_nodes.add(node_id)

            edges.append(GraphEdge(
                source=source_id,
                target=node_id,
                edge_type="comorbidity",
                probability=round(prob, 4),
                label=f"{prob:.0%} / yr",
            ))

            # Depth-2 expansion for strong connections
            if depth < 2 and weight >= _STRONG_WEIGHT:
                _expand(tgt, node_id, year + 1, joint_prob, depth + 1)

    for condition in profile.conditions:
        _expand(condition, f"current_{condition}", 1, 1.0, 1)

    # Expand symptom-derived conditions (scaled by their per-condition probability)
    for condition in symptom_conditions:
        if condition in _confirmed_set:
            continue
        _expand(condition, f"suspected_{condition}", 1, _symptom_probs.get(condition, 0.4), 1)

    # Process unmapped conditions (LLM last resort)
    # Skip any that overlap with confirmed conditions (e.g. "asthma" when "asthma_copd" is confirmed)
    for cond_text in unmapped_conditions:
        cond_key = cond_text.lower().replace(" ", "_")
        # Check if this unmapped term overlaps with any confirmed condition
        if any(cond_key in c or c in cond_key for c in _confirmed_set):
            continue
        node_id = f"current_{cond_key}"
        if node_id not in seen_nodes:
            fallback_cost = 2500.0  # generic fallback
            nodes.append(GraphNode(
                id=node_id,
                label=cond_text.title(),
                node_type="current",
                probability=1.0,
                annual_cost=fallback_cost,
                oop_estimate=_estimate_oop(fallback_cost, profile),
                year=0,
                is_llm_generated=True,
            ))
            seen_nodes.add(node_id)

        llm_nodes, llm_edges = await _generate_llm_progression(cond_text, profile)
        for n in llm_nodes:
            if n.id not in seen_nodes:
                nodes.append(n)
                seen_nodes.add(n.id)
        edges.extend(llm_edges)

    # Connect interventions to current conditions they affect
    for intervention in interventions:
        effects = INTERVENTION_EFFECTS.get(intervention, {})
        for (src, _tgt) in effects:
            if src in profile.conditions:
                edges.append(GraphEdge(
                    source=f"intervention_{intervention}",
                    target=f"current_{src}",
                    edge_type="intervention",
                    label=intervention.replace("_", " ").title(),
                ))

    # Compute 5-year expected costs (simple expected value)
    total_cost = 0.0
    total_oop = 0.0
    for node in nodes:
        years_active = max(1, time_horizon_years - node.year + 1)
        total_cost += node.annual_cost * node.probability * years_active
        total_oop += node.oop_estimate * node.probability * years_active

    return CarePathwayGraph(
        nodes=nodes,
        edges=edges,
        total_5yr_cost=round(total_cost, 2),
        total_5yr_oop=round(total_oop, 2),
    )
