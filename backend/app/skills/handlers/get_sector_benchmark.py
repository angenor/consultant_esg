"""Handler builtin : benchmarking sectoriel."""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carbon_footprint import CarbonFootprint
from app.models.entreprise import Entreprise
from app.models.esg_score import ESGScore
from app.models.referentiel_esg import ReferentielESG
from app.models.sector_benchmark import SectorBenchmark

logger = logging.getLogger(__name__)

_PAYS_MAPPING = {
    "côte d'ivoire": "CIV", "cote d'ivoire": "CIV", "ivory coast": "CIV",
    "sénégal": "SEN", "senegal": "SEN",
    "cameroun": "CMR", "cameroon": "CMR",
    "mali": "MLI",
    "burkina faso": "BFA", "burkina": "BFA",
    "ghana": "GHA",
    "guinée-bissau": "GNB", "guinee-bissau": "GNB",
    "togo": "TGO",
    "bénin": "BEN", "benin": "BEN",
    "niger": "NER",
    "nigeria": "NGA",
    "kenya": "KEN",
}


def _normalize_pays(pays: str) -> str:
    if not pays:
        return "CIV"
    p = pays.strip().upper()
    if len(p) == 3 and p.isalpha():
        return p
    return _PAYS_MAPPING.get(pays.strip().lower(), "CIV")


async def get_sector_benchmark(params: dict, context: dict) -> dict:
    """
    Récupère les moyennes sectorielles et compare avec l'entreprise.

    params:
      - secteur: str (requis)
      - pays: str (optionnel, code ISO 3 ou nom)
      - referentiel_code: str (optionnel)
    """
    db: AsyncSession = context["db"]
    entreprise_id = context.get("entreprise_id")

    secteur = (params.get("secteur") or "").strip().lower()
    if not secteur:
        return {"error": "Le paramètre 'secteur' est requis."}

    pays_input = params.get("pays", "")
    pays_code = _normalize_pays(pays_input) if pays_input else None
    referentiel_code = params.get("referentiel_code")

    # Résoudre le référentiel si un code est fourni
    referentiel_id = None
    if referentiel_code:
        result = await db.execute(
            select(ReferentielESG).where(ReferentielESG.code == referentiel_code)
        )
        ref = result.scalar_one_or_none()
        if ref:
            referentiel_id = ref.id

    # Chercher le benchmark
    query = select(SectorBenchmark).where(
        SectorBenchmark.secteur == secteur
    )
    if pays_code:
        query = query.where(SectorBenchmark.pays == pays_code)
    if referentiel_id:
        query = query.where(SectorBenchmark.referentiel_id == referentiel_id)

    query = query.order_by(SectorBenchmark.updated_at.desc()).limit(1)
    result = await db.execute(query)
    benchmark = result.scalar_one_or_none()

    if not benchmark:
        # Fallback : chercher sans filtre pays
        if pays_code:
            query_fallback = (
                select(SectorBenchmark)
                .where(SectorBenchmark.secteur == secteur)
                .order_by(SectorBenchmark.updated_at.desc())
                .limit(1)
            )
            result = await db.execute(query_fallback)
            benchmark = result.scalar_one_or_none()

    if not benchmark:
        return {
            "error": f"Aucun benchmark trouvé pour le secteur '{secteur}'.",
            "secteurs_disponibles": await _list_secteurs(db),
        }

    # Construire le résultat benchmark
    bench_data = {
        "secteur": benchmark.secteur,
        "pays": benchmark.pays,
        "periode": benchmark.periode,
        "nombre_entreprises": benchmark.nombre_entreprises,
        "moyennes": {
            "score_e": float(benchmark.score_e_moyen or 0),
            "score_s": float(benchmark.score_s_moyen or 0),
            "score_g": float(benchmark.score_g_moyen or 0),
            "score_global": float(benchmark.score_global_moyen or 0),
            "carbone_tco2e": float(benchmark.carbone_moyen_tco2e or 0),
        },
    }

    # Comparer avec l'entreprise si disponible
    comparaison = None
    if entreprise_id:
        comparaison = await _comparer_entreprise(
            db, entreprise_id, bench_data["moyennes"]
        )

    return {
        "benchmark": bench_data,
        "comparaison_entreprise": comparaison,
    }


async def _comparer_entreprise(
    db: AsyncSession, entreprise_id: str, moyennes: dict
) -> dict | None:
    """Compare les scores de l'entreprise avec les moyennes sectorielles."""
    result = await db.execute(
        select(Entreprise).where(Entreprise.id == entreprise_id)
    )
    entreprise = result.scalar_one_or_none()
    if not entreprise:
        return None

    # Dernier score ESG
    result = await db.execute(
        select(ESGScore)
        .where(ESGScore.entreprise_id == entreprise_id)
        .order_by(ESGScore.created_at.desc())
        .limit(1)
    )
    esg = result.scalar_one_or_none()

    # Dernière empreinte carbone
    result = await db.execute(
        select(CarbonFootprint)
        .where(CarbonFootprint.entreprise_id == entreprise_id)
        .order_by(CarbonFootprint.created_at.desc())
        .limit(1)
    )
    footprint = result.scalar_one_or_none()

    if not esg and not footprint:
        return {
            "entreprise": entreprise.nom,
            "message": "Aucun score ESG ni empreinte carbone disponible pour comparer.",
        }

    comp: dict[str, Any] = {"entreprise": entreprise.nom}

    if esg:
        score_e = float(esg.score_e or 0)
        score_s = float(esg.score_s or 0)
        score_g = float(esg.score_g or 0)
        score_global = float(esg.score_global or 0)

        comp["scores"] = {
            "environnement": {
                "entreprise": score_e,
                "moyenne_secteur": moyennes["score_e"],
                "ecart": round(score_e - moyennes["score_e"], 1),
                "position": "au-dessus" if score_e >= moyennes["score_e"] else "en-dessous",
            },
            "social": {
                "entreprise": score_s,
                "moyenne_secteur": moyennes["score_s"],
                "ecart": round(score_s - moyennes["score_s"], 1),
                "position": "au-dessus" if score_s >= moyennes["score_s"] else "en-dessous",
            },
            "gouvernance": {
                "entreprise": score_g,
                "moyenne_secteur": moyennes["score_g"],
                "ecart": round(score_g - moyennes["score_g"], 1),
                "position": "au-dessus" if score_g >= moyennes["score_g"] else "en-dessous",
            },
            "global": {
                "entreprise": score_global,
                "moyenne_secteur": moyennes["score_global"],
                "ecart": round(score_global - moyennes["score_global"], 1),
                "position": "au-dessus" if score_global >= moyennes["score_global"] else "en-dessous",
            },
        }

    if footprint:
        carbone = float(footprint.total_tco2e)
        moy_carbone = moyennes["carbone_tco2e"]
        comp["carbone"] = {
            "entreprise_tco2e": carbone,
            "moyenne_secteur_tco2e": moy_carbone,
            "ecart_tco2e": round(carbone - moy_carbone, 2),
            "position": "en-dessous" if carbone <= moy_carbone else "au-dessus",
            "note": (
                "Votre empreinte est inférieure à la moyenne du secteur."
                if carbone <= moy_carbone
                else "Votre empreinte est supérieure à la moyenne du secteur."
            ),
        }

    return comp


async def _list_secteurs(db: AsyncSession) -> list[str]:
    """Liste les secteurs disponibles dans les benchmarks."""
    result = await db.execute(
        select(SectorBenchmark.secteur).distinct()
    )
    return [row[0] for row in result.all()]
