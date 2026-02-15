"""
Handler: generate_document
Génère des documents Word (.docx) professionnels pour les dossiers de candidature.
"""

import logging

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.documents.word_generator import (
    TYPE_LABELS,
    VALID_TYPES,
    generate_word_document,
)

logger = logging.getLogger(__name__)


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
                    "Tu es un rédacteur professionnel spécialisé dans les documents "
                    "d'entreprise pour des PME africaines. Rédige en français, "
                    "ton formel et professionnel. Sois concis et factuel. "
                    "Ne mets pas de titres de section (ils sont déjà dans le template)."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


async def generate_document(params: dict, context: dict) -> dict:
    """
    Génère un document Word (.docx) professionnel.

    params:
        - entreprise_id: str (requis)
        - document_type: str (requis) — lettre_motivation, note_presentation,
          plan_affaires, engagement_esg, budget_previsionnel
        - fonds_id: str (optionnel) — ID du fonds vert ciblé
        - instructions: str (optionnel) — instructions spécifiques de l'utilisateur
    """
    db: AsyncSession = context["db"]
    entreprise_id = params.get("entreprise_id")
    document_type = params.get("document_type")
    fonds_id = params.get("fonds_id")
    instructions = params.get("instructions")

    if not entreprise_id:
        return {"error": "entreprise_id est requis"}

    if not document_type:
        return {"error": "document_type est requis"}

    if document_type not in VALID_TYPES:
        return {
            "error": (
                f"Type de document inconnu : '{document_type}'. "
                f"Types valides : {', '.join(VALID_TYPES)}"
            )
        }

    try:
        docx_bytes, filename = await generate_word_document(
            entreprise_id=entreprise_id,
            document_type=document_type,
            db=db,
            llm_callback=_llm_generate,
            fonds_id=fonds_id,
            instructions=instructions,
        )
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.exception("Erreur lors de la génération du document Word")
        return {"error": f"Erreur lors de la génération du document : {e}"}

    label = TYPE_LABELS.get(document_type, "Document")

    return {
        "status": "ok",
        "message": f"{label} généré avec succès.",
        "filename": filename,
        "size_kb": round(len(docx_bytes) / 1024, 1),
        "download_url": f"/api/reports/download/{filename}",
    }
