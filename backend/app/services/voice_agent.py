"""
Voice Agent Service

Uses Groq (Llama 3) for intent parsing and natural language generation.
All numerical outputs come from the simulation engine — the LLM is only
used for the conversational interface, never for generating cost numbers.
"""

from groq import AsyncGroq
from app.config import GROQ_API_KEY

client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

SYSTEM_PROMPT = """You are CareGraph's voice assistant. You help patients understand
their health care costs through a clinical-financial digital twin.

Your role:
- Parse patient descriptions into structured profiles (age, sex, conditions, insurance)
- Interpret what-if questions about interventions and scenarios
- Explain simulation results in plain, empathetic language

CRITICAL RULES:
- NEVER invent or hallucinate cost numbers. All costs come from the simulation engine.
- When you need to present numbers, use the data provided in the context.
- Be empathetic but direct. Patients need clarity, not hedging.
- Keep responses concise — this is a voice interface."""


async def parse_patient_input(text: str) -> dict:
    """Parse natural language patient description into a structured profile."""
    if client is None:
        return {"error": "GROQ_API_KEY not configured"}

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + """

Extract the patient profile from the user's description. Return JSON with:
{
  "age": int,
  "sex": "M" or "F",
  "conditions": ["condition_1", "condition_2"],
  "insurance_type": "PPO" | "HMO" | "HDHP" | "unknown"
}

Use these condition keys: pre-diabetes, type_2_diabetes, hypertension,
high_cholesterol, ckd_stage_2, ckd_stage_3, retinopathy, neuropathy,
cad, heart_failure.

Return ONLY valid JSON, no other text."""},
            {"role": "user", "content": text},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    import json
    return json.loads(response.choices[0].message.content)


async def interpret_scenario(text: str, current_conditions: list[str]) -> dict:
    """Parse a what-if question into intervention parameters."""
    if client is None:
        return {"error": "GROQ_API_KEY not configured"}

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + f"""

The patient currently has: {', '.join(current_conditions)}

Parse the user's what-if question. Return JSON with:
{{
  "intent": "add_intervention" | "remove_intervention" | "compare_plans" | "explain_risk" | "general_question",
  "interventions": ["intervention_1"],
  "plan_comparison": {{"plan_a": "...", "plan_b": "..."}} // only if intent is compare_plans
}}

Available interventions: metformin, sglt2_inhibitor, statin, ace_inhibitor, lifestyle_change

Return ONLY valid JSON, no other text."""},
            {"role": "user", "content": text},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    import json
    return json.loads(response.choices[0].message.content)


async def generate_explanation(graph_data: dict, question: str) -> str:
    """Generate a natural language explanation of simulation results."""
    if client is None:
        return "Voice agent not configured. Set GROQ_API_KEY."

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + """

Explain the simulation results to the patient. Use the provided data
for all numbers. Keep it under 3 sentences for voice output.
Be warm but clear."""},
            {"role": "user", "content": f"Question: {question}\n\nSimulation data: {graph_data}"},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content
