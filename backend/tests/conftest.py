"""
Shared fixtures for API tests.
Reuses the same real DB connection pattern as test_agent.py / test_skills.py.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core.security import hash_password
from app.main import app
from app.models.user import User


# ---- DB session fixture (same pattern as existing tests) ----


@pytest_asyncio.fixture
async def db_session():
    """Async SQLAlchemy session connected to the real database."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


# ---- HTTP client fixture ----


@pytest_asyncio.fixture
async def client():
    """httpx AsyncClient wired to the FastAPI app (no network needed)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---- Test user fixture ----


@pytest_asyncio.fixture
async def test_user(db_session):
    """
    Creates a temporary user in the DB for testing.
    Email uses uuid4 to avoid collisions. Cleaned up after the test.
    """
    unique = uuid.uuid4().hex[:12]
    email = f"test_api_{unique}@test.com"
    password = "testpass123"

    user = User(
        email=email,
        password_hash=hash_password(password),
        nom_complet="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Attach plain password so tests can use it for login
    user._test_password = password

    yield user

    # Cleanup: delete related data then the user
    await db_session.execute(
        text("DELETE FROM conversations WHERE entreprise_id IN (SELECT id FROM entreprises WHERE user_id = :uid)"),
        {"uid": str(user.id)},
    )
    await db_session.execute(
        text("DELETE FROM entreprises WHERE user_id = :uid"),
        {"uid": str(user.id)},
    )
    await db_session.execute(
        text("DELETE FROM users WHERE id = :uid"),
        {"uid": str(user.id)},
    )
    await db_session.commit()


# ---- Auth headers fixture ----


@pytest_asyncio.fixture
async def auth_headers(client, test_user):
    """
    Logs in with the test_user and returns Authorization headers.
    """
    response = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": test_user._test_password},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
