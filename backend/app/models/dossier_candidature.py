import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DossierCandidature(Base):
    __tablename__ = "dossiers_candidature"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entreprise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("entreprises.id", ondelete="CASCADE"), nullable=False
    )
    fonds_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fonds_verts.id", ondelete="CASCADE"), nullable=False
    )
    intermediaire_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("intermediaires.id", ondelete="SET NULL")
    )

    type_dossier: Mapped[str] = mapped_column(String(30), default="complet")
    documents_json: Mapped[list | None] = mapped_column(JSONB)
    zip_path: Mapped[str | None] = mapped_column(String(500))
    statut: Mapped[str] = mapped_column(String(30), default="genere")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relations
    entreprise = relationship("Entreprise", backref="dossiers_candidature")
    fonds = relationship("FondsVert", backref="dossiers_candidature")
