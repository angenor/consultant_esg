"""Handler builtin : calculateur d'empreinte carbone."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carbon_footprint import CarbonFootprint
from app.models.entreprise import Entreprise
from app.models.sector_benchmark import SectorBenchmark

logger = logging.getLogger(__name__)

# Charger les facteurs d'émission au démarrage du module
_FACTEURS_PATH = Path("/app/data/facteurs_emission.json")
_FACTEURS: dict[str, Any] = {}

try:
    _FACTEURS = json.loads(_FACTEURS_PATH.read_text(encoding="utf-8"))
except FileNotFoundError:
    # Fallback dev local
    _local = Path(__file__).resolve().parents[3] / "data" / "facteurs_emission.json"
    if _local.exists():
        _FACTEURS = json.loads(_local.read_text(encoding="utf-8"))
    else:
        logger.warning("facteurs_emission.json introuvable")


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
    """Convertit un nom de pays ou code en code ISO 3."""
    if not pays:
        return "CIV"
    p = pays.strip().upper()
    if len(p) == 3 and p.isalpha():
        return p
    return _PAYS_MAPPING.get(pays.strip().lower(), "CIV")


def _get_facteurs_pays(pays_code: str) -> dict[str, Any]:
    """Retourne les facteurs d'émission pour un pays donné (fallback CIV)."""
    pays_data = _FACTEURS.get("pays", {})
    return pays_data.get(pays_code, pays_data.get("CIV", {}))


async def calculate_carbon(params: dict, context: dict) -> dict:
    """
    Calcule l'empreinte carbone annuelle d'une entreprise.

    params:
      - entreprise_id: str (optionnel si dans context)
      - annee: int (optionnel, défaut année courante)
      - mois: int (optionnel, pour un calcul mensuel)
      - data: dict avec clés de consommation :
          - electricite_kwh: float
          - generateur_litres: float
          - type_generateur: str ("diesel" | "essence")
          - vehicules_km: float
          - nombre_vehicules: int
          - type_carburant: str ("diesel" | "essence")
          - type_vehicule: str ("voiture" | "camion" | "moto")
          - dechets_tonnes: float
          - type_traitement: str ("enfouissement" | "recyclage" | "compostage" | "incineration")
          - achats_montant: float (en FCFA)

    Retourne : total tCO2e, répartition par source, détails, comparaison sectorielle.
    """
    db: AsyncSession = context["db"]
    entreprise_id = params.get("entreprise_id") or context.get("entreprise_id")

    if not entreprise_id:
        return {"error": "entreprise_id requis"}

    # Charger l'entreprise pour le pays et le secteur
    result = await db.execute(
        select(Entreprise).where(Entreprise.id == entreprise_id)
    )
    entreprise = result.scalar_one_or_none()
    if not entreprise:
        return {"error": "Entreprise introuvable"}

    pays_code = _normalize_pays(entreprise.pays)
    secteur = entreprise.secteur or ""
    facteurs = _get_facteurs_pays(pays_code)

    data: dict[str, Any] = params.get("data", {})
    annee = params.get("annee", datetime.now().year)
    mois = params.get("mois")

    # ── Calculs par source ──

    details: dict[str, Any] = {}
    energie_tco2 = 0.0
    transport_tco2 = 0.0
    dechets_tco2 = 0.0
    achats_tco2 = 0.0

    # 1. Énergie — Électricité
    elec_kwh = _to_float(data.get("electricite_kwh"))
    if elec_kwh:
        facteur_elec = facteurs.get("electricite_kgco2_par_kwh", 0.45)
        elec_co2 = elec_kwh * facteur_elec / 1000  # kgCO2 → tCO2
        energie_tco2 += elec_co2
        details["electricite"] = {
            "consommation_kwh": elec_kwh,
            "facteur_kgco2_kwh": facteur_elec,
            "emissions_tco2e": round(elec_co2, 3),
        }

    # 2. Énergie — Générateur
    gen_litres = _to_float(data.get("generateur_litres"))
    if gen_litres:
        type_gen = data.get("type_generateur", "diesel").lower()
        sources = facteurs.get("sources", {})
        facteur_gen = sources.get(
            f"{type_gen}_kgco2_par_litre",
            sources.get("diesel_kgco2_par_litre", 2.68),
        )
        gen_co2 = gen_litres * facteur_gen / 1000
        energie_tco2 += gen_co2
        details["generateur"] = {
            "consommation_litres": gen_litres,
            "type_carburant": type_gen,
            "facteur_kgco2_litre": facteur_gen,
            "emissions_tco2e": round(gen_co2, 3),
        }

    # 3. Transport — Véhicules
    vehicules_km = _to_float(data.get("vehicules_km"))
    if vehicules_km:
        type_carb = data.get("type_carburant", "diesel").lower()
        type_vehicule = data.get("type_vehicule", "voiture").lower()
        nb_vehicules = int(data.get("nombre_vehicules", 1))

        transport_factors = facteurs.get("transport", {})
        facteur_key = f"{type_vehicule}_{type_carb}_kgco2_par_km"
        facteur_transport = transport_factors.get(
            facteur_key,
            transport_factors.get(f"voiture_{type_carb}_kgco2_par_km", 0.21),
        )

        total_km = vehicules_km * nb_vehicules
        transport_co2 = total_km * facteur_transport / 1000
        transport_tco2 += transport_co2
        details["transport"] = {
            "km_par_vehicule": vehicules_km,
            "nombre_vehicules": nb_vehicules,
            "total_km": total_km,
            "type_vehicule": type_vehicule,
            "type_carburant": type_carb,
            "facteur_kgco2_km": facteur_transport,
            "emissions_tco2e": round(transport_co2, 3),
        }

    # 4. Déchets
    dechets_tonnes = _to_float(data.get("dechets_tonnes"))
    if dechets_tonnes:
        type_trait = data.get("type_traitement", "enfouissement").lower()
        dechets_factors = facteurs.get("dechets", {})
        facteur_dechets = dechets_factors.get(
            f"{type_trait}_kgco2_par_tonne",
            dechets_factors.get("enfouissement_kgco2_par_tonne", 580),
        )
        dechets_co2 = dechets_tonnes * facteur_dechets / 1000
        dechets_tco2 += dechets_co2
        details["dechets"] = {
            "tonnes": dechets_tonnes,
            "type_traitement": type_trait,
            "facteur_kgco2_tonne": facteur_dechets,
            "emissions_tco2e": round(dechets_co2, 3),
        }

    # 5. Achats
    achats_montant = _to_float(data.get("achats_montant"))
    if achats_montant:
        facteur_achats = _FACTEURS.get("achats", {}).get(
            "facteur_defaut_kgco2_par_1000xof", 0.5
        )
        achats_co2 = (achats_montant / 1000) * facteur_achats / 1000
        achats_tco2 += achats_co2
        details["achats"] = {
            "montant_fcfa": achats_montant,
            "facteur_kgco2_par_1000xof": facteur_achats,
            "emissions_tco2e": round(achats_co2, 3),
        }

    # ── Total ──
    total_tco2 = round(energie_tco2 + transport_tco2 + dechets_tco2 + achats_tco2, 3)

    if total_tco2 == 0:
        return {
            "error": (
                "Aucune donnée de consommation fournie. "
                "Merci de renseigner au moins une donnée parmi : "
                "electricite_kwh, generateur_litres, vehicules_km, "
                "dechets_tonnes, achats_montant."
            )
        }

    # Répartition en pourcentage
    repartition = {}
    if total_tco2 > 0:
        repartition = {
            "energie": round(energie_tco2 / total_tco2 * 100, 1),
            "transport": round(transport_tco2 / total_tco2 * 100, 1),
            "dechets": round(dechets_tco2 / total_tco2 * 100, 1),
            "achats": round(achats_tco2 / total_tco2 * 100, 1),
        }

    # ── Comparaison sectorielle ──
    benchmark_info = None
    if secteur:
        bench_result = await db.execute(
            select(SectorBenchmark).where(
                SectorBenchmark.secteur == secteur.lower(),
                (SectorBenchmark.pays == pays_code) | (SectorBenchmark.pays.is_(None)),
            ).order_by(SectorBenchmark.pays.desc().nulls_last())
            .limit(1)
        )
        benchmark = bench_result.scalar_one_or_none()
        if benchmark and benchmark.carbone_moyen_tco2e:
            moyenne = float(benchmark.carbone_moyen_tco2e)
            ecart_pct = round((total_tco2 - moyenne) / moyenne * 100, 1) if moyenne else 0
            if total_tco2 < moyenne * 0.8:
                position = "Nettement en dessous de la moyenne"
            elif total_tco2 < moyenne:
                position = "En dessous de la moyenne"
            elif total_tco2 < moyenne * 1.2:
                position = "Proche de la moyenne"
            else:
                position = "Au-dessus de la moyenne"

            benchmark_info = {
                "secteur": secteur,
                "pays": pays_code,
                "moyenne_tco2e": moyenne,
                "votre_total_tco2e": total_tco2,
                "ecart_pct": ecart_pct,
                "position": position,
                "nombre_entreprises": benchmark.nombre_entreprises,
            }

    # ── Sauvegarde en BDD ──
    carbon = CarbonFootprint(
        entreprise_id=entreprise_id,
        annee=annee,
        mois=mois,
        energie=round(energie_tco2, 2),
        transport=round(transport_tco2, 2),
        dechets=round(dechets_tco2, 2),
        achats=round(achats_tco2, 2),
        total_tco2e=total_tco2,
        details_json={
            "pays": pays_code,
            "facteurs_utilises": facteurs.get("nom", pays_code),
            "calculs": details,
        },
        source="conversation",
    )
    db.add(carbon)
    await db.commit()
    await db.refresh(carbon)

    return {
        "carbon_footprint_id": str(carbon.id),
        "entreprise": entreprise.nom,
        "annee": annee,
        "mois": mois,
        "total_tco2e": total_tco2,
        "repartition_pct": repartition,
        "detail_par_source": {
            "energie_tco2e": round(energie_tco2, 3),
            "transport_tco2e": round(transport_tco2, 3),
            "dechets_tco2e": round(dechets_tco2, 3),
            "achats_tco2e": round(achats_tco2, 3),
        },
        "calculs_detailles": details,
        "benchmark": benchmark_info,
        "pays_facteurs": facteurs.get("nom", pays_code),
    }


def _to_float(val: Any) -> float | None:
    """Convertit une valeur en float, retourne None si impossible."""
    if val is None:
        return None
    try:
        f = float(val)
        return f if f > 0 else None
    except (ValueError, TypeError):
        return None
