from fastapi import APIRouter

from app.models.patient import PatientProfile, ScenarioRequest
from app.models.graph import CarePathwayGraph
from app.simulation.engine import simulate_pathway

router = APIRouter()


@router.post("/pathway", response_model=CarePathwayGraph)
async def generate_pathway(request: ScenarioRequest):
    """Generate a care pathway graph for the given patient profile and interventions."""
    graph = await simulate_pathway(
        profile=request.profile,
        interventions=request.interventions,
        time_horizon_years=request.time_horizon_years,
        symptom_conditions=request.symptom_conditions,
        unmapped_conditions=request.unmapped_conditions,
    )
    return graph


@router.post("/compare")
async def compare_scenarios(
    profile: PatientProfile,
    scenarios: list[list[str]],  # list of intervention lists
    time_horizon_years: int = 5,
):
    """Compare multiple intervention scenarios side by side."""
    results = []
    for interventions in scenarios:
        graph = await simulate_pathway(
            profile=profile,
            interventions=interventions,
            time_horizon_years=time_horizon_years,
        )
        results.append({
            "interventions": interventions,
            "graph": graph,
        })
    return {"scenarios": results}
