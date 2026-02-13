"""Handler builtin : calcul du score ESG multi-référentiel."""

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.esg_score import ESGScore
from app.models.referentiel_esg import ReferentielESG

logger = logging.getLogger(__name__)


async def calculate_esg_score(params: dict, context: dict) -> dict:
    """
    Calcule le score ESG selon UN ou PLUSIEURS référentiels.
    La grille vient de la BDD (pas codée en dur).

    params:
      - entreprise_id: str (UUID)
      - data: dict  (réponses aux critères, clé = critere_id, valeur = réponse)
      - referentiel_codes: list[str] | None
        Si None → score sur tous les référentiels actifs
        Si ["bceao_fd_2024"] → score sur ce référentiel uniquement
    """
    db: AsyncSession = context["db"]
    entreprise_id = params.get("entreprise_id") or context.get("entreprise_id")
    data: dict[str, Any] = params.get("data", {})
    ref_codes: list[str] | None = params.get("referentiel_codes")

    if not entreprise_id:
        return {"error": "entreprise_id est requis"}
    if not data:
        return {"error": "data est requis (réponses aux critères ESG)"}

    # 1. Charger les référentiels demandés
    query = select(ReferentielESG).where(ReferentielESG.is_active.is_(True))
    if ref_codes:
        query = query.where(ReferentielESG.code.in_(ref_codes))
    query = query.order_by(ReferentielESG.nom)

    result = await db.execute(query)
    referentiels = result.scalars().all()

    if not referentiels:
        return {"error": "Aucun référentiel trouvé", "scores": []}

    # 2. Calculer le score pour chaque référentiel
    resultats = []

    for ref in referentiels:
        grille = ref.grille_json
        methode = grille.get("methode_aggregation", "weighted_average")
        scores_piliers: dict[str, dict] = {}

        for pilier_key, pilier_config in grille.get("piliers", {}).items():
            critere_scores = []

            for critere in pilier_config.get("criteres", []):
                critere_id = critere["id"]
                valeur = data.get(critere_id)

                if valeur is None:
                    score_critere = 0
                elif critere["type"] == "quantitatif":
                    score_critere = _score_quantitatif(valeur, critere.get("seuils", {}))
                elif critere["type"] == "qualitatif":
                    score_critere = _score_qualitatif(valeur, critere.get("options", []))
                else:
                    score_critere = min(max(int(valeur), 0), 100)

                critere_scores.append({
                    "id": critere_id,
                    "label": critere["label"],
                    "poids": critere["poids"],
                    "score": score_critere,
                    "statut": _statut(score_critere),
                    "valeur_brute": valeur,
                })

            # Score du pilier = somme pondérée des critères
            pilier_score = sum(c["poids"] * c["score"] for c in critere_scores)
            scores_piliers[pilier_key] = {
                "score": round(pilier_score, 1),
                "poids_global": pilier_config["poids_global"],
                "criteres": critere_scores,
            }

        # Score global selon la méthode du référentiel
        if methode == "threshold":
            all_above = True
            for pilier_config in grille.get("piliers", {}).values():
                for critere in pilier_config.get("criteres", []):
                    seuil_min = critere.get("seuil_minimum")
                    if seuil_min is not None:
                        score_c = next(
                            (
                                c["score"]
                                for p in scores_piliers.values()
                                for c in p["criteres"]
                                if c["id"] == critere["id"]
                            ),
                            0,
                        )
                        if score_c < seuil_min:
                            all_above = False
                            break
            score_global = (
                sum(p["score"] * p["poids_global"] for p in scores_piliers.values())
                if all_above
                else 0
            )
        else:
            # weighted_average (défaut)
            score_global = sum(
                p["score"] * p["poids_global"] for p in scores_piliers.values()
            )

        score_global = round(score_global, 1)

        # Sauvegarder en BDD
        details = {
            "referentiel": ref.nom,
            "referentiel_code": ref.code,
            "methode": methode,
            **{k: v for k, v in scores_piliers.items()},
        }
        esg_score = ESGScore(
            entreprise_id=entreprise_id,
            referentiel_id=ref.id,
            score_e=scores_piliers.get("environnement", {}).get("score", 0),
            score_s=scores_piliers.get("social", {}).get("score", 0),
            score_g=scores_piliers.get("gouvernance", {}).get("score", 0),
            score_global=score_global,
            details_json=details,
            source="conversation",
        )
        db.add(esg_score)

        resultats.append({
            "referentiel": ref.nom,
            "referentiel_code": ref.code,
            "institution": ref.institution,
            "score_global": score_global,
            "niveau": _niveau(score_global),
            "scores_piliers": {k: v["score"] for k, v in scores_piliers.items()},
            "details": scores_piliers,
        })

    await db.commit()

    # 3. Identifier les données manquantes
    all_critere_ids: set[str] = set()
    for ref in referentiels:
        for p in ref.grille_json.get("piliers", {}).values():
            for c in p.get("criteres", []):
                all_critere_ids.add(c["id"])

    donnees_manquantes = [cid for cid in sorted(all_critere_ids) if cid not in data]

    # Enrichir les données manquantes avec les questions de collecte
    questions_manquantes = []
    for ref in referentiels:
        for p in ref.grille_json.get("piliers", {}).values():
            for c in p.get("criteres", []):
                if c["id"] in donnees_manquantes and c["id"] not in [
                    q["id"] for q in questions_manquantes
                ]:
                    questions_manquantes.append({
                        "id": c["id"],
                        "label": c["label"],
                        "type": c["type"],
                        "question": c.get("question_collecte", ""),
                    })

    return {
        "nombre_referentiels": len(resultats),
        "scores": resultats,
        "donnees_manquantes": donnees_manquantes,
        "questions_manquantes": questions_manquantes,
    }


# ── Fonctions utilitaires de scoring ──────────────────────────────────


def _score_quantitatif(valeur: Any, seuils: dict) -> int:
    """
    Convertit une valeur numérique en score 0-100 selon les seuils définis.
    Les seuils sont testés du meilleur (excellent) au pire (faible).
    """
    try:
        valeur = float(valeur)
    except (TypeError, ValueError):
        return 0

    for niveau in ["excellent", "bon", "moyen", "faible"]:
        seuil = seuils.get(niveau)
        if not seuil:
            continue
        # Seuil "min" → la valeur doit être >= min
        if "min" in seuil and valeur >= seuil["min"]:
            return seuil["score"]
        # Seuil "max" → la valeur doit être <= max
        if "max" in seuil and valeur <= seuil["max"]:
            return seuil["score"]
    return 0


def _score_qualitatif(valeur: Any, options: list[dict]) -> int:
    """
    Trouve le score correspondant à une réponse qualitative.
    Comparaison insensible à la casse.
    """
    valeur_str = str(valeur).strip().lower()
    for option in options:
        if option["label"].strip().lower() == valeur_str:
            return option["score"]
    # Tentative de correspondance partielle (le LLM peut reformuler)
    for option in options:
        if valeur_str in option["label"].strip().lower() or option["label"].strip().lower() in valeur_str:
            return option["score"]
    return 0


def _statut(score: int | float) -> str:
    """Détermine le statut de conformité selon le score."""
    if score >= 70:
        return "conforme"
    if score >= 40:
        return "partiel"
    return "non_conforme"


def _niveau(score: int | float) -> str:
    """Détermine le niveau qualitatif selon le score global."""
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Bon"
    if score >= 40:
        return "À améliorer"
    return "Insuffisant"
