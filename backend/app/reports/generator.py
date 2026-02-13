"""
Générateur de rapports PDF.
Charge un template depuis report_templates, collecte les données,
rend le HTML avec Jinja2, convertit en PDF avec WeasyPrint.
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report_template import ReportTemplate
from app.models.entreprise import Entreprise
from app.models.esg_score import ESGScore
from app.models.referentiel_esg import ReferentielESG
from app.models.carbon_footprint import CarbonFootprint
from app.models.credit_score import CreditScore
from app.models.action_plan import ActionPlan, ActionItem
from app.reports.charts import (
    generate_radar_chart,
    generate_bar_chart,
    generate_pie_chart,
    generate_evolution_chart,
)

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "reports"


def _score_class(score: float | None) -> str:
    """Returns CSS class name for a score value."""
    if score is None:
        return ""
    if score >= 75:
        return "score-excellent"
    if score >= 60:
        return "score-good"
    if score >= 40:
        return "score-average"
    return "score-low"


async def _get_referentiel_nom(db: AsyncSession, referentiel_id) -> str:
    """Resolve referentiel_id to its name."""
    if not referentiel_id:
        return "N/A"
    result = await db.execute(
        select(ReferentielESG.nom).where(ReferentielESG.id == referentiel_id)
    )
    row = result.scalar_one_or_none()
    return row or "N/A"


async def _load_entreprise(db: AsyncSession, entreprise_id: str) -> dict | None:
    result = await db.execute(
        select(Entreprise).where(Entreprise.id == uuid.UUID(entreprise_id))
    )
    ent = result.scalar_one_or_none()
    if not ent:
        return None
    return {
        "id": str(ent.id),
        "nom": ent.nom,
        "secteur_activite": ent.secteur or "",
        "pays": ent.pays or "",
        "taille": f"{ent.effectifs} employés" if ent.effectifs else None,
        "nombre_employes": ent.effectifs,
        "chiffre_affaires_formatted": f"{ent.chiffre_affaires:,.0f} XOF" if ent.chiffre_affaires else None,
        "date_creation": str(ent.created_at.date()) if ent.created_at else None,
    }


async def _load_latest_esg_score(db: AsyncSession, entreprise_id: str) -> dict | None:
    result = await db.execute(
        select(ESGScore)
        .where(ESGScore.entreprise_id == uuid.UUID(entreprise_id))
        .order_by(desc(ESGScore.created_at))
        .limit(1)
    )
    score = result.scalar_one_or_none()
    if not score:
        return None
    ref_nom = await _get_referentiel_nom(db, score.referentiel_id)
    return {
        "score_global": float(score.score_global) if score.score_global is not None else 0,
        "score_e": float(score.score_e) if score.score_e is not None else 0,
        "score_s": float(score.score_s) if score.score_s is not None else 0,
        "score_g": float(score.score_g) if score.score_g is not None else 0,
        "referentiel_nom": ref_nom,
        "created_at": str(score.created_at) if score.created_at else "",
        "details_json": score.details_json if score.details_json else None,
    }


async def _load_all_esg_scores(db: AsyncSession, entreprise_id: str) -> list[dict]:
    result = await db.execute(
        select(ESGScore)
        .where(ESGScore.entreprise_id == uuid.UUID(entreprise_id))
        .order_by(desc(ESGScore.created_at))
    )
    scores = result.scalars().all()
    out = []
    for s in scores:
        ref_nom = await _get_referentiel_nom(db, s.referentiel_id)
        out.append({
            "score_global": float(s.score_global) if s.score_global is not None else 0,
            "score_e": float(s.score_e) if s.score_e is not None else 0,
            "score_s": float(s.score_s) if s.score_s is not None else 0,
            "score_g": float(s.score_g) if s.score_g is not None else 0,
            "referentiel_nom": ref_nom,
            "created_at": str(s.created_at) if s.created_at else "",
        })
    return out


async def _load_carbon(db: AsyncSession, entreprise_id: str) -> dict | None:
    result = await db.execute(
        select(CarbonFootprint)
        .where(CarbonFootprint.entreprise_id == uuid.UUID(entreprise_id))
        .order_by(desc(CarbonFootprint.created_at))
        .limit(1)
    )
    cf = result.scalar_one_or_none()
    if not cf:
        return None
    details = cf.details_json or {}
    # total_tco2e is in tonnes, convert to kg for display
    total_kg = float(cf.total_tco2e) * 1000 if cf.total_tco2e is not None else 0
    return {
        "total_kg": total_kg,
        "par_employe": details.get("par_employe"),
        "variation": details.get("variation"),
        "periode": details.get("periode", "an"),
        "details": {
            "energie": float(cf.energie) if cf.energie else 0,
            "transport": float(cf.transport) if cf.transport else 0,
            "dechets": float(cf.dechets) if cf.dechets else 0,
            "achats": float(cf.achats) if cf.achats else 0,
            **details,
        },
    }


async def _load_credit_score(db: AsyncSession, entreprise_id: str) -> dict | None:
    result = await db.execute(
        select(CreditScore)
        .where(CreditScore.entreprise_id == uuid.UUID(entreprise_id))
        .order_by(desc(CreditScore.created_at))
        .limit(1)
    )
    cs = result.scalar_one_or_none()
    if not cs:
        return None
    return {
        "score_combine": float(cs.score_combine) if cs.score_combine is not None else 0,
        "score_solvabilite": float(cs.score_solvabilite) if cs.score_solvabilite is not None else 0,
        "score_impact_vert": float(cs.score_impact_vert) if cs.score_impact_vert is not None else 0,
    }


async def _load_action_plan(db: AsyncSession, entreprise_id: str) -> dict | None:
    result = await db.execute(
        select(ActionPlan)
        .where(ActionPlan.entreprise_id == uuid.UUID(entreprise_id))
        .order_by(desc(ActionPlan.created_at))
        .limit(1)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        return None

    items_result = await db.execute(
        select(ActionItem)
        .where(ActionItem.plan_id == plan.id)
        .order_by(ActionItem.created_at)
    )
    items = items_result.scalars().all()

    total = len(items)
    done = sum(1 for i in items if i.statut == "fait")
    pct = round(done / total * 100) if total > 0 else 0

    action_items = [
        {
            "titre": item.titre,
            "priorite": item.priorite,
            "statut": item.statut,
            "echeance": str(item.echeance) if item.echeance else None,
            "impact_estime": float(item.impact_score_estime) if item.impact_score_estime else 0,
            "pilier": item.pilier,
        }
        for item in items
    ]
    return {
        "titre": plan.titre,
        "pourcentage": pct,
        "action_items": action_items,
    }


def _build_charts(score: dict | None, all_scores: list[dict], carbon: dict | None) -> dict:
    """Generate all charts as base64 strings."""
    charts: dict = {}

    # Radar chart E/S/G
    if score:
        charts["radar_chart"] = generate_radar_chart({
            "Environnement": score["score_e"],
            "Social": score["score_s"],
            "Gouvernance": score["score_g"],
        })

    # Evolution chart
    if len(all_scores) >= 2:
        dates = [s["created_at"][:10] for s in reversed(all_scores)]
        charts["evolution_chart"] = generate_evolution_chart(
            dates=dates,
            scores={
                "Global": [s["score_global"] for s in reversed(all_scores)],
                "E": [s["score_e"] for s in reversed(all_scores)],
                "S": [s["score_s"] for s in reversed(all_scores)],
                "G": [s["score_g"] for s in reversed(all_scores)],
            },
        )

    # Comparison bar chart (multi-referentiel)
    if len(all_scores) >= 2:
        ref_scores = {}
        for s in all_scores:
            ref_name = s.get("referentiel_nom", "N/A")
            if ref_name not in ref_scores:
                ref_scores[ref_name] = s["score_global"]
        if len(ref_scores) >= 2:
            charts["comparison_chart"] = generate_bar_chart(
                ref_scores,
                title="Comparaison par Référentiel",
                ylabel="Score Global",
                horizontal=True,
            )

    # Carbon pie chart
    if carbon and carbon.get("details"):
        details = carbon["details"]
        sources = {}
        for key in ["energie", "transport", "dechets", "achats"]:
            val = details.get(key, 0)
            if val and float(val) > 0:
                label = key.capitalize()
                sources[label] = float(val)
        if sources:
            charts["pie_chart"] = generate_pie_chart(sources, title="Répartition des Émissions")

    return charts


async def generate_report(
    entreprise_id: str,
    template_name: str,
    db: AsyncSession,
    llm_callback=None,
) -> tuple[bytes, str]:
    """
    Generate a PDF report.

    Args:
        entreprise_id: UUID of the enterprise
        template_name: name of the template (esg_full, carbon, funding_application)
        db: async database session
        llm_callback: optional async function(prompt: str) -> str for LLM sections

    Returns:
        tuple of (pdf_bytes, filename)
    """
    # Load template from DB
    result = await db.execute(
        select(ReportTemplate).where(
            ReportTemplate.nom == template_name,
            ReportTemplate.is_active.is_(True),
        )
    )
    template_record = result.scalar_one_or_none()
    if not template_record:
        raise ValueError(f"Template '{template_name}' introuvable ou inactif")

    # Load data
    entreprise = await _load_entreprise(db, entreprise_id)
    if not entreprise:
        raise ValueError(f"Entreprise '{entreprise_id}' introuvable")

    score = await _load_latest_esg_score(db, entreprise_id)
    all_scores = await _load_all_esg_scores(db, entreprise_id)
    carbon = await _load_carbon(db, entreprise_id)
    credit_score = await _load_credit_score(db, entreprise_id)
    plan_action = await _load_action_plan(db, entreprise_id)

    # Generate charts
    charts = _build_charts(score, all_scores, carbon)

    # Generate LLM sections
    llm_sections = {}
    if llm_callback:
        sections_json = template_record.sections_json or []
        for section in sections_json:
            if section.get("source") == "llm" and section.get("prompt"):
                prompt = section["prompt"]
                # Substitute placeholders
                replacements = {
                    "{entreprise_nom}": entreprise.get("nom", ""),
                    "{secteur}": entreprise.get("secteur_activite", ""),
                    "{taille}": entreprise.get("taille", ""),
                    "{pays}": entreprise.get("pays", ""),
                }
                if score:
                    replacements.update({
                        "{score_global}": str(score.get("score_global", "")),
                        "{score_e}": str(score.get("score_e", "")),
                        "{score_s}": str(score.get("score_s", "")),
                        "{score_g}": str(score.get("score_g", "")),
                        "{referentiel_nom}": score.get("referentiel_nom", ""),
                    })
                if carbon:
                    replacements.update({
                        "{total_kg}": str(carbon.get("total_kg", "")),
                    })
                if plan_action:
                    replacements.update({
                        "{plan_pourcentage}": str(plan_action.get("pourcentage", "")),
                        "{plan_actions}": ", ".join(
                            i["titre"] for i in plan_action.get("action_items", [])[:5]
                        ),
                    })

                for key, val in replacements.items():
                    prompt = prompt.replace(key, val)

                try:
                    text = await llm_callback(prompt)
                    section_id = section["id"]
                    llm_sections[section_id] = text
                except Exception as e:
                    logger.warning("LLM section '%s' failed: %s", section["id"], e)

    # Build Jinja2 context
    now = datetime.now(timezone.utc)
    context = {
        "entreprise": entreprise,
        "score": score,
        "all_scores": all_scores,
        "comparaison_referentiels": all_scores if len(all_scores) >= 2 else None,
        "empreinte": carbon,
        "credit_score": credit_score,
        "plan_action": plan_action,
        "date_generation": now.strftime("%d/%m/%Y à %Hh%M"),
        "score_class": _score_class,
        # Charts
        **charts,
        # LLM sections mapped to template variables
        "resume_llm": llm_sections.get("resume"),
        "analyse_e": llm_sections.get("detail_e"),
        "analyse_s": llm_sections.get("detail_s"),
        "analyse_g": llm_sections.get("detail_g"),
        "plan_action_llm": llm_sections.get("plan_action_reco"),
        "plan_reduction_llm": llm_sections.get("plan_reduction"),
        "profil_llm": llm_sections.get("profil"),
        "eligibilite_llm": llm_sections.get("eligibilite"),
        "budget_llm": llm_sections.get("budget"),
        "conclusion_llm": llm_sections.get("conclusion"),
    }

    # Render HTML with Jinja2
    jinja_env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
    )
    template_html = template_record.template_html
    jinja_template = jinja_env.from_string(template_html)
    html_content = jinja_template.render(**context)

    # Convert HTML to PDF with WeasyPrint
    from weasyprint import HTML
    pdf_bytes = HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf()

    # Save to disk
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{template_name}_{entreprise['nom'].replace(' ', '_')}_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = UPLOADS_DIR / filename
    filepath.write_bytes(pdf_bytes)

    logger.info("Report generated: %s (%d bytes)", filepath, len(pdf_bytes))

    return pdf_bytes, filename
