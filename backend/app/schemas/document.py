"""Schemas Pydantic pour le module documents."""

import uuid
from datetime import datetime

from pydantic import BaseModel


# ---- Responses ----


class DocumentResponse(BaseModel):
    id: uuid.UUID
    entreprise_id: uuid.UUID
    nom_fichier: str
    type_mime: str | None
    taille: int | None
    metadata_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetailResponse(DocumentResponse):
    texte_extrait: str | None
    chunk_count: int = 0
