import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fonds_vert import FondsVert
from app.models.intermediaire import Intermediaire

DATA_PATH = Path("/app/data/intermediaires.json")


async def seed_intermediaires(db: AsyncSession) -> int:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    # Charger la correspondance nom -> id des fonds
    result = await db.execute(select(FondsVert))
    fonds_map = {f.nom: f.id for f in result.scalars().all()}

    count = 0
    for entry in data:
        fonds_nom = entry["fonds_nom"]
        fonds_id = fonds_map.get(fonds_nom)
        if fonds_id is None:
            print(f"  [!] Fonds introuvable : {fonds_nom}")
            continue

        for inter_data in entry["intermediaires"]:
            inter_data["fonds_id"] = fonds_id

            # Vérifier si l'intermédiaire existe déjà (par nom + fonds_id)
            result = await db.execute(
                select(Intermediaire).where(
                    Intermediaire.nom == inter_data["nom"],
                    Intermediaire.fonds_id == fonds_id,
                )
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                db.add(Intermediaire(**inter_data))
                count += 1
            else:
                # Mettre à jour les champs existants
                for key, value in inter_data.items():
                    if key not in ("nom", "fonds_id") and value is not None:
                        setattr(existing, key, value)
                count += 1

    await db.commit()
    return count
