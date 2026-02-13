import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SectorBenchmark(Base):
    __tablename__ = "sector_benchmarks"
    __table_args__ = (
        UniqueConstraint("secteur", "pays", "referentiel_id", "periode", name="idx_benchmark_unique"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    secteur: Mapped[str] = mapped_column(String(100), nullable=False)
    pays: Mapped[str | None] = mapped_column(String(100))
    referentiel_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("referentiels_esg.id"))
    score_e_moyen: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_s_moyen: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_g_moyen: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_global_moyen: Mapped[float | None] = mapped_column(Numeric(5, 2))
    carbone_moyen_tco2e: Mapped[float | None] = mapped_column(Numeric(10, 2))
    nombre_entreprises: Mapped[int | None] = mapped_column(Integer)
    periode: Mapped[str | None] = mapped_column(String(20))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
