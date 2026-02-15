"""Endpoint agrégé pour le tableau de bord entreprise."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.action_plan import ActionItem, ActionPlan
from app.models.esg_score import ESGScore
from app.models.entreprise import Entreprise
from app.models.fonds_vert import FondsVert
from app.models.referentiel_esg import ReferentielESG
from app.models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _niveau(score: float | None) -> str:
    if score is None:
        return "Non calculé"
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Bon"
    if score >= 40:
        return "À améliorer"
    return "Insuffisant"


@router.get("/data")
async def dashboard_data(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Données agrégées pour le tableau de bord multi-référentiel."""
    # 1. Trouver l'entreprise de l'utilisateur
    ent_result = await db.execute(
        select(Entreprise).where(Entreprise.user_id == user.id).limit(1)
    )
    entreprise = ent_result.scalar_one_or_none()
    if not entreprise:
        return None

    ent_id = entreprise.id

    # 2. Référentiels actifs
    ref_result = await db.execute(
        select(ReferentielESG)
        .where(ReferentielESG.is_active == True)
        .order_by(ReferentielESG.nom)
    )
    referentiels = ref_result.scalars().all()
    ref_map = {r.id: r for r in referentiels}

    # 3. Dernier score par référentiel (subquery) — exclut les scores à 0
    latest_sub = (
        select(
            ESGScore.referentiel_id,
            func.max(ESGScore.created_at).label("max_date"),
        )
        .where(
            ESGScore.entreprise_id == ent_id,
            ESGScore.score_global > 0,
        )
        .group_by(ESGScore.referentiel_id)
        .subquery()
    )

    scores_result = await db.execute(
        select(ESGScore).join(
            latest_sub,
            (ESGScore.referentiel_id == latest_sub.c.referentiel_id)
            & (ESGScore.created_at == latest_sub.c.max_date),
        ).where(ESGScore.entreprise_id == ent_id)
    )
    latest_scores = scores_result.scalars().all()

    scores_par_referentiel = []
    alerts = []
    for s in latest_scores:
        ref = ref_map.get(s.referentiel_id)
        sg = float(s.score_global) if s.score_global is not None else None
        entry = {
            "referentiel_id": str(s.referentiel_id) if s.referentiel_id else None,
            "referentiel_nom": ref.nom if ref else "Inconnu",
            "referentiel_code": ref.code if ref else None,
            "score_e": float(s.score_e) if s.score_e is not None else None,
            "score_s": float(s.score_s) if s.score_s is not None else None,
            "score_g": float(s.score_g) if s.score_g is not None else None,
            "score_global": sg,
            "niveau": _niveau(sg),
            "created_at": str(s.created_at),
        }
        scores_par_referentiel.append(entry)

        # Vérifier les seuils critiques par pilier
        if ref and ref.grille_json:
            grille = ref.grille_json
            piliers = grille.get("piliers", {})
            for pilier_key, pilier_data in piliers.items():
                criteres = pilier_data.get("criteres", [])
                for c in criteres:
                    seuils = c.get("seuils", {})
                    minimum = seuils.get("minimum")
                    if minimum is not None and s.details_json:
                        details = s.details_json.get("details", [])
                        for d in details:
                            if d.get("critere_id") == c.get("id"):
                                val = d.get("score")
                                if val is not None and val < minimum:
                                    alerts.append({
                                        "type": "seuil_non_atteint",
                                        "referentiel": ref.nom,
                                        "referentiel_code": ref.code,
                                        "critere": c.get("nom", c.get("id")),
                                        "score": val,
                                        "minimum": minimum,
                                    })

    # 4. Historique des scores (tous référentiels, 50 derniers)
    history_result = await db.execute(
        select(ESGScore)
        .where(ESGScore.entreprise_id == ent_id)
        .order_by(ESGScore.created_at.asc())
        .limit(50)
    )
    all_scores = history_result.scalars().all()

    score_history = []
    for s in all_scores:
        ref = ref_map.get(s.referentiel_id)
        score_history.append({
            "referentiel_code": ref.code if ref else None,
            "referentiel_nom": ref.nom if ref else "Inconnu",
            "score_e": float(s.score_e) if s.score_e is not None else None,
            "score_s": float(s.score_s) if s.score_s is not None else None,
            "score_g": float(s.score_g) if s.score_g is not None else None,
            "score_global": float(s.score_global) if s.score_global is not None else None,
            "created_at": str(s.created_at),
        })

    # 5. Fonds verts recommandés
    fonds_query = select(FondsVert, ReferentielESG).outerjoin(
        ReferentielESG, FondsVert.referentiel_id == ReferentielESG.id
    ).where(FondsVert.is_active == True)

    fonds_result = await db.execute(fonds_query)
    fonds_rows = fonds_result.all()

    fonds_recommandes = []
    for fonds, ref in fonds_rows:
        # Calculer la compatibilité basique
        compatibilite = 50  # Base
        secteurs = fonds.secteurs_json or []
        if entreprise.secteur and secteurs:
            sect_lower = entreprise.secteur.lower()
            if any(sect_lower in s.lower() for s in secteurs) or not secteurs:
                compatibilite += 15
        elif not secteurs:
            compatibilite += 10

        pays_elig = fonds.pays_eligibles or []
        if pays_elig:
            pays_ent = entreprise.pays or ""
            if any(p.lower() in pays_ent.lower() or pays_ent.lower() in p.lower() for p in pays_elig):
                compatibilite += 15
        else:
            compatibilite += 10

        # Bonus si score ESG disponible et au-dessus du minimum
        score_min = None
        if fonds.criteres_json:
            score_min = fonds.criteres_json.get("score_esg_minimum")

        matching_score = None
        if ref:
            for s in latest_scores:
                if s.referentiel_id == ref.id and s.score_global is not None:
                    matching_score = float(s.score_global)
                    break

        if matching_score is not None and score_min is not None:
            if matching_score >= score_min:
                compatibilite += 20
            else:
                compatibilite -= 10

        compatibilite = max(0, min(100, compatibilite))

        montant_range = None
        if fonds.montant_min or fonds.montant_max:
            parts = []
            if fonds.montant_min:
                parts.append(f"{int(fonds.montant_min):,}".replace(",", " "))
            if fonds.montant_max:
                parts.append(f"{int(fonds.montant_max):,}".replace(",", " "))
            montant_range = " — ".join(parts) + f" {fonds.devise}"

        fonds_recommandes.append({
            "id": str(fonds.id),
            "nom": fonds.nom,
            "institution": fonds.institution,
            "type": fonds.type,
            "referentiel_nom": ref.nom if ref else None,
            "referentiel_code": ref.code if ref else None,
            "montant_range": montant_range,
            "devise": fonds.devise,
            "score_esg_minimum": score_min,
            "compatibilite": compatibilite,
            "date_limite": str(fonds.date_limite) if fonds.date_limite else None,
        })

    # Trier par compatibilité décroissante
    fonds_recommandes.sort(key=lambda f: f["compatibilite"], reverse=True)

    # 6. Plans d'action résumés (un par référentiel, type ESG)
    plans_result = await db.execute(
        select(ActionPlan)
        .where(
            ActionPlan.entreprise_id == ent_id,
            ActionPlan.type_plan == "esg",
        )
        .order_by(ActionPlan.created_at.desc())
    )
    all_plans = plans_result.scalars().all()

    # Dédupliquer : garder le plus récent par referentiel_id
    seen_refs: set = set()
    unique_plans = []
    for p in all_plans:
        key = p.referentiel_id
        if key not in seen_refs:
            seen_refs.add(key)
            unique_plans.append(p)

    action_plans = []
    for plan in unique_plans:
        items_result = await db.execute(
            select(ActionItem)
            .where(ActionItem.plan_id == plan.id)
            .order_by(ActionItem.echeance.asc().nulls_last())
        )
        items = items_result.scalars().all()

        total = len(items)
        fait = sum(1 for i in items if i.statut == "fait")
        pourcentage = round(fait / total * 100) if total > 0 else 0

        ref = ref_map.get(plan.referentiel_id) if plan.referentiel_id else None

        prochaines = [
            {
                "id": str(i.id),
                "titre": i.titre,
                "pilier": i.pilier,
                "priorite": i.priorite,
                "statut": i.statut,
                "echeance": str(i.echeance) if i.echeance else None,
            }
            for i in items
            if i.statut != "fait"
        ][:5]

        action_plans.append({
            "id": str(plan.id),
            "titre": plan.titre,
            "referentiel_id": str(plan.referentiel_id) if plan.referentiel_id else None,
            "referentiel_code": ref.code if ref else None,
            "nb_total": total,
            "nb_fait": fait,
            "pourcentage": pourcentage,
            "prochaines_actions": prochaines,
        })

    return {
        "entreprise": {
            "id": str(entreprise.id),
            "nom": entreprise.nom,
            "secteur": entreprise.secteur,
            "pays": entreprise.pays,
        },
        "referentiels": [
            {
                "id": str(r.id),
                "nom": r.nom,
                "code": r.code,
                "institution": r.institution,
            }
            for r in referentiels
        ],
        "scores_par_referentiel": scores_par_referentiel,
        "score_history": score_history,
        "fonds_recommandes": fonds_recommandes,
        "action_plans": action_plans,
        "alerts": alerts,
    }
