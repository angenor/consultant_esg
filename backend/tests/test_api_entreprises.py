"""
Tests for /api/entreprises endpoints (CRUD).
"""

import pytest


class TestEntreprises:
    """Tests for entreprises API endpoints."""

    @pytest.mark.asyncio
    async def test_create_entreprise(self, client, auth_headers):
        """POST /api/entreprises/ creates an entreprise and returns it."""
        response = await client.post(
            "/api/entreprises/",
            json={"nom": "TestCorp"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["nom"] == "TestCorp"
        assert data["pays"] == "Côte d'Ivoire"  # default value
        assert data["devise"] == "XOF"  # default value

    @pytest.mark.asyncio
    async def test_list_entreprises(self, client, auth_headers):
        """GET /api/entreprises/ returns a list."""
        # Create one first to ensure the list is not empty
        await client.post(
            "/api/entreprises/",
            json={"nom": "ListTestCorp"},
            headers=auth_headers,
        )

        response = await client.get(
            "/api/entreprises/",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # Verify structure of returned items
        assert "id" in data[0]
        assert "nom" in data[0]

    @pytest.mark.asyncio
    async def test_get_entreprise(self, client, auth_headers):
        """GET /api/entreprises/{id} returns the correct entreprise."""
        # Create an entreprise
        create_resp = await client.post(
            "/api/entreprises/",
            json={"nom": "DetailCorp", "secteur": "agriculture", "ville": "Abidjan"},
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        created = create_resp.json()
        entreprise_id = created["id"]

        # Fetch it by ID
        response = await client.get(
            f"/api/entreprises/{entreprise_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == entreprise_id
        assert data["nom"] == "DetailCorp"
        assert data["secteur"] == "agriculture"
        assert data["ville"] == "Abidjan"
