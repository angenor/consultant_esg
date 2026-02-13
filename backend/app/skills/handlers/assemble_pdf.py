"""
Handler: assemble_pdf
Point d'entrée pour le LLM quand l'utilisateur demande un rapport.
Orchestre le générateur de rapports.
"""

import logging

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.reports.generator import generate_report

logger = logging.getLogger(__name__)


async def _llm_generate(prompt: str) -> str:
    """Helper to call the LLM for report sections."""
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


async def assemble_pdf(params: dict, context: dict) -> dict:
    """
    Assemble et génère un rapport PDF complet.

    params:
        - entreprise_id: str (requis)
        - template_name: str (optionnel, défaut: "esg_full")
          Valeurs possibles : "esg_full", "carbon", "funding_application"
    """
    db: AsyncSession = context["db"]
    entreprise_id = params.get("entreprise_id")
    template_name = params.get("template_name", "esg_full")

    if not entreprise_id:
        return {"error": "entreprise_id est requis"}

    valid_templates = ["esg_full", "carbon", "funding_application"]
    if template_name not in valid_templates:
        return {
            "error": f"Template inconnu: '{template_name}'. Valeurs possibles: {', '.join(valid_templates)}"
        }

    try:
        pdf_bytes, filename = await generate_report(
            entreprise_id=entreprise_id,
            template_name=template_name,
            db=db,
            llm_callback=_llm_generate,
        )
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.exception("Erreur lors de la génération du rapport")
        return {"error": f"Erreur lors de la génération du rapport: {e}"}

    template_labels = {
        "esg_full": "Rapport ESG complet",
        "carbon": "Rapport Empreinte Carbone",
        "funding_application": "Dossier de Candidature Fonds Vert",
    }

    return {
        "status": "ok",
        "message": f"{template_labels.get(template_name, 'Rapport')} généré avec succès.",
        "filename": filename,
        "size_kb": round(len(pdf_bytes) / 1024, 1),
        "download_url": f"/api/reports/download/{filename}",
    }
