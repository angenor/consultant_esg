"""Handler builtin : simulation d'éligibilité à un fonds vert."""

import logging
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carbon_footprint import CarbonFootprint
from app.models.entreprise import Entreprise
from app.models.esg_score import ESGScore
from app.models.fonds_vert import FondsVert
from app.models.action_plan import ActionPlan

logger = logging.getLogger(__name__)

_MODE_ACCES_LABELS = {
    "banque_partenaire": "Via banque partenaire locale",
    "entite_accreditee": "Via entité nationale accréditée",
    "appel_propositions": "Appel à propositions périodique",
    "banque_multilaterale": "Via banque multilatérale de développement",
    "direct": "Candidature directe",
    "garantie_bancaire": "Demande via votre banque (garantie)",
}

# Mapping pays nom → ISO 3
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


async def simulate_funding(params: dict, context: dict) -> dict:
    """
    Simule l'éligibilité d'une entreprise à un fonds vert donné.

    params:
      - entreprise_id: str (optionnel si dans context)
      - fonds_id: str (ID du fonds vert)
      - montant_demande: float (optionnel)
    """
    db: AsyncSession = context["db"]
    entreprise_id = params.get("entreprise_id") or context.get("entreprise_id")
    fonds_id = params.get("fonds_id")

    if not entreprise_id:
        return {"error": "entreprise_id requis"}
    if not fonds_id:
        return {"error": "fonds_id requis. Utilisez d'abord search_green_funds pour trouver les fonds disponibles."}

    # ── Charger l'entreprise ──
    result = await db.execute(
        select(Entreprise).where(Entreprise.id == entreprise_id)
    )
    entreprise = result.scalar_one_or_none()
    if not entreprise:
        return {"error": "Entreprise introuvable"}

    # ── Charger le fonds ──
    result = await db.execute(
        select(FondsVert).where(FondsVert.id == fonds_id)
    )
    fonds = result.scalar_one_or_none()
    if not fonds:
        return {"error": "Fonds introuvable. Utilisez search_green_funds pour voir les fonds disponibles."}

    pays_code = _normalize_pays(entreprise.pays)
    secteur = (entreprise.secteur or "").lower()
    criteres = fonds.criteres_json or {}
    montant_demande = params.get("montant_demande")

    # ── Vérification des critères d'éligibilité ──
    criteres_remplis: list[dict] = []
    criteres_manquants: list[dict] = []

    # 1. Pays éligible
    pays_eligibles = fonds.pays_eligibles or []
    if pays_eligibles:
        if pays_code in pays_eligibles:
            criteres_remplis.append({
                "critere": "Pays éligible",
                "detail": f"{entreprise.pays} ({pays_code}) est dans la liste des pays éligibles",
            })
        else:
            criteres_manquants.append({
                "critere": "Pays éligible",
                "detail": f"{entreprise.pays} ({pays_code}) n'est pas dans la liste: {', '.join(pays_eligibles)}",
                "bloquant": True,
            })

    # 2. Secteur éligible
    secteurs_fonds = fonds.secteurs_json or []
    if secteurs_fonds:
        if secteur in secteurs_fonds or "tous" in secteurs_fonds:
            criteres_remplis.append({
                "critere": "Secteur éligible",
                "detail": f"Le secteur '{secteur}' est éligible pour ce fonds",
            })
        else:
            criteres_manquants.append({
                "critere": "Secteur éligible",
                "detail": f"Le secteur '{secteur}' n'est pas dans la liste: {', '.join(secteurs_fonds)}",
                "bloquant": True,
            })

    # 3. Score ESG minimum
    score_min = criteres.get("score_esg_minimum")
    esg_score = None
    if score_min is not None:
        # Chercher le score ESG le plus récent (avec le bon référentiel si possible)
        query = select(ESGScore).where(
            ESGScore.entreprise_id == entreprise_id
        )
        if fonds.referentiel_id:
            query_ref = query.where(ESGScore.referentiel_id == fonds.referentiel_id)
            result = await db.execute(
                query_ref.order_by(ESGScore.created_at.desc()).limit(1)
            )
            esg_score = result.scalar_one_or_none()

        # Fallback: dernier score ESG quel que soit le référentiel
        if not esg_score:
            result = await db.execute(
                query.order_by(ESGScore.created_at.desc()).limit(1)
            )
            esg_score = result.scalar_one_or_none()

        if esg_score:
            score_global = float(esg_score.score_global or 0)
            if score_global >= score_min:
                criteres_remplis.append({
                    "critere": "Score ESG minimum",
                    "detail": f"Score ESG {score_global}/100 ≥ minimum requis {score_min}/100",
                    "score_actuel": score_global,
                    "score_requis": score_min,
                })
            else:
                criteres_manquants.append({
                    "critere": "Score ESG minimum",
                    "detail": f"Score ESG {score_global}/100 < minimum requis {score_min}/100. "
                              f"Il manque {round(score_min - score_global, 1)} points.",
                    "score_actuel": score_global,
                    "score_requis": score_min,
                    "bloquant": True,
                })
        else:
            criteres_manquants.append({
                "critere": "Score ESG minimum",
                "detail": f"Aucun score ESG trouvé. Score minimum requis : {score_min}/100. "
                          "Utilisez calculate_esg_score pour obtenir un score.",
                "score_requis": score_min,
                "bloquant": True,
            })

    # 4. Ancienneté minimum
    anciennete_min_mois = criteres.get("anciennete_minimum_mois")
    if anciennete_min_mois:
        date_creation = entreprise.profil_json.get("date_creation") if entreprise.profil_json else None
        if date_creation:
            try:
                dt = datetime.fromisoformat(str(date_creation))
                mois_anciennete = (datetime.now(timezone.utc) - dt).days // 30
                if mois_anciennete >= anciennete_min_mois:
                    criteres_remplis.append({
                        "critere": "Ancienneté",
                        "detail": f"Entreprise créée depuis {mois_anciennete} mois ≥ {anciennete_min_mois} mois requis",
                    })
                else:
                    criteres_manquants.append({
                        "critere": "Ancienneté",
                        "detail": f"Entreprise créée depuis {mois_anciennete} mois < {anciennete_min_mois} mois requis",
                        "bloquant": True,
                    })
            except (ValueError, TypeError):
                criteres_manquants.append({
                    "critere": "Ancienneté",
                    "detail": f"Date de création non renseignée. Ancienneté minimum : {anciennete_min_mois} mois.",
                    "bloquant": False,
                })
        else:
            criteres_manquants.append({
                "critere": "Ancienneté",
                "detail": f"Date de création non renseignée. Ancienneté minimum : {anciennete_min_mois} mois.",
                "bloquant": False,
            })

    # 5. Plan de réduction carbone requis
    if criteres.get("plan_reduction_carbone_requis"):
        result = await db.execute(
            select(ActionPlan)
            .where(ActionPlan.entreprise_id == entreprise_id)
            .order_by(ActionPlan.created_at.desc())
            .limit(1)
        )
        plan = result.scalar_one_or_none()
        if plan:
            criteres_remplis.append({
                "critere": "Plan de réduction carbone",
                "detail": f"Plan existant : '{plan.titre}' (cible : {plan.score_cible} tCO2e)",
            })
        else:
            criteres_manquants.append({
                "critere": "Plan de réduction carbone",
                "detail": "Aucun plan de réduction carbone. Utilisez generate_reduction_plan pour en créer un.",
                "bloquant": True,
            })

    # 6. Impact climatique requis
    if criteres.get("impact_climatique_requis"):
        result = await db.execute(
            select(CarbonFootprint)
            .where(CarbonFootprint.entreprise_id == entreprise_id)
            .order_by(CarbonFootprint.created_at.desc())
            .limit(1)
        )
        footprint = result.scalar_one_or_none()
        if footprint:
            criteres_remplis.append({
                "critere": "Impact climatique documenté",
                "detail": f"Empreinte carbone calculée : {float(footprint.total_tco2e)} tCO2e",
            })
        else:
            criteres_manquants.append({
                "critere": "Impact climatique documenté",
                "detail": "Aucune empreinte carbone. Utilisez calculate_carbon pour la calculer.",
                "bloquant": True,
            })

    # ── Calcul d'éligibilité ──
    bloquants = [c for c in criteres_manquants if c.get("bloquant")]
    eligible = len(bloquants) == 0

    # ── Calcul du montant estimé ──
    montant_min = float(fonds.montant_min or 0)
    montant_max = float(fonds.montant_max or 0)

    if montant_demande:
        if montant_demande < montant_min:
            montant_estime = montant_min
            note_montant = f"Le montant demandé ({montant_demande:,.0f} {fonds.devise}) est inférieur au minimum ({montant_min:,.0f} {fonds.devise})"
        elif montant_demande > montant_max:
            montant_estime = montant_max
            note_montant = f"Le montant demandé ({montant_demande:,.0f} {fonds.devise}) dépasse le maximum ({montant_max:,.0f} {fonds.devise})"
        else:
            montant_estime = montant_demande
            note_montant = f"Le montant demandé est dans la fourchette éligible"
    else:
        # Estimer un montant basé sur le score ESG et la taille
        if esg_score and montant_max > 0:
            score_ratio = min(float(esg_score.score_global or 50) / 100, 1.0)
            montant_estime = round(montant_min + (montant_max - montant_min) * score_ratio * 0.5)
            note_montant = f"Montant estimé basé sur votre score ESG ({float(esg_score.score_global or 0)}/100)"
        else:
            montant_estime = round((montant_min + montant_max) / 2)
            note_montant = "Estimation médiane (score ESG non disponible pour affiner)"

    # ── Timeline estimée ──
    if fonds.type == "subvention":
        timeline = {
            "depot_dossier": "4-6 semaines",
            "evaluation": "2-3 mois",
            "decision": "1-2 mois",
            "decaissement": "1-3 mois",
            "total_estime": "6-12 mois",
        }
    elif fonds.type == "garantie":
        timeline = {
            "depot_dossier": "2-4 semaines",
            "evaluation": "1-2 mois",
            "decision": "2-4 semaines",
            "mise_en_place": "1-2 mois",
            "total_estime": "3-6 mois",
        }
    else:  # prêt
        timeline = {
            "depot_dossier": "2-4 semaines",
            "evaluation": "1-2 mois",
            "decision": "2-4 semaines",
            "decaissement": "1-2 mois",
            "total_estime": "3-6 mois",
        }

    # ── ROI vert estimé ──
    roi_vert = None
    result = await db.execute(
        select(CarbonFootprint)
        .where(CarbonFootprint.entreprise_id == entreprise_id)
        .order_by(CarbonFootprint.created_at.desc())
        .limit(1)
    )
    footprint = result.scalar_one_or_none()
    if footprint and montant_estime > 0:
        total_tco2 = float(footprint.total_tco2e)
        # Estimation : 20% de réduction à terme pour le montant investi
        reduction_estimee = round(total_tco2 * 0.20, 2)
        cout_par_tco2 = round(montant_estime / max(reduction_estimee, 1))
        roi_vert = {
            "empreinte_actuelle_tco2e": total_tco2,
            "reduction_estimee_tco2e": reduction_estimee,
            "cout_par_tco2e_evitee": cout_par_tco2,
            "devise": fonds.devise,
        }

    # ── Score de compatibilité ──
    total_criteres = len(criteres_remplis) + len(criteres_manquants)
    compatibilite_pct = round(len(criteres_remplis) / max(total_criteres, 1) * 100)

    return {
        "eligible": eligible,
        "compatibilite_pct": compatibilite_pct,
        "fonds": {
            "id": str(fonds.id),
            "nom": fonds.nom,
            "institution": fonds.institution,
            "type": fonds.type,
            "devise": fonds.devise,
            "montant_min": montant_min,
            "montant_max": montant_max,
            "description": criteres.get("description", ""),
            "mode_acces": fonds.mode_acces,
            "mode_acces_label": _MODE_ACCES_LABELS.get(fonds.mode_acces or "", "Non spécifié"),
            "acces_details": criteres.get("acces_details"),
        },
        "entreprise": {
            "nom": entreprise.nom,
            "secteur": secteur,
            "pays": f"{entreprise.pays} ({pays_code})",
        },
        "montant_estime": montant_estime,
        "note_montant": note_montant,
        "criteres_remplis": criteres_remplis,
        "criteres_manquants": criteres_manquants,
        "nombre_criteres_bloquants": len(bloquants),
        "timeline_estimee": timeline,
        "roi_vert": roi_vert,
        "date_limite": str(fonds.date_limite) if fonds.date_limite else None,
        "recommandations": _generer_recommandations(criteres_manquants, eligible),
        "prochaines_etapes": _generer_etapes(criteres, eligible),
    }


def _generer_recommandations(criteres_manquants: list[dict], eligible: bool) -> list[str]:
    """Génère des recommandations basées sur les critères manquants."""
    recommandations = []

    if eligible:
        recommandations.append("Votre entreprise remplit tous les critères d'éligibilité. Vous pouvez déposer votre dossier.")
        return recommandations

    for c in criteres_manquants:
        critere = c["critere"]
        if critere == "Score ESG minimum":
            recommandations.append(
                "Améliorez votre score ESG avec calculate_esg_score puis suivez les recommandations."
            )
        elif critere == "Plan de réduction carbone":
            recommandations.append(
                "Générez un plan de réduction carbone avec generate_reduction_plan."
            )
        elif critere == "Impact climatique documenté":
            recommandations.append(
                "Calculez votre empreinte carbone avec calculate_carbon."
            )
        elif critere == "Secteur éligible":
            recommandations.append(
                "Ce fonds n'est pas accessible pour votre secteur. Cherchez d'autres fonds avec search_green_funds."
            )
        elif critere == "Pays éligible":
            recommandations.append(
                "Ce fonds n'est pas accessible pour votre pays. Cherchez d'autres fonds avec search_green_funds."
            )

    return recommandations


def _generer_etapes(criteres: dict, eligible: bool) -> list[str]:
    """Génère les prochaines étapes basées sur le mode d'accès du fonds."""
    acces = criteres.get("acces_details", {})
    etapes = acces.get("etapes", [])

    if not eligible:
        return ["Remplir les critères manquants (voir critères ci-dessus)"] + etapes[:2]

    return etapes
