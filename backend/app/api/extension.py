from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.entreprise import Entreprise
from app.models.fonds_vert import FondsVert
from app.models.fund_application import FundApplication, FundSiteConfig
from app.schemas.extension import (
    CreateApplicationRequest,
    SaveProgressRequest,
    FieldSuggestRequest,
)

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


@router.get("/fund-recommendations")
async def get_fund_recommendations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retourne les fonds verts recommandes pour l'utilisateur"""
    result = await db.execute(
        select(FondsVert).where(FondsVert.is_active == True).limit(10)  # noqa: E712
    )
    fonds_list = result.scalars().all()
    return [
        {
            "id": str(f.id),
            "nom": f.nom,
            "institution": f.institution,
            "type": f.type,
            "montant_min": float(f.montant_min) if f.montant_min else None,
            "montant_max": float(f.montant_max) if f.montant_max else None,
            "devise": f.devise,
            "secteurs_json": f.secteurs_json,
            "pays_eligibles": f.pays_eligibles,
            "date_limite": f.date_limite.isoformat() if f.date_limite else None,
            "url_source": f.url_source,
            "is_active": f.is_active,
        }
        for f in fonds_list
    ]
