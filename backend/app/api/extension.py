import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.notifications import create_notification
from app.models.user import User
from app.models.entreprise import Entreprise
from app.models.fonds_vert import FondsVert
from app.models.fund_application import FundApplication, FundSiteConfig
from app.schemas.extension import (
    CreateApplicationRequest,
    SaveProgressRequest,
    FieldSuggestRequest,
    ExtensionEventRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/extension", tags=["extension"])


@router.get("/fund-configs")
async def get_fund_configs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retourne les configurations de sites de fonds actives"""
    query = (
        select(FundSiteConfig, FondsVert.nom)
        .join(FondsVert, FundSiteConfig.fonds_id == FondsVert.id)
        .where(FundSiteConfig.is_active == True)  # noqa: E712
    )
    result = await db.execute(query)
    configs = []
    for config, fonds_nom in result.all():
        configs.append({
            "id": str(config.id),
            "fonds_id": str(config.fonds_id),
            "intermediaire_id": str(config.intermediaire_id) if config.intermediaire_id else None,
            "fonds_nom": fonds_nom,
            "url_patterns": config.url_patterns,
            "steps": config.steps,
            "required_docs": config.required_docs,
            "tips": config.tips,
            "is_active": config.is_active,
            "version": config.version,
        })
    return configs


@router.get("/applications")
async def list_applications(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Liste les candidatures de l'utilisateur"""
    entreprises = await db.execute(
        select(Entreprise.id).where(Entreprise.user_id == user.id)
    )
    entreprise_ids = list(entreprises.scalars().all())

    if not entreprise_ids:
        return []

    query = (
        select(FundApplication, FondsVert.nom, FondsVert.institution)
        .outerjoin(FondsVert, FundApplication.fonds_id == FondsVert.id)
        .where(FundApplication.entreprise_id.in_(entreprise_ids))
        .order_by(FundApplication.updated_at.desc())
    )
    result = await db.execute(query)
    return [
        {
            "id": str(app.id),
            "entreprise_id": str(app.entreprise_id),
            "fonds_id": str(app.fonds_id) if app.fonds_id else None,
            "fonds_nom": nom or app.fonds_nom or "Fonds inconnu",
            "fonds_institution": institution or app.fonds_institution or "",
            "status": app.status,
            "progress_pct": app.progress_pct,
            "form_data": app.form_data,
            "current_step": app.current_step,
            "total_steps": app.total_steps,
            "url_candidature": app.url_candidature,
            "notes": app.notes,
            "started_at": app.started_at.isoformat() if app.started_at else None,
            "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
            "updated_at": app.updated_at.isoformat() if app.updated_at else None,
        }
        for app, nom, institution in result.all()
    ]


@router.post("/applications", status_code=201)
async def create_application(
    data: CreateApplicationRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cree une nouvelle candidature"""
    # Trouver l'entreprise de l'utilisateur
    result = await db.execute(
        select(Entreprise).where(Entreprise.user_id == user.id)
    )
    entreprise = result.scalar_one_or_none()
    if not entreprise:
        raise HTTPException(404, "Aucune entreprise trouvee")

    application = FundApplication(
        entreprise_id=entreprise.id,
        fonds_id=data.fonds_id,
        fonds_nom=data.fonds_nom,
        fonds_institution=data.fonds_institution,
        url_candidature=data.url_candidature,
        total_steps=data.total_steps,
        notes=data.notes,
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return {
        "id": str(application.id),
        "status": application.status,
        "progress_pct": application.progress_pct,
    }


@router.post("/field-suggest")
async def suggest_field(
    data: FieldSuggestRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Utilise le LLM pour suggerer le contenu d'un champ de formulaire"""
    result = await db.execute(
        select(Entreprise).where(Entreprise.user_id == user.id)
    )
    entreprise = result.scalar_one_or_none()

    if not entreprise:
        raise HTTPException(404, "Aucune entreprise trouvee")

    from app.config import settings
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
    )

    prompt = f"""Tu es un assistant specialise dans les candidatures aux fonds verts africains.

Contexte de l'entreprise :
- Nom : {entreprise.nom}
- Secteur : {entreprise.secteur}
- Pays : {entreprise.pays}
- Description : {entreprise.description or 'Non disponible'}

Le champ a remplir est : "{data.field_label}"
Contexte supplementaire : {data.context}

Genere une reponse appropriee pour ce champ de formulaire.
La reponse doit etre professionnelle, concise et adaptee au contexte ESG/fonds vert.
Reponds uniquement avec le texte a inserer dans le champ, sans explication."""

    response = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )

    return {"suggestion": response.choices[0].message.content}


@router.post("/progress")
async def save_progress(
    data: SaveProgressRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Sauvegarde l'etat du formulaire"""
    application = await db.get(FundApplication, data.application_id)
    if not application:
        raise HTTPException(404, "Candidature non trouvee")

    application.form_data = data.form_data
    application.current_step = data.current_step
    if data.progress_pct is not None:
        application.progress_pct = data.progress_pct

    await db.commit()
    return {"status": "ok"}


@router.get("/applications/{application_id}")
async def get_application(
    application_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retourne une candidature par ID"""
    from uuid import UUID
    application = await db.get(FundApplication, UUID(application_id))
    if not application:
        raise HTTPException(404, "Candidature non trouvee")

    return {
        "id": str(application.id),
        "entreprise_id": str(application.entreprise_id),
        "fonds_id": str(application.fonds_id) if application.fonds_id else None,
        "fonds_nom": application.fonds_nom,
        "fonds_institution": application.fonds_institution,
        "status": application.status,
        "progress_pct": application.progress_pct,
        "form_data": application.form_data,
        "current_step": application.current_step,
        "total_steps": application.total_steps,
        "url_candidature": application.url_candidature,
        "notes": application.notes,
        "started_at": application.started_at.isoformat() if application.started_at else None,
        "submitted_at": application.submitted_at.isoformat() if application.submitted_at else None,
        "updated_at": application.updated_at.isoformat() if application.updated_at else None,
    }


@router.post("/events")
async def extension_event(
    event: ExtensionEventRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Recoit les evenements de l'extension (etape completee, formulaire soumis, erreur)"""
    if event.type == "step_completed" and event.application_id:
        application = await db.get(FundApplication, event.application_id)
        if application:
            if event.step is not None:
                application.current_step = event.step
            if event.progress_pct is not None:
                application.progress_pct = event.progress_pct
            await db.commit()

            await create_notification(
                db,
                user.id,
                type="candidature_progress",
                titre="Progression de candidature",
                contenu=f"Etape {event.step} completee ({event.progress_pct or 0:.0f}%)",
            )
            await db.commit()

    elif event.type == "form_submitted" and event.application_id:
        application = await db.get(FundApplication, event.application_id)
        if application:
            application.status = "soumise"
            application.submitted_at = datetime.now(timezone.utc)
            application.progress_pct = 100
            await db.commit()

            await create_notification(
                db,
                user.id,
                type="candidature_soumise",
                titre="Candidature soumise",
                contenu=f"Votre candidature pour {application.fonds_nom} a ete soumise avec succes",
            )
            await db.commit()

    elif event.type == "error":
        logger.error("Extension error from user %s: %s", user.id, event.details)

    return {"status": "ok"}


@router.get("/fund-recommendations")
async def get_fund_recommendations(
    type: str | None = Query(None, description="Filtrer par type: pret, subvention, garantie"),
    montant_max: float | None = Query(None, description="Montant maximum souhaité"),
    secteur: str | None = Query(None, description="Filtrer par secteur"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retourne les fonds verts recommandés, triés par compatibilité avec le profil utilisateur."""
    from app.services.fund_matching import get_recommendations

    # Récupérer l'entreprise
    ent_result = await db.execute(
        select(Entreprise).where(Entreprise.user_id == user.id)
    )
    entreprise = ent_result.scalar_one_or_none()

    return await get_recommendations(
        db,
        entreprise,
        type_filter=type,
        montant_max=montant_max,
        secteur_filter=secteur,
        limit=10,
    )
