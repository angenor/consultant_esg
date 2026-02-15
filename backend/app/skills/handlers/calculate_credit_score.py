"""Handler builtin : calcul du score crédit vert alternatif (Module 5)."""

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_plan import ActionPlan
from app.models.credit_score import CreditScore
from app.models.document import Document
from app.models.esg_score import ESGScore

logger = logging.getLogger(__name__)

# Pondérations par défaut (configurable)
POIDS_SOLVABILITE = 0.50
POIDS_IMPACT_VERT = 0.50


async def calculate_credit_score(params: dict, context: dict) -> dict:
    """
    Calcule le score crédit vert alternatif.

    Combine un score de solvabilité financière (données déclaratives)
    et un score d'impact vert (données ESG) pour produire un score unique
    qui favorise les entreprises engagées dans la transition écologique.

    params:
      - entreprise_id: str (UUID)
      - donnees_financieres: dict (optionnel)
          - regularite_transactions: int (0-100, auto-évaluation)
          - volume_mensuel_moyen: float (en XOF)
          - anciennete_mois: int
      - donnees_declaratives: dict (optionnel)
          - pratiques_vertes: list[str]
          - projets_verts_en_cours: bool
          - participation_programmes: list[str]
      - poids_solvabilite: float (optionnel, défaut 0.50)
      - poids_impact_vert: float (optionnel, défaut 0.50)
    """
    db: AsyncSession = context["db"]
    entreprise_id = params.get("entreprise_id") or context.get("entreprise_id")

    if not entreprise_id:
        return {"error": "entreprise_id est requis"}

    donnees_fin = params.get("donnees_financieres", {})
    donnees_decl = params.get("donnees_declaratives", {})
    poids_solv = params.get("poids_solvabilite", POIDS_SOLVABILITE)
    poids_vert = params.get("poids_impact_vert", POIDS_IMPACT_VERT)
    referentiel_id = params.get("referentiel_id")

    facteurs_positifs: list[dict] = []
    facteurs_negatifs: list[dict] = []

    # ── 1. Score solvabilité (0-100) ──

    score_solv, f_pos, f_neg = await _calculer_solvabilite(
        db, entreprise_id, donnees_fin
    )
    facteurs_positifs.extend(f_pos)
    facteurs_negatifs.extend(f_neg)

    # ── 2. Score impact vert (0-100) ──

    score_vert, f_pos, f_neg, donnees_esg = await _calculer_impact_vert(
        db, entreprise_id, donnees_decl, referentiel_id=referentiel_id
    )
    facteurs_positifs.extend(f_pos)
    facteurs_negatifs.extend(f_neg)

    # ── 3. Score combiné ──

    score_combine = round(score_solv * poids_solv + score_vert * poids_vert, 1)

    # ── 4. Recommandations ──

    recommandations = _generer_recommandations(
        score_solv, score_vert, donnees_fin, donnees_decl, donnees_esg
    )

    # ── 5. Sauvegarder en BDD ──

    facteurs_json = {
        "facteurs_positifs": facteurs_positifs,
        "facteurs_negatifs": facteurs_negatifs,
    }

    credit_score = CreditScore(
        entreprise_id=entreprise_id,
        score_solvabilite=score_solv,
        score_impact_vert=score_vert,
        score_combine=score_combine,
        donnees_financieres_json=donnees_fin or None,
        donnees_esg_json=donnees_esg or None,
        donnees_declaratives_json=donnees_decl or None,
        facteurs_json=facteurs_json,
    )
    db.add(credit_score)
    await db.commit()
    await db.refresh(credit_score)

    return {
        "id": str(credit_score.id),
        "score_solvabilite": score_solv,
        "score_impact_vert": score_vert,
        "score_combine": score_combine,
        "niveau": _niveau_credit(score_combine),
        "facteurs": facteurs_json,
        "recommandations": recommandations,
        "poids": {
            "solvabilite": poids_solv,
            "impact_vert": poids_vert,
        },
    }


# ── Calcul solvabilité ──────────────────────────────────────────────


async def _calculer_solvabilite(
    db: AsyncSession, entreprise_id: str, donnees_fin: dict
) -> tuple[float, list[dict], list[dict]]:
    """Score de solvabilité basé sur les données financières déclaratives."""
    facteurs_pos: list[dict] = []
    facteurs_neg: list[dict] = []
    composantes: list[tuple[float, float]] = []  # (score, poids)

    # Régularité des transactions (0-100) — poids 30%
    regularite = donnees_fin.get("regularite_transactions")
    if regularite is not None:
        regularite = max(0, min(100, int(regularite)))
        composantes.append((regularite, 0.30))
        if regularite >= 70:
            facteurs_pos.append({
                "facteur": f"Transactions régulières ({regularite}/100)",
                "impact": f"+{round(regularite * 0.30 * 0.15)}",
                "categorie": "solvabilite",
            })
        elif regularite < 40:
            facteurs_neg.append({
                "facteur": f"Transactions irrégulières ({regularite}/100)",
                "impact": f"-{round((100 - regularite) * 0.30 * 0.15)}",
                "categorie": "solvabilite",
            })
    else:
        composantes.append((30, 0.30))  # Valeur par défaut conservatrice
        facteurs_neg.append({
            "facteur": "Régularité des transactions non renseignée",
            "impact": "-10",
            "categorie": "solvabilite",
        })

    # Volume d'activité mensuel — poids 25%
    volume = donnees_fin.get("volume_mensuel_moyen")
    if volume is not None:
        volume = float(volume)
        score_volume = _score_volume(volume)
        composantes.append((score_volume, 0.25))
        if score_volume >= 60:
            facteurs_pos.append({
                "facteur": f"Volume d'activité significatif ({volume:,.0f} XOF/mois)",
                "impact": f"+{round(score_volume * 0.25 * 0.15)}",
                "categorie": "solvabilite",
            })
        elif score_volume < 40:
            facteurs_neg.append({
                "facteur": f"Volume d'activité faible ({volume:,.0f} XOF/mois)",
                "impact": f"-{round((100 - score_volume) * 0.25 * 0.10)}",
                "categorie": "solvabilite",
            })
    else:
        composantes.append((25, 0.25))
        facteurs_neg.append({
            "facteur": "Volume d'activité non renseigné",
            "impact": "-8",
            "categorie": "solvabilite",
        })

    # Ancienneté — poids 25%
    anciennete = donnees_fin.get("anciennete_mois")
    if anciennete is not None:
        anciennete = int(anciennete)
        score_anc = _score_anciennete(anciennete)
        composantes.append((score_anc, 0.25))
        if anciennete >= 24:
            facteurs_pos.append({
                "facteur": f"Entreprise établie ({anciennete} mois d'activité)",
                "impact": f"+{round(score_anc * 0.25 * 0.15)}",
                "categorie": "solvabilite",
            })
        elif anciennete < 12:
            facteurs_neg.append({
                "facteur": f"Entreprise récente ({anciennete} mois)",
                "impact": f"-{round((100 - score_anc) * 0.25 * 0.10)}",
                "categorie": "solvabilite",
            })
    else:
        composantes.append((20, 0.25))
        facteurs_neg.append({
            "facteur": "Ancienneté non renseignée",
            "impact": "-8",
            "categorie": "solvabilite",
        })

    # Documents financiers uploadés — poids 20%
    result = await db.execute(
        select(func.count(Document.id)).where(
            Document.entreprise_id == entreprise_id
        )
    )
    nb_docs = result.scalar() or 0
    score_docs = min(100, nb_docs * 20)  # 5 docs = 100
    composantes.append((score_docs, 0.20))
    if nb_docs >= 3:
        facteurs_pos.append({
            "facteur": f"{nb_docs} document(s) financier(s) fourni(s)",
            "impact": f"+{round(score_docs * 0.20 * 0.15)}",
            "categorie": "solvabilite",
        })
    elif nb_docs == 0:
        facteurs_neg.append({
            "facteur": "Aucun document financier fourni",
            "impact": "-10",
            "categorie": "solvabilite",
        })

    # Score final solvabilité
    total_poids = sum(p for _, p in composantes)
    score_solv = round(
        sum(s * p for s, p in composantes) / total_poids if total_poids > 0 else 0, 1
    )

    return score_solv, facteurs_pos, facteurs_neg


# ── Calcul impact vert ───────────────────────────────────────────────


async def _calculer_impact_vert(
    db: AsyncSession, entreprise_id: str, donnees_decl: dict,
    referentiel_id: str | None = None,
) -> tuple[float, list[dict], list[dict], dict]:
    """Score d'impact vert basé sur les données ESG et pratiques déclarées."""
    facteurs_pos: list[dict] = []
    facteurs_neg: list[dict] = []
    composantes: list[tuple[float, float]] = []

    # Récupérer les données ESG depuis la BDD
    donnees_esg: dict[str, Any] = {}

    # Dernier score ESG — poids 40% (exclure les scores à zéro)
    esg_filters = [
        ESGScore.entreprise_id == entreprise_id,
        ESGScore.score_global > 0,
    ]
    if referentiel_id:
        esg_filters.append(ESGScore.referentiel_id == referentiel_id)
    result = await db.execute(
        select(ESGScore)
        .where(*esg_filters)
        .order_by(ESGScore.created_at.desc())
        .limit(2)
    )
    scores_esg = result.scalars().all()

    if scores_esg:
        dernier = scores_esg[0]
        score_esg = float(dernier.score_global or 0)
        donnees_esg["dernier_score_esg"] = score_esg
        donnees_esg["referentiel_id"] = str(dernier.referentiel_id) if dernier.referentiel_id else None

        composantes.append((score_esg, 0.40))
        if score_esg >= 60:
            facteurs_pos.append({
                "facteur": f"Score ESG élevé ({score_esg}/100)",
                "impact": f"+{round(score_esg * 0.40 * 0.15)}",
                "categorie": "impact_vert",
            })
        elif score_esg < 40:
            facteurs_neg.append({
                "facteur": f"Score ESG faible ({score_esg}/100)",
                "impact": f"-{round((100 - score_esg) * 0.40 * 0.10)}",
                "categorie": "impact_vert",
            })

        # Tendance (comparaison des 2 derniers scores) — poids 15%
        if len(scores_esg) >= 2:
            precedent = float(scores_esg[1].score_global or 0)
            diff = score_esg - precedent
            donnees_esg["tendance"] = "hausse" if diff > 0 else "baisse" if diff < 0 else "stable"
            if diff > 0:
                score_tendance = min(100, 60 + diff * 2)
                facteurs_pos.append({
                    "facteur": f"Score ESG en hausse (+{diff:.1f} points)",
                    "impact": f"+{round(score_tendance * 0.15 * 0.10)}",
                    "categorie": "impact_vert",
                })
            elif diff < 0:
                score_tendance = max(0, 40 + diff * 2)
                facteurs_neg.append({
                    "facteur": f"Score ESG en baisse ({diff:.1f} points)",
                    "impact": f"-{round((100 - score_tendance) * 0.15 * 0.05)}",
                    "categorie": "impact_vert",
                })
            else:
                score_tendance = 50
            composantes.append((score_tendance, 0.15))
        else:
            donnees_esg["tendance"] = "premier_score"
            composantes.append((50, 0.15))  # Neutre si pas de comparaison
    else:
        composantes.append((0, 0.40))
        composantes.append((0, 0.15))
        facteurs_neg.append({
            "facteur": "Aucun score ESG disponible",
            "impact": "-20",
            "categorie": "impact_vert",
        })

    # Certifications déclarées — poids 15%
    certifications = donnees_decl.get("certifications", [])
    donnees_esg["certifications"] = certifications
    if certifications:
        score_cert = min(100, len(certifications) * 35)
        composantes.append((score_cert, 0.15))
        facteurs_pos.append({
            "facteur": f"{len(certifications)} certification(s) : {', '.join(certifications[:3])}",
            "impact": f"+{round(score_cert * 0.15 * 0.15)}",
            "categorie": "impact_vert",
        })
    else:
        composantes.append((0, 0.15))
        facteurs_neg.append({
            "facteur": "Pas de certification environnementale",
            "impact": "-5",
            "categorie": "impact_vert",
        })

    # Plan d'action actif — poids 15%
    result = await db.execute(
        select(func.count(ActionPlan.id)).where(
            ActionPlan.entreprise_id == entreprise_id
        )
    )
    nb_plans = result.scalar() or 0
    if nb_plans > 0:
        composantes.append((80, 0.15))
        facteurs_pos.append({
            "facteur": f"Plan d'action ESG actif ({nb_plans} plan(s))",
            "impact": "+8",
            "categorie": "impact_vert",
        })
    else:
        composantes.append((0, 0.15))
        facteurs_neg.append({
            "facteur": "Aucun plan d'action ESG",
            "impact": "-5",
            "categorie": "impact_vert",
        })

    # Pratiques vertes déclarées — poids 15%
    pratiques = donnees_decl.get("pratiques_vertes", [])
    projets_verts = donnees_decl.get("projets_verts_en_cours", False)
    programmes = donnees_decl.get("participation_programmes", [])

    score_pratiques = 0
    if pratiques:
        score_pratiques += min(50, len(pratiques) * 15)
    if projets_verts:
        score_pratiques += 25
    if programmes:
        score_pratiques += min(25, len(programmes) * 15)
    score_pratiques = min(100, score_pratiques)
    composantes.append((score_pratiques, 0.15))

    if score_pratiques >= 40:
        details = []
        if pratiques:
            details.append(f"{len(pratiques)} pratique(s) verte(s)")
        if projets_verts:
            details.append("projets verts en cours")
        if programmes:
            details.append(f"programme(s): {', '.join(programmes[:2])}")
        facteurs_pos.append({
            "facteur": f"Engagement écologique : {', '.join(details)}",
            "impact": f"+{round(score_pratiques * 0.15 * 0.15)}",
            "categorie": "impact_vert",
        })
    elif not pratiques and not projets_verts and not programmes:
        facteurs_neg.append({
            "facteur": "Aucune pratique verte déclarée",
            "impact": "-5",
            "categorie": "impact_vert",
        })

    # Score final impact vert
    total_poids = sum(p for _, p in composantes)
    score_vert = round(
        sum(s * p for s, p in composantes) / total_poids if total_poids > 0 else 0, 1
    )

    return score_vert, facteurs_pos, facteurs_neg, donnees_esg


# ── Recommandations ──────────────────────────────────────────────────


def _generer_recommandations(
    score_solv: float,
    score_vert: float,
    donnees_fin: dict,
    donnees_decl: dict,
    donnees_esg: dict,
) -> list[str]:
    """Génère des recommandations personnalisées pour améliorer le score."""
    recs: list[str] = []

    # Recommandations solvabilité
    if score_solv < 50:
        if not donnees_fin.get("regularite_transactions"):
            recs.append(
                "Renseignez la régularité de vos transactions pour améliorer "
                "votre score de solvabilité."
            )
        if not donnees_fin.get("volume_mensuel_moyen"):
            recs.append(
                "Indiquez votre volume d'activité mensuel moyen pour "
                "renforcer votre profil financier."
            )
        if not donnees_fin.get("anciennete_mois"):
            recs.append(
                "Précisez l'ancienneté de votre entreprise — les entreprises "
                "établies obtiennent un meilleur score."
            )

    if score_solv < 70:
        recs.append(
            "Uploadez vos documents financiers (bilans, relevés bancaires) "
            "pour justifier votre solvabilité."
        )

    # Recommandations impact vert
    if not donnees_esg.get("dernier_score_esg"):
        recs.append(
            "Réalisez une évaluation ESG via le chat pour obtenir un score "
            "— c'est le facteur le plus important de l'impact vert."
        )
    elif donnees_esg.get("dernier_score_esg", 0) < 60:
        recs.append(
            "Améliorez votre score ESG en suivant les recommandations "
            "du dernier diagnostic. Chaque point compte."
        )

    if donnees_esg.get("tendance") == "baisse":
        recs.append(
            "Votre score ESG est en baisse — créez un plan d'action "
            "pour inverser la tendance."
        )

    if not donnees_decl.get("certifications"):
        recs.append(
            "Obtenez une certification environnementale (ISO 14001, "
            "label vert local) pour un boost significatif."
        )

    if not donnees_decl.get("pratiques_vertes"):
        recs.append(
            "Déclarez vos pratiques vertes (tri des déchets, énergie "
            "solaire, etc.) via le chat."
        )

    if not donnees_decl.get("participation_programmes"):
        recs.append(
            "Participez à un programme vert (REDD+, économie circulaire) "
            "pour améliorer votre profil."
        )

    # Limiter à 5 recommandations max
    return recs[:5]


# ── Utilitaires ──────────────────────────────────────────────────────


def _score_volume(volume: float) -> int:
    """Convertit un volume mensuel (XOF) en score 0-100."""
    # Seuils adaptés aux PME africaines (en XOF)
    if volume >= 10_000_000:  # 10M+ XOF/mois
        return 100
    if volume >= 5_000_000:
        return 85
    if volume >= 2_000_000:
        return 70
    if volume >= 1_000_000:
        return 55
    if volume >= 500_000:
        return 40
    if volume >= 100_000:
        return 25
    return 10


def _score_anciennete(mois: int) -> int:
    """Convertit l'ancienneté (mois) en score 0-100."""
    if mois >= 60:  # 5+ ans
        return 100
    if mois >= 36:  # 3+ ans
        return 85
    if mois >= 24:  # 2+ ans
        return 70
    if mois >= 12:  # 1+ an
        return 50
    if mois >= 6:
        return 30
    return 15


def _niveau_credit(score: float) -> str:
    """Détermine le niveau qualitatif du crédit vert."""
    if score >= 80:
        return "Excellent"
    if score >= 65:
        return "Bon"
    if score >= 50:
        return "Acceptable"
    if score >= 35:
        return "À améliorer"
    return "Insuffisant"
