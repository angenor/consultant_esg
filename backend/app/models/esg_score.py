import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ESGScore(Base):
    __tablename__ = "esg_scores"
    __table_args__ = (
        UniqueConstraint("entreprise_id", "referentiel_id", "created_at", name="idx_score_per_referentiel"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entreprise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entreprises.id", ondelete="CASCADE"), nullable=False)
    referentiel_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("referentiels_esg.id"))
    score_e: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_s: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_g: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_global: Mapped[float | None] = mapped_column(Numeric(5, 2))
    details_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="conversation")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
