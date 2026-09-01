from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class NamasteTerm(Base):
    __tablename__ = "namaste_terms"
    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    system: Mapped[str] = mapped_column(String(200), default="https://namaste.gov.in/sat-e")
    title_en: Mapped[str] = mapped_column(String(300), index=True)
    title_sanskrit: Mapped[str] = mapped_column(String(300), default="")
    title_tamil: Mapped[str] = mapped_column(String(300), default="")
    tradition: Mapped[str] = mapped_column(String(50), index=True)
    definition: Mapped[str] = mapped_column(Text, default="")


class Icd11Term(Base):
    __tablename__ = "icd11_tm2_terms"
    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    system: Mapped[str] = mapped_column(String(200), default="http://id.who.int/icd/release/11/mms")
    title: Mapped[str] = mapped_column(String(300), index=True)
    chapter: Mapped[str] = mapped_column(String(80), default="Chapter 26 TM2")
    biomedical_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    biomedical_title: Mapped[str | None] = mapped_column(String(300), nullable=True)


class ConceptMapLink(Base):
    __tablename__ = "concept_map"
    __table_args__ = (UniqueConstraint("namaste_code", "icd11_code", name="uq_concept_map_pair"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    namaste_code: Mapped[str] = mapped_column(ForeignKey("namaste_terms.code"), index=True)
    icd11_code: Mapped[str] = mapped_column(ForeignKey("icd11_tm2_terms.code"), index=True)
    equivalence: Mapped[str] = mapped_column(String(20))
    similarity: Mapped[float] = mapped_column(Float)
    mapping_method: Mapped[str] = mapped_column(String(30))


class ConditionRecord(Base):
    __tablename__ = "conditions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(String(80), index=True)
    encounter_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resource_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
