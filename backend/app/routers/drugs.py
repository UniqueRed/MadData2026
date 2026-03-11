from fastapi import APIRouter, Query

from app.services.openfda import get_drugs_for_condition

router = APIRouter()


@router.get("/by-condition")
async def drugs_by_condition(
    condition: str = Query(..., description="Condition key (e.g. 'diabetes', 'hypertension')"),
    limit: int = Query(3, ge=1, le=5),
):
    """
    Return FDA-approved drugs for a condition via openFDA.
    Results are cached in-memory after the first call per condition.
    """
    drugs = await get_drugs_for_condition(condition, limit)
    return {"condition": condition, "drugs": drugs, "count": len(drugs)}
