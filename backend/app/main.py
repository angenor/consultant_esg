from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.carbon import router as carbon_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.entreprises import router as entreprises_router
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


@app.get("/api/health")
async def health():
    return {"status": "ok"}
