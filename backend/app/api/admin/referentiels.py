"""
Router /api/admin/referentiels — CRUD référentiels ESG + toggle + preview scoring.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.referentiel_esg import ReferentielESG
from app.models.fonds_vert import FondsVert
from app.models.user import User
from app.schemas.referentiel import (
    ReferentielCreateRequest,
    ReferentielResponse,
    ReferentielUpdateRequest,
    ScorePreviewRequest,
    ScorePreviewResponse,
    PilierScoreDetail,
    CritereScoreDetail,
)

router = APIRouter(prefix="/api/admin/referentiels", tags=["admin-referentiels"])


def _validate_grille(grille: dict) -> tuple[bool, str | None]:
    """Valide la structure d'une grille ESG."""
    if "piliers" not in grille:
        return False, "La grille doit contenir un champ 'piliers'"
    if "methode_aggregation" not in grille:
        return False, "La grille doit contenir un champ 'methode_aggregation'"
    if grille["methode_aggregation"] not in ("weighted_average", "minimum_thresholds"):
        return False, "methode_aggregation doit être 'weighted_average' ou 'minimum_thresholds'"

    piliers = grille["piliers"]
    if not isinstance(piliers, dict) or len(piliers) == 0:
        return False, "La grille doit contenir au moins un pilier"

    total_poids_global = 0.0

    for pilier_name, pilier_data in piliers.items():
        if "poids_global" not in pilier_data:
            return False, f"Pilier '{pilier_name}': poids_global manquant"
        if "criteres" not in pilier_data or not isinstance(pilier_data["criteres"], list):
            return False, f"Pilier '{pilier_name}': criteres manquants ou invalides"

        total_poids_global += pilier_data["poids_global"]

        total_poids_criteres = 0.0
        ids_seen: set[str] = set()
        for critere in pilier_data["criteres"]:
            if "id" not in critere or "label" not in critere or "poids" not in critere or "type" not in critere:
                return False, f"Pilier '{pilier_name}': critère incomplet (id, label, poids, type requis)"
            if critere["id"] in ids_seen:
                return False, f"Pilier '{pilier_name}': ID de critère dupliqué '{critere['id']}'"
            ids_seen.add(critere["id"])
            total_poids_criteres += critere["poids"]

            if critere["type"] not in ("quantitatif", "qualitatif"):
                return False, f"Critère '{critere['id']}': type doit être 'quantitatif' ou 'qualitatif'"
            if critere["type"] == "quantitatif" and "seuils" not in critere:
                return False, f"Critère quantitatif '{critere['id']}': seuils requis"
            if critere["type"] == "qualitatif" and "options" not in critere:
                return False, f"Critère qualitatif '{critere['id']}': options requises"

        if abs(total_poids_criteres - 1.0) > 0.01:
            return False, f"Pilier '{pilier_name}': la somme des poids des critères doit être 1.00 (actuel: {total_poids_criteres:.2f})"

    if abs(total_poids_global - 1.0) > 0.01:
        return False, f"La somme des poids globaux des piliers doit être 1.00 (actuel: {total_poids_global:.2f})"

    return True, None


def _compute_score(grille: dict, reponses: dict) -> ScorePreviewResponse:
    """Calcule un score ESG à partir d'une grille et de réponses test."""
    piliers_result: dict[str, PilierScoreDetail] = {}
    score_global = 0.0

    for pilier_name, pilier_data in grille["piliers"].items():
        poids_global = pilier_data["poids_global"]
        criteres_details: list[CritereScoreDetail] = []
        pilier_score = 0.0

        for critere in pilier_data["criteres"]:
            cid = critere["id"]
            poids = critere["poids"]
            valeur = reponses.get(cid)

            if valeur is None:
                criteres_details.append(CritereScoreDetail(
                    critere_id=cid, label=critere["label"],
                    score=0, status="manquant", valeur=None,
                ))
                continue

            score = 0.0
            valeur_str = str(valeur)

            if critere["type"] == "quantitatif":
                try:
                    numeric_val = float(valeur)
                except (ValueError, TypeError):
                    criteres_details.append(CritereScoreDetail(
                        critere_id=cid, label=critere["label"],
                        score=0, status="manquant", valeur=valeur_str,
                    ))
                    continue

                seuils = critere["seuils"]
                # Evaluate from best to worst
                for niveau in ("excellent", "bon", "moyen", "faible"):
                    if niveau not in seuils:
                        continue
                    seuil = seuils[niveau]
                    if "min" in seuil and "max" in seuil:
                        if seuil["min"] <= numeric_val <= seuil["max"]:
                            score = seuil["score"]
                            break
                    elif "max" in seuil:
                        if numeric_val <= seuil["max"]:
                            score = seuil["score"]
                            break
                    elif "min" in seuil:
                        if numeric_val >= seuil["min"]:
                            score = seuil["score"]
                            break

            elif critere["type"] == "qualitatif":
                options = critere.get("options", [])
                for opt in options:
                    if opt["label"] == valeur:
                        score = opt["score"]
                        break

            status = "conforme" if score >= 70 else ("partiel" if score >= 30 else "manquant")
            criteres_details.append(CritereScoreDetail(
                critere_id=cid, label=critere["label"],
                score=score, status=status, valeur=valeur_str,
            ))
            pilier_score += score * poids

        piliers_result[pilier_name] = PilierScoreDetail(
            poids_global=poids_global,
            score=round(pilier_score, 1),
            criteres=criteres_details,
        )
        score_global += pilier_score * poids_global

    score_global = round(score_global, 1)
    if score_global >= 80:
        niveau = "Excellent"
    elif score_global >= 60:
        niveau = "Bon"
    elif score_global >= 40:
        niveau = "À améliorer"
    else:
        niveau = "Insuffisant"

    return ScorePreviewResponse(
        score_global=score_global,
        niveau=niveau,
        piliers=piliers_result,
    )


@router.get("/", response_model=list[ReferentielResponse])
async def list_referentiels(
    region: str | None = Query(None, description="Filtrer par région"),
    is_active: bool | None = Query(None, description="Filtrer par statut"),
    search: str | None = Query(None, description="Recherche par nom ou code"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Liste tous les référentiels ESG."""
    query = select(ReferentielESG).order_by(ReferentielESG.nom)

    if region:
        query = query.where(ReferentielESG.region == region)
    if is_active is not None:
        query = query.where(ReferentielESG.is_active == is_active)
    if search:
        query = query.where(
            ReferentielESG.nom.ilike(f"%{search}%") | ReferentielESG.code.ilike(f"%{search}%")
        )

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ReferentielResponse, status_code=201)
async def create_referentiel(
    body: ReferentielCreateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Crée un nouveau référentiel ESG."""
    existing = await db.execute(
        select(ReferentielESG).where(ReferentielESG.code == body.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"Un référentiel avec le code '{body.code}' existe déjà")

    valid, error = _validate_grille(body.grille_json)
    if not valid:
        raise HTTPException(400, f"Grille invalide : {error}")

    ref = ReferentielESG(
        nom=body.nom,
        code=body.code,
        institution=body.institution,
        description=body.description,
        region=body.region,
        grille_json=body.grille_json,
    )
    db.add(ref)
    await db.commit()
    await db.refresh(ref)
    return ref


@router.get("/{ref_id}", response_model=ReferentielResponse)
async def get_referentiel(
    ref_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Détail d'un référentiel avec grille complète."""
    result = await db.execute(
        select(ReferentielESG).where(ReferentielESG.id == ref_id)
    )
    ref = result.scalar_one_or_none()
    if not ref:
        raise HTTPException(404, "Référentiel introuvable")
    return ref


@router.put("/{ref_id}", response_model=ReferentielResponse)
async def update_referentiel(
    ref_id: uuid.UUID,
    body: ReferentielUpdateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Modifie un référentiel existant."""
    result = await db.execute(
        select(ReferentielESG).where(ReferentielESG.id == ref_id)
    )
    ref = result.scalar_one_or_none()
    if not ref:
        raise HTTPException(404, "Référentiel introuvable")

    update_data = body.model_dump(exclude_unset=True)

    if "grille_json" in update_data:
        valid, error = _validate_grille(update_data["grille_json"])
        if not valid:
            raise HTTPException(400, f"Grille invalide : {error}")

    for field, value in update_data.items():
        setattr(ref, field, value)

    ref.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(ref)
    return ref


@router.delete("/{ref_id}")
async def delete_referentiel(
    ref_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Supprime un référentiel. Échoue si des fonds y sont liés."""
    result = await db.execute(
        select(ReferentielESG).where(ReferentielESG.id == ref_id)
    )
    ref = result.scalar_one_or_none()
    if not ref:
        raise HTTPException(404, "Référentiel introuvable")

    # Vérifier qu'aucun fonds n'y est associé
    fonds_count = await db.execute(
        select(func.count()).select_from(FondsVert).where(FondsVert.referentiel_id == ref_id)
    )
    if fonds_count.scalar() > 0:
        raise HTTPException(400, "Impossible de supprimer : des fonds verts sont liés à ce référentiel")

    await db.delete(ref)
    await db.commit()
    return {"detail": "Référentiel supprimé"}


@router.post("/{ref_id}/toggle", response_model=ReferentielResponse)
async def toggle_referentiel(
    ref_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Active/désactive un référentiel."""
    result = await db.execute(
        select(ReferentielESG).where(ReferentielESG.id == ref_id)
    )
    ref = result.scalar_one_or_none()
    if not ref:
        raise HTTPException(404, "Référentiel introuvable")

    ref.is_active = not ref.is_active
    ref.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(ref)
    return ref


@router.post("/{ref_id}/preview", response_model=ScorePreviewResponse)
async def preview_scoring(
    ref_id: uuid.UUID,
    body: ScorePreviewRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Simule un scoring ESG avec des données test."""
    result = await db.execute(
        select(ReferentielESG).where(ReferentielESG.id == ref_id)
    )
    ref = result.scalar_one_or_none()
    if not ref:
        raise HTTPException(404, "Référentiel introuvable")

    return _compute_score(ref.grille_json, body.reponses)
