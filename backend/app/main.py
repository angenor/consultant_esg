from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.action_plans import router as action_plans_router
from app.api.benchmark import router as benchmark_router
from app.api.carbon import router as carbon_router
from app.api.credit_score import router as credit_score_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.entreprises import router as entreprises_router
from app.api.notifications import router as notifications_router
from app.api.dashboard import router as dashboard_router
from app.api.reports import router as reports_router
from app.api.admin import admin_router
from app.api.extension import router as extension_router
from app.config import settings
from app.core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: vérifier la connexion BDD
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    yield
    # Shutdown: fermer le pool
    await engine.dispose()


app = FastAPI(title="ESG Advisor API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.APP_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(entreprises_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(carbon_router)
app.include_router(credit_score_router)
app.include_router(action_plans_router)
app.include_router(notifications_router)
app.include_router(benchmark_router)
app.include_router(reports_router)
app.include_router(dashboard_router)
app.include_router(admin_router)
app.include_router(extension_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
