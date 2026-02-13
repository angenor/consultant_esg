"""Schemas Pydantic pour le module entreprises."""

import uuid
from datetime import datetime

from pydantic import BaseModel


# ---- Requests ----


class CreateEntrepriseRequest(BaseModel):
    nom: str
    secteur: str | None = None
    sous_secteur: str | None = None
    pays: str = "Côte d'Ivoire"
    ville: str | None = None
    effectifs: int | None = None
    chiffre_affaires: float | None = None
    devise: str = "XOF"
    description: str | None = None


class UpdateEntrepriseRequest(BaseModel):
    nom: str | None = None
    secteur: str | None = None
    sous_secteur: str | None = None
    pays: str | None = None
    ville: str | None = None
    effectifs: int | None = None
    chiffre_affaires: float | None = None
    devise: str | None = None
    description: str | None = None


# ---- Responses ----


class EntrepriseResponse(BaseModel):
    id: uuid.UUID
    nom: str
    secteur: str | None
    sous_secteur: str | None
    pays: str
    ville: str | None
    effectifs: int | None
    chiffre_affaires: float | None
    devise: str
    description: str | None
    profil_json: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
