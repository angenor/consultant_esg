import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fonds_vert import FondsVert
from app.models.fund_application import FundSiteConfig

DATA_PATH = Path("/app/data/fund_site_configs.json")


async def seed_fund_configs(db: AsyncSession) -> int:
    if not DATA_PATH.exists():
        return 0

    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    # Charger la correspondance nom -> id des fonds
    result = await db.execute(select(FondsVert))
    fonds_map = {}
    for f in result.scalars().all():
        # Creer une cle normalisee a partir du nom
        key = f.nom.lower().replace(" ", "_").replace("-", "_")
        fonds_map[key] = f.id
        # Aussi mapper par institution + nom
        if f.institution:
            fonds_map[f"{f.institution.lower()}_{key}"] = f.id

    count = 0
    for config_data in data:
        fonds_code = config_data.pop("fonds_code", "")

        # Trouver le fonds correspondant
        fonds_id = fonds_map.get(fonds_code)
        if not fonds_id:
            # Essayer une correspondance partielle
            for key, fid in fonds_map.items():
                if fonds_code in key or key in fonds_code:
                    fonds_id = fid
                    break

        if not fonds_id:
            # Prendre le premier fonds disponible comme fallback pour la demo
            result = await db.execute(select(FondsVert.id).limit(1))
            row = result.scalar_one_or_none()
            if not row:
                continue
            fonds_id = row

        # Verifier si la config existe deja
        existing = await db.execute(
            select(FundSiteConfig).where(FundSiteConfig.fonds_id == fonds_id)
        )
        if existing.scalar_one_or_none() is not None:
            continue

        config = FundSiteConfig(
            fonds_id=fonds_id,
            url_patterns=config_data.get("url_patterns", []),
            steps=config_data.get("steps", []),
            required_docs=config_data.get("required_docs", []),
            tips=config_data.get("tips"),
        )
        db.add(config)
        count += 1

    await db.commit()
    return count
