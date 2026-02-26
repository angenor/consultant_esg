import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Intermediaire(Base):
    __tablename__ = "intermediaires"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    fonds_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fonds_verts.id", ondelete="CASCADE"), nullable=False
    )
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    pays: Mapped[str | None] = mapped_column(String(100))
    ville: Mapped[str | None] = mapped_column(String(100))

    email: Mapped[str | None] = mapped_column(String(200))
    telephone: Mapped[str | None] = mapped_column(String(50))
    adresse: Mapped[str | None] = mapped_column(Text)
    site_web: Mapped[str | None] = mapped_column(String(500))

    url_formulaire: Mapped[str | None] = mapped_column(String(500))
    type_soumission: Mapped[str | None] = mapped_column(String(30))
    instructions_soumission: Mapped[str | None] = mapped_column(Text)

    documents_requis: Mapped[list | None] = mapped_column(JSONB)
    etapes_specifiques: Mapped[list | None] = mapped_column(JSONB)
    delai_traitement: Mapped[str | None] = mapped_column(String(50))

    est_recommande: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relation
    fonds = relationship("FondsVert", backref="intermediaires")
