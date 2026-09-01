from pydantic import BaseModel, Field


class ConditionCreate(BaseModel):
    patient_id: str = Field(examples=["Patient/demo-001"])
    namaste_code: str = Field(examples=["SAT-E-AYU-001"])
    encounter_id: str | None = Field(default=None, examples=["Encounter/demo-001"])
    clinical_status: str = Field(default="active", pattern="^(active|inactive|resolved)$")
    note: str | None = Field(default=None, max_length=500)
