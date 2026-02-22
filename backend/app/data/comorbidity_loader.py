"""
Comorbidity Network Loader (ICD-level)

Loads the combined ICD adjacency matrix (combined_adjacency_ICD.csv) and the
ICD mapping (icd_mapping.json) to provide comorbidity queries at the ICD-10
code level, aggregated back to engine condition keys.

The CSV contains 1080×1080 odds-ratio matrices for 16 sex/age strata.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent / "processed"
_CSV_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "data/AdjacencyMatrixUnified/combined_adjacency_ICD.csv"
)

# --- Loaded data (lazy) ---
_icd_mapping: list[dict] | None = None
_icd_code_to_idx: dict[str, int] | None = None
_icd_idx_to_code: dict[int, str] | None = None
_icd_idx_to_desc: dict[int, str] | None = None
_matrices: dict[str, np.ndarray] | None = None  # "M_6" → (1080, 1080) array

# ── Condition key ↔ ICD code mapping ──

CONDITION_TO_ICD: dict[str, list[str]] = {
    "hypertension": ["I10", "I11", "I12", "I13", "I15"],
    "high_cholesterol": ["E78"],
    "back_pain": ["M54"],
    "vision_loss": ["H53", "H54"],
    "arthrosis": ["M15", "M16", "M17", "M18", "M19"],
    "diabetes": ["E10", "E11", "E13", "E14"],
    "cad": ["I20", "I21", "I22", "I23", "I24", "I25"],
    "thyroid_disease": ["E00", "E01", "E02", "E03", "E04", "E05", "E06", "E07"],
    "arrhythmia": ["I44", "I45", "I46", "I47", "I48", "I49"],
    "obesity": ["E66"],
    "gout": ["M10"],
    "prostatic_hyperplasia": ["N40"],
    "varicosis": ["I83"],
    "liver_disease": ["K70", "K71", "K72", "K73", "K74", "K75", "K76", "K77"],
    "depression": ["F32", "F33"],
    "asthma_copd": ["J44", "J45"],
    "gynecological": ["N80", "N81", "N83", "N84", "N85", "N92", "N93", "N94", "N95"],
    "atherosclerosis": ["I70", "I73", "I74"],
    "osteoporosis": ["M80", "M81", "M82"],
    "ckd": ["N17", "N18", "N19"],
    "stroke": ["I60", "I61", "I62", "I63", "I64", "I65", "I66", "I67", "I68", "I69", "G45"],
    "heart_failure": ["I50"],
    "hearing_loss": ["H90", "H91"],
    "gallstones": ["K80"],
    "somatoform": ["F45"],
    "hemorrhoids": ["K64"],
    "diverticulosis": ["K57"],
    "arthritis": ["M05", "M06", "M08"],
    "valve_disorder": ["I34", "I35", "I36", "I37", "I38"],
    "neuropathy": ["G60", "G61", "G62", "G63"],
    "dizziness": ["H81", "H82"],
    "dementia": ["F00", "F01", "F02", "F03", "G30", "G31"],
    "urinary_incontinence": ["N39"],
    "kidney_stones": ["N20", "N21", "N22", "N23"],
    "anemia": ["D50", "D51", "D52", "D53", "D55", "D58", "D59", "D61", "D62", "D63", "D64"],
    "anxiety": ["F40", "F41"],
    "psoriasis": ["L40"],
    "migraine": ["G43"],
    "parkinsons": ["G20", "G21", "G22"],
    "cancer": [
        "C00", "C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09",
        "C10", "C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18", "C19",
        "C20", "C21", "C22", "C23", "C24", "C25", "C26", "C30", "C31", "C32",
        "C33", "C34", "C37", "C38", "C39", "C40", "C41", "C43", "C44", "C45",
        "C46", "C47", "C48", "C49", "C50", "C51", "C52", "C53", "C54", "C55",
        "C56", "C57", "C58", "C60", "C61", "C62", "C63", "C64", "C65", "C66",
        "C67", "C68", "C69", "C70", "C71", "C72", "C73", "C74", "C75", "C76",
        "C77", "C78", "C79", "C80", "C81", "C82", "C83", "C84", "C85", "C86",
        "C88", "C90", "C91", "C92", "C93", "C94", "C95", "C96",
    ],
    "allergy": ["J30"],
    "gerd": ["K21", "K29"],
    "sexual_dysfunction": ["N48", "F52"],
    "insomnia": ["G47"],
    "tobacco_use": ["F17"],
    "hypotension": ["I95"],
}

# Build reverse map: ICD code → condition key
_ICD_TO_CONDITION: dict[str, str] = {}
for _cond, _codes in CONDITION_TO_ICD.items():
    for _c in _codes:
        _ICD_TO_CONDITION[_c] = _cond

# Display labels
_CONDITION_LABELS: dict[str, str] = {
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
}


def _ensure_loaded():
    """Lazy-load ICD mapping and adjacency CSV on first access."""
    global _icd_mapping, _icd_code_to_idx, _icd_idx_to_code, _icd_idx_to_desc, _matrices

    if _matrices is not None:
        return

    # Load ICD mapping
    mapping_path = _DATA_DIR / "icd_mapping.json"
    if not mapping_path.exists():
        raise FileNotFoundError(
            f"ICD mapping not found at {mapping_path}. "
            "Run: cd backend && python3 -m app.data.icd_processor"
        )

    with open(mapping_path) as f:
        _icd_mapping = json.load(f)

    _icd_code_to_idx = {m["icd_code"]: m["index"] for m in _icd_mapping}
    _icd_idx_to_code = {m["index"]: m["icd_code"] for m in _icd_mapping}
    _icd_idx_to_desc = {m["index"]: m["description"] for m in _icd_mapping}

    # Load adjacency CSV
    if not _CSV_PATH.exists():
        raise FileNotFoundError(
            f"ICD adjacency CSV not found at {_CSV_PATH}."
        )

    df = pd.read_csv(_CSV_PATH)
    col_indices = [str(i) for i in range(1080)]

    # Pre-split into numpy arrays keyed by "M_6", "F_3" etc.
    _matrices = {}
    sex_map = {"Male": "M", "Female": "F"}
    for (sex, age), group in df.groupby(["sex", "age"]):
        key = f"{sex_map.get(sex, sex)}_{age}"
        arr = group[col_indices].to_numpy(dtype=np.float64)
        _matrices[key] = arr


def _age_to_group(age: int) -> int:
    """Map patient age to age group 1-8."""
    if age < 10:
        return 1
    elif age < 20:
        return 2
    elif age < 30:
        return 3
    elif age < 40:
        return 4
    elif age < 50:
        return 5
    elif age < 60:
        return 6
    elif age < 70:
        return 7
    else:
        return 8


def _sex_to_code(sex: str) -> str:
    if sex and sex.upper().startswith("F"):
        return "F"
    return "M"


def get_comorbid_conditions(
    condition: str,
    age: int = 45,
    sex: str = "M",
) -> list[dict]:
    """
    Get comorbid conditions for a given condition, using ICD-level adjacency data.

    For each ICD code belonging to `condition`, looks up all non-zero neighbors
    in the adjacency matrix, maps them back to condition keys, and aggregates
    using the maximum odds ratio across ICD code pairs.

    Returns list of dicts sorted by weight (descending):
        [{"condition": "diabetes", "weight": 7.23, "label": "Diabetes Mellitus"}, ...]
    """
    _ensure_loaded()

    # Resolve condition → ICD indices
    icd_codes = CONDITION_TO_ICD.get(condition, [])
    if not icd_codes:
        return []

    source_indices = [_icd_code_to_idx[c] for c in icd_codes if c in _icd_code_to_idx]
    if not source_indices:
        return []

    # Look up the right matrix
    sex_code = _sex_to_code(sex)
    age_group = _age_to_group(age)
    matrix_key = f"{sex_code}_{age_group}"

    matrix = _matrices.get(matrix_key)
    if matrix is None:
        # Fallback to nearest age group
        for offset in [1, -1, 2, -2]:
            fallback = f"{sex_code}_{max(1, min(8, age_group + offset))}"
            matrix = _matrices.get(fallback)
            if matrix is not None:
                break

    if matrix is None:
        return []

    # Collect all non-zero weights per target condition, then average.
    # Using mean (instead of max) smooths out extreme ICD-pair outliers
    # like I12→N18 (hypertensive CKD → CKD, OR>100).
    condition_weight_lists: dict[str, list[float]] = {}
    for src_idx in source_indices:
        row = matrix[src_idx]
        nonzero = np.nonzero(row)[0]
        for tgt_idx in nonzero:
            tgt_idx = int(tgt_idx)
            weight = float(row[tgt_idx])
            tgt_code = _icd_idx_to_code.get(tgt_idx)
            if tgt_code is None:
                continue

            tgt_condition = _ICD_TO_CONDITION.get(tgt_code)
            if tgt_condition is None:
                continue
            if tgt_condition == condition:
                continue

            if tgt_condition not in condition_weight_lists:
                condition_weight_lists[tgt_condition] = []
            condition_weight_lists[tgt_condition].append(weight)

    condition_weights = {
        cond: sum(ws) / len(ws) for cond, ws in condition_weight_lists.items()
    }

    # Build result list
    result = []
    for cond_key, weight in condition_weights.items():
        result.append({
            "condition": cond_key,
            "weight": round(weight, 4),
            "label": _CONDITION_LABELS.get(cond_key, cond_key),
        })

    result.sort(key=lambda x: x["weight"], reverse=True)
    return result


def get_condition_label(condition: str) -> str:
    """Get the display label for a condition key."""
    return _CONDITION_LABELS.get(condition, condition)


def get_all_condition_keys() -> list[str]:
    """Return all condition keys."""
    return list(CONDITION_TO_ICD.keys())


def get_condition_metadata() -> dict:
    """Return conditions metadata dict (key → {label, icd_codes})."""
    return {
        key: {"label": _CONDITION_LABELS.get(key, key), "icd_codes": codes}
        for key, codes in CONDITION_TO_ICD.items()
    }
