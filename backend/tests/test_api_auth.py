"""
Tests for /api/auth endpoints (register, login).
"""

import uuid

import pytest
from sqlalchemy import text


class TestAuth:
    """Tests for authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_register_success(self, client, db_session):
        """POST /api/auth/register with a unique email returns token + user."""
        unique = uuid.uuid4().hex[:12]
        email = f"test_register_{unique}@test.com"

        response = await client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "securepass123",
                "nom_complet": "Nouveau Utilisateur",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == email
        assert data["user"]["nom_complet"] == "Nouveau Utilisateur"

        # Cleanup: remove the registered user
        await db_session.execute(
            text("DELETE FROM users WHERE email = :email"),
            {"email": email},
        )
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, db_session):
        """Registering twice with the same email returns 409 Conflict."""
        unique = uuid.uuid4().hex[:12]
        email = f"test_dup_{unique}@test.com"
        payload = {
            "email": email,
            "password": "securepass123",
            "nom_complet": "Duplicate User",
        }

        # First registration should succeed
        resp1 = await client.post("/api/auth/register", json=payload)
        assert resp1.status_code == 200

        # Second registration with same email should fail
        resp2 = await client.post("/api/auth/register", json=payload)
        assert resp2.status_code == 409

        # Cleanup
        await db_session.execute(
            text("DELETE FROM users WHERE email = :email"),
            {"email": email},
        )
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user, auth_headers):
        """POST /api/auth/login with valid credentials returns a token."""
        response = await client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": test_user._test_password,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, test_user):
        """POST /api/auth/login with wrong password returns 401."""
        response = await client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
