from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import voice, simulation, plans

app = FastAPI(title="CareGraph API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice.router, prefix="/api/voice", tags=["voice"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["simulation"])
app.include_router(plans.router, prefix="/api/plans", tags=["plans"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
