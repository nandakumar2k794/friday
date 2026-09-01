import re
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models import ConceptMapLink, Icd11Term, NamasteTerm


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def create_mappings(db: Session, embedding_index=None) -> int:
    """Exact title pass followed by optional embedding similarity pass."""
    db.query(ConceptMapLink).delete()
    terms = list(db.scalars(select(Icd11Term)).all())
    by_title = {normalize_title(term.title): term for term in terms}
    settings = get_settings()
    made = 0
    for source in db.scalars(select(NamasteTerm)).all():
        exact = by_title.get(normalize_title(source.title_en))
        if exact:
            db.add(ConceptMapLink(namaste_code=source.code, icd11_code=exact.code,
                                  equivalence="equivalent", similarity=1.0, mapping_method="exact_title"))
            made += 1
            continue
        matches = embedding_index.query(source.title_en, settings.top_k_mappings) if embedding_index else []
        for target_code, similarity in matches:
            if similarity >= settings.similarity_threshold:
                db.add(ConceptMapLink(namaste_code=source.code, icd11_code=target_code,
                                      equivalence="related", similarity=similarity, mapping_method="embedding"))
                made += 1
    db.commit()
    return made


def mapping_rows(db: Session, namaste_code: str):
    return db.execute(
        select(ConceptMapLink, Icd11Term)
        .join(Icd11Term, ConceptMapLink.icd11_code == Icd11Term.code)
        .where(ConceptMapLink.namaste_code == namaste_code)
        .order_by(ConceptMapLink.similarity.desc())
    ).all()
