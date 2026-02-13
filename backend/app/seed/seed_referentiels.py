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
        if result.scalar_one_or_none() is None:
            db.add(ReferentielESG(**ref))
            count += 1
    await db.commit()
    return count
