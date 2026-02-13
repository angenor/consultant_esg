"""
Router /api/entreprises — CRUD basique entreprises + historique scores ESG.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.entreprise import Entreprise
from app.models.esg_score import ESGScore
from app.models.referentiel_esg import ReferentielESG
from app.models.user import User
from app.schemas.entreprise import (
    CreateEntrepriseRequest,
    EntrepriseResponse,
    UpdateEntrepriseRequest,
)
from app.schemas.esg import ESGScoreResponse, ESGScoreSummary

router = APIRouter(prefix="/api/entreprises", tags=["entreprises"])


@router.post("/", response_model=EntrepriseResponse, status_code=201)
async def create_entreprise(
    body: CreateEntrepriseRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Crée une entreprise liée à l'utilisateur connecté."""
    entreprise = Entreprise(
        user_id=user.id,
        **body.model_dump(),
    )
    db.add(entreprise)
    await db.commit()
    await db.refresh(entreprise)
    return entreprise


@router.get("/", response_model=list[EntrepriseResponse])
async def list_entreprises(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Liste les entreprises de l'utilisateur connecté."""
    result = await db.execute(
        select(Entreprise)
        .where(Entreprise.user_id == user.id)
        .order_by(Entreprise.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{entreprise_id}", response_model=EntrepriseResponse)
async def get_entreprise(
    entreprise_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Détail d'une entreprise."""
    result = await db.execute(
        select(Entreprise).where(
            Entreprise.id == entreprise_id,
            Entreprise.user_id == user.id,
        )
    )
    entreprise = result.scalar_one_or_none()
    if not entreprise:
        raise HTTPException(status_code=404, detail="Entreprise introuvable")
    return entreprise


@router.put("/{entreprise_id}", response_model=EntrepriseResponse)
async def update_entreprise(
    entreprise_id: uuid.UUID,
    body: UpdateEntrepriseRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Modifier une entreprise."""
    result = await db.execute(
        select(Entreprise).where(
            Entreprise.id == entreprise_id,
            Entreprise.user_id == user.id,
        )
    )
    entreprise = result.scalar_one_or_none()
    if not entreprise:
        raise HTTPException(status_code=404, detail="Entreprise introuvable")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entreprise, field, value)
    entreprise.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(entreprise)
    return entreprise


# ── Scores ESG ──


@router.get(
    "/{entreprise_id}/scores",
    response_model=list[ESGScoreSummary],
)
async def list_scores(
    entreprise_id: uuid.UUID,
    referentiel_code: str | None = Query(None, description="Filtrer par code référentiel"),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Historique des scores ESG d'une entreprise (tous référentiels)."""
    # Vérifier que l'entreprise appartient à l'utilisateur
    result = await db.execute(
        select(Entreprise).where(
            Entreprise.id == entreprise_id,
            Entreprise.user_id == user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Entreprise introuvable")

    # Construire la requête scores
    query = (
        select(ESGScore, ReferentielESG)
        .outerjoin(ReferentielESG, ESGScore.referentiel_id == ReferentielESG.id)
        .where(ESGScore.entreprise_id == entreprise_id)
    )
    if referentiel_code:
        query = query.where(ReferentielESG.code == referentiel_code)
    query = query.order_by(ESGScore.created_at.desc()).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    scores = []
    for score, ref in rows:
        niveau = None
        if score.score_global is not None:
            sg = float(score.score_global)
            if sg >= 80:
                niveau = "Excellent"
            elif sg >= 60:
                niveau = "Bon"
            elif sg >= 40:
                niveau = "À améliorer"
            else:
                niveau = "Insuffisant"

        scores.append(
            ESGScoreSummary(
                id=score.id,
                referentiel_id=score.referentiel_id,
                referentiel_nom=ref.nom if ref else None,
                referentiel_code=ref.code if ref else None,
                score_e=float(score.score_e) if score.score_e is not None else None,
                score_s=float(score.score_s) if score.score_s is not None else None,
                score_g=float(score.score_g) if score.score_g is not None else None,
                score_global=float(score.score_global) if score.score_global is not None else None,
                niveau=niveau,
                source=score.source,
                created_at=score.created_at,
            )
        )
    return scores


@router.get(
    "/{entreprise_id}/scores/{score_id}",
    response_model=ESGScoreResponse,
)
async def get_score_detail(
    entreprise_id: uuid.UUID,
    score_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Détail complet d'un score ESG (avec détails par critère)."""
    # Vérifier que l'entreprise appartient à l'utilisateur
    result = await db.execute(
        select(Entreprise).where(
            Entreprise.id == entreprise_id,
            Entreprise.user_id == user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Entreprise introuvable")

    result = await db.execute(
        select(ESGScore).where(
            ESGScore.id == score_id,
            ESGScore.entreprise_id == entreprise_id,
        )
    )
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(status_code=404, detail="Score introuvable")
    return score
