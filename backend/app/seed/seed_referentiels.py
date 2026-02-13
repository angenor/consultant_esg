import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.referentiel_esg import ReferentielESG

DATA_PATH = Path("/app/data/referentiels_esg.json")


async def seed_referentiels(db: AsyncSession) -> int:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    count = 0
    for ref in data:
        result = await db.execute(select(ReferentielESG).where(ReferentielESG.code == ref["code"]))
        existing = result.scalar_one_or_none()
        if existing is None:
            db.add(ReferentielESG(**ref))
            count += 1
        else:
            # Mettre à jour la grille et la description si les données ont changé
            existing.grille_json = ref["grille_json"]
            existing.description = ref.get("description", existing.description)
            existing.nom = ref.get("nom", existing.nom)
    await db.commit()
    return count
