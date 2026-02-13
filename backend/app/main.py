from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from app.api.auth import router as auth_router
from app.config import settings
from app.core.database import Base, engine
import app.models  # noqa: F401 — enregistre tous les modèles


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: créer les tables (sera remplacé par Alembic à l'étape 3)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
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


@app.get("/api/health")
async def health():
    return {"status": "ok"}
