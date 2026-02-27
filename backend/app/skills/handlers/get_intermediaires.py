"""Handler builtin : liste les intermédiaires d'un fonds vert."""

import logging

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intermediaire import Intermediaire

logger = logging.getLogger(__name__)


async def get_intermediaires(params: dict, context: dict) -> dict:
    """
    Liste les intermédiaires disponibles pour un fonds vert,
    filtrables par pays et type.

    params:
      - fonds_id: str (requis)
      - pays: str (optionnel, filtre par pays — inclut les intermédiaires régionaux)
      - type: str (optionnel, ex: banque_partenaire, entite_accreditee, agence_nationale, bmd)
    """
    db: AsyncSession = context["db"]
    fonds_id = params.get("fonds_id")
    pays = params.get("pays")
    type_filtre = params.get("type")

    if not fonds_id:
        return {"error": "fonds_id est requis"}

    query = (
        select(Intermediaire)
        .where(
            Intermediaire.fonds_id == fonds_id,
            Intermediaire.is_active.is_(True),
        )
        .order_by(Intermediaire.est_recommande.desc(), Intermediaire.nom)
    )

    if pays is not None:
        query = query.where(
            or_(Intermediaire.pays == pays, Intermediaire.pays.is_(None))
        )
    if type_filtre is not None:
        query = query.where(Intermediaire.type == type_filtre)

    result = await db.execute(query)
    rows = result.scalars().all()

    intermediaires = []
    for i in rows:
        intermediaires.append({
            "id": str(i.id),
            "fonds_id": str(i.fonds_id),
            "nom": i.nom,
            "type": i.type,
            "pays": i.pays,
            "ville": i.ville,
            "email": i.email,
            "telephone": i.telephone,
            "adresse": i.adresse,
            "site_web": i.site_web,
            "url_formulaire": i.url_formulaire,
            "type_soumission": i.type_soumission,
            "instructions_soumission": i.instructions_soumission,
            "documents_requis": i.documents_requis or [],
            "etapes_specifiques": i.etapes_specifiques or [],
            "delai_traitement": i.delai_traitement,
            "est_recommande": i.est_recommande,
            "notes": i.notes,
        })

    return {
        "nombre": len(intermediaires),
        "intermediaires": intermediaires,
    }
