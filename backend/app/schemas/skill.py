"""Schemas Pydantic pour le module admin skills."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---- Requests ----


class SkillCreateRequest(BaseModel):
    nom: str = Field(..., pattern=r"^[a-z_]+$", min_length=2, max_length=100)
    description: str = Field(..., min_length=5)
    category: str = Field(..., pattern=r"^(esg|finance|carbon|report|utils|document|knowledge|profile)$")
    input_schema: dict
    handler_key: str = Field(..., max_length=100)
    handler_code: str | None = None


class SkillUpdateRequest(BaseModel):
    description: str | None = None
    category: str | None = None
    input_schema: dict | None = None
    handler_code: str | None = None
    is_active: bool | None = None


class SkillTestRequest(BaseModel):
    params: dict = Field(default_factory=dict)


# ---- Responses ----


class SkillResponse(BaseModel):
    id: uuid.UUID
    nom: str
    description: str
    category: str | None
    input_schema: dict
    handler_key: str
    handler_code: str | None
    is_active: bool
    version: int
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SkillTestResponse(BaseModel):
    success: bool
    result: dict | None = None
    error: str | None = None
    duration_ms: int | None = None
