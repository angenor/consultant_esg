"""Schemas Pydantic pour le module ESG (scores, référentiels)."""

import uuid
from datetime import datetime

from pydantic import BaseModel


# ── Responses ──


class ESGScoreResponse(BaseModel):
    id: uuid.UUID
    entreprise_id: uuid.UUID
    referentiel_id: uuid.UUID | None
    score_e: float | None
    score_s: float | None
    score_g: float | None
    score_global: float | None
    details_json: dict
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ESGScoreSummary(BaseModel):
    """Version allégée pour les listes."""
    id: uuid.UUID
    referentiel_id: uuid.UUID | None
    referentiel_nom: str | None = None
    referentiel_code: str | None = None
    score_e: float | None
    score_s: float | None
    score_g: float | None
    score_global: float | None
    niveau: str | None = None
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}
