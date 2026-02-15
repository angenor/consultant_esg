import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ActionPlan(Base):
    __tablename__ = "action_plans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entreprise_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entreprises.id", ondelete="CASCADE"), nullable=False)
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    type_plan: Mapped[str] = mapped_column(String(20), default="esg", nullable=False)
    horizon: Mapped[str | None] = mapped_column(String(20))
    referentiel_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("referentiels_esg.id"))
    score_initial: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_cible: Mapped[float | None] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )


class ActionItem(Base):
    __tablename__ = "action_items"
    __table_args__ = (
        Index("idx_action_items_plan", "plan_id", "statut"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("action_plans.id", ondelete="CASCADE"), nullable=False)
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    priorite: Mapped[str | None] = mapped_column(String(20))
    pilier: Mapped[str | None] = mapped_column(String(20))
    critere_id: Mapped[str | None] = mapped_column(String(100))
    statut: Mapped[str] = mapped_column(String(20), default="a_faire")
    echeance: Mapped[date | None] = mapped_column(Date)
    impact_score_estime: Mapped[float | None] = mapped_column(Numeric(5, 2))
    cout_estime: Mapped[float | None] = mapped_column(Numeric)
    benefice_estime: Mapped[float | None] = mapped_column(Numeric)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
