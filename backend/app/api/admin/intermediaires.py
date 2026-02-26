"""
Router /api/admin/intermediaires — CRUD intermédiaires.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.fonds_vert import FondsVert
from app.models.intermediaire import Intermediaire
from app.models.user import User
from app.schemas.intermediaire import (
    IntermediaireCreateRequest,
    IntermediaireResponse,
    IntermediaireUpdateRequest,
)

router = APIRouter(prefix="/api/admin/intermediaires", tags=["admin-intermediaires"])


@router.get("/", response_model=list[IntermediaireResponse])
async def list_intermediaires(
    fonds_id: uuid.UUID | None = Query(None, description="Filtrer par fonds"),
    pays: str | None = Query(None, description="Filtrer par pays"),
    type: str | None = Query(None, description="Filtrer par type"),
    is_active: bool | None = Query(None, description="Filtrer par statut"),
    search: str | None = Query(None, description="Recherche par nom"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Liste tous les intermédiaires."""
    query = select(Intermediaire).order_by(Intermediaire.nom)

    if fonds_id is not None:
        query = query.where(Intermediaire.fonds_id == fonds_id)
    if pays is not None:
        query = query.where(Intermediaire.pays == pays)
    if type is not None:
        query = query.where(Intermediaire.type == type)
    if is_active is not None:
        query = query.where(Intermediaire.is_active == is_active)
    if search:
        query = query.where(Intermediaire.nom.ilike(f"%{search}%"))

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=IntermediaireResponse, status_code=201)
async def create_intermediaire(
    body: IntermediaireCreateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Crée un nouvel intermédiaire."""
    # Vérifier que le fonds existe
    fonds = await db.execute(
        select(FondsVert).where(FondsVert.id == body.fonds_id)
    )
    if not fonds.scalar_one_or_none():
        raise HTTPException(400, "Fonds introuvable")

    intermediaire = Intermediaire(**body.model_dump())
    db.add(intermediaire)
    await db.commit()
    await db.refresh(intermediaire)
    return intermediaire


@router.get("/{intermediaire_id}", response_model=IntermediaireResponse)
async def get_intermediaire(
    intermediaire_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Détail d'un intermédiaire."""
    result = await db.execute(
        select(Intermediaire).where(Intermediaire.id == intermediaire_id)
    )
    intermediaire = result.scalar_one_or_none()
    if not intermediaire:
        raise HTTPException(404, "Intermédiaire introuvable")
    return intermediaire


@router.put("/{intermediaire_id}", response_model=IntermediaireResponse)
async def update_intermediaire(
    intermediaire_id: uuid.UUID,
    body: IntermediaireUpdateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Modifie un intermédiaire existant."""
    result = await db.execute(
        select(Intermediaire).where(Intermediaire.id == intermediaire_id)
    )
    intermediaire = result.scalar_one_or_none()
    if not intermediaire:
        raise HTTPException(404, "Intermédiaire introuvable")

    update_data = body.model_dump(exclude_unset=True)

    if "fonds_id" in update_data and update_data["fonds_id"]:
        fonds = await db.execute(
            select(FondsVert).where(FondsVert.id == update_data["fonds_id"])
        )
        if not fonds.scalar_one_or_none():
            raise HTTPException(400, "Fonds introuvable")

    for field, value in update_data.items():
        setattr(intermediaire, field, value)

    await db.commit()
    await db.refresh(intermediaire)
    return intermediaire


@router.delete("/{intermediaire_id}")
async def delete_intermediaire(
    intermediaire_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Supprime un intermédiaire."""
    result = await db.execute(
        select(Intermediaire).where(Intermediaire.id == intermediaire_id)
    )
    intermediaire = result.scalar_one_or_none()
    if not intermediaire:
        raise HTTPException(404, "Intermédiaire introuvable")

    await db.delete(intermediaire)
    await db.commit()
    return {"detail": "Intermédiaire supprimé"}
