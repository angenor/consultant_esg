from pydantic import BaseModel
from uuid import UUID


class CreateApplicationRequest(BaseModel):
    fonds_id: UUID | None = None
    fonds_nom: str
    fonds_institution: str = ""
    url_candidature: str | None = None
    total_steps: int | None = None
    notes: str | None = None


class SaveProgressRequest(BaseModel):
    application_id: UUID
    form_data: dict = {}
    current_step: int = 0
    progress_pct: float | None = None


class FieldSuggestRequest(BaseModel):
    fonds_id: str | None = None
    field_name: str
    field_label: str
    context: str = ""


class ExtensionEventRequest(BaseModel):
    type: str  # "step_completed" | "form_submitted" | "error"
    application_id: UUID | None = None
    step: int | None = None
    progress_pct: float | None = None
    details: dict = {}
