from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.models.patient import PatientProfile
from app.simulation.engine import simulate_pathway
from app.data.puf_loader import get_available_states, search_plans, get_plan_with_premium

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


class MarketplacePlanCompareRequest(BaseModel):
    age: int
    sex: str
    conditions: list[str]
    interventions: list[str] = []
    state: str
    plan_ids: list[str]
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
        graph = await simulate_pathway(
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


@router.get("/states")
async def list_states():
    """Return all states with available marketplace plans."""
    return {"states": get_available_states()}


@router.get("/search")
async def search_marketplace_plans(
    state: str = Query(..., description="Two-letter state code"),
    metal_level: str | None = Query(None, description="Metal level filter"),
    age: int = Query(45, description="Age for premium rating"),
):
    """Search marketplace plans for a state with optional metal level filter."""
    plans = search_plans(state=state, metal_level=metal_level, age=age)
    return {"plans": plans, "count": len(plans)}


@router.post("/marketplace-compare")
async def compare_marketplace_plans(request: MarketplacePlanCompareRequest):
    """Compare real marketplace plans using PUF data + MEPS simulation."""
    results = []
    for plan_id in request.plan_ids:
        plan_data = get_plan_with_premium(
            plan_id=plan_id, state=request.state, age=request.age
        )
        if plan_data is None:
            continue

        profile = PatientProfile(
            age=request.age,
            sex=request.sex,
            conditions=request.conditions,
            insurance_type=plan_data["plan_type"],
            deductible=plan_data["deductible"],
            coinsurance=plan_data["coinsurance"],
            oop_max=plan_data["oop_max"],
        )
        graph = await simulate_pathway(
            profile=profile,
            interventions=request.interventions,
            time_horizon_years=request.time_horizon_years,
        )
        annual_premium = plan_data["monthly_premium"] * 12
        results.append({
            "plan": plan_data,
            "graph": graph,
            "total_with_premium": round(
                graph.total_5yr_oop + annual_premium * request.time_horizon_years, 2
            ),
        })

    return {"plan_comparisons": results}
