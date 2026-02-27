import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class CandidatureCreateRequest(BaseModel):
    fonds_id: uuid.UUID | None = None
    fonds_nom: str = Field(..., min_length=1, max_length=255)
    fonds_institution: str = ""
    url_candidature: str | None = None
    total_steps: int | None = None
    notes: str | None = None
    montant_demande: float | None = None


class CandidatureUpdateRequest(BaseModel):
    status: str | None = Field(None, max_length=50)
    notes: str | None = None
    current_step: int | None = None
    progress_pct: float | None = None
    montant_demande: float | None = None


class HistoryEntryRequest(BaseModel):
    action: str = Field(..., min_length=1, max_length=255)
    details: str | None = None


class TimelineStep(BaseModel):
    title: str
    status: str  # done, current, pending
    date: str | None = None
    estimated: str | None = None
    description: str | None = None
    actions: list[dict] = []


class CandidatureListItem(BaseModel):
    id: uuid.UUID
    fonds_id: uuid.UUID | None
    fonds_nom: str
    fonds_institution: str
    status: str
    progress_pct: float
    current_step: int
    total_steps: int | None
    url_candidature: str | None
    notes: str | None
    started_at: datetime
    submitted_at: datetime | None
    updated_at: datetime
    next_step: str | None = None
    dossier_id: uuid.UUID | None = None
    documents_count: int = 0

    model_config = {"from_attributes": True}


class CandidatureDetail(CandidatureListItem):
    form_data: dict | None = None
    timeline: list[TimelineStep] = []
    documents: list[dict] = []
    history: list[dict] = []


class CandidatureStats(BaseModel):
    total: int = 0
    brouillon: int = 0
    en_cours: int = 0
    soumise: int = 0
    acceptee: int = 0
    refusee: int = 0
    abandonnee: int = 0
