"""
CMS Marketplace PUF Data Loader

Loads plan_attributes_PUF.csv and Rate_PUF.csv from data/,
provides search and lookup functions for marketplace plan comparison.

Data is lazy-loaded on first access and cached in memory.
"""

import re
import pandas as pd
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

# Module-level caches
_plan_attrs: pd.DataFrame | None = None
_rate_index: pd.DataFrame | None = None


def _parse_dollars(val: str) -> float | None:
    """Parse dollar strings like '$6,500' → 6500.0."""
    if not isinstance(val, str):
        return None
    m = re.search(r"\$([\d,]+(?:\.\d+)?)", val)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def _parse_coinsurance(val: str) -> float | None:
    """Parse coinsurance strings like '30.00%' → 0.30."""
    if not isinstance(val, str):
        return None
    m = re.search(r"([\d.]+)%", val)
    if m:
        return round(float(m.group(1)) / 100, 4)
    return None


def _load_plan_attributes() -> pd.DataFrame:
    """Load and parse plan_attributes_PUF.csv."""
    cols = [
        "StandardComponentId", "PlanMarketingName",
        "IssuerMarketPlaceMarketingName", "MetalLevel", "PlanType",
        "DentalOnlyPlan", "MarketCoverage", "CSRVariationType",
        "TEHBDedInnTier1Individual", "TEHBInnTier1IndividualMOOP",
        "TEHBDedInnTier1Coinsurance", "IsHSAEligible", "StateCode",
    ]
    path = _DATA_DIR / "plan_attributes_PUF.csv"
    df = pd.read_csv(path, usecols=cols, dtype=str, encoding="utf-8-sig")

    # Filter: medical individual plans, standard (non-CSR) variants only
    df = df[df["DentalOnlyPlan"] == "No"]
    df = df[df["MarketCoverage"] == "Individual"]
    df = df[df["CSRVariationType"].str.startswith("Standard", na=False)]

    # Deduplicate: same plan appears as both On/Off Exchange variants
    df = df.drop_duplicates(subset=["StandardComponentId"], keep="first")

    # Parse dollar / percentage fields
    df["deductible"] = df["TEHBDedInnTier1Individual"].apply(_parse_dollars)
    df["oop_max"] = df["TEHBInnTier1IndividualMOOP"].apply(_parse_dollars)
    df["coinsurance"] = df["TEHBDedInnTier1Coinsurance"].apply(_parse_coinsurance)

    # Defaults for missing values
    df["deductible"] = df["deductible"].fillna(0.0)
    df["oop_max"] = df["oop_max"].fillna(8700.0)
    df["coinsurance"] = df["coinsurance"].fillna(0.20)

    # Rename for cleaner access
    df = df.rename(columns={
        "StandardComponentId": "plan_id",
        "PlanMarketingName": "plan_name",
        "IssuerMarketPlaceMarketingName": "issuer",
        "MetalLevel": "metal_level",
        "PlanType": "plan_type",
        "StateCode": "state",
        "IsHSAEligible": "is_hsa_eligible",
    })

    # Clean up metal level capitalization
    df["metal_level"] = df["metal_level"].str.strip().str.title()

    df = df[["plan_id", "plan_name", "issuer", "metal_level", "plan_type",
             "state", "deductible", "oop_max", "coinsurance", "is_hsa_eligible"]]

    return df.reset_index(drop=True)


def _age_to_rate_age(age: int) -> str:
    """Convert numeric age to Rate PUF age string."""
    if age < 15:
        return "0-14"
    elif age >= 64:
        return "64 and over"
    else:
        return str(age)


def _load_rate_index() -> pd.DataFrame:
    """Load Rate_PUF.csv in chunks, average premiums per (PlanId, Age)."""
    path = _DATA_DIR / "Rate_PUF.csv"
    cols = ["PlanId", "StateCode", "Age", "Tobacco", "IndividualRate"]

    chunks = []
    for chunk in pd.read_csv(path, usecols=cols, dtype=str,
                             chunksize=200_000, encoding="utf-8-sig"):
        # Filter out tobacco-specific rows and family option
        chunk = chunk[chunk["Tobacco"] != "Tobacco User/Non-Tobacco User"]
        chunk = chunk[chunk["Age"] != "Family Option"]
        chunk["IndividualRate"] = pd.to_numeric(chunk["IndividualRate"],
                                                errors="coerce")
        chunk = chunk.dropna(subset=["IndividualRate"])
        chunks.append(chunk[["PlanId", "StateCode", "Age", "IndividualRate"]])

    df = pd.concat(chunks, ignore_index=True)

    # Average across rating areas per (PlanId, Age)
    df = df.groupby(["PlanId", "StateCode", "Age"], as_index=False).agg(
        monthly_premium=("IndividualRate", "mean")
    )
    df["monthly_premium"] = df["monthly_premium"].round(2)

    return df


def _ensure_loaded():
    """Lazy-load both PUF files on first access."""
    global _plan_attrs, _rate_index

    if _plan_attrs is not None:
        return

    _plan_attrs = _load_plan_attributes()
    _rate_index = _load_rate_index()


def get_available_states() -> list[str]:
    """Return sorted list of state codes with marketplace plans."""
    _ensure_loaded()
    return sorted(_plan_attrs["state"].unique().tolist())


def search_plans(state: str, metal_level: str | None = None,
                 age: int = 45) -> list[dict]:
    """Search marketplace plans for a state, optionally filtered by metal level.

    Returns list of plan dicts with age-rated premium included.
    """
    _ensure_loaded()

    df = _plan_attrs[_plan_attrs["state"] == state.upper()]

    if metal_level and metal_level.lower() != "all":
        df = df[df["metal_level"].str.lower() == metal_level.lower()]

    # Look up premiums for the given age
    rate_age = _age_to_rate_age(age)
    rates = _rate_index[
        (_rate_index["StateCode"] == state.upper()) &
        (_rate_index["Age"] == rate_age)
    ][["PlanId", "monthly_premium"]]

    # Join plans with rates
    merged = df.merge(rates, left_on="plan_id", right_on="PlanId", how="inner")

    # Sort by premium
    merged = merged.sort_values("monthly_premium")

    result = []
    for _, row in merged.iterrows():
        result.append({
            "plan_id": row["plan_id"],
            "plan_name": row["plan_name"],
            "issuer": row["issuer"],
            "metal_level": row["metal_level"],
            "plan_type": row["plan_type"],
            "deductible": row["deductible"],
            "oop_max": row["oop_max"],
            "coinsurance": row["coinsurance"],
            "monthly_premium": row["monthly_premium"],
            "is_hsa_eligible": row["is_hsa_eligible"] == "Yes",
        })

    return result


def get_plan_with_premium(plan_id: str, state: str,
                          age: int) -> dict | None:
    """Get full plan dict with age-rated premium for a specific plan."""
    _ensure_loaded()

    plan_rows = _plan_attrs[_plan_attrs["plan_id"] == plan_id]
    if plan_rows.empty:
        return None

    plan = plan_rows.iloc[0]

    rate_age = _age_to_rate_age(age)
    rate_rows = _rate_index[
        (_rate_index["PlanId"] == plan_id) &
        (_rate_index["StateCode"] == state.upper()) &
        (_rate_index["Age"] == rate_age)
    ]

    premium = rate_rows.iloc[0]["monthly_premium"] if not rate_rows.empty else 0.0

    return {
        "plan_id": plan["plan_id"],
        "plan_name": plan["plan_name"],
        "issuer": plan["issuer"],
        "metal_level": plan["metal_level"],
        "plan_type": plan["plan_type"],
        "deductible": float(plan["deductible"]),
        "oop_max": float(plan["oop_max"]),
        "coinsurance": float(plan["coinsurance"]),
        "monthly_premium": float(premium),
        "is_hsa_eligible": plan["is_hsa_eligible"] == "Yes",
    }
