"""Handler builtin : recherche de fonds verts compatibles (SQL + RAG)."""

import logging

from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fonds_vert import FondsVert, FondsChunk
from app.models.intermediaire import Intermediaire
from app.models.referentiel_esg import ReferentielESG

logger = logging.getLogger(__name__)

_MODE_ACCES_LABELS = {
    "banque_partenaire": "Via banque partenaire locale",
    "entite_accreditee": "Via entité nationale accréditée",
    "appel_propositions": "Appel à propositions périodique",
    "banque_multilaterale": "Via banque multilatérale de développement",
    "direct": "Candidature directe",
    "garantie_bancaire": "Demande via votre banque (garantie)",
}


async def search_green_funds(params: dict, context: dict) -> dict:
    """
    Recherche les fonds verts compatibles avec le profil de l'entreprise.

    Étape 1 : Filtrage SQL (rapide) sur fonds_verts
    Étape 2 : RAG sur fonds_chunks pour les critères détaillés
    Étape 3 : Score de compatibilité simplifié

    params:
      - secteur: str (secteur d'activité)
      - pays: str (code pays ISO 3, ex: "CIV")
      - montant_recherche: float (montant recherché, optionnel)
      - score_esg: float (score ESG actuel, optionnel)
    """
    db: AsyncSession = context["db"]
    secteur = params.get("secteur")
    pays = params.get("pays", "CIV")
    montant = params.get("montant_recherche")
    score_esg = params.get("score_esg")

    # ── Étape 1 : Filtrage SQL ──

    query = select(FondsVert, ReferentielESG).outerjoin(
        ReferentielESG, FondsVert.referentiel_id == ReferentielESG.id
    ).where(FondsVert.is_active.is_(True))

    # Filtre date limite (fonds non expirés)
    query = query.where(
        (FondsVert.date_limite.is_(None)) | (FondsVert.date_limite > func.current_date())
    )

    query = query.order_by(FondsVert.montant_max.desc())

    result = await db.execute(query)
    rows = result.all()

    if not rows:
        return {"nombre_fonds": 0, "fonds": [], "message": "Aucun fonds vert actif trouvé."}

    # ── Étape 2 : Scoring de compatibilité + RAG ──

    resultats = []

    for fonds, ref in rows[:15]:  # Max 15 fonds à évaluer
        compatibilite = 50  # Score de base

        # Bonus secteur
        if secteur and fonds.secteurs_json:
            secteur_lower = secteur.lower()
            secteurs_fonds = [s.lower() for s in fonds.secteurs_json]
            if secteur_lower in secteurs_fonds:
                compatibilite += 15
            elif any(secteur_lower in s or s in secteur_lower for s in secteurs_fonds):
                compatibilite += 10

        # Bonus pays
        if pays and fonds.pays_eligibles:
            pays_upper = pays.upper()
            if pays_upper in [p.upper() for p in fonds.pays_eligibles]:
                compatibilite += 10

        # Bonus montant dans la fourchette
        if montant is not None:
            min_ok = fonds.montant_min is None or montant >= float(fonds.montant_min)
            max_ok = fonds.montant_max is None or montant <= float(fonds.montant_max)
            if min_ok and max_ok:
                compatibilite += 10
            elif min_ok or max_ok:
                compatibilite += 5

        # Bonus score ESG au-dessus du minimum requis
        score_min_requis = None
        if fonds.criteres_json and "score_esg_minimum" in fonds.criteres_json:
            score_min_requis = fonds.criteres_json["score_esg_minimum"]
        if score_esg is not None and score_min_requis is not None:
            if score_esg >= score_min_requis:
                compatibilite += 15
            elif score_esg >= score_min_requis * 0.8:
                compatibilite += 5
            else:
                compatibilite -= 10

        # Recherche RAG dans fonds_chunks (si disponible)
        criteres_extraits = []
        try:
            if secteur:
                rag_query = f"critères éligibilité {secteur} PME {pays}"
            else:
                rag_query = f"critères éligibilité PME {pays}"

            from app.rag.embeddings import get_embedding
            query_embedding = await get_embedding(rag_query)
            embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

            chunk_result = await db.execute(
                text("""
                    SELECT contenu, type_info,
                           1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
                    FROM fonds_chunks
                    WHERE fonds_id = :fonds_id
                    ORDER BY embedding <=> CAST(:embedding AS vector)
                    LIMIT 3
                """),
                {"embedding": embedding_str, "fonds_id": str(fonds.id)},
            )
            chunks = chunk_result.mappings().all()

            for chunk in chunks:
                criteres_extraits.append(chunk["contenu"])
                if chunk["similarity"] > 0.5:
                    compatibilite += 5

        except Exception as e:
            logger.debug("RAG indisponible pour fonds %s : %s", fonds.nom, e)

        # Construire le résultat
        montant_min_val = float(fonds.montant_min) if fonds.montant_min else None
        montant_max_val = float(fonds.montant_max) if fonds.montant_max else None

        if montant_min_val and montant_max_val:
            montant_range = f"{_format_montant(montant_min_val)} - {_format_montant(montant_max_val)} {fonds.devise}"
        elif montant_max_val:
            montant_range = f"Jusqu'à {_format_montant(montant_max_val)} {fonds.devise}"
        else:
            montant_range = "Non spécifié"

        # Compter les intermédiaires pour ce fonds
        nb_intermediaires = 0
        try:
            inter_result = await db.execute(
                select(func.count(Intermediaire.id)).where(
                    Intermediaire.fonds_id == fonds.id,
                    Intermediaire.is_active.is_(True),
                )
            )
            nb_intermediaires = inter_result.scalar() or 0
        except Exception:
            pass

        resultats.append({
            "fonds_id": str(fonds.id),
            "nom": fonds.nom,
            "institution": fonds.institution,
            "type": fonds.type,
            "referentiel": ref.nom if ref else None,
            "referentiel_code": ref.code if ref else None,
            "montant_range": montant_range,
            "devise": fonds.devise,
            "secteurs": fonds.secteurs_json or [],
            "pays_eligibles": fonds.pays_eligibles or [],
            "score_esg_minimum": score_min_requis,
            "compatibilite": min(max(compatibilite, 0), 100),
            "criteres_extraits": criteres_extraits,
            "description": fonds.criteres_json.get("description", "") if fonds.criteres_json else "",
            "date_limite": str(fonds.date_limite) if fonds.date_limite else None,
            "url": fonds.url_source,
            "mode_acces": fonds.mode_acces,
            "mode_acces_label": _MODE_ACCES_LABELS.get(fonds.mode_acces or "", "Non spécifié"),
            "acces_details": fonds.criteres_json.get("acces_details") if fonds.criteres_json else None,
            "nb_intermediaires": nb_intermediaires,
            "candidature_directe": fonds.mode_acces == "direct",
        })

    # Trier par compatibilité décroissante
    resultats.sort(key=lambda x: x["compatibilite"], reverse=True)

    return {
        "nombre_fonds": len(resultats),
        "fonds": resultats,
    }


def _format_montant(montant: float) -> str:
    """Formate un montant avec séparateurs de milliers."""
    if montant >= 1_000_000_000:
        return f"{montant / 1_000_000_000:.1f}Md"
    if montant >= 1_000_000:
        return f"{montant / 1_000_000:.1f}M"
    if montant >= 1_000:
        return f"{montant / 1_000:.0f}K"
    return f"{montant:.0f}"
