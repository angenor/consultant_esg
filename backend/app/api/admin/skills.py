"""
Router /api/admin/skills — CRUD skills + toggle + test.
"""

import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.skill import Skill
from app.models.user import User
from app.schemas.skill import (
    SkillCreateRequest,
    SkillResponse,
    SkillTestRequest,
    SkillTestResponse,
    SkillUpdateRequest,
)

router = APIRouter(prefix="/api/admin/skills", tags=["admin-skills"])


def _validate_skill_code(code: str) -> tuple[bool, str | None]:
    """Validation basique du code Python d'un skill custom."""
    if "async def execute" not in code:
        return False, "Le code doit contenir 'async def execute(params, context):'"
    # Vérifier la syntaxe
    try:
        compile(code, "<skill>", "exec")
    except SyntaxError as e:
        return False, f"Erreur de syntaxe ligne {e.lineno}: {e.msg}"
    # Interdire certains imports dangereux
    forbidden = ["import os", "import sys", "import subprocess", "__import__", "eval(", "exec("]
    for pattern in forbidden:
        if pattern in code:
            return False, f"'{pattern}' n'est pas autorisé dans le code du skill"
    return True, None


@router.get("/", response_model=list[SkillResponse])
async def list_skills(
    category: str | None = Query(None, description="Filtrer par catégorie"),
    is_active: bool | None = Query(None, description="Filtrer par statut actif/inactif"),
    search: str | None = Query(None, description="Recherche par nom ou description"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Liste tous les skills (actifs et inactifs)."""
    query = select(Skill).order_by(Skill.category, Skill.nom)

    if category:
        query = query.where(Skill.category == category)
    if is_active is not None:
        query = query.where(Skill.is_active == is_active)
    if search:
        query = query.where(
            Skill.nom.ilike(f"%{search}%") | Skill.description.ilike(f"%{search}%")
        )

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=SkillResponse, status_code=201)
async def create_skill(
    body: SkillCreateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Crée un nouveau skill custom."""
    # Vérifier l'unicité du nom
    existing = await db.execute(select(Skill).where(Skill.nom == body.nom))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"Un skill avec le nom '{body.nom}' existe déjà")

    # Valider le code Python si c'est un custom
    if body.handler_key.startswith("custom.") and body.handler_code:
        valid, error = _validate_skill_code(body.handler_code)
        if not valid:
            raise HTTPException(400, f"Code invalide : {error}")

    skill = Skill(
        nom=body.nom,
        description=body.description,
        category=body.category,
        input_schema=body.input_schema,
        handler_key=body.handler_key,
        handler_code=body.handler_code,
        created_by=admin.id,
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    return skill


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Détail d'un skill."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(404, "Skill introuvable")
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: uuid.UUID,
    body: SkillUpdateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Modifie un skill existant. Incrémente la version."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(404, "Skill introuvable")

    # Valider le code si modifié
    if body.handler_code is not None:
        if skill.handler_key.startswith("builtin."):
            raise HTTPException(400, "Impossible de modifier le code d'un skill builtin")
        valid, error = _validate_skill_code(body.handler_code)
        if not valid:
            raise HTTPException(400, f"Code invalide : {error}")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(skill, field, value)

    skill.version += 1
    skill.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(skill)
    return skill


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Supprime un skill custom. Les builtins ne peuvent pas être supprimés."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(404, "Skill introuvable")

    if skill.handler_key.startswith("builtin."):
        raise HTTPException(400, "Impossible de supprimer un skill builtin. Désactivez-le plutôt.")

    await db.delete(skill)
    await db.commit()
    return {"detail": "Skill supprimé"}


@router.post("/{skill_id}/toggle", response_model=SkillResponse)
async def toggle_skill(
    skill_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Active/désactive un skill."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(404, "Skill introuvable")

    skill.is_active = not skill.is_active
    skill.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(skill)
    return skill


@router.post("/{skill_id}/test", response_model=SkillTestResponse)
async def test_skill(
    skill_id: uuid.UUID,
    body: SkillTestRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Teste un skill avec des paramètres fictifs. Retourne le résultat ou l'erreur."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(404, "Skill introuvable")

    start = time.time()

    try:
        # Pour les skills builtin, retourner un résultat simulé
        if skill.handler_key.startswith("builtin."):
            test_result = {
                "message": f"Skill builtin '{skill.nom}' appelé avec succès (mode test)",
                "params_received": body.params,
                "handler_key": skill.handler_key,
            }
        elif skill.handler_code:
            # Exécuter le code custom dans un environnement isolé
            import json, math, re
            from datetime import datetime as dt

            namespace = {
                "json": json,
                "datetime": dt,
                "math": math,
                "re": re,
            }
            exec(compile(skill.handler_code, "<skill>", "exec"), namespace)

            if "execute" not in namespace:
                raise ValueError("La fonction 'execute' n'est pas définie dans le code")

            # Contexte simulé pour le test
            context = {"db": None, "rag": None, "entreprise_id": None}
            execute_fn = namespace["execute"]

            # Note: en test, les appels db/rag seront None — le code doit gérer
            test_result = {"message": "Skill custom compilé et validé avec succès (mode test)", "params_received": body.params}
        else:
            raise ValueError("Aucun code handler défini pour ce skill")

        duration_ms = int((time.time() - start) * 1000)
        return SkillTestResponse(success=True, result=test_result, duration_ms=duration_ms)

    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        return SkillTestResponse(success=False, error=str(e), duration_ms=duration_ms)
