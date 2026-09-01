"""FHIR R4 terminology demo. NAMASTE/ABDM connectivity is deliberately mocked."""
import json
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db import get_db
from app.models import ConceptMapLink, ConditionRecord, Icd11Term, NamasteTerm
from app.schemas import ConditionCreate
from app.services.fhir import codesystem_resource, conceptmap_resource, condition_resource
from app.services.mapping import mapping_rows

settings = get_settings()
app = FastAPI(title="NAMASTE ↔ ICD-11 TM2 FHIR Terminology Service", version="0.1.0", openapi_url="/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
bearer = HTTPBearer(auto_error=False)


def demo_auth(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    """Mock ABHA-style bearer check; never represents an ABDM integration."""
    if credentials and credentials.scheme.lower() == "bearer":
        return {"sub": "demo-clinician", "mode": "mock"}
    return {"sub": "anonymous-demo", "mode": "mock"}


@app.get("/health")
def health():
    return {"status": "ok", "storage": "SQLite (demo default)", "terminology_data": "mock"}


@app.get("/CodeSystem/namaste")
def namaste_codesystem(db: Session = Depends(get_db)):
    return codesystem_resource(list(db.scalars(select(NamasteTerm).order_by(NamasteTerm.code)).all()))


@app.get("/ConceptMap/namaste-icd11")
def full_conceptmap(db: Session = Depends(get_db)):
    rows = db.execute(select(ConceptMapLink, Icd11Term).join(Icd11Term, ConceptMapLink.icd11_code == Icd11Term.code)
                      .order_by(ConceptMapLink.namaste_code, ConceptMapLink.similarity.desc())).all()
    return conceptmap_resource(rows)


@app.get("/ConceptMap/{namaste_code}")
def code_conceptmap(namaste_code: str, db: Session = Depends(get_db)):
    if not db.get(NamasteTerm, namaste_code):
        raise HTTPException(404, f"Unknown NAMASTE code: {namaste_code}")
    rows = mapping_rows(db, namaste_code)
    return conceptmap_resource(rows, namaste_code)


@app.get("/search")
def search(q: str = Query(min_length=1, max_length=100), limit: int = Query(default=25, ge=1, le=50),
           db: Session = Depends(get_db)):
    """One joined search: every row includes NAMASTE and its ICD-11 mapping, if available."""
    needle = f"%{q.strip()}%"
    rows = db.execute(
        select(NamasteTerm, ConceptMapLink, Icd11Term)
        .outerjoin(ConceptMapLink, NamasteTerm.code == ConceptMapLink.namaste_code)
        .outerjoin(Icd11Term, ConceptMapLink.icd11_code == Icd11Term.code)
        .where(or_(NamasteTerm.title_en.ilike(needle), NamasteTerm.title_sanskrit.ilike(needle),
                   NamasteTerm.title_tamil.ilike(needle), NamasteTerm.code.ilike(needle),
                   Icd11Term.title.ilike(needle), Icd11Term.code.ilike(needle)))
        .order_by(NamasteTerm.code)
        .limit(limit)
    ).all()
    return {"query": q, "results": [{
        "namaste_code": source.code,
        "namaste_title": source.title_en,
        "namaste_native_title": source.title_sanskrit or source.title_tamil or None,
        "system": source.tradition,
        "icd11_tm2_code": target.code if target else None,
        "icd11_tm2_title": target.title if target else None,
        "equivalence": link.equivalence if link else "unmatched",
    } for source, link, target in rows]}


@app.post("/Condition", status_code=201)
def create_condition(payload: ConditionCreate, db: Session = Depends(get_db), _auth=Depends(demo_auth)):
    term = db.get(NamasteTerm, payload.namaste_code)
    if not term:
        raise HTTPException(422, f"Unknown NAMASTE code: {payload.namaste_code}")
    mappings = mapping_rows(db, term.code)
    if not mappings:
        raise HTTPException(422, f"No TM2 mapping available for {term.code}")
    record = ConditionRecord(patient_id=payload.patient_id, encounter_id=payload.encounter_id, resource_json="{}")
    db.add(record); db.flush()
    resource = condition_resource(record.id, payload.patient_id, payload.encounter_id, term, mappings,
                                  payload.clinical_status, payload.note)
    record.resource_json = json.dumps(resource)
    db.commit()
    return resource


@app.get("/Condition/{condition_id}")
def get_condition(condition_id: int, db: Session = Depends(get_db)):
    record = db.get(ConditionRecord, condition_id)
    if not record:
        raise HTTPException(404, "Condition not found")
    return json.loads(record.resource_json)
