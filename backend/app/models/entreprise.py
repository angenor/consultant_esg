import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Numeric, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Entreprise(Base):
    __tablename__ = "entreprises"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    secteur: Mapped[str | None] = mapped_column(String(100))
    sous_secteur: Mapped[str | None] = mapped_column(String(100))
    pays: Mapped[str] = mapped_column(String(100), default="Côte d'Ivoire")
    ville: Mapped[str | None] = mapped_column(String(100))
    effectifs: Mapped[int | None] = mapped_column(Integer)
    chiffre_affaires: Mapped[float | None] = mapped_column(Numeric)
    devise: Mapped[str] = mapped_column(String(10), default="XOF")
    description: Mapped[str | None] = mapped_column(Text)
    profil_json: Mapped[dict | None] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
