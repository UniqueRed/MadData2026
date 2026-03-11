"""
openFDA Drug Label Service

Queries the openFDA drug/label endpoint to find FDA-approved treatments
for a given condition. Returns brand names, generic names, warnings,
interactions, and common adverse reactions.

Results are cached in-memory (LRU) since drug labels rarely change.
"""

import httpx
from functools import lru_cache

_BASE = "https://api.fda.gov/drug/label.json"

# Map our 46 condition keys to effective openFDA search terms.
# These are tuned to match the indications_and_usage field in SPL labels.
CONDITION_SEARCH_TERMS = {
    "diabetes": "type 2 diabetes mellitus",
    "pre-diabetes": "type 2 diabetes mellitus",
    "hypertension": "hypertension",
    "high_cholesterol": "hyperlipidemia OR hypercholesterolemia",
    "obesity": "obesity OR weight management",
    "asthma_copd": "asthma OR chronic obstructive pulmonary disease",
    "cad": "coronary artery disease OR angina",
    "heart_failure": "heart failure",
    "arrhythmia": "atrial fibrillation OR arrhythmia",
    "stroke": "stroke prevention OR anticoagulant",
    "ckd": "chronic kidney disease",
    "arthritis": "osteoarthritis OR rheumatoid arthritis",
    "osteoporosis": "osteoporosis",
    "depression": "major depressive disorder",
    "anxiety": "generalized anxiety disorder",
    "gerd": "gastroesophageal reflux",
    "thyroid_disease": "hypothyroidism",
    "neuropathy": "neuropathic pain OR diabetic neuropathy",
    "back_pain": "chronic pain OR back pain",
    "dementia": "alzheimer OR dementia",
    "parkinsons": "parkinson",
    "psoriasis": "psoriasis",
    "gout": "gout OR hyperuricemia",
    "allergy": "allergic rhinitis OR antihistamine",
    "anemia": "anemia OR iron deficiency",
    "cancer": "oncology OR antineoplastic",
    "liver_disease": "hepatitis OR liver disease",
    "migraine": "migraine",
    "insomnia": "insomnia",
    "prostatic_hyperplasia": "benign prostatic hyperplasia",
    "urinary_incontinence": "overactive bladder OR urinary incontinence",
    "vision_loss": "glaucoma OR macular degeneration",
    "atherosclerosis": "peripheral arterial disease OR atherosclerosis",
    "tobacco_use": "smoking cessation",
    "sexual_dysfunction": "erectile dysfunction",
    "kidney_stones": "nephrolithiasis OR kidney stones",
    "dizziness": "vertigo OR dizziness",
    "hearing_loss": "hearing loss",
    "varicose_veins": "chronic venous insufficiency",
    "diverticulosis": "diverticulitis",
    "hemorrhoids": "hemorrhoids",
    "gallstones": "gallstones",
    "cardiac_valve": "heart valve",
    "rheumatoid_arthritis": "rheumatoid arthritis",
    "hypotension": "hypotension",
    "somatoform_disorder": "somatic symptom",
    "gynecological": "menopause OR hormone replacement",
}


def _truncate(text: str, max_len: int = 300) -> str:
    """Truncate text to max_len, adding ellipsis if needed."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def _extract_drug(result: dict) -> dict | None:
    """Extract a clean drug record from an openFDA label result."""
    openfda = result.get("openfda", {})
    brand = openfda.get("brand_name", [None])[0]
    generic = openfda.get("generic_name", [None])[0]

    if not brand and not generic:
        return None

    return {
        "brand_name": brand,
        "generic_name": generic.title() if generic else None,
        "route": (openfda.get("route") or [None])[0],
        "manufacturer": (openfda.get("manufacturer_name") or [None])[0],
        "indications": _truncate(
            (result.get("indications_and_usage") or [""])[0], 400
        ),
        "adverse_reactions": _truncate(
            (result.get("adverse_reactions") or [""])[0], 300
        ),
        "drug_interactions": _truncate(
            (result.get("drug_interactions") or [""])[0], 300
        ),
        "warnings": _truncate(
            (result.get("warnings_and_cautions") or result.get("warnings") or [""])[0],
            300,
        ),
    }


@lru_cache(maxsize=128)
def _cached_query(search_term: str, limit: int) -> tuple:
    """Cached synchronous fetch (returns tuple for hashability)."""
    params = {
        "search": f'indications_and_usage:"{search_term}" AND openfda.product_type:"HUMAN PRESCRIPTION DRUG"',
        "limit": limit,
    }
    try:
        resp = httpx.get(_BASE, params=params, timeout=8)
        if resp.status_code != 200:
            return ()
        data = resp.json()
        results = data.get("results", [])

        drugs = []
        seen_generics = set()
        for r in results:
            d = _extract_drug(r)
            if d is None:
                continue
            # Deduplicate by generic name
            key = (d["generic_name"] or "").lower()
            if key in seen_generics:
                continue
            seen_generics.add(key)
            drugs.append(d)

        return tuple(drugs)
    except Exception:
        return ()


async def get_drugs_for_condition(condition: str, limit: int = 5) -> list[dict]:
    """
    Query openFDA for FDA-approved drugs used to treat a condition.

    Returns a list of drug dicts with keys:
        brand_name, generic_name, route, manufacturer,
        indications, adverse_reactions, drug_interactions, warnings
    """
    search_term = CONDITION_SEARCH_TERMS.get(condition)
    if not search_term:
        return []

    # Use cached sync call (openFDA is fast, <1s typically)
    results = _cached_query(search_term, min(limit * 2, 10))
    return list(results)[:limit]
