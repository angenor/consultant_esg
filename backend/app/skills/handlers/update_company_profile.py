"""Handler builtin : met à jour le profil d'une entreprise (merge, pas écrasement)."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entreprise import Entreprise


async def update_company_profile(params: dict, context: dict) -> dict:
    """
    Met à jour profil_json de l'entreprise par merge (pas d'écrasement des données existantes).
    Exemples de clés : pratiques_environnementales, certifications, objectifs_declares, risques_identifies.
    """
    db: AsyncSession = context["db"]
    entreprise_id = params["entreprise_id"]
    updates = params.get("updates", {})

    if not updates:
        return {"error": "Aucune mise à jour fournie"}

    result = await db.execute(
        select(Entreprise).where(Entreprise.id == entreprise_id)
    )
    entreprise = result.scalar_one_or_none()

    if not entreprise:
        return {"error": f"Entreprise '{entreprise_id}' introuvable"}

    # Merge du profil_json existant avec les nouvelles données
    profil = dict(entreprise.profil_json or {})
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(profil.get(key), dict):
            # Merge profond pour les sous-dicts
            profil[key] = {**profil[key], **value}
        elif isinstance(value, list) and isinstance(profil.get(key), list):
            # Concaténation pour les listes (dédupliquées)
            existing = profil[key]
            for item in value:
                if item not in existing:
                    existing.append(item)
            profil[key] = existing
        else:
            profil[key] = value

    entreprise.profil_json = profil
    entreprise.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "status": "updated",
        "entreprise_id": str(entreprise.id),
        "updated_keys": list(updates.keys()),
        "profil": profil,
    }
