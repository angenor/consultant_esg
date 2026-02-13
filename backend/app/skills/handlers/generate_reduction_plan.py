"""Handler builtin : génération d'un plan de réduction carbone priorisé."""

import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_plan import ActionPlan, ActionItem
from app.models.carbon_footprint import CarbonFootprint
from app.models.entreprise import Entreprise

logger = logging.getLogger(__name__)

# Charger les actions de réduction au démarrage
_ACTIONS_PATH = Path("/app/data/actions_reduction_carbone.json")
_ACTIONS_DB: dict[str, Any] = {}

try:
    _ACTIONS_DB = json.loads(_ACTIONS_PATH.read_text(encoding="utf-8"))
except FileNotFoundError:
    _local = Path(__file__).resolve().parents[3] / "data" / "actions_reduction_carbone.json"
    if _local.exists():
        _ACTIONS_DB = json.loads(_local.read_text(encoding="utf-8"))
    else:
        logger.warning("actions_reduction_carbone.json introuvable")


async def generate_reduction_plan(params: dict, context: dict) -> dict:
    """
    Génère un plan de réduction carbone priorisé.

    1. Récupère la dernière empreinte carbone
    2. Identifie les sources les plus émettrices
    3. Sélectionne les actions adaptées (secteur, horizon)
    4. Crée un ActionPlan + ActionItems en BDD

    params:
      - entreprise_id: str (optionnel si dans context)
      - objectif_reduction_pct: float (objectif en %, défaut 20)
    """
    db: AsyncSession = context["db"]
    entreprise_id = params.get("entreprise_id") or context.get("entreprise_id")

    if not entreprise_id:
        return {"error": "entreprise_id requis"}

    # Charger l'entreprise
    result = await db.execute(
        select(Entreprise).where(Entreprise.id == entreprise_id)
    )
    entreprise = result.scalar_one_or_none()
    if not entreprise:
        return {"error": "Entreprise introuvable"}

    # Récupérer la dernière empreinte carbone
    result = await db.execute(
        select(CarbonFootprint)
        .where(CarbonFootprint.entreprise_id == entreprise_id)
        .order_by(CarbonFootprint.created_at.desc())
        .limit(1)
    )
    footprint = result.scalar_one_or_none()
    if not footprint:
        return {
            "error": (
                "Aucune empreinte carbone trouvée pour cette entreprise. "
                "Utilisez d'abord l'outil calculate_carbon pour calculer l'empreinte."
            )
        }

    total = float(footprint.total_tco2e)
    objectif_pct = params.get("objectif_reduction_pct", 20)
    secteur = (entreprise.secteur or "").lower()

    # Répartition actuelle
    sources = {
        "energie": float(footprint.energie),
        "transport": float(footprint.transport),
        "dechets": float(footprint.dechets),
        "achats": float(footprint.achats),
    }

    # Trier par émissions décroissantes
    sources_triees = sorted(sources.items(), key=lambda x: x[1], reverse=True)

    # Sélectionner les actions adaptées
    actions_db = _ACTIONS_DB.get("actions", {})
    actions_selectionnees: list[dict] = []

    for source_nom, source_tco2 in sources_triees:
        if source_tco2 <= 0:
            continue

        actions_source = actions_db.get(source_nom, [])
        for action in actions_source:
            # Filtrer par secteur
            secteurs_action = action.get("secteurs", ["tous"])
            if "tous" not in secteurs_action and secteur not in secteurs_action:
                continue

            # Calculer la réduction estimée en tCO2e
            reduction_tco2 = round(source_tco2 * action["reduction_pct"] / 100, 2)

            actions_selectionnees.append({
                "titre": action["titre"],
                "description": action["description"],
                "horizon": action["horizon"],
                "source": source_nom,
                "source_tco2e": source_tco2,
                "reduction_tco2e": reduction_tco2,
                "reduction_pct_source": action["reduction_pct"],
                "cout_estime_xof": action["cout_estime_xof"],
                "economie_annuelle_xof": action["economie_annuelle_xof"],
                "roi_mois": (
                    round(action["cout_estime_xof"] / action["economie_annuelle_xof"] * 12)
                    if action["economie_annuelle_xof"] > 0 and action["cout_estime_xof"] > 0
                    else 0
                ),
            })

    # Trier : quick_win d'abord, puis par ratio réduction/coût décroissant
    horizon_order = {"quick_win": 0, "moyen_terme": 1, "long_terme": 2}
    actions_selectionnees.sort(
        key=lambda a: (
            horizon_order.get(a["horizon"], 9),
            -a["reduction_tco2e"] / max(a["cout_estime_xof"], 1),
        )
    )

    # Grouper par horizon
    plan_par_horizon: dict[str, list[dict]] = {
        "quick_win": [],
        "moyen_terme": [],
        "long_terme": [],
    }
    for action in actions_selectionnees:
        plan_par_horizon[action["horizon"]].append(action)

    # Calculer les totaux
    reduction_totale = sum(a["reduction_tco2e"] for a in actions_selectionnees)
    cout_total = sum(a["cout_estime_xof"] for a in actions_selectionnees)
    economie_totale = sum(a["economie_annuelle_xof"] for a in actions_selectionnees)

    # Créer le plan en BDD
    plan = ActionPlan(
        entreprise_id=entreprise_id,
        titre=f"Plan de réduction carbone - {entreprise.nom}",
        horizon="12_mois",
        score_initial=total,
        score_cible=round(total * (1 - objectif_pct / 100), 2),
    )
    db.add(plan)
    await db.flush()  # Pour obtenir plan.id

    # Créer les ActionItems
    items_crees = 0
    for action in actions_selectionnees:
        echeance = _calculer_echeance(action["horizon"])
        item = ActionItem(
            plan_id=plan.id,
            titre=action["titre"],
            description=action["description"],
            priorite=_priorite_from_horizon(action["horizon"]),
            pilier="E",  # Toutes les actions carbone sont pilier Environnement
            statut="a_faire",
            echeance=echeance,
            impact_score_estime=action["reduction_tco2e"],
            cout_estime=action["cout_estime_xof"],
            benefice_estime=action["economie_annuelle_xof"],
        )
        db.add(item)
        items_crees += 1

    await db.commit()

    return {
        "plan_id": str(plan.id),
        "entreprise": entreprise.nom,
        "empreinte_actuelle_tco2e": total,
        "objectif_reduction_pct": objectif_pct,
        "cible_tco2e": round(total * (1 - objectif_pct / 100), 2),
        "nombre_actions": len(actions_selectionnees),
        "actions_items_crees": items_crees,
        "reduction_totale_estimee_tco2e": round(reduction_totale, 2),
        "cout_total_estime_xof": cout_total,
        "economie_annuelle_totale_xof": economie_totale,
        "repartition_emissions": {
            source: {"tco2e": val, "pct": round(val / total * 100, 1) if total > 0 else 0}
            for source, val in sources_triees
        },
        "plan": {
            horizon: [
                {
                    "titre": a["titre"],
                    "description": a["description"],
                    "source": a["source"],
                    "reduction_tco2e": a["reduction_tco2e"],
                    "cout_xof": a["cout_estime_xof"],
                    "economie_xof": a["economie_annuelle_xof"],
                    "roi_mois": a["roi_mois"],
                }
                for a in actions
            ]
            for horizon, actions in plan_par_horizon.items()
        },
    }


def _calculer_echeance(horizon: str) -> date:
    """Calcule une échéance en fonction de l'horizon."""
    today = date.today()
    if horizon == "quick_win":
        return date(today.year, min(today.month + 3, 12), 28)
    elif horizon == "moyen_terme":
        return date(today.year + 1, today.month, 28)
    else:
        return date(today.year + 2, today.month, 28)


def _priorite_from_horizon(horizon: str) -> str:
    """Convertit un horizon en priorité."""
    return {"quick_win": "haute", "moyen_terme": "moyenne", "long_terme": "basse"}.get(
        horizon, "moyenne"
    )
