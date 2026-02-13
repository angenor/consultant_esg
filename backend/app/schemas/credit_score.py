"""Schemas Pydantic pour le module Crédit Vert (Module 5)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Requests ──


class DonneesFinancieres(BaseModel):
    regularite_transactions: int | None = Field(
        None, ge=0, le=100, description="Auto-évaluation régularité (0-100)"
    )
    volume_mensuel_moyen: float | None = Field(
        None, ge=0, description="Volume mensuel moyen en XOF"
    )
    anciennete_mois: int | None = Field(
        None, ge=0, description="Ancienneté de l'entreprise en mois"
    )


class DonneesDeclaratives(BaseModel):
    pratiques_vertes: list[str] = Field(
        default_factory=list,
        description="Ex: tri_dechets, solaire, compostage",
    )
    projets_verts_en_cours: bool = False
    participation_programmes: list[str] = Field(
        default_factory=list,
        description="Ex: REDD+, économie circulaire",
    )
    certifications: list[str] = Field(
        default_factory=list,
        description="Ex: ISO 14001, label vert",
    )


class CalculateCreditScoreRequest(BaseModel):
    entreprise_id: uuid.UUID
    donnees_financieres: DonneesFinancieres | None = None
    donnees_declaratives: DonneesDeclaratives | None = None
    poids_solvabilite: float = Field(0.50, ge=0, le=1)
    poids_impact_vert: float = Field(0.50, ge=0, le=1)


class ShareScoreRequest(BaseModel):
    duree_heures: int = Field(72, ge=1, le=720, description="Durée de validité du lien (heures)")


# ── Responses ──


class FacteurDetail(BaseModel):
    facteur: str
    impact: str
    categorie: str


class FacteursJson(BaseModel):
    facteurs_positifs: list[FacteurDetail] = []
    facteurs_negatifs: list[FacteurDetail] = []


class CreditScoreResponse(BaseModel):
    id: uuid.UUID
    entreprise_id: uuid.UUID
    score_solvabilite: float | None
    score_impact_vert: float | None
    score_combine: float | None
    donnees_financieres_json: dict | None = None
    donnees_esg_json: dict | None = None
    donnees_declaratives_json: dict | None = None
    facteurs_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class CreditScoreSummary(BaseModel):
    id: uuid.UUID
    score_solvabilite: float | None
    score_impact_vert: float | None
    score_combine: float | None
    niveau: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CreditScoreCalculated(BaseModel):
    """Réponse du calcul avec facteurs et recommandations."""
    id: str
    score_solvabilite: float
    score_impact_vert: float
    score_combine: float
    niveau: str
    facteurs: FacteursJson
    recommandations: list[str]
    poids: dict


class ShareLinkResponse(BaseModel):
    lien: str
    expire_at: datetime
    token: str
