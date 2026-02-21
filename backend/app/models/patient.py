from pydantic import BaseModel


class PatientProfile(BaseModel):
    age: int
    sex: str  # "M" or "F"
    conditions: list[str]  # e.g. ["pre-diabetes", "hypertension"]
    insurance_type: str  # e.g. "PPO", "HMO", "HDHP"
    deductible: float = 2000.0
    coinsurance: float = 0.20
    oop_max: float = 8000.0


class ScenarioRequest(BaseModel):
    profile: PatientProfile
    interventions: list[str] = []  # e.g. ["metformin", "lifestyle_change"]
    time_horizon_years: int = 5
