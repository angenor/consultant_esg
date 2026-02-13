"""Endpoints API pour le benchmarking sectoriel."""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.sector_benchmark import SectorBenchmark
from app.models.user import User

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])


# ── Schemas ──


class BenchmarkResponse(BaseModel):
    secteur: str
    pays: str | None
    periode: str | None
    score_e_moyen: float | None
    score_s_moyen: float | None
    score_g_moyen: float | None
    score_global_moyen: float | None
    carbone_moyen_tco2e: float | None
    nombre_entreprises: int | None

    model_config = {"from_attributes": True}


# ── Endpoints ──


@router.get(
    "/secteur/{secteur}",
    response_model=list[BenchmarkResponse],
)
async def get_benchmarks_by_sector(
    secteur: str,
    pays: str | None = Query(None, description="Filtrer par code pays (ISO 3)"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Moyennes sectorielles pour un secteur donné."""
    query = select(SectorBenchmark).where(
        SectorBenchmark.secteur == secteur.lower()
    )
    if pays:
        query = query.where(SectorBenchmark.pays == pays.upper())
    query = query.order_by(SectorBenchmark.updated_at.desc())

    result = await db.execute(query)
    return result.scalars().all()
