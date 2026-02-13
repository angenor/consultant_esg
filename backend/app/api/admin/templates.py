"""
Router /api/admin/templates — CRUD templates de rapports.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.report_template import ReportTemplate
from app.models.user import User
from app.schemas.template import (
    TemplateCreateRequest,
    TemplateResponse,
    TemplateUpdateRequest,
)

router = APIRouter(prefix="/api/admin/templates", tags=["admin-templates"])


@router.get("/", response_model=list[TemplateResponse])
async def list_templates(
    is_active: bool | None = Query(None, description="Filtrer par statut"),
    search: str | None = Query(None, description="Recherche par nom"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Liste tous les templates de rapports."""
    query = select(ReportTemplate).order_by(ReportTemplate.nom)

    if is_active is not None:
        query = query.where(ReportTemplate.is_active == is_active)
    if search:
        query = query.where(ReportTemplate.nom.ilike(f"%{search}%"))

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=TemplateResponse, status_code=201)
async def create_template(
    body: TemplateCreateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Crée un nouveau template de rapport."""
    existing = await db.execute(
        select(ReportTemplate).where(ReportTemplate.nom == body.nom)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"Un template avec le nom '{body.nom}' existe déjà")

    template = ReportTemplate(**body.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Détail d'un template."""
    result = await db.execute(
        select(ReportTemplate).where(ReportTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(404, "Template introuvable")
    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    body: TemplateUpdateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Modifie un template existant."""
    result = await db.execute(
        select(ReportTemplate).where(ReportTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(404, "Template introuvable")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    template.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(template)
    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Supprime un template."""
    result = await db.execute(
        select(ReportTemplate).where(ReportTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(404, "Template introuvable")

    await db.delete(template)
    await db.commit()
    return {"detail": "Template supprimé"}
