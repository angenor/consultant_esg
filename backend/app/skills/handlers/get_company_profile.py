"""Handler builtin : récupère le profil complet d'une entreprise."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entreprise import Entreprise


async def get_company_profile(params: dict, context: dict) -> dict:
    """
    Charge l'entreprise depuis la BDD et retourne un dict structuré
    avec toutes les infos connues (infos de base + profil_json enrichi).
    """
    db: AsyncSession = context["db"]
    entreprise_id = params["entreprise_id"]

    result = await db.execute(
        select(Entreprise).where(Entreprise.id == entreprise_id)
    )
    entreprise = result.scalar_one_or_none()

    if not entreprise:
        return {"error": f"Entreprise '{entreprise_id}' introuvable"}

    profil = entreprise.profil_json or {}

    return {
        "id": str(entreprise.id),
        "nom": entreprise.nom,
        "secteur": entreprise.secteur,
        "sous_secteur": entreprise.sous_secteur,
        "pays": entreprise.pays,
        "ville": entreprise.ville,
        "effectifs": entreprise.effectifs,
        "chiffre_affaires": float(entreprise.chiffre_affaires) if entreprise.chiffre_affaires else None,
        "devise": entreprise.devise,
        "description": entreprise.description,
        "profil": profil,
    }
