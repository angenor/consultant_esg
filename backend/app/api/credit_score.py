"""Endpoints API pour le scoring crédit vert (Module 5)."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.credit_score import CreditScore
from app.models.entreprise import Entreprise
from app.models.referentiel_esg import ReferentielESG
from app.models.user import User
from app.schemas.credit_score import (
    CalculateCreditScoreRequest,
    CreditScoreCalculated,
    CreditScoreResponse,
    CreditScoreSummary,
    ShareLinkResponse,
    ShareScoreRequest,
)
from app.skills.handlers.calculate_credit_score import calculate_credit_score

router = APIRouter(prefix="/api/credit-score", tags=["credit-score"])


# ── Helpers ──


def _niveau_credit(score: float | None) -> str:
    if score is None:
        return "Non calculé"
    if score >= 80:
        return "Excellent"
    if score >= 65:
        return "Bon"
    if score >= 50:
        return "Acceptable"
    if score >= 35:
        return "À améliorer"
    return "Insuffisant"


async def _verify_ownership(
    db: AsyncSession, entreprise_id: uuid.UUID, user: User
) -> Entreprise:
    """Vérifie que l'entreprise appartient à l'utilisateur."""
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


# ── Endpoints ──


@router.get("/latest")
async def latest_credit_score(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dernier score crédit vert de l'entreprise de l'utilisateur."""
    ent_result = await db.execute(
        select(Entreprise.id).where(Entreprise.user_id == user.id).limit(1)
    )
    ent_id = ent_result.scalar_one_or_none()
    if not ent_id:
        return None

    result = await db.execute(
        select(CreditScore)
        .where(CreditScore.entreprise_id == ent_id)
        .order_by(CreditScore.created_at.desc())
        .limit(1)
    )
    cs = result.scalar_one_or_none()
    if not cs:
        return None

    return {
        "id": str(cs.id),
        "entreprise_id": str(cs.entreprise_id),
        "score_combine": float(cs.score_combine) if cs.score_combine else 0,
        "score_solvabilite": float(cs.score_solvabilite) if cs.score_solvabilite else 0,
        "score_impact_vert": float(cs.score_impact_vert) if cs.score_impact_vert else 0,
        "facteurs_json": cs.facteurs_json or {},
        "created_at": str(cs.created_at),
    }


@router.post("/recalculate")
async def recalculate(
    referentiel_code: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Recalcule le score crédit vert, optionnellement filtré par référentiel."""
    ent_result = await db.execute(
        select(Entreprise.id).where(Entreprise.user_id == user.id).limit(1)
    )
    ent_id = ent_result.scalar_one_or_none()
    if not ent_id:
        raise HTTPException(status_code=404, detail="Entreprise introuvable")

    # Résoudre referentiel_code → referentiel_id
    referentiel_id = None
    if referentiel_code:
        ref_result = await db.execute(
            select(ReferentielESG.id).where(ReferentielESG.code == referentiel_code)
        )
        referentiel_id = ref_result.scalar_one_or_none()

    params = {
        "entreprise_id": str(ent_id),
        "referentiel_id": str(referentiel_id) if referentiel_id else None,
    }
    context = {"db": db, "entreprise_id": str(ent_id)}

    result = await calculate_credit_score(params, context)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/calculate", response_model=CreditScoreCalculated)
async def calculate(
    body: CalculateCreditScoreRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Calcule le score crédit vert pour une entreprise."""
    await _verify_ownership(db, body.entreprise_id, user)

    params = {
        "entreprise_id": str(body.entreprise_id),
        "donnees_financieres": body.donnees_financieres.model_dump() if body.donnees_financieres else {},
        "donnees_declaratives": body.donnees_declaratives.model_dump() if body.donnees_declaratives else {},
        "poids_solvabilite": body.poids_solvabilite,
        "poids_impact_vert": body.poids_impact_vert,
    }
    context = {"db": db, "entreprise_id": str(body.entreprise_id)}

    result = await calculate_credit_score(params, context)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get(
    "/entreprise/{entreprise_id}",
    response_model=list[CreditScoreSummary],
)
async def list_scores(
    entreprise_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dernier score + historique des scores crédit vert."""
    await _verify_ownership(db, entreprise_id, user)

    result = await db.execute(
        select(CreditScore)
        .where(CreditScore.entreprise_id == entreprise_id)
        .order_by(CreditScore.created_at.desc())
        .limit(limit)
    )
    scores = result.scalars().all()

    return [
        CreditScoreSummary(
            id=s.id,
            score_solvabilite=float(s.score_solvabilite) if s.score_solvabilite else None,
            score_impact_vert=float(s.score_impact_vert) if s.score_impact_vert else None,
            score_combine=float(s.score_combine) if s.score_combine else None,
            niveau=_niveau_credit(float(s.score_combine) if s.score_combine else None),
            created_at=s.created_at,
        )
        for s in scores
    ]


@router.get(
    "/entreprise/{entreprise_id}/latest",
    response_model=CreditScoreResponse | None,
)
async def latest_score(
    entreprise_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dernier score crédit vert avec détails complets."""
    await _verify_ownership(db, entreprise_id, user)

    result = await db.execute(
        select(CreditScore)
        .where(CreditScore.entreprise_id == entreprise_id)
        .order_by(CreditScore.created_at.desc())
        .limit(1)
    )
    score = result.scalar_one_or_none()
    if not score:
        return None
    return score


@router.post(
    "/entreprise/{entreprise_id}/share",
    response_model=ShareLinkResponse,
)
async def share_score(
    entreprise_id: uuid.UUID,
    body: ShareScoreRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Génère un lien de partage sécurisé pour le dernier score crédit vert."""
    await _verify_ownership(db, entreprise_id, user)

    # Vérifier qu'un score existe
    result = await db.execute(
        select(CreditScore)
        .where(CreditScore.entreprise_id == entreprise_id)
        .order_by(CreditScore.created_at.desc())
        .limit(1)
    )
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(
            status_code=404,
            detail="Aucun score crédit vert disponible. Calculez d'abord un score.",
        )

    duree = body.duree_heures if body else 72
    expire_at = datetime.now(timezone.utc) + timedelta(hours=duree)

    # Générer un token JWT dédié au partage
    payload = {
        "type": "credit_score_share",
        "entreprise_id": str(entreprise_id),
        "score_id": str(score.id),
        "exp": expire_at,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    lien = f"{settings.APP_URL}/shared/credit-score/{token}"

    return ShareLinkResponse(lien=lien, expire_at=expire_at, token=token)


@router.get("/shared/{token:path}", response_model=CreditScoreResponse)
async def view_shared_score(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Accès public à un score partagé via token."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        raise HTTPException(status_code=403, detail="Lien invalide ou expiré")

    if payload.get("type") != "credit_score_share":
        raise HTTPException(status_code=403, detail="Token invalide")

    score_id = payload.get("score_id")
    if not score_id:
        raise HTTPException(status_code=403, detail="Token invalide")

    result = await db.execute(
        select(CreditScore).where(CreditScore.id == uuid.UUID(score_id))
    )
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(status_code=404, detail="Score introuvable")

    return score
