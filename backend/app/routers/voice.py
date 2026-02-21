from fastapi import APIRouter
from pydantic import BaseModel

from app.services.voice_agent import (
    parse_patient_input,
    interpret_scenario,
    generate_explanation,
)

router = APIRouter()


class TextInput(BaseModel):
    text: str
    current_conditions: list[str] = []


class ExplanationRequest(BaseModel):
    graph_data: dict
    question: str


@router.post("/parse-profile")
async def parse_profile(input: TextInput):
    """Parse natural language patient description into structured profile."""
    result = await parse_patient_input(input.text)
    return result


@router.post("/parse-scenario")
async def parse_scenario(input: TextInput):
    """Parse a what-if question into intervention parameters."""
    result = await interpret_scenario(input.text, input.current_conditions)
    return result


@router.post("/explain")
async def explain(request: ExplanationRequest):
    """Generate natural language explanation of simulation results."""
    explanation = await generate_explanation(request.graph_data, request.question)
    return {"explanation": explanation}
