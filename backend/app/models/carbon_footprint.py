import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CarbonFootprint(Base):
    __tablename__ = "carbon_footprints"
    __table_args__ = (
        Index("idx_carbon_entreprise", "entreprise_id", "annee", "mois"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entreprise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entreprises.id", ondelete="CASCADE"), nullable=False)
    annee: Mapped[int] = mapped_column(Integer, nullable=False)
    mois: Mapped[int | None] = mapped_column(Integer)
    energie: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    transport: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    dechets: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    achats: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_tco2e: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    details_json: Mapped[dict | None] = mapped_column(JSONB)
    source: Mapped[str] = mapped_column(String(20), default="conversation")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
