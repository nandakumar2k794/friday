"""Load the checked-in curated 50-term NAMASTE ↔ ICD-11 fixture into the demo DB."""
import csv
import json
import sys
from pathlib import Path
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db import Base, SessionLocal, engine
from app.models import ConceptMapLink, ConditionRecord, Icd11Term, NamasteTerm
from app.services.embeddings import EmbeddingIndex
from app.services.fhir import condition_resource
from app.services.mapping import mapping_rows

FIXTURE = ROOT / "data" / "namaste_icd11_curated.csv"


def read_fixture() -> list[dict[str, str]]:
    with FIXTURE.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    if len(rows) != 50:
        raise ValueError(f"Expected exactly 50 curated rows in {FIXTURE.name}; found {len(rows)}")
    return rows


def main():
    rows = read_fixture()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # These values come directly from the checked-in curated CSV; no random data is generated.
        for row in rows:
            db.add(NamasteTerm(code=row["namaste_code"], title_en=row["namaste_title_en"],
                               title_sanskrit=row["namaste_title_sanskrit"], title_tamil="",
                               tradition=row["system"], definition="Curated SIH demo fixture; not an official release."))
        for code in sorted({row["icd11_tm2_code"] for row in rows}):
            row = next(item for item in rows if item["icd11_tm2_code"] == code)
            db.add(Icd11Term(code=code, title=row["icd11_tm2_title"], chapter="Mock ICD-11 TM2/biomedical fixture"))
        db.commit()
        if engine.dialect.name == "sqlite":
            db.execute(text("DROP TABLE IF EXISTS namaste_fts"))
            db.execute(text("DROP TABLE IF EXISTS icd11_tm2_fts"))
            db.execute(text("CREATE VIRTUAL TABLE namaste_fts USING fts5(code, title_en, title_sanskrit, title_tamil)"))
            db.execute(text("CREATE VIRTUAL TABLE icd11_tm2_fts USING fts5(code, title)"))
            for row in rows:
                db.execute(text("INSERT INTO namaste_fts VALUES (:code, :title, :sanskrit, '')"),
                           {"code": row["namaste_code"], "title": row["namaste_title_en"], "sanskrit": row["namaste_title_sanskrit"]})
            for term in db.query(Icd11Term).all():
                db.execute(text("INSERT INTO icd11_tm2_fts VALUES (:code, :title)"), {"code": term.code, "title": term.title})

        # CSV mappings are authoritative; the optional FAISS index never replaces supplied equivalence values.
        for row in rows:
            db.add(ConceptMapLink(namaste_code=row["namaste_code"], icd11_code=row["icd11_tm2_code"],
                                  equivalence=row["equivalence"], similarity=1.0, mapping_method="curated_csv"))
        db.commit()
        try:
            index = EmbeddingIndex("all-MiniLM-L6-v2")
            index.build([(term.code, term.title) for term in db.query(Icd11Term).all()], ROOT / "data" / "icd11_tm2.faiss")
            print("Built optional FAISS semantic index from curated TM2 titles.")
        except Exception as error:
            print(f"Optional FAISS semantic index skipped ({error}). Curated mappings are fully loaded.")

        for number, row in enumerate(rows[:8], 1):
            term = db.get(NamasteTerm, row["namaste_code"])
            resource = condition_resource(number, f"Patient/demo-{number:03d}", f"Encounter/demo-{number:03d}", term,
                                          mapping_rows(db, term.code), "active", "Curated mock encounter for live demo.")
            db.add(ConditionRecord(id=number, patient_id=f"Patient/demo-{number:03d}",
                                   encounter_id=f"Encounter/demo-{number:03d}", resource_json=json.dumps(resource)))
        db.commit()
        print(f"Initialized {len(rows)}/50 curated NAMASTE mappings and 8 demo Conditions.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
