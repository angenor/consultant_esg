"""
API endpoints pour la génération et le téléchargement de rapports PDF.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.entreprise import Entreprise
from app.reports.generator import generate_report, UPLOADS_DIR

router = APIRouter(prefix="/api/reports", tags=["reports"])


# ── Schemas ──────────────────────────────────────────────

class GenerateReportRequest(BaseModel):
    entreprise_id: str
    template_name: str = "esg_full"


class ReportFileInfo(BaseModel):
    filename: str
    size_kb: float
    download_url: str


class GenerateReportResponse(BaseModel):
    status: str
    message: str
    report: ReportFileInfo


# ── Helpers ──────────────────────────────────────────────

async def _verify_ownership(
    entreprise_id: str, user: User, db: AsyncSession
) -> Entreprise:
    result = await db.execute(
        select(Entreprise).where(Entreprise.id == uuid.UUID(entreprise_id))
    )
    entreprise = result.scalar_one_or_none()
    if not entreprise:
        raise HTTPException(404, "Entreprise introuvable")
    if entreprise.user_id != user.id:
        raise HTTPException(403, "Accès interdit")
    return entreprise


# ── LLM callback ─────────────────────────────────────────

async def _llm_callback(prompt: str) -> str:
    from openai import AsyncOpenAI
    from app.config import settings

    client = AsyncOpenAI(
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
    )
    response = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        max_tokens=1500,
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es un expert ESG qui rédige des sections de rapports professionnels "
                    "pour des PME africaines. Rédige en français, ton professionnel et factuel. "
                    "Ne mets pas de titre de section. 2-3 paragraphes max."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


# ── Endpoints ────────────────────────────────────────────

@router.post("/generate", response_model=GenerateReportResponse)
async def generate_report_endpoint(
    body: GenerateReportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Génère un rapport PDF pour une entreprise."""
    await _verify_ownership(body.entreprise_id, user, db)

    valid_templates = ["esg_full", "carbon", "funding_application"]
    if body.template_name not in valid_templates:
        raise HTTPException(400, f"Template inconnu. Valeurs: {', '.join(valid_templates)}")

    try:
        pdf_bytes, filename = await generate_report(
            entreprise_id=body.entreprise_id,
            template_name=body.template_name,
            db=db,
            llm_callback=_llm_callback,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    template_labels = {
        "esg_full": "Rapport ESG complet",
        "carbon": "Rapport Empreinte Carbone",
        "funding_application": "Dossier de Candidature Fonds Vert",
    }

    return GenerateReportResponse(
        status="ok",
        message=f"{template_labels.get(body.template_name, 'Rapport')} généré avec succès.",
        report=ReportFileInfo(
            filename=filename,
            size_kb=round(len(pdf_bytes) / 1024, 1),
            download_url=f"/api/reports/download/{filename}",
        ),
    )


@router.get("/entreprise/{entreprise_id}")
async def list_reports(
    entreprise_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Liste les rapports générés pour une entreprise."""
    ent = await _verify_ownership(entreprise_id, user, db)
    nom_clean = ent.nom.replace(" ", "_")

    reports = []
    if UPLOADS_DIR.exists():
        for f in sorted(UPLOADS_DIR.iterdir(), reverse=True):
            if f.is_file() and f.suffix in (".pdf", ".docx", ".zip") and nom_clean in f.name:
                reports.append(
                    ReportFileInfo(
                        filename=f.name,
                        size_kb=round(f.stat().st_size / 1024, 1),
                        download_url=f"/api/reports/download/{f.name}",
                    )
                )

    return {"reports": reports, "count": len(reports)}


@router.get("/download/{filename}")
async def download_report(
    filename: str,
    user: User = Depends(get_current_user),
):
    """Télécharge un rapport (PDF ou Word)."""
    filepath = UPLOADS_DIR / filename
    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(404, "Rapport introuvable")

    # Basic security: ensure path doesn't escape uploads dir
    if not filepath.resolve().is_relative_to(UPLOADS_DIR.resolve()):
        raise HTTPException(403, "Accès interdit")

    media_types = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".zip": "application/zip",
    }
    media_type = media_types.get(filepath.suffix.lower(), "application/octet-stream")

    return FileResponse(
        path=str(filepath),
        media_type=media_type,
        filename=filename,
    )
