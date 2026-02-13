from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report_template import ReportTemplate

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "reports" / "templates"


def _read_template(filename: str) -> str:
    return (TEMPLATES_DIR / filename).read_text(encoding="utf-8")


REPORT_TEMPLATES = [
    {
        "nom": "esg_full",
        "description": (
            "Rapport ESG complet : page de garde, résumé exécutif, scores par pilier, "
            "détails critères, radar chart, comparaison multi-référentiel, benchmark sectoriel, "
            "historique, plan d'action, fonds recommandés."
        ),
        "sections_json": [
            {"id": "page_garde", "titre": "Page de garde", "source": "db"},
            {"id": "resume", "titre": "Résumé Exécutif", "source": "llm", "prompt": (
                "Rédige un résumé exécutif de 3-4 paragraphes pour le rapport ESG de l'entreprise {entreprise_nom}. "
                "Score global : {score_global}/100 (E: {score_e}, S: {score_s}, G: {score_g}). "
                "Référentiel : {referentiel_nom}. Mets en avant les points forts, les axes d'amélioration, "
                "et les recommandations clés. Ton professionnel, orienté décision."
            )},
            {"id": "radar_chart", "titre": "Profil ESG", "source": "code", "chart": "radar"},
            {"id": "detail_e", "titre": "Analyse Environnement", "source": "llm", "prompt": (
                "Analyse détaillée du pilier Environnement pour {entreprise_nom}. Score E : {score_e}/100. "
                "Critères évalués : {criteres_e}. Rédige 2-3 paragraphes d'analyse avec forces et faiblesses."
            )},
            {"id": "detail_s", "titre": "Analyse Social", "source": "llm", "prompt": (
                "Analyse détaillée du pilier Social pour {entreprise_nom}. Score S : {score_s}/100. "
                "Critères évalués : {criteres_s}. Rédige 2-3 paragraphes."
            )},
            {"id": "detail_g", "titre": "Analyse Gouvernance", "source": "llm", "prompt": (
                "Analyse détaillée du pilier Gouvernance pour {entreprise_nom}. Score G : {score_g}/100. "
                "Critères évalués : {criteres_g}. Rédige 2-3 paragraphes."
            )},
            {"id": "comparaison", "titre": "Comparaison Multi-Référentiel", "source": "db"},
            {"id": "benchmark", "titre": "Benchmark Sectoriel", "source": "db"},
            {"id": "evolution", "titre": "Évolution des Scores", "source": "code", "chart": "evolution"},
            {"id": "plan_action", "titre": "Plan d'Action", "source": "db"},
            {"id": "plan_action_reco", "titre": "Recommandations Plan d'Action", "source": "llm", "prompt": (
                "Rédige des recommandations pour le plan d'action ESG de {entreprise_nom}. "
                "Progression actuelle : {plan_pourcentage}%. Actions en cours : {plan_actions}. "
                "Propose des conseils pour accélérer l'amélioration du score."
            )},
            {"id": "fonds", "titre": "Fonds Verts Recommandés", "source": "db"},
        ],
        "template_file": "rapport_esg.html",
    },
    {
        "nom": "carbon",
        "description": (
            "Rapport d'empreinte carbone : bilan total, répartition par source et scope, "
            "évolution, comparaison sectorielle, plan de réduction."
        ),
        "sections_json": [
            {"id": "page_garde", "titre": "Page de garde", "source": "db"},
            {"id": "resume", "titre": "Résumé", "source": "llm", "prompt": (
                "Rédige un résumé de 2-3 paragraphes sur l'empreinte carbone de {entreprise_nom}. "
                "Total : {total_kg} kg CO₂eq. Principales sources : {top_sources}. "
                "Mets en avant les enjeux et les leviers de réduction."
            )},
            {"id": "repartition", "titre": "Répartition par Source", "source": "code", "chart": "pie"},
            {"id": "scopes", "titre": "Détail par Scope", "source": "db"},
            {"id": "evolution", "titre": "Évolution", "source": "code", "chart": "evolution"},
            {"id": "benchmark", "titre": "Comparaison Sectorielle", "source": "db"},
            {"id": "plan_reduction", "titre": "Plan de Réduction", "source": "llm", "prompt": (
                "Propose un plan de réduction carbone pour {entreprise_nom} dans le secteur {secteur}. "
                "Empreinte actuelle : {total_kg} kg CO₂eq. Source principale : {source_principale}. "
                "Classe les actions en quick-wins, moyen terme et long terme avec estimations de réduction."
            )},
            {"id": "methodologie", "titre": "Méthodologie", "source": "db"},
        ],
        "template_file": "rapport_carbone.html",
    },
    {
        "nom": "funding_application",
        "description": (
            "Dossier de candidature pour un fonds vert : profil entreprise, fonds ciblé, "
            "performance ESG, analyse d'éligibilité, score crédit vert, plan d'action, budget."
        ),
        "sections_json": [
            {"id": "page_garde", "titre": "Page de garde", "source": "db"},
            {"id": "profil", "titre": "Profil de l'Entreprise", "source": "llm", "prompt": (
                "Rédige un paragraphe de présentation professionnelle de {entreprise_nom}. "
                "Secteur : {secteur}. Taille : {taille}. Pays : {pays}. "
                "Met en avant les atouts et l'engagement environnemental."
            )},
            {"id": "fonds_cible", "titre": "Fonds Ciblé", "source": "db"},
            {"id": "scores_esg", "titre": "Performance ESG", "source": "db"},
            {"id": "radar_chart", "titre": "Profil ESG", "source": "code", "chart": "radar"},
            {"id": "eligibilite", "titre": "Analyse d'Éligibilité", "source": "llm", "prompt": (
                "Analyse l'éligibilité de {entreprise_nom} au fonds {fonds_nom}. "
                "Score ESG : {score_global}/100 (minimum requis : {score_minimum}). "
                "Secteur : {secteur}. Évalue chaque critère d'éligibilité."
            )},
            {"id": "credit_score", "titre": "Score Crédit Vert", "source": "db"},
            {"id": "plan_action", "titre": "Plan d'Action", "source": "db"},
            {"id": "budget", "titre": "Budget Prévisionnel", "source": "llm", "prompt": (
                "Propose un budget prévisionnel pour la candidature de {entreprise_nom} au fonds {fonds_nom}. "
                "Montant demandé : {montant_demande}. Secteur : {secteur}. "
                "Détaille les postes de dépenses et justifie chaque ligne."
            )},
            {"id": "conclusion", "titre": "Conclusion", "source": "llm", "prompt": (
                "Rédige une conclusion convaincante pour le dossier de candidature de {entreprise_nom} "
                "au fonds {fonds_nom}. Score ESG : {score_global}/100. "
                "Résume les points forts et l'engagement de l'entreprise."
            )},
        ],
        "template_file": "dossier_candidature.html",
    },
]


async def seed_report_templates(db: AsyncSession) -> int:
    count = 0
    for tpl_data in REPORT_TEMPLATES:
        result = await db.execute(
            select(ReportTemplate).where(ReportTemplate.nom == tpl_data["nom"])
        )
        if result.scalar_one_or_none() is None:
            template_html = _read_template(tpl_data["template_file"])
            db.add(ReportTemplate(
                nom=tpl_data["nom"],
                description=tpl_data["description"],
                sections_json=tpl_data["sections_json"],
                template_html=template_html,
            ))
            count += 1
    await db.commit()
    return count
