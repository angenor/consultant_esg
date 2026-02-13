import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.referentiel_esg import ReferentielESG
from app.models.sector_benchmark import SectorBenchmark

DATA_PATH = Path("/app/data/sector_benchmarks.json")


async def seed_benchmarks(db: AsyncSession) -> int:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    # Charger la correspondance code -> id des référentiels
    result = await db.execute(select(ReferentielESG))
    ref_map = {r.code: r.id for r in result.scalars().all()}

    count = 0
    for bench_data in data:
        ref_code = bench_data.pop("referentiel_code", None)
        bench_data["referentiel_id"] = ref_map.get(ref_code)

        # Vérifier si le benchmark existe déjà
        result = await db.execute(
            select(SectorBenchmark).where(
                SectorBenchmark.secteur == bench_data["secteur"],
                SectorBenchmark.pays == bench_data.get("pays"),
                SectorBenchmark.periode == bench_data.get("periode"),
            )
        )
        if result.scalar_one_or_none() is None:
            db.add(SectorBenchmark(**bench_data))
            count += 1

    await db.commit()
    return count
