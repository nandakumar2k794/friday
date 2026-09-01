# NAMASTE ↔ ICD-11 TM2 FHIR Terminology Demo

Demo-first prototype for SIH25026. It ingests a checked-in, curated 50-term NAMASTE ↔ ICD-11 fixture, maps diagnoses, and saves dual-coded FHIR R4 `Condition` resources.

## Quick start (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python scripts/init.py
uvicorn app.main:app --reload
```

The API is at `http://127.0.0.1:8000`; interactive documentation is at `/docs`.

To start the optional demo UI in a second PowerShell window:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite (normally `http://localhost:5173`) and search `vata`.

## Demo API walkthrough

```powershell
# 1. Autocomplete across both terminologies
curl.exe "http://127.0.0.1:8000/search?q=vata"

# 2. Inspect one NAMASTE → TM2 FHIR R4 ConceptMap
curl.exe "http://127.0.0.1:8000/ConceptMap/SR11"

# 3. Save a dual-coded FHIR R4 Condition
curl.exe -X POST "http://127.0.0.1:8000/Condition" -H "Content-Type: application/json" -H "Authorization: Bearer demo-abha-token" -d "{\"patient_id\":\"Patient/demo-live-001\",\"encounter_id\":\"Encounter/demo-live-001\",\"namaste_code\":\"SR11\"}"
```

The saved Condition's `code.coding` starts with NAMASTE and includes its TM2 target plus a mock biomedical ICD-11 coding where available.

## Tests

```powershell
python -m pytest -q
```

Before the walkthrough, initialize the database then run the judge-friendly coverage report:

```powershell
python scripts/init.py
python -m pytest -s tests/test_search_coverage.py
```

It prints one `PASS`/`FAIL` row for each curated CSV term and ends with `50/50 pass` when the API search is working.

## Project layout

```text
app/        FastAPI API, database models, mapping and FHIR builders
data/       Mock NAMASTE and ICD-11 TM2 CSV source data
scripts/    Repeatable database/data initialization
tests/      FHIR shape tests
frontend/   Minimal React + Tailwind demo client
```

## Storage choice

This repository **defaults to SQLite plus FAISS** for the one-day demo. This deliberately avoids spending setup time on PostgreSQL/pgvector. `DATABASE_URL` supports PostgreSQL through SQLAlchemy, but pgvector persistence is not implemented in this prototype.

## Known limitations / what is mocked

- `data/namaste_icd11_curated.csv` is a curated **demo fixture**, not an official Ministry/WHO terminology release.
- No real ABDM, ABHA, NAMASTE, or WHO ICD API is called. JWT authentication is a local demo stub only.
- Mapping suggestions are lexical/embedding-assisted prototype results and require clinical terminology governance before use.
- `Condition` resources are stored locally only; this is not an EMR/ABDM production integration.
- The frontend is a minimal React/Tailwind demo client, not a clinical user interface.
