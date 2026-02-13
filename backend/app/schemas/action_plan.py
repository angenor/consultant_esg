"""Schemas Pydantic pour le module Plan d'Action (Module 6)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# ── Requests ──


class CreateActionPlanRequest(BaseModel):
    entreprise_id: uuid.UUID
    titre: str | None = None
    horizon: str = Field("12_mois", pattern="^(6_mois|12_mois|24_mois)$")
    referentiel_code: str | None = None
    score_cible: float | None = Field(None, ge=0, le=100)


class AddActionItemRequest(BaseModel):
    titre: str
    description: str | None = None
    priorite: str = Field("moyen_terme", pattern="^(quick_win|moyen_terme|long_terme)$")
    pilier: str | None = Field(None, pattern="^(environnement|social|gouvernance)$")
    critere_id: str | None = None
    echeance: date | None = None
    impact_score_estime: float | None = Field(None, ge=0)
    cout_estime: float | None = Field(None, ge=0)
    benefice_estime: float | None = Field(None, ge=0)


class UpdateActionItemRequest(BaseModel):
    statut: str = Field(..., pattern="^(a_faire|en_cours|fait)$")


# ── Responses ──


class ActionItemResponse(BaseModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    titre: str
    description: str | None = None
    priorite: str | None = None
    pilier: str | None = None
    critere_id: str | None = None
    statut: str
    echeance: date | None = None
    impact_score_estime: float | None = None
    cout_estime: float | None = None
    benefice_estime: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ActionPlanSummary(BaseModel):
    id: uuid.UUID
    entreprise_id: uuid.UUID
    titre: str
    horizon: str | None = None
    referentiel_id: uuid.UUID | None = None
    score_initial: float | None = None
    score_cible: float | None = None
    nb_items: int = 0
    nb_fait: int = 0
    pourcentage: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class ActionPlanDetail(BaseModel):
    id: uuid.UUID
    entreprise_id: uuid.UUID
    titre: str
    horizon: str | None = None
    referentiel_id: uuid.UUID | None = None
    score_initial: float | None = None
    score_cible: float | None = None
    items: list[ActionItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProgressionInfo(BaseModel):
    total_items: int
    fait: int
    en_cours: int
    a_faire: int
    pourcentage_completion: int


class ImpactInfo(BaseModel):
    score_estime: float
    score_gagne: float


class EcheanceInfo(BaseModel):
    item_id: uuid.UUID
    titre: str
    echeance: date | None = None
    priorite: str | None = None
    statut: str
    en_retard: bool = False


class ProgressResponse(BaseModel):
    plan_id: uuid.UUID
    titre: str
    horizon: str | None = None
    score_initial: float | None = None
    score_cible: float | None = None
    progression: ProgressionInfo
    impact_cumule: ImpactInfo
    prochaines_echeances: list[EcheanceInfo] = []
