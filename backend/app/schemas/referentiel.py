"""Schemas for ReferentielESG admin API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReferentielCreateRequest(BaseModel):
    nom: str = Field(..., min_length=3, max_length=255)
    code: str = Field(..., pattern=r"^[a-z][a-z0-9_]+$", min_length=3, max_length=50)
    institution: str | None = Field(None, max_length=255)
    description: str | None = None
    region: str | None = Field(None, max_length=100)
    grille_json: dict = Field(..., description="Grille ESG avec piliers et critères")


class ReferentielUpdateRequest(BaseModel):
    nom: str | None = Field(None, min_length=3, max_length=255)
    institution: str | None = Field(None, max_length=255)
    description: str | None = None
    region: str | None = Field(None, max_length=100)
    grille_json: dict | None = None
    is_active: bool | None = None


class ReferentielResponse(BaseModel):
    id: uuid.UUID
    nom: str
    code: str
    institution: str | None
    description: str | None
    region: str | None
    grille_json: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScorePreviewRequest(BaseModel):
    reponses: dict = Field(..., description="Réponses aux critères de la grille")


class CritereScoreDetail(BaseModel):
    critere_id: str
    label: str
    score: float
    status: str  # "conforme", "partiel", "manquant"
    valeur: str | None = None


class PilierScoreDetail(BaseModel):
    poids_global: float
    score: float
    criteres: list[CritereScoreDetail]


class ScorePreviewResponse(BaseModel):
    score_global: float
    niveau: str
    piliers: dict[str, PilierScoreDetail]
