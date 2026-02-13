"""Handler builtin : liste les référentiels ESG disponibles."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.referentiel_esg import ReferentielESG
from app.models.fonds_vert import FondsVert


async def list_referentiels(params: dict, context: dict) -> dict:
    """
    Liste les référentiels ESG actifs.
    Le LLM utilise ce skill pour savoir quels référentiels existent
    et recommander le bon selon le fonds visé.
    """
    db: AsyncSession = context["db"]
    region = params.get("region")
    fonds_id = params.get("fonds_id")
    include_criteres = params.get("include_criteres", False)

    # Référentiel lié à un fonds spécifique
    if fonds_id:
        result = await db.execute(
            select(FondsVert).where(FondsVert.id == fonds_id)
        )
        fonds = result.scalar_one_or_none()
        if fonds and fonds.referentiel_id:
            result = await db.execute(
                select(ReferentielESG).where(ReferentielESG.id == fonds.referentiel_id)
            )
            ref = result.scalar_one_or_none()
            if ref:
                return {"referentiels": [_format_ref(ref, include_criteres)]}
        return {"referentiels": [], "note": "Ce fonds n'a pas de référentiel associé"}

    # Liste tous les référentiels actifs (optionnellement filtrés par région)
    query = select(ReferentielESG).where(ReferentielESG.is_active.is_(True))
    if region:
        query = query.where(ReferentielESG.region == region)
    query = query.order_by(ReferentielESG.nom)

    result = await db.execute(query)
    refs = result.scalars().all()

    return {
        "nombre": len(refs),
        "referentiels": [_format_ref(r, include_criteres) for r in refs],
    }


def _format_ref(ref: ReferentielESG, include_criteres: bool = False) -> dict:
    grille = ref.grille_json or {}
    result = {
        "id": str(ref.id),
        "code": ref.code,
        "nom": ref.nom,
        "institution": ref.institution,
        "region": ref.region,
        "methode": grille.get("methode_aggregation"),
        "piliers": {},
    }
    for pilier, config in grille.get("piliers", {}).items():
        pilier_info: dict = {
            "poids": config.get("poids_global"),
            "nb_criteres": len(config.get("criteres", [])),
        }
        if include_criteres:
            pilier_info["criteres"] = [
                {
                    "id": c["id"],
                    "label": c["label"],
                    "type": c["type"],
                    "poids": c["poids"],
                    "question_collecte": c.get("question_collecte", ""),
                    **({"options": [o["label"] for o in c["options"]]} if c["type"] == "qualitatif" else {}),
                    **({"unite": c.get("unite", "")} if c["type"] == "quantitatif" else {}),
                }
                for c in config.get("criteres", [])
            ]
        result["piliers"][pilier] = pilier_info
    return result
