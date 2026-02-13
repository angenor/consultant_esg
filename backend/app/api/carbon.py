"""Endpoints API pour l'empreinte carbone."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.carbon_footprint import CarbonFootprint
from app.models.entreprise import Entreprise
from app.models.user import User

router = APIRouter(prefix="/api/carbon", tags=["carbon"])


# ── Schemas ──


class CarbonSummary(BaseModel):
    id: uuid.UUID
    annee: int
    mois: int | None
    energie: float
    transport: float
    dechets: float
    achats: float
    total_tco2e: float
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CarbonDetail(CarbonSummary):
    entreprise_id: uuid.UUID
    details_json: dict | None

    model_config = {"from_attributes": True}


class EvolutionPoint(BaseModel):
    annee: int
    mois: int | None
    total_tco2e: float
    energie: float
    transport: float
    dechets: float
    achats: float


# ── Endpoints ──


@router.get("/latest", response_model=CarbonDetail | None)
async def latest_carbon(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dernière empreinte carbone de l'entreprise de l'utilisateur."""
    ent_result = await db.execute(
        select(Entreprise.id).where(Entreprise.user_id == user.id).limit(1)
    )
    ent_id = ent_result.scalar_one_or_none()
    if not ent_id:
        return None

    result = await db.execute(
        select(CarbonFootprint)
        .where(CarbonFootprint.entreprise_id == ent_id)
        .order_by(CarbonFootprint.annee.desc(), CarbonFootprint.mois.desc().nulls_last())
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.get(
    "/entreprise/{entreprise_id}",
    response_model=list[CarbonSummary],
)
async def list_carbon(
    entreprise_id: uuid.UUID,
    annee: int | None = Query(None, description="Filtrer par année"),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Historique des empreintes carbone d'une entreprise."""
    # Vérifier que l'entreprise appartient à l'utilisateur
    result = await db.execute(
        select(Entreprise).where(
            Entreprise.id == entreprise_id,
            Entreprise.user_id == user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Entreprise introuvable")

    query = select(CarbonFootprint).where(
        CarbonFootprint.entreprise_id == entreprise_id
    )
    if annee:
        query = query.where(CarbonFootprint.annee == annee)
    query = query.order_by(
        CarbonFootprint.annee.desc(),
        CarbonFootprint.mois.desc().nulls_last(),
    ).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/entreprise/{entreprise_id}/evolution",
    response_model=list[EvolutionPoint],
)
async def evolution_carbon(
    entreprise_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Évolution de l'empreinte carbone (pour graphiques)."""
    # Vérifier propriété
    result = await db.execute(
        select(Entreprise).where(
            Entreprise.id == entreprise_id,
            Entreprise.user_id == user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Entreprise introuvable")

    result = await db.execute(
        select(CarbonFootprint)
        .where(CarbonFootprint.entreprise_id == entreprise_id)
        .order_by(CarbonFootprint.annee.asc(), CarbonFootprint.mois.asc().nulls_first())
    )
    footprints = result.scalars().all()

    return [
        EvolutionPoint(
            annee=fp.annee,
            mois=fp.mois,
            total_tco2e=float(fp.total_tco2e),
            energie=float(fp.energie),
            transport=float(fp.transport),
            dechets=float(fp.dechets),
            achats=float(fp.achats),
        )
        for fp in footprints
    ]
