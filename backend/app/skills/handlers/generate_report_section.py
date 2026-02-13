"""
Handler: generate_report_section
Génère le texte d'une section de rapport via le LLM.
"""

import logging
import uuid

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.report_template import ReportTemplate

logger = logging.getLogger(__name__)


async def generate_report_section(params: dict, context: dict) -> dict:
    """
    Génère le contenu textuel d'une section de rapport.

    params:
        - entreprise_id: str
        - template_id: str (optionnel, sinon déduit de template_name)
        - template_name: str (optionnel)
        - section_id: str — id de la section dans sections_json
        - context_data: dict (optionnel) — données contextuelles à injecter dans le prompt
    """
    db: AsyncSession = context["db"]
    section_id = params.get("section_id")
    template_name = params.get("template_name")
    template_id = params.get("template_id")
    context_data = params.get("context_data", {})

    if not section_id:
        return {"error": "section_id est requis"}

    # Load template
    if template_id:
        result = await db.execute(
            select(ReportTemplate).where(ReportTemplate.id == uuid.UUID(template_id))
        )
    elif template_name:
        result = await db.execute(
            select(ReportTemplate).where(ReportTemplate.nom == template_name)
        )
    else:
        return {"error": "template_id ou template_name est requis"}

    template = result.scalar_one_or_none()
    if not template:
        return {"error": "Template introuvable"}

    # Find section in sections_json
    sections = template.sections_json or []
    section = next((s for s in sections if s.get("id") == section_id), None)
    if not section:
        return {"error": f"Section '{section_id}' introuvable dans le template"}

    if section.get("source") != "llm":
        return {"error": f"La section '{section_id}' n'est pas de type LLM (source: {section.get('source')})"}

    prompt = section.get("prompt", "")
    if not prompt:
        return {"error": f"Pas de prompt défini pour la section '{section_id}'"}

    # Substitute context_data into prompt
    for key, val in context_data.items():
        prompt = prompt.replace(f"{{{key}}}", str(val))

    # Call LLM
    client = AsyncOpenAI(
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
    )

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            max_tokens=1500,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un expert ESG qui rédige des sections de rapports professionnels. "
                        "Rédige en français, de manière claire et structurée. "
                        "Ne mets pas de titre (il est déjà dans le template). "
                        "Utilise un ton professionnel et factuel."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        generated_text = response.choices[0].message.content or ""
    except Exception as e:
        logger.error("LLM call failed for section '%s': %s", section_id, e)
        return {"error": f"Erreur lors de la génération LLM: {e}"}

    return {
        "status": "ok",
        "section_id": section_id,
        "titre": section.get("titre", ""),
        "contenu": generated_text,
    }
