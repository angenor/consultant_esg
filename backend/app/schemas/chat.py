"""Schemas Pydantic pour le module chat."""

import uuid
from datetime import datetime

from pydantic import BaseModel


# ---- Requests ----


class CreateConversationRequest(BaseModel):
    entreprise_id: uuid.UUID
    titre: str | None = None


class SendMessageRequest(BaseModel):
    message: str


# ---- Responses ----


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    tool_calls_json: dict | list | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: uuid.UUID
    entreprise_id: uuid.UUID
    titre: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse] = []
