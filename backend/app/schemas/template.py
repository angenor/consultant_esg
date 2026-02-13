"""Schemas for ReportTemplate admin API."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TemplateCreateRequest(BaseModel):
    nom: str = Field(..., min_length=3, max_length=100)
    description: str | None = None
    sections_json: dict | list = Field(..., description="Structure des sections du rapport")
    template_html: str = Field(..., min_length=10)


class TemplateUpdateRequest(BaseModel):
    nom: str | None = Field(None, min_length=3, max_length=100)
    description: str | None = None
    sections_json: dict | list | None = None
    template_html: str | None = None
    is_active: bool | None = None


class TemplateResponse(BaseModel):
    id: uuid.UUID
    nom: str
    description: str | None
    sections_json: Any
    template_html: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
