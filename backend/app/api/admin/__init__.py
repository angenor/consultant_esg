"""Admin API routers."""

from fastapi import APIRouter

from app.api.admin.skills import router as skills_router
from app.api.admin.referentiels import router as referentiels_router
from app.api.admin.fonds import router as fonds_router
from app.api.admin.templates import router as templates_router
from app.api.admin.intermediaires import router as intermediaires_router
from app.api.admin.stats import router as stats_router

admin_router = APIRouter()
admin_router.include_router(skills_router)
admin_router.include_router(referentiels_router)
admin_router.include_router(fonds_router)
admin_router.include_router(intermediaires_router)
admin_router.include_router(templates_router)
admin_router.include_router(stats_router)
