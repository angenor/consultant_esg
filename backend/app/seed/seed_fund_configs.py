import json
import unicodedata
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fonds_vert import FondsVert
from app.models.fund_application import FundSiteConfig
from app.models.intermediaire import Intermediaire

DATA_PATH = Path("/app/data/fund_site_configs.json")


def _normalize_key(s: str) -> str:
    """Normalise une chaine pour la correspondance : sans accents, minuscules, underscores."""
    nfkd = unicodedata.normalize("NFKD", s)
    ascii_str = nfkd.encode("ASCII", "ignore").decode("ASCII")
    return ascii_str.lower().replace(" ", "_").replace("-", "_").replace("'", "")


async def seed_fund_configs(db: AsyncSession) -> int:
    if not DATA_PATH.exists():
        return 0

    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    # Charger la correspondance nom -> id des fonds (cle normalisee sans accents)
    result = await db.execute(select(FondsVert))
    fonds_map = {}
    for f in result.scalars().all():
        key = _normalize_key(f.nom)
        fonds_map[key] = f.id
        if f.institution:
            fonds_map[f"{_normalize_key(f.institution)}_{key}"] = f.id

    # Charger la correspondance nom -> id des intermediaires
    result = await db.execute(select(Intermediaire))
    intermediaire_map = {}
    for inter in result.scalars().all():
        key = _normalize_key(inter.nom)
        intermediaire_map[key] = inter.id

    # Charger les configs existantes pour eviter les doublons
    result = await db.execute(select(FundSiteConfig))
    existing_configs = set()
    for cfg in result.scalars().all():
        existing_configs.add((str(cfg.fonds_id), str(cfg.intermediaire_id or "")))

    count = 0
    for config_data in data:
        fonds_code = config_data.pop("fonds_code", "")
        intermediaire_name = config_data.pop("intermediaire_name", None)

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

        # Trouver l'intermediaire si specifie
        intermediaire_id = None
        if intermediaire_name:
            inter_key = _normalize_key(intermediaire_name)
            intermediaire_id = intermediaire_map.get(inter_key)
            if not intermediaire_id:
                # Correspondance partielle
                for key, iid in intermediaire_map.items():
                    if inter_key in key or key in inter_key:
                        intermediaire_id = iid
                        break

        # Verifier si cette combinaison fonds + intermediaire existe deja
        config_key = (str(fonds_id), str(intermediaire_id or ""))
        if config_key in existing_configs:
            continue

        config = FundSiteConfig(
            fonds_id=fonds_id,
            intermediaire_id=intermediaire_id,
            url_patterns=config_data.get("url_patterns", []),
            steps=config_data.get("steps", []),
            required_docs=config_data.get("required_docs", []),
            tips=config_data.get("tips"),
        )
        db.add(config)
        existing_configs.add(config_key)
        count += 1

    await db.commit()
    return count
