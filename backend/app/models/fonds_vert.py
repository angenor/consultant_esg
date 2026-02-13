import uuid
from datetime import date, datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FondsVert(Base):
    __tablename__ = "fonds_verts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    institution: Mapped[str | None] = mapped_column(String(255))
    type: Mapped[str | None] = mapped_column(String(50))
    referentiel_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("referentiels_esg.id"))
    montant_min: Mapped[float | None] = mapped_column(Numeric)
    montant_max: Mapped[float | None] = mapped_column(Numeric)
    devise: Mapped[str] = mapped_column(String(10), default="USD")
    secteurs_json: Mapped[list | None] = mapped_column(JSONB)
    pays_eligibles: Mapped[list | None] = mapped_column(JSONB)
    criteres_json: Mapped[dict | None] = mapped_column(JSONB)
    date_limite: Mapped[date | None] = mapped_column(Date)
    url_source: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class FondsChunk(Base):
    __tablename__ = "fonds_chunks"
    __table_args__ = (
        Index(
            "idx_fonds_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    fonds_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fonds_verts.id", ondelete="CASCADE"), nullable=False)
    contenu: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(1024))
    type_info: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
