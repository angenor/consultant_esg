"""
Router /api/admin/stats — Dashboard statistiques admin.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.models.entreprise import Entreprise
from app.models.conversation import Conversation
from app.models.esg_score import ESGScore
from app.models.skill import Skill
from app.models.referentiel_esg import ReferentielESG
from app.models.fonds_vert import FondsVert

router = APIRouter(prefix="/api/admin/stats", tags=["admin-stats"])


@router.get("/dashboard")
async def get_dashboard_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Statistiques globales pour le dashboard admin."""
    users_count = (await db.execute(select(func.count()).select_from(User))).scalar()
    entreprises_count = (await db.execute(select(func.count()).select_from(Entreprise))).scalar()
    conversations_count = (await db.execute(select(func.count()).select_from(Conversation))).scalar()
    scores_count = (await db.execute(select(func.count()).select_from(ESGScore))).scalar()
    skills_count = (await db.execute(select(func.count()).select_from(Skill))).scalar()
    skills_active = (await db.execute(
        select(func.count()).select_from(Skill).where(Skill.is_active.is_(True))
    )).scalar()
    referentiels_count = (await db.execute(select(func.count()).select_from(ReferentielESG))).scalar()
    fonds_count = (await db.execute(select(func.count()).select_from(FondsVert))).scalar()

    return {
        "users": users_count,
        "entreprises": entreprises_count,
        "conversations": conversations_count,
        "scores_esg": scores_count,
        "skills": {"total": skills_count, "active": skills_active},
        "referentiels": referentiels_count,
        "fonds_verts": fonds_count,
    }
