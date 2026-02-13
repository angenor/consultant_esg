import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fonds_vert import FondsVert
from app.models.referentiel_esg import ReferentielESG

DATA_PATH = Path("/app/data/fonds_verts.json")


async def seed_fonds(db: AsyncSession) -> int:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    # Charger la correspondance code -> id des référentiels
    result = await db.execute(select(ReferentielESG))
    ref_map = {r.code: r.id for r in result.scalars().all()}

    count = 0
    for fonds_data in data:
        # Résoudre le referentiel_code en referentiel_id
        ref_code = fonds_data.pop("referentiel_code", None)
        fonds_data["referentiel_id"] = ref_map.get(ref_code)

        # Vérifier si le fonds existe déjà (par nom + institution)
        result = await db.execute(
            select(FondsVert).where(
                FondsVert.nom == fonds_data["nom"],
                FondsVert.institution == fonds_data["institution"],
            )
        )
        if result.scalar_one_or_none() is None:
            db.add(FondsVert(**fonds_data))
            count += 1

    await db.commit()
    return count
