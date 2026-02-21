from fastapi import APIRouter
from pydantic import BaseModel

from app.models.patient import PatientProfile
from app.simulation.engine import simulate_pathway

router = APIRouter()


class PlanConfig(BaseModel):
    name: str
    deductible: float
    coinsurance: float
    oop_max: float
    monthly_premium: float


class PlanCompareRequest(BaseModel):
    age: int
    sex: str
    conditions: list[str]
    interventions: list[str] = []
    plans: list[PlanConfig]
    time_horizon_years: int = 5


@router.post("/compare")
async def compare_plans(request: PlanCompareRequest):
    """Compare the same care pathway across different insurance plans."""
    results = []
    for plan in request.plans:
        profile = PatientProfile(
            age=request.age,
            sex=request.sex,
            conditions=request.conditions,
            insurance_type=plan.name,
            deductible=plan.deductible,
            coinsurance=plan.coinsurance,
            oop_max=plan.oop_max,
        )
        graph = simulate_pathway(
            profile=profile,
            interventions=request.interventions,
            time_horizon_years=request.time_horizon_years,
        )
        annual_premium = plan.monthly_premium * 12
        results.append({
            "plan": plan.model_dump(),
            "graph": graph,
            "total_with_premium": round(
                graph.total_5yr_oop + annual_premium * request.time_horizon_years, 2
            ),
        })

    return {"plan_comparisons": results}
