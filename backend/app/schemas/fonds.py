"""Schemas for FondsVert admin API."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class FondsCreateRequest(BaseModel):
    nom: str = Field(..., min_length=3, max_length=255)
    institution: str | None = Field(None, max_length=255)
    type: str | None = Field(None, max_length=50)
    referentiel_id: uuid.UUID | None = None
    montant_min: float | None = None
    montant_max: float | None = None
    devise: str = Field("USD", max_length=10)
    secteurs_json: list | None = None
    pays_eligibles: list | None = None
    criteres_json: dict | None = None
    date_limite: date | None = None
    url_source: str | None = Field(None, max_length=500)
    mode_acces: str | None = Field(None, max_length=30)


class FondsUpdateRequest(BaseModel):
    nom: str | None = Field(None, min_length=3, max_length=255)
    institution: str | None = Field(None, max_length=255)
    type: str | None = Field(None, max_length=50)
    referentiel_id: uuid.UUID | None = None
    montant_min: float | None = None
    montant_max: float | None = None
    devise: str | None = Field(None, max_length=10)
    secteurs_json: list | None = None
    pays_eligibles: list | None = None
    criteres_json: dict | None = None
    date_limite: date | None = None
    url_source: str | None = Field(None, max_length=500)
    mode_acces: str | None = Field(None, max_length=30)
    is_active: bool | None = None


class FondsResponse(BaseModel):
    id: uuid.UUID
    nom: str
    institution: str | None
    type: str | None
    referentiel_id: uuid.UUID | None
    montant_min: float | None
    montant_max: float | None
    devise: str
    secteurs_json: list | None
    pays_eligibles: list | None
    criteres_json: dict | None
    date_limite: date | None
    url_source: str | None
    mode_acces: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
