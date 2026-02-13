"""
Router /api/admin/fonds — CRUD fonds verts.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.fonds_vert import FondsVert
from app.models.referentiel_esg import ReferentielESG
from app.models.user import User
from app.schemas.fonds import (
    FondsCreateRequest,
    FondsResponse,
    FondsUpdateRequest,
)

router = APIRouter(prefix="/api/admin/fonds", tags=["admin-fonds"])


@router.get("/", response_model=list[FondsResponse])
async def list_fonds(
    is_active: bool | None = Query(None, description="Filtrer par statut"),
    search: str | None = Query(None, description="Recherche par nom"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Liste tous les fonds verts."""
    query = select(FondsVert).order_by(FondsVert.nom)

    if is_active is not None:
        query = query.where(FondsVert.is_active == is_active)
    if search:
        query = query.where(FondsVert.nom.ilike(f"%{search}%"))

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=FondsResponse, status_code=201)
async def create_fonds(
    body: FondsCreateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Crée un nouveau fonds vert."""
    if body.referentiel_id:
        ref = await db.execute(
            select(ReferentielESG).where(ReferentielESG.id == body.referentiel_id)
        )
        if not ref.scalar_one_or_none():
            raise HTTPException(400, "Référentiel introuvable")

    fonds = FondsVert(**body.model_dump())
    db.add(fonds)
    await db.commit()
    await db.refresh(fonds)
    return fonds


@router.get("/{fonds_id}", response_model=FondsResponse)
async def get_fonds(
    fonds_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Détail d'un fonds vert."""
    result = await db.execute(select(FondsVert).where(FondsVert.id == fonds_id))
    fonds = result.scalar_one_or_none()
    if not fonds:
        raise HTTPException(404, "Fonds introuvable")
    return fonds


@router.put("/{fonds_id}", response_model=FondsResponse)
async def update_fonds(
    fonds_id: uuid.UUID,
    body: FondsUpdateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Modifie un fonds vert existant."""
    result = await db.execute(select(FondsVert).where(FondsVert.id == fonds_id))
    fonds = result.scalar_one_or_none()
    if not fonds:
        raise HTTPException(404, "Fonds introuvable")

    update_data = body.model_dump(exclude_unset=True)

    if "referentiel_id" in update_data and update_data["referentiel_id"]:
        ref = await db.execute(
            select(ReferentielESG).where(ReferentielESG.id == update_data["referentiel_id"])
        )
        if not ref.scalar_one_or_none():
            raise HTTPException(400, "Référentiel introuvable")

    for field, value in update_data.items():
        setattr(fonds, field, value)

    await db.commit()
    await db.refresh(fonds)
    return fonds


@router.delete("/{fonds_id}")
async def delete_fonds(
    fonds_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Supprime un fonds vert."""
    result = await db.execute(select(FondsVert).where(FondsVert.id == fonds_id))
    fonds = result.scalar_one_or_none()
    if not fonds:
        raise HTTPException(404, "Fonds introuvable")

    await db.delete(fonds)
    await db.commit()
    return {"detail": "Fonds supprimé"}
