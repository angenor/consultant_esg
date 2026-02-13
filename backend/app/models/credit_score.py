import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CreditScore(Base):
    __tablename__ = "credit_scores"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entreprise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entreprises.id", ondelete="CASCADE"), nullable=False)
    score_solvabilite: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_impact_vert: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_combine: Mapped[float | None] = mapped_column(Numeric(5, 2))
    donnees_financieres_json: Mapped[dict | None] = mapped_column(JSONB)
    donnees_esg_json: Mapped[dict | None] = mapped_column(JSONB)
    donnees_declaratives_json: Mapped[dict | None] = mapped_column(JSONB)
    facteurs_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
