"""
MEPS HC-233 Data Processor

Reads the raw h233.csv (28,336 person-level records) and produces
aggregated cost lookup tables that the simulation engine uses at runtime.

The MEPS Full Year Consolidated file contains:
- Demographics (age, sex)
- Priority condition diagnosis flags (1=Yes, 2=No)
- Annual expenditure variables (total, OOP/self, private, Medicare, Medicaid)
- Insurance coverage indicators

This processor builds two artifacts:
1. Per-condition cost stats stratified by age_group × sex × insurance_type
2. Comorbidity cost multipliers for common condition pairs

Run directly to regenerate:
    python -m app.data.meps_processor
"""

import os
import pandas as pd
import numpy as np
import json
from pathlib import Path

# ── MEPS column name → our internal condition name ──
# These are the "priority condition" diagnosis flags in HC-233.
# Each is a binary: 1 = diagnosed, 2 = not diagnosed, negative = inapplicable.
MEPS_CONDITION_MAP = {
    "DIABDX_M18": "type_2_diabetes",
    "HIBPDX":     "hypertension",
    "CHOLDX":     "high_cholesterol",
    "CHDDX":      "coronary_heart_disease",
    "ANGIDX":     "angina",
    "MIDX":       "heart_attack",
    "OHRTDX":     "other_heart_disease",
    "STRKDX":     "stroke",
    "EMPHDX":     "emphysema",
    "CANCERDX":   "cancer",
    "ARTHDX":     "arthritis",
    "ASTHDX":     "asthma",
}

# Map our engine's internal condition names to MEPS flags where they differ
ENGINE_TO_MEPS = {
    "type_2_diabetes": "DIABDX_M18",
    "hypertension":    "HIBPDX",
    "high_cholesterol": "CHOLDX",
    "cad":             "CHDDX",       # coronary heart disease ≈ CAD
    "heart_attack":    "MIDX",
    "stroke":          "STRKDX",
    "heart_failure":   "OHRTDX",      # best available proxy
    "asthma":          "ASTHDX",
    "arthritis":       "ARTHDX",
    "cancer":          "CANCERDX",
    "emphysema":       "EMPHDX",
    "angina":          "ANGIDX",
}

AGE_BINS = [0, 30, 40, 50, 60, 70, 80, 120]
AGE_LABELS = ["<30", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]

# INSCOV21: 1=Any Private, 2=Public Only, 3=Uninsured
INSURANCE_MAP = {1: "private", 2: "public", 3: "uninsured"}

# SEX: 1=Male, 2=Female
SEX_MAP = {1: "M", 2: "F"}


def _find_data_file() -> str:
    """Locate h233.csv from various possible locations."""
    candidates = [
        Path(__file__).resolve().parents[3] / "data" / "h233.csv",       # project_root/data/
        Path(__file__).resolve().parents[2] / "data" / "h233.csv",       # backend/data/
        Path.cwd() / "data" / "h233.csv",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    raise FileNotFoundError(
        f"h233.csv not found. Searched: {[str(c) for c in candidates]}"
    )


def load_raw_meps(path: str | None = None) -> pd.DataFrame:
    """Load the raw MEPS CSV and prepare core columns."""
    if path is None:
        path = _find_data_file()

    # Only load columns we need (1488 total, we need ~30)
    use_cols = (
        ["AGE21X", "SEX", "INSCOV21", "TOTEXP21", "TOTSLF21", "TOTPRV21", "TOTMCR21", "TOTMCD21"]
        + list(MEPS_CONDITION_MAP.keys())
    )
    df = pd.read_csv(path, usecols=use_cols)

    # Derived columns
    df["age_group"] = pd.cut(
        df["AGE21X"], bins=AGE_BINS, labels=AGE_LABELS, right=False
    )
    df["sex"] = df["SEX"].map(SEX_MAP)
    df["insurance_type"] = df["INSCOV21"].map(INSURANCE_MAP)

    return df


def build_condition_cost_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each condition, compute expenditure stats stratified by
    age_group, sex, and insurance_type.

    For each person with condition X, we use their TOTAL expenditure
    (not condition-specific, since MEPS consolidated doesn't split by condition).
    To isolate the incremental cost of a condition, we also compute the
    average expenditure for people WITHOUT that condition in the same stratum,
    and store the difference as `incremental_cost`.
    """
    rows = []

    for meps_col, condition_name in MEPS_CONDITION_MAP.items():
        # People with this condition (flag == 1)
        has = df[df[meps_col] == 1]
        # People without (flag == 2, exclude unknowns/inapplicable)
        no = df[df[meps_col] == 2]

        for (age_grp, sex, ins), group in has.groupby(
            ["age_group", "sex", "insurance_type"], observed=True
        ):
            if len(group) < 5:  # skip thin cells
                continue

            # Matching stratum without condition
            baseline = no[
                (no["age_group"] == age_grp)
                & (no["sex"] == sex)
                & (no["insurance_type"] == ins)
            ]
            baseline_mean = baseline["TOTEXP21"].mean() if len(baseline) >= 5 else 0

            rows.append({
                "condition": condition_name,
                "age_group": str(age_grp),
                "sex": sex,
                "insurance_type": ins,
                "n": len(group),
                "mean_total_exp": round(group["TOTEXP21"].mean(), 2),
                "median_total_exp": round(group["TOTEXP21"].median(), 2),
                "p25_total_exp": round(group["TOTEXP21"].quantile(0.25), 2),
                "p75_total_exp": round(group["TOTEXP21"].quantile(0.75), 2),
                "mean_oop": round(group["TOTSLF21"].mean(), 2),
                "median_oop": round(group["TOTSLF21"].median(), 2),
                "p25_oop": round(group["TOTSLF21"].quantile(0.25), 2),
                "p75_oop": round(group["TOTSLF21"].quantile(0.75), 2),
                "baseline_mean_exp": round(baseline_mean, 2),
                "incremental_cost": round(group["TOTEXP21"].mean() - baseline_mean, 2),
            })

    return pd.DataFrame(rows)


def build_condition_summary(df: pd.DataFrame) -> dict:
    """
    Build a simple condition → cost dict (unstratified) as a fallback
    for when stratified data is too thin.
    """
    summary = {}
    for meps_col, condition_name in MEPS_CONDITION_MAP.items():
        has = df[df[meps_col] == 1]
        no = df[df[meps_col] == 2]
        if len(has) < 10:
            continue
        baseline = no["TOTEXP21"].mean() if len(no) >= 10 else 0
        summary[condition_name] = {
            "n": int(len(has)),
            "mean_total_exp": round(has["TOTEXP21"].mean(), 2),
            "mean_oop": round(has["TOTSLF21"].mean(), 2),
            "median_total_exp": round(has["TOTEXP21"].median(), 2),
            "median_oop": round(has["TOTSLF21"].median(), 2),
            "incremental_cost": round(has["TOTEXP21"].mean() - baseline, 2),
            "incremental_oop": round(has["TOTSLF21"].mean() - no["TOTSLF21"].mean(), 2),
        }
    return summary


def build_comorbidity_costs(df: pd.DataFrame) -> dict:
    """
    For common condition pairs, compute the combined cost and the
    interaction effect (how much more than sum of individual costs).
    """
    pairs = [
        ("DIABDX_M18", "HIBPDX", "diabetes_hypertension"),
        ("DIABDX_M18", "CHOLDX", "diabetes_cholesterol"),
        ("HIBPDX", "CHOLDX", "hypertension_cholesterol"),
        ("DIABDX_M18", "CHDDX", "diabetes_heart_disease"),
        ("HIBPDX", "CHDDX", "hypertension_heart_disease"),
    ]
    result = {}
    for col_a, col_b, name in pairs:
        both = df[(df[col_a] == 1) & (df[col_b] == 1)]
        only_a = df[(df[col_a] == 1) & (df[col_b] != 1)]
        only_b = df[(df[col_a] != 1) & (df[col_b] == 1)]
        if len(both) < 20:
            continue
        result[name] = {
            "n_both": int(len(both)),
            "mean_exp_both": round(both["TOTEXP21"].mean(), 2),
            "mean_exp_a_only": round(only_a["TOTEXP21"].mean(), 2) if len(only_a) >= 10 else None,
            "mean_exp_b_only": round(only_b["TOTEXP21"].mean(), 2) if len(only_b) >= 10 else None,
            "mean_oop_both": round(both["TOTSLF21"].mean(), 2),
        }
    return result


def process_and_save(csv_path: str | None = None, output_dir: str | None = None):
    """Run the full pipeline and save processed data."""
    if output_dir is None:
        output_dir = str(Path(__file__).resolve().parent / "processed")

    os.makedirs(output_dir, exist_ok=True)

    print("Loading raw MEPS data...")
    df = load_raw_meps(csv_path)
    print(f"  {len(df)} records, {len(df.columns)} columns")

    print("Building stratified cost table...")
    cost_table = build_condition_cost_table(df)
    cost_path = os.path.join(output_dir, "condition_costs.csv")
    cost_table.to_csv(cost_path, index=False)
    print(f"  {len(cost_table)} rows → {cost_path}")

    print("Building condition summary...")
    summary = build_condition_summary(df)
    summary_path = os.path.join(output_dir, "condition_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  {len(summary)} conditions → {summary_path}")

    print("Building comorbidity costs...")
    comorbidity = build_comorbidity_costs(df)
    comorbidity_path = os.path.join(output_dir, "comorbidity_costs.json")
    with open(comorbidity_path, "w") as f:
        json.dump(comorbidity, f, indent=2)
    print(f"  {len(comorbidity)} pairs → {comorbidity_path}")

    print("Done.")
    return cost_table, summary, comorbidity


if __name__ == "__main__":
    process_and_save()
