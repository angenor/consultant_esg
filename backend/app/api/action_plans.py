"""Endpoints API pour les plans d'action ESG (Module 6)."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.notifications import create_notification
from app.models.action_plan import ActionItem, ActionPlan
from app.models.entreprise import Entreprise
from app.models.referentiel_esg import ReferentielESG
from app.models.user import User
from app.schemas.action_plan import (
    ActionItemResponse,
    ActionPlanDetail,
    ActionPlanSummary,
    AddActionItemRequest,
    CreateActionPlanRequest,
    ProgressResponse,
    UpdateActionItemRequest,
)
from app.skills.handlers.manage_action_plan import manage_action_plan

router = APIRouter(prefix="/api/action-plans", tags=["action-plans"])


# ── Helpers ──


async def _verify_ownership(
    db: AsyncSession, entreprise_id: uuid.UUID, user: User
) -> Entreprise:
    result = await db.execute(
        select(Entreprise).where(
            Entreprise.id == entreprise_id,
            Entreprise.user_id == user.id,
        )
    )
    entreprise = result.scalar_one_or_none()
    if not entreprise:
        raise HTTPException(status_code=404, detail="Entreprise introuvable")
    return entreprise


async def _verify_plan_ownership(
    db: AsyncSession, plan_id: uuid.UUID, user: User
) -> ActionPlan:
    """Vérifie que le plan appartient à une entreprise de l'utilisateur."""
    result = await db.execute(
        select(ActionPlan).where(ActionPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan introuvable")

    await _verify_ownership(db, plan.entreprise_id, user)
    return plan


# ── Endpoints ──


@router.get("/latest")
async def latest_plan(
    type_plan: str = Query("esg", pattern="^(esg|carbone)$"),
    referentiel_code: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dernier plan d'action filtré par type et optionnellement par référentiel."""
    ent_result = await db.execute(
        select(Entreprise.id).where(Entreprise.user_id == user.id).limit(1)
    )
    ent_id = ent_result.scalar_one_or_none()
    if not ent_id:
        return None

    query = (
        select(ActionPlan)
        .where(
            ActionPlan.entreprise_id == ent_id,
            ActionPlan.type_plan == type_plan,
        )
    )

    if referentiel_code:
        query = query.join(
            ReferentielESG, ActionPlan.referentiel_id == ReferentielESG.id
        ).where(ReferentielESG.code == referentiel_code)

    result = await db.execute(
        query.order_by(ActionPlan.created_at.desc()).limit(1)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        return None

    # Charger le référentiel associé
    ref = None
    if plan.referentiel_id:
        ref_result = await db.execute(
            select(ReferentielESG).where(ReferentielESG.id == plan.referentiel_id)
        )
        ref = ref_result.scalar_one_or_none()

    items_result = await db.execute(
        select(ActionItem)
        .where(ActionItem.plan_id == plan.id)
        .order_by(ActionItem.echeance.asc().nulls_last())
    )
    items = items_result.scalars().all()

    return {
        "id": str(plan.id),
        "titre": plan.titre,
        "type_plan": plan.type_plan,
        "horizon": plan.horizon,
        "referentiel_id": str(plan.referentiel_id) if plan.referentiel_id else None,
        "referentiel_code": ref.code if ref else None,
        "score_initial": float(plan.score_initial) if plan.score_initial else None,
        "score_cible": float(plan.score_cible) if plan.score_cible else None,
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
    }


@router.post("/", response_model=dict)
async def create_plan(
    body: CreateActionPlanRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Crée un plan d'action basé sur les lacunes ESG."""
    await _verify_ownership(db, body.entreprise_id, user)

    params = {
        "entreprise_id": str(body.entreprise_id),
        "action": "create",
        "horizon": body.horizon,
        "score_cible": body.score_cible,
        "referentiel_code": body.referentiel_code,
    }
    context = {"db": db, "entreprise_id": str(body.entreprise_id)}

    result = await manage_action_plan(params, context)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/entreprise/{entreprise_id}", response_model=list[ActionPlanSummary])
async def list_plans(
    entreprise_id: uuid.UUID,
    type_plan: str | None = Query(None, pattern="^(esg|carbone)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Liste les plans d'action d'une entreprise, avec filtre optionnel par type."""
    await _verify_ownership(db, entreprise_id, user)

    query = (
        select(ActionPlan)
        .where(ActionPlan.entreprise_id == entreprise_id)
    )
    if type_plan:
        query = query.where(ActionPlan.type_plan == type_plan)
    query = query.order_by(ActionPlan.created_at.desc())

    result = await db.execute(query)
    plans = result.scalars().all()

    summaries = []
    for plan in plans:
        # Compter les items par statut
        count_result = await db.execute(
            select(
                func.count(ActionItem.id),
                func.count(ActionItem.id).filter(ActionItem.statut == "fait"),
            ).where(ActionItem.plan_id == plan.id)
        )
        row = count_result.one()
        total = row[0]
        fait = row[1]
        pourcentage = round(fait / total * 100) if total > 0 else 0

        summaries.append(
            ActionPlanSummary(
                id=plan.id,
                entreprise_id=plan.entreprise_id,
                titre=plan.titre,
                type_plan=plan.type_plan,
                horizon=plan.horizon,
                referentiel_id=plan.referentiel_id,
                score_initial=float(plan.score_initial) if plan.score_initial else None,
                score_cible=float(plan.score_cible) if plan.score_cible else None,
                nb_items=total,
                nb_fait=fait,
                pourcentage=pourcentage,
                created_at=plan.created_at,
            )
        )

    return summaries


@router.get("/{plan_id}", response_model=ActionPlanDetail)
async def get_plan(
    plan_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Détail d'un plan avec ses actions."""
    plan = await _verify_plan_ownership(db, plan_id, user)

    result = await db.execute(
        select(ActionItem)
        .where(ActionItem.plan_id == plan_id)
        .order_by(ActionItem.echeance.asc().nulls_last())
    )
    items = result.scalars().all()

    return ActionPlanDetail(
        id=plan.id,
        entreprise_id=plan.entreprise_id,
        titre=plan.titre,
        type_plan=plan.type_plan,
        horizon=plan.horizon,
        referentiel_id=plan.referentiel_id,
        score_initial=float(plan.score_initial) if plan.score_initial else None,
        score_cible=float(plan.score_cible) if plan.score_cible else None,
        items=[ActionItemResponse.model_validate(i) for i in items],
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.post("/{plan_id}/items", response_model=ActionItemResponse)
async def add_item(
    plan_id: uuid.UUID,
    body: AddActionItemRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ajoute une action à un plan existant."""
    plan = await _verify_plan_ownership(db, plan_id, user)

    item = ActionItem(
        plan_id=plan_id,
        titre=body.titre,
        description=body.description,
        priorite=body.priorite,
        pilier=body.pilier,
        critere_id=body.critere_id,
        statut="a_faire",
        echeance=body.echeance,
        impact_score_estime=body.impact_score_estime,
        cout_estime=body.cout_estime,
        benefice_estime=body.benefice_estime,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return ActionItemResponse.model_validate(item)


@router.put("/items/{item_id}", response_model=ActionItemResponse)
async def update_item_status(
    item_id: uuid.UUID,
    body: UpdateActionItemRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Met à jour le statut d'une action."""
    result = await db.execute(
        select(ActionItem).where(ActionItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Action introuvable")

    # Vérifier la propriété via le plan
    plan_obj = await _verify_plan_ownership(db, item.plan_id, user)

    ancien_statut = item.statut
    item.statut = body.statut
    await db.commit()
    await db.refresh(item)

    # Notification si action complétée
    if body.statut == "fait" and ancien_statut != "fait":
        lien = "/carbon" if plan_obj.type_plan == "carbone" else "/action-plan"
        await create_notification(
            db,
            user_id=user.id,
            type="action_completee",
            titre=f"Action terminée : {item.titre}",
            contenu=f"L'action \"{item.titre}\" a été marquée comme terminée.",
            lien=lien,
        )
        await db.commit()

    return ActionItemResponse.model_validate(item)


@router.get("/{plan_id}/progress", response_model=ProgressResponse)
async def get_progress(
    plan_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Progression globale d'un plan."""
    plan = await _verify_plan_ownership(db, plan_id, user)

    result = await db.execute(
        select(ActionItem)
        .where(ActionItem.plan_id == plan_id)
        .order_by(ActionItem.echeance.asc().nulls_last())
    )
    items = result.scalars().all()

    total = len(items)
    fait = sum(1 for i in items if i.statut == "fait")
    en_cours = sum(1 for i in items if i.statut == "en_cours")
    a_faire = sum(1 for i in items if i.statut == "a_faire")
    pourcentage = round(fait / total * 100) if total > 0 else 0

    impact_cumule = sum(float(i.impact_score_estime or 0) for i in items if i.statut == "fait")
    score_estime = float(plan.score_initial or 0) + impact_cumule

    today = date.today()
    prochaines = [
        {
            "item_id": i.id,
            "titre": i.titre,
            "echeance": i.echeance,
            "priorite": i.priorite,
            "statut": i.statut,
            "en_retard": i.echeance < today if i.echeance else False,
        }
        for i in items
        if i.statut != "fait" and i.echeance
    ][:5]

    return ProgressResponse(
        plan_id=plan.id,
        titre=plan.titre,
        type_plan=plan.type_plan,
        horizon=plan.horizon,
        score_initial=float(plan.score_initial) if plan.score_initial else None,
        score_cible=float(plan.score_cible) if plan.score_cible else None,
        progression={
            "total_items": total,
            "fait": fait,
            "en_cours": en_cours,
            "a_faire": a_faire,
            "pourcentage_completion": pourcentage,
        },
        impact_cumule={
            "score_estime": round(score_estime, 1),
            "score_gagne": round(impact_cumule, 1),
        },
        prochaines_echeances=prochaines,
    )
