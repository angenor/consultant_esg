import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FundApplication(Base):
    __tablename__ = "fund_applications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entreprise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("entreprises.id", ondelete="CASCADE"), nullable=False
    )
    fonds_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("fonds_verts.id", ondelete="SET NULL")
    )
    fonds_nom: Mapped[str] = mapped_column(String(255), nullable=False)
    fonds_institution: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(50), default="brouillon")
    progress_pct: Mapped[float] = mapped_column(Float, default=0)
    form_data: Mapped[dict | None] = mapped_column(JSONB, default={})
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    total_steps: Mapped[int | None] = mapped_column(Integer)
    url_candidature: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class FundSiteConfig(Base):
    __tablename__ = "fund_site_configs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    fonds_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fonds_verts.id", ondelete="CASCADE"), nullable=False
    )
    url_patterns: Mapped[list] = mapped_column(JSONB, default=[])
    steps: Mapped[list] = mapped_column(JSONB, default=[])
    required_docs: Mapped[list] = mapped_column(JSONB, default=[])
    tips: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
