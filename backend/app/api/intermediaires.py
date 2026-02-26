"""
Router /api/intermediaires — endpoints publics (lecture seule).
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.intermediaire import Intermediaire
from app.models.user import User
from app.schemas.intermediaire import IntermediaireResponse

router = APIRouter(prefix="/api/intermediaires", tags=["intermediaires"])


@router.get("/fonds/{fonds_id}", response_model=list[IntermediaireResponse])
async def list_by_fonds(
    fonds_id: uuid.UUID,
    pays: str | None = Query(None, description="Filtrer par pays"),
    type: str | None = Query(None, description="Filtrer par type"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Liste les intermédiaires actifs d'un fonds, optionnellement filtrés par pays."""
    query = (
        select(Intermediaire)
        .where(Intermediaire.fonds_id == fonds_id, Intermediaire.is_active.is_(True))
        .order_by(Intermediaire.est_recommande.desc(), Intermediaire.nom)
    )

    if pays is not None:
        query = query.where(
            (Intermediaire.pays == pays) | (Intermediaire.pays.is_(None))
        )
    if type is not None:
        query = query.where(Intermediaire.type == type)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{intermediaire_id}", response_model=IntermediaireResponse)
async def get_intermediaire(
    intermediaire_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Détail d'un intermédiaire."""
    from fastapi import HTTPException

    result = await db.execute(
        select(Intermediaire).where(Intermediaire.id == intermediaire_id)
    )
    intermediaire = result.scalar_one_or_none()
    if not intermediaire:
        raise HTTPException(404, "Intermédiaire introuvable")
    return intermediaire
