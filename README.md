# CareGraph

### Clinical-Financial Digital Twin

> A voice-powered financial simulation engine that turns your health profile into a navigable, interactive cost map — so you can see the financial future of your health before it happens.

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

Copy `.env.example` to `.env` and fill in:

```
GROQ_API_KEY=
DEEPGRAM_API_KEY=
SUPABASE_URL=
SUPABASE_ANON_KEY=
```

## Architecture

```
Frontend (React + Cytoscape.js + Deepgram Voice)
        ↕
FastAPI Backend (Voice Agent + Simulation Engine + Plan Comparator)
        ↕
Supabase (users, sessions) + MEPS/CMS Data (parquet/DB)
```

## Data Sources

- **MEPS** — Medical Expenditure Panel Survey (ahrq.gov)
- **CMS** — Chronic Conditions Dashboard (cms.gov)

Every cost estimate and progression probability is traceable to a public federal dataset.
