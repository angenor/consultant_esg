"""
Tests for /api/chat endpoints (conversations CRUD).
"""

import pytest


class TestChat:
    """Tests for chat conversation API endpoints."""

    async def _create_entreprise(self, client, auth_headers):
        """Helper: create an entreprise and return its ID."""
        resp = await client.post(
            "/api/entreprises/",
            json={"nom": "ChatTestCorp"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    @pytest.mark.asyncio
    async def test_create_conversation(self, client, auth_headers):
        """POST /api/chat/conversations creates a conversation linked to an entreprise."""
        entreprise_id = await self._create_entreprise(client, auth_headers)

        response = await client.post(
            "/api/chat/conversations",
            json={"entreprise_id": entreprise_id, "titre": "Test conversation"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["entreprise_id"] == entreprise_id
        assert data["titre"] == "Test conversation"

    @pytest.mark.asyncio
    async def test_list_conversations(self, client, auth_headers):
        """GET /api/chat/conversations returns a list of conversations."""
        response = await client.get(
            "/api/chat/conversations",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_delete_conversation(self, client, auth_headers):
        """DELETE /api/chat/conversations/{id} removes the conversation."""
        entreprise_id = await self._create_entreprise(client, auth_headers)

        # Create a conversation
        create_resp = await client.post(
            "/api/chat/conversations",
            json={"entreprise_id": entreprise_id},
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        conversation_id = create_resp.json()["id"]

        # Delete it
        delete_resp = await client.delete(
            f"/api/chat/conversations/{conversation_id}",
            headers=auth_headers,
        )
        assert delete_resp.status_code == 204

        # Verify it's gone: fetching should return 404
        get_resp = await client.get(
            f"/api/chat/conversations/{conversation_id}",
            headers=auth_headers,
        )
        assert get_resp.status_code == 404
