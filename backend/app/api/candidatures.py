import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.dossier_candidature import DossierCandidature
from app.models.entreprise import Entreprise
from app.models.fonds_vert import FondsVert
from app.models.fund_application import FundApplication, FundSiteConfig
from app.models.intermediaire import Intermediaire
from app.models.user import User
from app.schemas.candidature import (
    CandidatureCreateRequest,
    CandidatureDetail,
    CandidatureListItem,
    CandidatureStats,
    CandidatureUpdateRequest,
    HistoryEntryRequest,
    TimelineStep,
)

router = APIRouter(prefix="/api/candidatures", tags=["candidatures"])


async def _get_entreprise_ids(db: AsyncSession, user: User) -> list[uuid.UUID]:
    result = await db.execute(
        select(Entreprise.id).where(Entreprise.user_id == user.id)
    )
    return list(result.scalars().all())


@router.get("/", response_model=list[CandidatureListItem])
async def list_candidatures(
    status: str | None = Query(None, description="Filtrer par statut"),
    fonds_id: uuid.UUID | None = Query(None, description="Filtrer par fonds"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Liste toutes les candidatures de l'utilisateur avec infos enrichies."""
    entreprise_ids = await _get_entreprise_ids(db, user)
    if not entreprise_ids:
        return []

    query = (
        select(FundApplication, FondsVert.nom, FondsVert.institution)
        .outerjoin(FondsVert, FundApplication.fonds_id == FondsVert.id)
        .where(FundApplication.entreprise_id.in_(entreprise_ids))
        .order_by(FundApplication.updated_at.desc())
    )

    if status:
        query = query.where(FundApplication.status == status)
    if fonds_id:
        query = query.where(FundApplication.fonds_id == fonds_id)

    result = await db.execute(query)
    items = []

    for app, fonds_nom, fonds_institution in result.all():
        # Chercher un dossier lié
        dossier_result = await db.execute(
            select(DossierCandidature)
            .where(
                DossierCandidature.entreprise_id == app.entreprise_id,
                DossierCandidature.fonds_id == app.fonds_id,
            )
            .order_by(DossierCandidature.created_at.desc())
            .limit(1)
        )
        dossier = dossier_result.scalar_one_or_none()

        # Déterminer la prochaine étape
        next_step = None
        if app.status in ("brouillon", "en_cours"):
            if app.fonds_id:
                config_result = await db.execute(
                    select(FundSiteConfig)
                    .where(FundSiteConfig.fonds_id == app.fonds_id, FundSiteConfig.is_active == True)  # noqa: E712
                    .limit(1)
                )
                config = config_result.scalar_one_or_none()
                if config and config.steps and app.current_step < len(config.steps):
                    step = config.steps[app.current_step]
                    next_step = step.get("title") or step.get("name", "")

        items.append(
            CandidatureListItem(
                id=app.id,
                fonds_id=app.fonds_id,
                fonds_nom=fonds_nom or app.fonds_nom or "Fonds inconnu",
                fonds_institution=fonds_institution or app.fonds_institution or "",
                status=app.status,
                progress_pct=app.progress_pct,
                current_step=app.current_step,
                total_steps=app.total_steps,
                url_candidature=app.url_candidature,
                notes=app.notes,
                started_at=app.started_at,
                submitted_at=app.submitted_at,
                updated_at=app.updated_at,
                next_step=next_step,
                dossier_id=dossier.id if dossier else None,
                documents_count=len(dossier.documents_json) if dossier and dossier.documents_json else 0,
            )
        )

    return items


@router.get("/fonds-eligibles")
async def get_fonds_eligibles(
    type: str | None = Query(None, description="Filtrer par type: pret, subvention, garantie"),
    montant_max: float | None = Query(None, description="Montant maximum souhaité"),
    secteur: str | None = Query(None, description="Filtrer par secteur"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retourne les fonds éligibles pour la plateforme web, avec intermédiaires disponibles."""
    from app.services.fund_matching import get_recommendations

    result = await db.execute(
        select(Entreprise).where(Entreprise.user_id == user.id)
    )
    entreprise = result.scalar_one_or_none()

    recommendations = await get_recommendations(
        db,
        entreprise,
        type_filter=type,
        montant_max=montant_max,
        secteur_filter=secteur,
        limit=20,
    )

    # Enrichir avec les intermédiaires disponibles
    for rec in recommendations:
        fonds_id = rec["id"]
        intermediaires_result = await db.execute(
            select(Intermediaire)
            .where(
                Intermediaire.fonds_id == fonds_id,
                Intermediaire.is_active == True,  # noqa: E712
            )
        )
        intermediaires = intermediaires_result.scalars().all()
        rec["intermediaires"] = [
            {
                "id": str(i.id),
                "nom": i.nom,
                "type": i.type,
                "pays": i.pays,
                "email": i.email,
                "site_web": i.site_web,
                "est_recommande": i.est_recommande,
            }
            for i in intermediaires
        ]

    return recommendations


@router.get("/stats", response_model=CandidatureStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Statistiques des candidatures."""
    entreprise_ids = await _get_entreprise_ids(db, user)
    if not entreprise_ids:
        return CandidatureStats()

    result = await db.execute(
        select(FundApplication.status, func.count(FundApplication.id))
        .where(FundApplication.entreprise_id.in_(entreprise_ids))
        .group_by(FundApplication.status)
    )
    counts = dict(result.all())
    total = sum(counts.values())

    return CandidatureStats(
        total=total,
        brouillon=counts.get("brouillon", 0),
        en_cours=counts.get("en_cours", 0),
        soumise=counts.get("soumise", 0),
        acceptee=counts.get("acceptee", 0),
        refusee=counts.get("refusee", 0),
        abandonnee=counts.get("abandonnee", 0),
    )


@router.get("/{candidature_id}", response_model=CandidatureDetail)
async def get_candidature(
    candidature_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Détail complet d'une candidature avec timeline, documents, historique."""
    entreprise_ids = await _get_entreprise_ids(db, user)

    result = await db.execute(
        select(FundApplication, FondsVert.nom, FondsVert.institution)
        .outerjoin(FondsVert, FundApplication.fonds_id == FondsVert.id)
        .where(
            FundApplication.id == candidature_id,
            FundApplication.entreprise_id.in_(entreprise_ids),
        )
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(404, "Candidature introuvable")

    app, fonds_nom, fonds_institution = row

    # Dossier lié
    dossier = None
    if app.fonds_id:
        dossier_result = await db.execute(
            select(DossierCandidature)
            .where(
                DossierCandidature.entreprise_id == app.entreprise_id,
                DossierCandidature.fonds_id == app.fonds_id,
            )
            .order_by(DossierCandidature.created_at.desc())
            .limit(1)
        )
        dossier = dossier_result.scalar_one_or_none()

    # Construire la timeline
    timeline = await _build_timeline(db, app, dossier)

    # Documents du dossier
    documents = []
    if dossier and dossier.documents_json:
        for doc in dossier.documents_json:
            documents.append({
                "nom": doc.get("titre") or doc.get("nom", "Document"),
                "type": doc.get("type", ""),
                "url_docx": doc.get("chemin_docx") or doc.get("url_docx"),
                "url_pdf": doc.get("chemin_pdf") or doc.get("url_pdf"),
                "date": dossier.created_at.strftime("%d/%m/%Y"),
            })

    # Historique (reconstitué depuis form_data metadata)
    history = _build_history(app, dossier)

    return CandidatureDetail(
        id=app.id,
        fonds_id=app.fonds_id,
        fonds_nom=fonds_nom or app.fonds_nom or "Fonds inconnu",
        fonds_institution=fonds_institution or app.fonds_institution or "",
        status=app.status,
        progress_pct=app.progress_pct,
        current_step=app.current_step,
        total_steps=app.total_steps,
        url_candidature=app.url_candidature,
        notes=app.notes,
        form_data=app.form_data,
        started_at=app.started_at,
        submitted_at=app.submitted_at,
        updated_at=app.updated_at,
        dossier_id=dossier.id if dossier else None,
        documents_count=len(documents),
        timeline=timeline,
        documents=documents,
        history=history,
    )


@router.post("/", status_code=201)
async def create_candidature(
    data: CandidatureCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Créer une candidature depuis la plateforme web."""
    result = await db.execute(
        select(Entreprise).where(Entreprise.user_id == user.id)
    )
    entreprise = result.scalar_one_or_none()
    if not entreprise:
        raise HTTPException(404, "Aucune entreprise trouvée")

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


@router.put("/{candidature_id}")
async def update_candidature(
    candidature_id: uuid.UUID,
    data: CandidatureUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Modifier statut, notes, progression d'une candidature."""
    entreprise_ids = await _get_entreprise_ids(db, user)

    result = await db.execute(
        select(FundApplication).where(
            FundApplication.id == candidature_id,
            FundApplication.entreprise_id.in_(entreprise_ids),
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Candidature introuvable")

    if data.status is not None:
        app.status = data.status
        if data.status == "soumise" and not app.submitted_at:
            app.submitted_at = datetime.now(timezone.utc)
    if data.notes is not None:
        app.notes = data.notes
    if data.current_step is not None:
        app.current_step = data.current_step
    if data.progress_pct is not None:
        app.progress_pct = data.progress_pct

    await db.commit()
    await db.refresh(app)

    return {"id": str(app.id), "status": app.status, "progress_pct": app.progress_pct}


@router.get("/{candidature_id}/timeline")
async def get_timeline(
    candidature_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Timeline du processus de candidature."""
    entreprise_ids = await _get_entreprise_ids(db, user)

    result = await db.execute(
        select(FundApplication).where(
            FundApplication.id == candidature_id,
            FundApplication.entreprise_id.in_(entreprise_ids),
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Candidature introuvable")

    dossier = None
    if app.fonds_id:
        dossier_result = await db.execute(
            select(DossierCandidature)
            .where(
                DossierCandidature.entreprise_id == app.entreprise_id,
                DossierCandidature.fonds_id == app.fonds_id,
            )
            .order_by(DossierCandidature.created_at.desc())
            .limit(1)
        )
        dossier = dossier_result.scalar_one_or_none()

    timeline = await _build_timeline(db, app, dossier)
    return timeline


@router.get("/{candidature_id}/documents")
async def get_documents(
    candidature_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Documents générés pour cette candidature."""
    entreprise_ids = await _get_entreprise_ids(db, user)

    result = await db.execute(
        select(FundApplication).where(
            FundApplication.id == candidature_id,
            FundApplication.entreprise_id.in_(entreprise_ids),
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Candidature introuvable")

    documents = []
    if app.fonds_id:
        dossier_result = await db.execute(
            select(DossierCandidature)
            .where(
                DossierCandidature.entreprise_id == app.entreprise_id,
                DossierCandidature.fonds_id == app.fonds_id,
            )
            .order_by(DossierCandidature.created_at.desc())
            .limit(1)
        )
        dossier = dossier_result.scalar_one_or_none()
        if dossier and dossier.documents_json:
            for doc in dossier.documents_json:
                documents.append({
                    "nom": doc.get("titre") or doc.get("nom", "Document"),
                    "type": doc.get("type", ""),
                    "url_docx": doc.get("chemin_docx") or doc.get("url_docx"),
                    "url_pdf": doc.get("chemin_pdf") or doc.get("url_pdf"),
                    "date": dossier.created_at.strftime("%d/%m/%Y"),
                })

    return documents


@router.post("/{candidature_id}/history")
async def add_history_entry(
    candidature_id: uuid.UUID,
    data: HistoryEntryRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Ajouter une entrée dans l'historique d'une candidature."""
    entreprise_ids = await _get_entreprise_ids(db, user)

    result = await db.execute(
        select(FundApplication).where(
            FundApplication.id == candidature_id,
            FundApplication.entreprise_id.in_(entreprise_ids),
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Candidature introuvable")

    # Stocker l'historique dans form_data._history
    form_data = app.form_data or {}
    history = form_data.get("_history", [])
    history.append({
        "action": data.action,
        "details": data.details,
        "date": datetime.now(timezone.utc).isoformat(),
    })
    form_data["_history"] = history
    app.form_data = form_data

    await db.commit()
    return {"status": "ok"}


async def _build_timeline(
    db: AsyncSession,
    app: FundApplication,
    dossier: DossierCandidature | None,
) -> list[TimelineStep]:
    """Construit la timeline dynamique d'une candidature."""
    steps: list[TimelineStep] = []

    # Étape 1 : Analyse d'éligibilité (toujours présente)
    steps.append(TimelineStep(
        title="Analyse d'éligibilité",
        status="done" if app.progress_pct > 0 else "current" if app.status == "brouillon" else "pending",
        date=app.started_at.strftime("%d/%m/%Y") if app.started_at else None,
        description="Candidature créée",
        actions=[{"type": "view_score", "label": "Voir le score ESG"}] if app.progress_pct > 0 else [],
    ))

    # Étape 2 : Dossier préparé
    if dossier:
        doc_count = len(dossier.documents_json) if dossier.documents_json else 0
        steps.append(TimelineStep(
            title="Dossier préparé",
            status="done",
            date=dossier.created_at.strftime("%d/%m/%Y"),
            description=f"{doc_count} documents générés",
            actions=[{"type": "view_dossier", "label": "Voir le dossier"}],
        ))
    elif app.progress_pct >= 20:
        steps.append(TimelineStep(
            title="Préparation du dossier",
            status="current" if app.progress_pct < 50 else "done",
            description="Documents en cours de génération",
        ))

    # Étapes spécifiques du fonds (depuis FundSiteConfig)
    if app.fonds_id:
        config_result = await db.execute(
            select(FundSiteConfig)
            .where(FundSiteConfig.fonds_id == app.fonds_id, FundSiteConfig.is_active == True)  # noqa: E712
            .limit(1)
        )
        config = config_result.scalar_one_or_none()

        if config and config.steps:
            # offset : les étapes du config commencent après les étapes génériques
            generic_count = len(steps)
            for i, step_config in enumerate(config.steps):
                adjusted_index = i
                if adjusted_index < app.current_step:
                    step_status = "done"
                elif adjusted_index == app.current_step and app.status in ("brouillon", "en_cours"):
                    step_status = "current"
                else:
                    step_status = "pending"

                step_title = step_config.get("title") or step_config.get("name", f"Étape {i + 1}")
                actions = []
                if step_status == "current" and app.url_candidature:
                    actions.append({"type": "open_extension", "label": "Ouvrir l'extension"})

                steps.append(TimelineStep(
                    title=step_title,
                    status=step_status,
                    description=step_config.get("description"),
                    actions=actions,
                ))

    # Étape finale : Soumission
    if app.status == "soumise":
        steps.append(TimelineStep(
            title="Candidature soumise",
            status="done",
            date=app.submitted_at.strftime("%d/%m/%Y") if app.submitted_at else None,
            description="En attente de réponse",
        ))
    elif app.status == "acceptee":
        steps.append(TimelineStep(
            title="Candidature acceptée",
            status="done",
            date=app.updated_at.strftime("%d/%m/%Y"),
            description="Félicitations !",
        ))
    elif app.status == "refusee":
        steps.append(TimelineStep(
            title="Candidature refusée",
            status="done",
            date=app.updated_at.strftime("%d/%m/%Y"),
        ))
    elif app.status not in ("abandonnee",):
        steps.append(TimelineStep(
            title="Soumission",
            status="pending",
            estimated="À venir",
        ))

    return steps


def _build_history(
    app: FundApplication,
    dossier: DossierCandidature | None,
) -> list[dict]:
    """Reconstitue l'historique des actions."""
    history = []

    # Création
    if app.started_at:
        history.append({
            "date": app.started_at.strftime("%d/%m/%Y"),
            "action": "Candidature créée",
        })

    # Dossier généré
    if dossier:
        doc_count = len(dossier.documents_json) if dossier.documents_json else 0
        history.append({
            "date": dossier.created_at.strftime("%d/%m/%Y"),
            "action": f"Dossier de candidature généré ({doc_count} documents)",
        })

    # Entrées manuelles depuis form_data._history
    form_data = app.form_data or {}
    for entry in form_data.get("_history", []):
        date_str = entry.get("date", "")
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str)
                date_str = dt.strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                pass
        history.append({
            "date": date_str,
            "action": entry.get("action", ""),
            "details": entry.get("details"),
        })

    # Progression du formulaire
    if app.progress_pct > 0 and app.status in ("en_cours", "brouillon"):
        history.append({
            "date": app.updated_at.strftime("%d/%m/%Y"),
            "action": f"Formulaire rempli à {app.progress_pct:.0f}% via extension",
        })

    # Soumission
    if app.submitted_at:
        history.append({
            "date": app.submitted_at.strftime("%d/%m/%Y"),
            "action": "Candidature soumise",
        })

    # Trier par date décroissante
    history.sort(key=lambda h: h.get("date", ""), reverse=True)
    return history
