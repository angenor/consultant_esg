"""
Router /api/entreprises — CRUD basique entreprises.
Nécessaire pour que le chat puisse charger le contexte entreprise.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.entreprise import Entreprise
from app.models.user import User
from app.schemas.entreprise import (
    CreateEntrepriseRequest,
    EntrepriseResponse,
    UpdateEntrepriseRequest,
)

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
