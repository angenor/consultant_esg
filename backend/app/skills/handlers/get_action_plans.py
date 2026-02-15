"""Handler builtin : récupère les plans d'action existants (ESG et/ou carbone)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_plan import ActionItem, ActionPlan
from app.models.entreprise import Entreprise


async def get_action_plans(params: dict, context: dict) -> dict:
    """
    Récupère les plans d'action existants pour une entreprise.
    Supporte le filtrage par type (esg, carbone, ou tous).
    Retourne le dernier plan de chaque type demandé avec items et progression.
    """
    db: AsyncSession = context["db"]
    entreprise_id = params.get("entreprise_id") or context.get("entreprise_id")
    if not entreprise_id:
        return {"error": "entreprise_id manquant"}

    # Vérifier que l'entreprise existe
    result = await db.execute(
        select(Entreprise).where(Entreprise.id == entreprise_id)
    )
    if not result.scalar_one_or_none():
        return {"error": f"Entreprise '{entreprise_id}' introuvable"}

    type_plan = params.get("type_plan")  # "esg", "carbone", or None (= tous)

    # Déterminer les types à chercher
    if type_plan in ("esg", "carbone"):
        types = [type_plan]
    else:
        types = ["esg", "carbone"]

    plans_result = []

    for tp in types:
        result = await db.execute(
            select(ActionPlan)
            .where(
                ActionPlan.entreprise_id == entreprise_id,
                ActionPlan.type_plan == tp,
            )
            .order_by(ActionPlan.created_at.desc())
            .limit(1)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            continue

        # Charger les items
        items_result = await db.execute(
            select(ActionItem)
            .where(ActionItem.plan_id == plan.id)
            .order_by(ActionItem.echeance.asc().nulls_last())
        )
        items = items_result.scalars().all()

        total = len(items)
        fait = sum(1 for i in items if i.statut == "fait")
        en_cours = sum(1 for i in items if i.statut == "en_cours")
        a_faire = sum(1 for i in items if i.statut == "a_faire")
        pourcentage = round(fait / total * 100) if total > 0 else 0

        plans_result.append({
            "id": str(plan.id),
            "titre": plan.titre,
            "type_plan": plan.type_plan,
            "horizon": plan.horizon,
            "score_initial": float(plan.score_initial) if plan.score_initial else None,
            "score_cible": float(plan.score_cible) if plan.score_cible else None,
            "created_at": str(plan.created_at),
            "progression": {
                "total": total,
                "fait": fait,
                "en_cours": en_cours,
                "a_faire": a_faire,
                "pourcentage": pourcentage,
            },
            "items": [
                {
                    "id": str(i.id),
                    "titre": i.titre,
                    "description": i.description,
                    "priorite": i.priorite,
                    "pilier": i.pilier,
                    "statut": i.statut,
                    "echeance": str(i.echeance) if i.echeance else None,
                    "impact_score_estime": float(i.impact_score_estime) if i.impact_score_estime else None,
                    "cout_estime": float(i.cout_estime) if i.cout_estime else None,
                    "benefice_estime": float(i.benefice_estime) if i.benefice_estime else None,
                }
                for i in items
            ],
        })

    if not plans_result:
        return {"message": "Aucun plan d'action trouvé pour cette entreprise."}

    return {"plans": plans_result}
