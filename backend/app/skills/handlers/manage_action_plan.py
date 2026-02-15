"""Handler builtin : gestion des plans d'action ESG (Module 6)."""

import logging
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_plan import ActionItem, ActionPlan
from app.models.esg_score import ESGScore
from app.models.referentiel_esg import ReferentielESG

logger = logging.getLogger(__name__)


async def manage_action_plan(params: dict, context: dict) -> dict:
    """
    Crée ou met à jour un plan d'action structuré.

    params:
      - entreprise_id: str (UUID)
      - action: str — "create" | "add_item" | "update_status"
      - (create) referentiel_code: str | None, horizon: str, score_cible: float
      - (add_item) plan_id: str, titre: str, description: str, priorite: str, ...
      - (update_status) item_id: str, statut: str
    """
    db: AsyncSession = context["db"]
    entreprise_id = params.get("entreprise_id") or context.get("entreprise_id")
    action = params.get("action")

    if not entreprise_id:
        return {"error": "entreprise_id est requis"}
    if not action:
        return {"error": "action est requis (create, add_item, update_status)"}

    if action == "create":
        return await _create_plan(db, entreprise_id, params)
    elif action == "add_item":
        return await _add_item(db, params)
    elif action == "update_status":
        return await _update_status(db, params)
    else:
        return {"error": f"Action inconnue: {action}. Utilisez create, add_item ou update_status"}


# ── Action: create ───────────────────────────────────────────────────


async def _create_plan(db: AsyncSession, entreprise_id: str, params: dict) -> dict:
    """Crée un plan d'action basé sur les lacunes du dernier score ESG."""
    horizon = params.get("horizon", "12_mois")
    score_cible = params.get("score_cible")
    referentiel_code = params.get("referentiel_code")

    # Trouver le dernier score ESG
    query = (
        select(ESGScore)
        .where(ESGScore.entreprise_id == entreprise_id)
        .order_by(ESGScore.created_at.desc())
    )
    if referentiel_code:
        ref_result = await db.execute(
            select(ReferentielESG).where(ReferentielESG.code == referentiel_code)
        )
        ref = ref_result.scalar_one_or_none()
        if ref:
            query = query.where(ESGScore.referentiel_id == ref.id)

    result = await db.execute(query.limit(1))
    dernier_score = result.scalar_one_or_none()

    score_initial = float(dernier_score.score_global or 0) if dernier_score else 0
    if not score_cible:
        score_cible = min(100, score_initial + 15)

    referentiel_id = dernier_score.referentiel_id if dernier_score else None

    # Charger le référentiel pour analyser les lacunes
    ref_obj = None
    if referentiel_id:
        ref_result = await db.execute(
            select(ReferentielESG).where(ReferentielESG.id == referentiel_id)
        )
        ref_obj = ref_result.scalar_one_or_none()

    # Créer le plan
    titre = f"Plan d'amélioration ESG — {horizon.replace('_', ' ')}"
    if ref_obj:
        titre = f"Plan {ref_obj.nom} — {score_initial:.0f} → {score_cible:.0f}"

    plan = ActionPlan(
        entreprise_id=entreprise_id,
        titre=titre,
        type_plan="esg",
        horizon=horizon,
        referentiel_id=referentiel_id,
        score_initial=score_initial,
        score_cible=score_cible,
    )
    db.add(plan)
    await db.flush()

    # Générer les actions à partir des lacunes
    items = _generer_actions(
        plan.id, dernier_score, ref_obj, score_initial, score_cible, horizon
    )
    for item in items:
        db.add(item)

    await db.commit()
    await db.refresh(plan)

    # Charger les items créés
    result = await db.execute(
        select(ActionItem)
        .where(ActionItem.plan_id == plan.id)
        .order_by(ActionItem.echeance.asc().nulls_last())
    )
    plan_items = result.scalars().all()

    return _format_plan_response(plan, plan_items)


def _generer_actions(
    plan_id,
    dernier_score: ESGScore | None,
    ref_obj: ReferentielESG | None,
    score_initial: float,
    score_cible: float,
    horizon: str,
) -> list[ActionItem]:
    """Génère des actions basées sur les lacunes du score ESG."""
    items: list[ActionItem] = []
    today = date.today()

    # Durées selon l'horizon
    horizons_mois = {"6_mois": 6, "12_mois": 12, "24_mois": 24}
    mois_max = horizons_mois.get(horizon, 12)

    if dernier_score and dernier_score.details_json and ref_obj:
        # Analyser les critères faibles à partir du score détaillé
        details = dernier_score.details_json
        ecart = score_cible - score_initial

        for pilier_key in ["environnement", "social", "gouvernance"]:
            pilier_data = details.get(pilier_key, {})
            if not isinstance(pilier_data, dict):
                continue

            criteres = pilier_data.get("criteres", [])
            for critere in criteres:
                score_c = critere.get("score", 0)
                poids = critere.get("poids", 0)
                label = critere.get("label", "Critère")

                # Cibler les critères faibles (score < 60)
                if score_c < 60:
                    impact = round(poids * (70 - score_c) / 100 * pilier_data.get("poids_global", 0.33) * 100, 1)

                    if score_c < 30:
                        priorite = "quick_win" if impact > 2 else "moyen_terme"
                        echeance = today + timedelta(days=90)
                    elif score_c < 50:
                        priorite = "moyen_terme"
                        echeance = today + timedelta(days=min(180, mois_max * 30))
                    else:
                        priorite = "long_terme"
                        echeance = today + timedelta(days=min(365, mois_max * 30))

                    items.append(ActionItem(
                        plan_id=plan_id,
                        titre=f"Améliorer : {label}",
                        description=f"Score actuel: {score_c}/100. Objectif: atteindre au moins 70/100. "
                                    f"Pilier: {pilier_key}.",
                        priorite=priorite,
                        pilier=pilier_key,
                        critere_id=critere.get("id"),
                        statut="a_faire",
                        echeance=echeance,
                        impact_score_estime=max(0.5, impact),
                    ))

    # Si aucune action générée (pas de score détaillé), créer des actions génériques
    if not items:
        actions_generiques = [
            {
                "titre": "Réaliser un diagnostic ESG complet",
                "description": "Passer le questionnaire ESG sur un référentiel pour obtenir un score détaillé.",
                "priorite": "quick_win",
                "pilier": "gouvernance",
                "echeance": today + timedelta(days=14),
                "impact": 5.0,
            },
            {
                "titre": "Mettre en place le tri sélectif des déchets",
                "description": "Installer des bacs de tri, former le personnel, établir un partenariat avec un collecteur.",
                "priorite": "quick_win",
                "pilier": "environnement",
                "echeance": today + timedelta(days=30),
                "impact": 3.0,
            },
            {
                "titre": "Rédiger une politique environnementale",
                "description": "Document formalisant les engagements de l'entreprise en matière de protection de l'environnement.",
                "priorite": "quick_win",
                "pilier": "environnement",
                "echeance": today + timedelta(days=30),
                "impact": 2.5,
            },
            {
                "titre": "Former les employés aux pratiques durables",
                "description": "Organiser des sessions de sensibilisation à l'environnement et aux bonnes pratiques ESG.",
                "priorite": "moyen_terme",
                "pilier": "social",
                "echeance": today + timedelta(days=90),
                "impact": 3.0,
            },
            {
                "titre": "Réaliser un bilan carbone simplifié",
                "description": "Estimer l'empreinte carbone de l'entreprise (énergie, transport, déchets).",
                "priorite": "moyen_terme",
                "pilier": "environnement",
                "echeance": today + timedelta(days=60),
                "impact": 2.0,
            },
            {
                "titre": "Mettre en place un code de conduite éthique",
                "description": "Document cadrant les pratiques anticorruption, transparence et éthique des affaires.",
                "priorite": "moyen_terme",
                "pilier": "gouvernance",
                "echeance": today + timedelta(days=90),
                "impact": 2.5,
            },
            {
                "titre": "Obtenir une certification environnementale",
                "description": "Viser ISO 14001 ou un label vert local pour formaliser la démarche.",
                "priorite": "long_terme",
                "pilier": "environnement",
                "echeance": today + timedelta(days=min(365, mois_max * 30)),
                "impact": 5.0,
            },
        ]

        for a in actions_generiques:
            items.append(ActionItem(
                plan_id=plan_id,
                titre=a["titre"],
                description=a["description"],
                priorite=a["priorite"],
                pilier=a["pilier"],
                statut="a_faire",
                echeance=a["echeance"],
                impact_score_estime=a["impact"],
            ))

    # Trier par priorité (quick_win d'abord)
    ordre = {"quick_win": 0, "moyen_terme": 1, "long_terme": 2}
    items.sort(key=lambda i: (ordre.get(i.priorite, 1), i.echeance or date.max))

    return items


# ── Action: add_item ─────────────────────────────────────────────────


async def _add_item(db: AsyncSession, params: dict) -> dict:
    """Ajoute une action à un plan existant."""
    plan_id = params.get("plan_id")
    if not plan_id:
        return {"error": "plan_id est requis"}

    titre = params.get("titre")
    if not titre:
        return {"error": "titre est requis"}

    # Vérifier que le plan existe
    result = await db.execute(
        select(ActionPlan).where(ActionPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        return {"error": f"Plan '{plan_id}' introuvable"}

    echeance = None
    if params.get("echeance"):
        try:
            echeance = date.fromisoformat(params["echeance"])
        except ValueError:
            pass

    item = ActionItem(
        plan_id=plan_id,
        titre=titre,
        description=params.get("description"),
        priorite=params.get("priorite", "moyen_terme"),
        pilier=params.get("pilier"),
        critere_id=params.get("critere_id"),
        statut="a_faire",
        echeance=echeance,
        impact_score_estime=params.get("impact_score_estime"),
        cout_estime=params.get("cout_estime"),
        benefice_estime=params.get("benefice_estime"),
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    # Recharger le plan complet
    result = await db.execute(
        select(ActionItem)
        .where(ActionItem.plan_id == plan_id)
        .order_by(ActionItem.echeance.asc().nulls_last())
    )
    plan_items = result.scalars().all()

    return _format_plan_response(plan, plan_items)


# ── Action: update_status ────────────────────────────────────────────


async def _update_status(db: AsyncSession, params: dict) -> dict:
    """Met à jour le statut d'une action."""
    item_id = params.get("item_id")
    nouveau_statut = params.get("statut")

    if not item_id:
        return {"error": "item_id est requis"}
    if nouveau_statut not in ("a_faire", "en_cours", "fait"):
        return {"error": "statut doit être: a_faire, en_cours ou fait"}

    result = await db.execute(
        select(ActionItem).where(ActionItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        return {"error": f"Action '{item_id}' introuvable"}

    ancien_statut = item.statut
    item.statut = nouveau_statut
    await db.commit()

    # Charger le plan et tous les items pour la progression
    result = await db.execute(
        select(ActionPlan).where(ActionPlan.id == item.plan_id)
    )
    plan = result.scalar_one_or_none()

    result = await db.execute(
        select(ActionItem)
        .where(ActionItem.plan_id == item.plan_id)
        .order_by(ActionItem.echeance.asc().nulls_last())
    )
    plan_items = result.scalars().all()

    response = _format_plan_response(plan, plan_items)
    response["mise_a_jour"] = {
        "item_id": str(item_id),
        "titre": item.titre,
        "ancien_statut": ancien_statut,
        "nouveau_statut": nouveau_statut,
    }

    return response


# ── Formatage réponse ────────────────────────────────────────────────


def _format_plan_response(plan: ActionPlan, items: list[ActionItem]) -> dict:
    """Formate la réponse du plan avec progression et échéances."""
    total = len(items)
    fait = sum(1 for i in items if i.statut == "fait")
    en_cours = sum(1 for i in items if i.statut == "en_cours")
    a_faire = sum(1 for i in items if i.statut == "a_faire")
    pourcentage = round(fait / total * 100) if total > 0 else 0

    # Impact cumulé des actions complétées
    impact_cumule = sum(
        float(i.impact_score_estime or 0) for i in items if i.statut == "fait"
    )
    score_estime = float(plan.score_initial or 0) + impact_cumule

    # Prochaines échéances (items non complétés avec échéance)
    today = date.today()
    prochaines = [
        {
            "item_id": str(i.id),
            "titre": i.titre,
            "echeance": i.echeance.isoformat() if i.echeance else None,
            "priorite": i.priorite,
            "statut": i.statut,
            "en_retard": i.echeance < today if i.echeance else False,
        }
        for i in items
        if i.statut != "fait" and i.echeance
    ][:5]

    items_list = [
        {
            "id": str(i.id),
            "titre": i.titre,
            "description": i.description,
            "priorite": i.priorite,
            "pilier": i.pilier,
            "critere_id": i.critere_id,
            "statut": i.statut,
            "echeance": i.echeance.isoformat() if i.echeance else None,
            "impact_score_estime": float(i.impact_score_estime) if i.impact_score_estime else None,
            "cout_estime": float(i.cout_estime) if i.cout_estime else None,
            "benefice_estime": float(i.benefice_estime) if i.benefice_estime else None,
        }
        for i in items
    ]

    return {
        "plan": {
            "id": str(plan.id),
            "titre": plan.titre,
            "type_plan": plan.type_plan,
            "horizon": plan.horizon,
            "score_initial": float(plan.score_initial) if plan.score_initial else None,
            "score_cible": float(plan.score_cible) if plan.score_cible else None,
            "referentiel_id": str(plan.referentiel_id) if plan.referentiel_id else None,
            "items": items_list,
        },
        "progression": {
            "total_items": total,
            "fait": fait,
            "en_cours": en_cours,
            "a_faire": a_faire,
            "pourcentage": pourcentage,
        },
        "impact_cumule": {
            "score_estime": round(score_estime, 1),
            "score_gagne": round(impact_cumule, 1),
        },
        "prochaines_echeances": prochaines,
    }
