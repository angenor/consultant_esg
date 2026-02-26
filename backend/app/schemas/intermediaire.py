"""Schemas for Intermediaire API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class IntermediaireCreateRequest(BaseModel):
    fonds_id: uuid.UUID
    nom: str = Field(..., min_length=2, max_length=200)
    type: str = Field(..., max_length=50)
    pays: str | None = Field(None, max_length=100)
    ville: str | None = Field(None, max_length=100)
    email: str | None = Field(None, max_length=200)
    telephone: str | None = Field(None, max_length=50)
    adresse: str | None = None
    site_web: str | None = Field(None, max_length=500)
    url_formulaire: str | None = Field(None, max_length=500)
    type_soumission: str | None = Field(None, max_length=30)
    instructions_soumission: str | None = None
    documents_requis: list | None = None
    etapes_specifiques: list | None = None
    delai_traitement: str | None = Field(None, max_length=50)
    est_recommande: bool = False
    notes: str | None = None


class IntermediaireUpdateRequest(BaseModel):
    fonds_id: uuid.UUID | None = None
    nom: str | None = Field(None, min_length=2, max_length=200)
    type: str | None = Field(None, max_length=50)
    pays: str | None = Field(None, max_length=100)
    ville: str | None = Field(None, max_length=100)
    email: str | None = Field(None, max_length=200)
    telephone: str | None = Field(None, max_length=50)
    adresse: str | None = None
    site_web: str | None = Field(None, max_length=500)
    url_formulaire: str | None = Field(None, max_length=500)
    type_soumission: str | None = Field(None, max_length=30)
    instructions_soumission: str | None = None
    documents_requis: list | None = None
    etapes_specifiques: list | None = None
    delai_traitement: str | None = Field(None, max_length=50)
    est_recommande: bool | None = None
    notes: str | None = None
    is_active: bool | None = None


class IntermediaireResponse(BaseModel):
    id: uuid.UUID
    fonds_id: uuid.UUID
    nom: str
    type: str
    pays: str | None
    ville: str | None
    email: str | None
    telephone: str | None
    adresse: str | None
    site_web: str | None
    url_formulaire: str | None
    type_soumission: str | None
    instructions_soumission: str | None
    documents_requis: list | None
    etapes_specifiques: list | None
    delai_traitement: str | None
    est_recommande: bool
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
