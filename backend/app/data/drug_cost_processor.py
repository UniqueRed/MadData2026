"""
MEPS H239 Prescribed Medicines Data Processor

Reads the H239 prescribed medicines CSV (232,605 prescription records) and
produces per-condition drug cost estimates and per-intervention drug costs.

The H239 file contains individual prescription fill records with:
- DUPERSID — person ID
- TC1S1 — therapeutic sub-class code
- RXSF22X — out-of-pocket cost per fill
- RXXP22X — total cost per fill
- PERWT22F — survey weight for population-level estimates
- RXDRGNAM — drug name

This processor builds two artifacts:
1. drug_costs_by_condition.json — per-condition drug cost statistics
2. intervention_drug_costs.json — per-intervention (specific drug) cost statistics

Run directly to regenerate:
    python -m app.data.drug_cost_processor
"""

import os
import json
import re
import pandas as pd
import numpy as np
from pathlib import Path

# ── TC1S1 → condition mapping ──
# Based on actual codes present in the H239 dataset.
TC1S1_TO_CONDITION = {
    # Cardiovascular — hypertension
    42: "hypertension",         # ACE inhibitors (lisinopril, enalapril)
    47: "hypertension",         # Beta-blockers (metoprolol, carvedilol)
    48: "hypertension",         # Calcium channel blockers (amlodipine)
    55: "hypertension",         # Antihypertensive combinations
    56: "hypertension",         # ARBs (losartan, valsartan)
    # Cardiovascular — other
    46: "arrhythmia",           # Antiarrhythmics (amiodarone, diltiazem)
    82: "arrhythmia",           # Anticoagulants (apixaban, warfarin)
    45: "cad",                  # Antianginals (nitroglycerin, isosorbide)
    83: "atherosclerosis",      # Platelet aggregation inhibitors (clopidogrel)
    49: "heart_failure",        # Diuretics (furosemide, spironolactone)
    482: "heart_failure",       # Sacubitril-valsartan
    # Lipids
    19: "high_cholesterol",     # Statins (atorvastatin, rosuvastatin)
    # Diabetes
    99: "diabetes",             # Antidiabetics (metformin, insulin, SGLT2i)
    # Respiratory
    125: "asthma_copd",         # Bronchodilators (albuterol)
    243: "asthma_copd",         # Leukotriene modifiers (montelukast)
    130: "asthma_copd",         # Inhaled corticosteroids (fluticasone)
    # Mental health
    249: "depression",          # SSRIs/antidepressants (sertraline, escitalopram)
    67: "anxiety",              # Anxiolytics/sedatives (alprazolam, buspirone, zolpidem)
    251: "depression",          # Atypical antipsychotics (quetiapine — often used as adjunct)
    # Musculoskeletal
    58: "back_pain",            # Analgesics/NSAIDs (meloxicam, ibuprofen, tramadol)
    73: "back_pain",            # Skeletal muscle relaxants (cyclobenzaprine)
    98: "arthritis",            # Corticosteroids (prednisone)
    194: "gout",                # Antigout agents (allopurinol, colchicine)
    409: "osteoporosis",        # Bisphosphonates (alendronate)
    # GI
    272: "gerd",                # PPIs (omeprazole, pantoprazole)
    94: "gerd",                 # H2 antagonists (famotidine)
    # Neuro
    64: "neuropathy",           # Anticonvulsants/neuropathic pain (gabapentin)
    66: "parkinsons",           # Antiparkinson agents (carbidopa-levodopa)
    313: "dementia",            # Cholinesterase inhibitors (donepezil)
    80: "dementia",             # Memantine
    # Thyroid
    103: "thyroid_disease",     # Thyroid hormones (levothyroxine)
    # Allergy
    123: "allergy",             # Antihistamines (cetirizine, loratadine)
    247: "allergy",             # Nasal steroids (fluticasone nasal)
    # Urological
    519: "prostatic_hyperplasia",  # Alpha-adrenoreceptor antagonists (tamsulosin)
    288: "prostatic_hyperplasia",  # 5-alpha-reductase inhibitors (finasteride)
    264: "urinary_incontinence",   # Urinary antispasmodics (oxybutynin)
    303: "sexual_dysfunction",     # PDE5 inhibitors (sildenafil, tadalafil)
    # Hematology
    116: "anemia",              # Iron products
    # Dermatology
    136: "psoriasis",           # Dermatological agents (clobetasol, triamcinolone topical)
    # Ophthalmology
    147: "vision_loss",         # Ophthalmic glaucoma agents (latanoprost)
    # Smoking cessation
    320: "tobacco_use",         # Bupropion / smoking cessation agents
    # Dizziness
    65: "dizziness",            # Antiemetics (meclizine, ondansetron)
}

# ── Intervention drug name patterns ──
# Maps RXDRGNAM substrings to intervention keys used in engine.py
INTERVENTION_PATTERNS = {
    "metformin": [r"METFORMIN"],
    "statin": [r"ATORVASTATIN", r"ROSUVASTATIN", r"SIMVASTATIN", r"PRAVASTATIN", r"LOVASTATIN"],
    "ace_inhibitor": [r"LISINOPRIL", r"ENALAPRIL", r"RAMIPRIL", r"BENAZEPRIL"],
    "sglt2_inhibitor": [r"EMPAGLIFLOZIN", r"DAPAGLIFLOZIN", r"CANAGLIFLOZIN"],
}

USE_COLS = ["DUPERSID", "TC1S1", "RXSF22X", "RXXP22X", "PERWT22F", "RXDRGNAM"]


def _find_data_file() -> str:
    """Locate the H239 prescribed medicines CSV."""
    candidates = [
        Path(__file__).resolve().parents[3] / "data" / "drug_costs" / "h239 - costs by drug type - data.csv",
        Path(__file__).resolve().parents[2] / "data" / "drug_costs" / "h239 - costs by drug type - data.csv",
        Path.cwd() / "data" / "drug_costs" / "h239 - costs by drug type - data.csv",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    raise FileNotFoundError(
        f"H239 drug cost data not found. Searched: {[str(c) for c in candidates]}"
    )


def load_raw_h239(path: str | None = None) -> pd.DataFrame:
    """Load the raw H239 CSV with only the columns we need."""
    if path is None:
        path = _find_data_file()

    df = pd.read_csv(path, usecols=USE_COLS)

    # Clean cost columns: negative values mean missing/inapplicable in MEPS
    for col in ["RXSF22X", "RXXP22X"]:
        df[col] = df[col].clip(lower=0)

    # Filter to rows with valid TC1S1 codes in our mapping
    df = df[df["TC1S1"].isin(TC1S1_TO_CONDITION.keys())].copy()

    # Map TC1S1 to condition
    df["condition"] = df["TC1S1"].map(TC1S1_TO_CONDITION)

    return df


def build_drug_costs_by_condition(df: pd.DataFrame) -> dict:
    """
    For each condition, compute population-weighted annual drug cost statistics.

    Steps:
    1. Group by person + condition → sum all fills to get annual drug cost per person
    2. Compute weighted statistics across persons
    """
    # Sum costs per person per condition (annual total across all fills)
    person_condition = (
        df.groupby(["DUPERSID", "condition"])
        .agg(
            annual_drug_cost=("RXXP22X", "sum"),
            annual_drug_oop=("RXSF22X", "sum"),
            weight=("PERWT22F", "first"),  # weight is person-level, same across fills
        )
        .reset_index()
    )

    result = {}
    for condition, group in person_condition.groupby("condition"):
        weights = group["weight"].values
        costs = group["annual_drug_cost"].values
        oops = group["annual_drug_oop"].values

        # Weighted mean
        total_weight = weights.sum()
        if total_weight == 0:
            continue

        wmean_cost = np.average(costs, weights=weights)
        wmean_oop = np.average(oops, weights=weights)

        # Unweighted percentiles (good enough for our purposes)
        result[condition] = {
            "mean_drug_cost": round(float(wmean_cost), 2),
            "mean_drug_oop": round(float(wmean_oop), 2),
            "median_drug_cost": round(float(np.median(costs)), 2),
            "median_drug_oop": round(float(np.median(oops)), 2),
            "p25_drug_cost": round(float(np.percentile(costs, 25)), 2),
            "p75_drug_cost": round(float(np.percentile(costs, 75)), 2),
            "n_persons": int(len(group)),
        }

    return result


def build_intervention_drug_costs(df: pd.DataFrame) -> dict:
    """
    For specific intervention drugs, compute average annual cost per person.

    Uses RXDRGNAM substring matching to identify fills for each intervention.
    """
    result = {}

    for intervention, patterns in INTERVENTION_PATTERNS.items():
        # Build regex pattern for this intervention
        combined_pattern = "|".join(patterns)
        mask = df["RXDRGNAM"].str.contains(combined_pattern, case=False, na=False)
        intervention_fills = df[mask]

        if len(intervention_fills) == 0:
            continue

        # Sum costs per person (annual total)
        person_costs = (
            intervention_fills.groupby("DUPERSID")
            .agg(
                annual_cost=("RXXP22X", "sum"),
                annual_oop=("RXSF22X", "sum"),
                weight=("PERWT22F", "first"),
            )
            .reset_index()
        )

        weights = person_costs["weight"].values
        costs = person_costs["annual_cost"].values
        oops = person_costs["annual_oop"].values

        total_weight = weights.sum()
        if total_weight == 0:
            continue

        result[intervention] = {
            "mean_annual_cost": round(float(np.average(costs, weights=weights)), 2),
            "mean_annual_oop": round(float(np.average(oops, weights=weights)), 2),
            "median_annual_cost": round(float(np.median(costs)), 2),
            "n_persons": int(len(person_costs)),
        }

    # Lifestyle change has zero drug cost
    result["lifestyle_change"] = {
        "mean_annual_cost": 0.0,
        "mean_annual_oop": 0.0,
        "median_annual_cost": 0.0,
        "n_persons": 0,
    }

    return result


def process_and_save(csv_path: str | None = None, output_dir: str | None = None):
    """Run the full pipeline and save processed drug cost data."""
    if output_dir is None:
        output_dir = str(Path(__file__).resolve().parent / "processed")

    os.makedirs(output_dir, exist_ok=True)

    print("Loading H239 prescribed medicines data...")
    df = load_raw_h239(csv_path)
    print(f"  {len(df)} prescription fills after filtering to mapped TC1S1 codes")
    print(f"  {df['DUPERSID'].nunique()} unique persons")
    print(f"  {df['condition'].nunique()} conditions mapped")

    print("\nBuilding drug costs by condition...")
    drug_costs = build_drug_costs_by_condition(df)
    drug_costs_path = os.path.join(output_dir, "drug_costs_by_condition.json")
    with open(drug_costs_path, "w") as f:
        json.dump(drug_costs, f, indent=2)
    print(f"  {len(drug_costs)} conditions → {drug_costs_path}")
    for cond, data in sorted(drug_costs.items()):
        print(f"    {cond:30s}  mean=${data['mean_drug_cost']:>8,.0f}  oop=${data['mean_drug_oop']:>6,.0f}  n={data['n_persons']}")

    print("\nBuilding intervention drug costs...")
    intervention_costs = build_intervention_drug_costs(df)
    intervention_path = os.path.join(output_dir, "intervention_drug_costs.json")
    with open(intervention_path, "w") as f:
        json.dump(intervention_costs, f, indent=2)
    print(f"  {len(intervention_costs)} interventions → {intervention_path}")
    for name, data in sorted(intervention_costs.items()):
        print(f"    {name:20s}  mean=${data['mean_annual_cost']:>8,.0f}  oop=${data['mean_annual_oop']:>6,.0f}")

    print("\nDone.")
    return drug_costs, intervention_costs


if __name__ == "__main__":
    process_and_save()
