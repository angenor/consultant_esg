"""
Handler builtin : génère un dossier complet de candidature pour un fonds vert.
Orchestre la génération de multiples documents (Word + PDF) et crée un ZIP.
"""

import io
import logging
import re
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.documents.word_generator import VALID_TYPES as WORD_VALID_TYPES, generate_word_document
from app.models.entreprise import Entreprise
from app.models.fonds_vert import FondsVert
from app.models.intermediaire import Intermediaire
from app.reports.generator import UPLOADS_DIR, generate_report

logger = logging.getLogger(__name__)

# Mapping : type de document → stratégie de génération
_WORD_DOCS = {
    "lettre_motivation",
    "plan_affaires",
    "budget_previsionnel",
    "engagement_esg",
    "note_presentation",
}

_PDF_REPORTS = {
    "rapport_esg_complet": "esg_full",
    "bilan_carbone": "carbon",
}

_DEFAULT_DOCUMENTS = [
    "lettre_motivation",
    "plan_affaires",
    "budget_previsionnel",
    "engagement_esg",
    "rapport_esg_complet",
    "bilan_carbone",
]

_DOC_LABELS = {
    "lettre_motivation": "Lettre de motivation",
    "plan_affaires": "Plan d'affaires vert",
    "budget_previsionnel": "Budget prévisionnel",
    "engagement_esg": "Lettre d'engagement ESG",
    "note_presentation": "Note de présentation",
    "rapport_esg_complet": "Rapport ESG complet",
    "bilan_carbone": "Bilan carbone",
}


async def _llm_generate(prompt: str) -> str:
    """Appelle le LLM pour générer du contenu textuel."""
    client = AsyncOpenAI(
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
    )
    response = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        max_tokens=2000,
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es un rédacteur professionnel spécialisé dans les dossiers de candidature "
                    "aux fonds verts pour des PME africaines. Rédige en français, "
                    "ton formel et professionnel. Sois concis et factuel. "
                    "Ne mets pas de titres de section (ils sont déjà dans le template)."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


def _sanitize_filename(name: str) -> str:
    """Nettoie un nom pour l'utiliser dans un nom de fichier."""
    clean = re.sub(r"[^\w\s-]", "", name)
    clean = re.sub(r"\s+", "_", clean.strip())
    return clean[:50]


async def generate_dossier_candidature(params: dict, context: dict) -> dict:
    """
    Génère un dossier complet de candidature pour un fonds vert.

    params:
      - entreprise_id: str (requis)
      - fonds_id: str (requis)
      - intermediaire_id: str (optionnel)
      - format: str (word | pdf | both, défaut: both)
      - type_dossier: str (complet | template_vierge, défaut: complet)
      - documents: list[str] (optionnel, si vide génère le dossier complet)
      - instructions: str (optionnel)
    """
    db: AsyncSession = context["db"]
    entreprise_id = params.get("entreprise_id") or context.get("entreprise_id")
    fonds_id = params.get("fonds_id")
    intermediaire_id = params.get("intermediaire_id")
    format_sortie = params.get("format", "both")
    instructions = params.get("instructions")

    if not entreprise_id:
        return {"error": "entreprise_id est requis"}
    if not fonds_id:
        return {"error": "fonds_id est requis"}

    # ── Chargement des données ──

    result = await db.execute(select(Entreprise).where(Entreprise.id == entreprise_id))
    entreprise = result.scalar_one_or_none()
    if not entreprise:
        return {"error": "Entreprise introuvable"}

    result = await db.execute(select(FondsVert).where(FondsVert.id == fonds_id))
    fonds = result.scalar_one_or_none()
    if not fonds:
        return {"error": "Fonds introuvable"}

    intermediaire = None
    if intermediaire_id:
        result = await db.execute(
            select(Intermediaire).where(Intermediaire.id == intermediaire_id)
        )
        intermediaire = result.scalar_one_or_none()

    # ── Liste des documents à générer ──

    doc_list = params.get("documents") or _DEFAULT_DOCUMENTS
    known_types = _WORD_DOCS | set(_PDF_REPORTS.keys())
    doc_list = [d for d in doc_list if d in known_types]

    if not doc_list:
        return {"error": f"Aucun type de document valide. Types possibles : {', '.join(sorted(known_types))}"}

    # ── Enrichir les instructions avec le contexte intermédiaire ──

    enriched_instructions = ""
    if intermediaire:
        enriched_instructions = (
            f"Ce document est destiné à l'intermédiaire {intermediaire.nom} "
            f"({intermediaire.type}) pour le fonds {fonds.nom} ({fonds.institution}). "
        )
    else:
        enriched_instructions = (
            f"Ce document est pour une candidature au fonds {fonds.nom} ({fonds.institution}). "
        )
    if instructions:
        enriched_instructions += instructions

    # ── Génération des documents ──

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    documents_generes = []
    documents_en_erreur = []

    for doc_type in doc_list:

        # Documents Word
        if doc_type in _WORD_DOCS:
            if format_sortie in ("word", "both"):
                try:
                    docx_bytes, filename = await generate_word_document(
                        entreprise_id=str(entreprise_id),
                        document_type=doc_type,
                        db=db,
                        llm_callback=_llm_generate,
                        fonds_id=str(fonds_id),
                        instructions=enriched_instructions,
                    )
                    documents_generes.append({
                        "type": doc_type,
                        "nom": filename,
                        "label": _DOC_LABELS.get(doc_type, doc_type),
                        "format": "docx",
                        "taille": len(docx_bytes),
                        "url_telechargement": f"/api/reports/download/{filename}",
                    })
                except Exception as e:
                    logger.exception("Erreur génération Word %s", doc_type)
                    documents_en_erreur.append({
                        "type": doc_type,
                        "format": "docx",
                        "erreur": str(e),
                    })

        # Rapports PDF
        elif doc_type in _PDF_REPORTS:
            if format_sortie in ("pdf", "both"):
                template_name = _PDF_REPORTS[doc_type]
                try:
                    pdf_bytes, filename = await generate_report(
                        entreprise_id=str(entreprise_id),
                        template_name=template_name,
                        db=db,
                        llm_callback=_llm_generate,
                    )
                    documents_generes.append({
                        "type": doc_type,
                        "nom": filename,
                        "label": _DOC_LABELS.get(doc_type, doc_type),
                        "format": "pdf",
                        "taille": len(pdf_bytes),
                        "url_telechargement": f"/api/reports/download/{filename}",
                    })
                except Exception as e:
                    logger.exception("Erreur génération PDF %s", doc_type)
                    documents_en_erreur.append({
                        "type": doc_type,
                        "format": "pdf",
                        "erreur": str(e),
                    })

    # ── Créer le ZIP ──

    zip_url = None
    if documents_generes:
        fonds_clean = _sanitize_filename(fonds.nom)
        entreprise_clean = _sanitize_filename(entreprise.nom)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        zip_filename = f"Dossier_{fonds_clean}_{entreprise_clean}_{timestamp}.zip"
        zip_path = UPLOADS_DIR / zip_filename

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for doc in documents_generes:
                filepath = UPLOADS_DIR / doc["nom"]
                if filepath.exists():
                    zf.write(filepath, doc["nom"])

        zip_path.write_bytes(zip_buffer.getvalue())
        zip_url = f"/api/reports/download/{zip_filename}"

    # ── Documents manquants (non générables) ──

    documents_manquants = []
    if intermediaire and intermediaire.documents_requis:
        _noms_generes = {
            "lettre de motivation", "plan d'affaires", "budget prévisionnel",
            "engagement esg", "note de présentation", "rapport esg", "bilan carbone",
        }
        for doc in intermediaire.documents_requis:
            nom = doc if isinstance(doc, str) else doc.get("nom", str(doc))
            if nom.lower() not in _noms_generes:
                documents_manquants.append({
                    "nom": nom,
                    "note": "À fournir par l'entreprise (non générable automatiquement)",
                })

    # ── Prochaine étape ──

    if intermediaire:
        type_soumission = intermediaire.type_soumission or ""
        if type_soumission in ("formulaire_en_ligne", "portail_dedie"):
            prochaine_etape = f"Téléchargez le dossier et soumettez-le via le portail de {intermediaire.nom}"
        elif type_soumission == "email":
            prochaine_etape = f"Envoyez le dossier par email à {intermediaire.email or intermediaire.nom}"
        else:
            prochaine_etape = f"Déposez le dossier auprès de {intermediaire.nom}"
    else:
        prochaine_etape = "Téléchargez le dossier et soumettez-le selon les instructions du fonds"

    return {
        "dossier_id": str(uuid.uuid4()),
        "fonds": fonds.nom,
        "intermediaire": intermediaire.nom if intermediaire else None,
        "documents_generes": documents_generes,
        "documents_en_erreur": documents_en_erreur if documents_en_erreur else None,
        "documents_manquants": documents_manquants if documents_manquants else None,
        "zip_url": zip_url,
        "prochaine_etape": prochaine_etape,
    }
