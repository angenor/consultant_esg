"""Handler builtin : guide l'utilisateur dans le processus de candidature à un fonds vert."""

import logging

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_plan import ActionPlan
from app.models.carbon_footprint import CarbonFootprint
from app.models.entreprise import Entreprise
from app.models.esg_score import ESGScore
from app.models.fonds_vert import FondsVert
from app.models.intermediaire import Intermediaire

logger = logging.getLogger(__name__)

_MODE_ACCES_LABELS = {
    "banque_partenaire": "Via banque partenaire locale",
    "entite_accreditee": "Via entité nationale accréditée",
    "appel_propositions": "Appel à propositions périodique",
    "banque_multilaterale": "Via banque multilatérale de développement",
    "direct": "Candidature directe",
    "garantie_bancaire": "Demande via votre banque (garantie)",
}

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


async def guide_candidature(params: dict, context: dict) -> dict:
    """
    Guide l'utilisateur dans le processus de candidature à un fonds vert.

    params:
      - entreprise_id: str (requis)
      - fonds_id: str (optionnel)
      - fonds_nom: str (optionnel, recherche par nom si fonds_id absent)
      - action: str (analyser | lister_intermediaires | preparer_dossier | lancer_soumission)
      - intermediaire_id: str (optionnel, pour preparer_dossier et lancer_soumission)
    """
    action = params.get("action", "analyser")

    if action == "analyser":
        return await _action_analyser(params, context)
    elif action == "lister_intermediaires":
        return await _action_lister_intermediaires(params, context)
    elif action == "preparer_dossier":
        return await _action_preparer_dossier(params, context)
    elif action == "lancer_soumission":
        return await _action_lancer_soumission(params, context)
    else:
        return {"error": f"Action inconnue : '{action}'. Actions valides : analyser, lister_intermediaires, preparer_dossier, lancer_soumission"}


# ── Helpers communs ────────────────────────────────────────────────


async def _load_fonds(db: AsyncSession, params: dict) -> FondsVert | None:
    """Charge un fonds par ID ou par recherche de nom."""
    fonds_id = params.get("fonds_id")
    fonds_nom = params.get("fonds_nom")

    if fonds_id:
        result = await db.execute(select(FondsVert).where(FondsVert.id == fonds_id))
        return result.scalar_one_or_none()

    if fonds_nom:
        result = await db.execute(
            select(FondsVert)
            .where(FondsVert.nom.ilike(f"%{fonds_nom}%"))
            .limit(1)
        )
        return result.scalar_one_or_none()

    return None


async def _load_intermediaires_for_fund(
    db: AsyncSession, fonds_id, pays_entreprise: str | None
) -> list[Intermediaire]:
    """Charge les intermédiaires d'un fonds filtrés par pays de l'entreprise."""
    query = (
        select(Intermediaire)
        .where(
            Intermediaire.fonds_id == fonds_id,
            Intermediaire.is_active.is_(True),
        )
        .order_by(Intermediaire.est_recommande.desc(), Intermediaire.nom)
    )
    if pays_entreprise:
        query = query.where(
            or_(Intermediaire.pays == pays_entreprise, Intermediaire.pays.is_(None))
        )
    result = await db.execute(query)
    return list(result.scalars().all())


def _serialize_intermediaire(i: Intermediaire) -> dict:
    """Sérialise un intermédiaire en dict."""
    return {
        "id": str(i.id),
        "nom": i.nom,
        "type": i.type,
        "pays": i.pays,
        "ville": i.ville,
        "email": i.email,
        "telephone": i.telephone,
        "site_web": i.site_web,
        "url_formulaire": i.url_formulaire,
        "type_soumission": i.type_soumission,
        "instructions_soumission": i.instructions_soumission,
        "documents_requis": i.documents_requis or [],
        "etapes_specifiques": i.etapes_specifiques or [],
        "delai_traitement": i.delai_traitement,
        "est_recommande": i.est_recommande,
    }


# ── Action : analyser ─────────────────────────────────────────────


async def _action_analyser(params: dict, context: dict) -> dict:
    db: AsyncSession = context["db"]
    entreprise_id = params.get("entreprise_id") or context.get("entreprise_id")

    if not entreprise_id:
        return {"error": "entreprise_id requis"}

    # Charger le fonds
    fonds = await _load_fonds(db, params)
    if not fonds:
        return {"error": "Fonds introuvable. Précisez fonds_id ou fonds_nom."}

    # Charger l'entreprise
    result = await db.execute(select(Entreprise).where(Entreprise.id == entreprise_id))
    entreprise = result.scalar_one_or_none()
    if not entreprise:
        return {"error": "Entreprise introuvable"}

    pays_code = _normalize_pays(entreprise.pays)
    secteur = (entreprise.secteur or "").lower()
    criteres = fonds.criteres_json or {}

    # Dernier score ESG
    result = await db.execute(
        select(ESGScore)
        .where(ESGScore.entreprise_id == entreprise_id)
        .order_by(ESGScore.created_at.desc())
        .limit(1)
    )
    esg_score = result.scalar_one_or_none()
    score_global = float(esg_score.score_global or 0) if esg_score else None

    # Vérification d'éligibilité
    criteres_manquants = []

    # Pays
    pays_eligibles = fonds.pays_eligibles or []
    if pays_eligibles and pays_code not in [p.upper() for p in pays_eligibles]:
        criteres_manquants.append({
            "critere": "Pays éligible",
            "detail": f"{entreprise.pays} ({pays_code}) n'est pas dans la liste des pays éligibles",
        })

    # Secteur
    secteurs_fonds = fonds.secteurs_json or []
    if secteurs_fonds and secteur not in [s.lower() for s in secteurs_fonds] and "tous" not in secteurs_fonds:
        criteres_manquants.append({
            "critere": "Secteur éligible",
            "detail": f"Le secteur '{secteur}' n'est pas éligible pour ce fonds",
        })

    # Score ESG minimum
    score_min = criteres.get("score_esg_minimum")
    if score_min is not None:
        if score_global is None:
            criteres_manquants.append({
                "critere": "Score ESG minimum",
                "detail": f"Aucun score ESG calculé. Minimum requis : {score_min}/100",
            })
        elif score_global < score_min:
            criteres_manquants.append({
                "critere": "Score ESG minimum",
                "detail": f"Score ESG {score_global}/100 < minimum requis {score_min}/100",
            })

    eligible = len(criteres_manquants) == 0

    # Intermédiaires filtrés par pays
    intermediaires = await _load_intermediaires_for_fund(db, fonds.id, entreprise.pays)

    # Étapes du processus
    acces_details = criteres.get("acces_details", {})
    etapes_processus = acces_details.get("etapes", [])
    if not etapes_processus and intermediaires:
        # Utiliser les étapes du premier intermédiaire recommandé
        recommande = next((i for i in intermediaires if i.est_recommande), intermediaires[0])
        etapes_processus = recommande.etapes_specifiques or []

    # Documents nécessaires
    documents_necessaires = []
    if intermediaires:
        recommande = next((i for i in intermediaires if i.est_recommande), intermediaires[0])
        for doc in (recommande.documents_requis or []):
            if isinstance(doc, str):
                documents_necessaires.append(doc)
            elif isinstance(doc, dict):
                documents_necessaires.append(doc.get("nom", str(doc)))

    candidature_directe_possible = fonds.mode_acces == "direct"
    formulaire_en_ligne_disponible = any(
        i.type_soumission in ("formulaire_en_ligne", "portail_dedie")
        for i in intermediaires
    )

    # Actions proposées
    actions_proposees = []
    if eligible:
        actions_proposees.append({
            "action": "preparer_dossier",
            "label": "Préparer le dossier de candidature",
        })
        if formulaire_en_ligne_disponible:
            actions_proposees.append({
                "action": "lancer_soumission",
                "label": "Ouvrir le formulaire en ligne",
            })
    else:
        actions_proposees.append({
            "action": "lister_intermediaires",
            "label": "Voir les intermédiaires disponibles",
        })

    return {
        "fonds": {
            "id": str(fonds.id),
            "nom": fonds.nom,
            "institution": fonds.institution,
            "type": fonds.type,
            "mode_acces": fonds.mode_acces,
            "mode_acces_label": _MODE_ACCES_LABELS.get(fonds.mode_acces or "", "Non spécifié"),
            "url": fonds.url_source,
        },
        "eligible": eligible,
        "criteres_manquants": criteres_manquants,
        "score_esg_actuel": score_global,
        "intermediaires_disponibles": [_serialize_intermediaire(i) for i in intermediaires],
        "etapes_processus": etapes_processus,
        "documents_necessaires": documents_necessaires,
        "candidature_directe_possible": candidature_directe_possible,
        "formulaire_en_ligne_disponible": formulaire_en_ligne_disponible,
        "actions_proposees": actions_proposees,
    }


# ── Action : lister_intermediaires ─────────────────────────────────


async def _action_lister_intermediaires(params: dict, context: dict) -> dict:
    db: AsyncSession = context["db"]
    entreprise_id = params.get("entreprise_id") or context.get("entreprise_id")

    if not entreprise_id:
        return {"error": "entreprise_id requis"}

    fonds = await _load_fonds(db, params)
    if not fonds:
        return {"error": "Fonds introuvable. Précisez fonds_id ou fonds_nom."}

    # Charger l'entreprise pour le pays
    result = await db.execute(select(Entreprise).where(Entreprise.id == entreprise_id))
    entreprise = result.scalar_one_or_none()
    if not entreprise:
        return {"error": "Entreprise introuvable"}

    intermediaires = await _load_intermediaires_for_fund(db, fonds.id, entreprise.pays)

    return {
        "fonds": fonds.nom,
        "pays_filtre": entreprise.pays,
        "nombre": len(intermediaires),
        "intermediaires": [_serialize_intermediaire(i) for i in intermediaires],
    }


# ── Action : preparer_dossier ─────────────────────────────────────


async def _action_preparer_dossier(params: dict, context: dict) -> dict:
    db: AsyncSession = context["db"]
    entreprise_id = params.get("entreprise_id") or context.get("entreprise_id")

    if not entreprise_id:
        return {"error": "entreprise_id requis"}

    fonds = await _load_fonds(db, params)
    if not fonds:
        return {"error": "Fonds introuvable. Précisez fonds_id ou fonds_nom."}

    # Charger intermédiaire si spécifié
    intermediaire = None
    intermediaire_id = params.get("intermediaire_id")
    if intermediaire_id:
        result = await db.execute(
            select(Intermediaire).where(Intermediaire.id == intermediaire_id)
        )
        intermediaire = result.scalar_one_or_none()

    # Si pas d'intermédiaire spécifié, prendre le recommandé
    if not intermediaire:
        result = await db.execute(select(Entreprise).where(Entreprise.id == entreprise_id))
        entreprise = result.scalar_one_or_none()
        if entreprise:
            intermediaires = await _load_intermediaires_for_fund(db, fonds.id, entreprise.pays)
            if intermediaires:
                intermediaire = next(
                    (i for i in intermediaires if i.est_recommande),
                    intermediaires[0],
                )

    # Vérifier les données disponibles sur la plateforme
    esg_result = await db.execute(
        select(ESGScore)
        .where(ESGScore.entreprise_id == entreprise_id)
        .order_by(ESGScore.created_at.desc())
        .limit(1)
    )
    has_esg = esg_result.scalar_one_or_none() is not None

    carbon_result = await db.execute(
        select(CarbonFootprint)
        .where(CarbonFootprint.entreprise_id == entreprise_id)
        .order_by(CarbonFootprint.created_at.desc())
        .limit(1)
    )
    has_carbon = carbon_result.scalar_one_or_none() is not None

    plan_result = await db.execute(
        select(ActionPlan)
        .where(ActionPlan.entreprise_id == entreprise_id)
        .order_by(ActionPlan.created_at.desc())
        .limit(1)
    )
    has_plan = plan_result.scalar_one_or_none() is not None

    # Construire la liste des documents requis avec statut
    documents_requis = []

    # Documents générables automatiquement
    _auto_docs = [
        {
            "nom": "Lettre de motivation",
            "statut": "a_generer",
            "skill": "generate_document",
            "params": {"document_type": "lettre_motivation"},
        },
        {
            "nom": "Plan d'affaires vert",
            "statut": "a_generer",
            "skill": "generate_document",
            "params": {"document_type": "plan_affaires"},
        },
        {
            "nom": "Budget prévisionnel",
            "statut": "a_generer",
            "skill": "generate_document",
            "params": {"document_type": "budget_previsionnel"},
        },
        {
            "nom": "Lettre d'engagement ESG",
            "statut": "a_generer",
            "skill": "generate_document",
            "params": {"document_type": "engagement_esg"},
        },
        {
            "nom": "Rapport ESG complet",
            "statut": "disponible" if has_esg else "prerequis_manquant",
            "skill": "assemble_pdf",
            "params": {"template_name": "esg_full"},
            "note": None if has_esg else "Score ESG requis. Utilisez calculate_esg_score d'abord.",
        },
        {
            "nom": "Bilan carbone",
            "statut": "disponible" if has_carbon else "prerequis_manquant",
            "skill": "assemble_pdf",
            "params": {"template_name": "carbon"},
            "note": None if has_carbon else "Empreinte carbone requise. Utilisez calculate_carbon d'abord.",
        },
        {
            "nom": "Plan d'action ESG",
            "statut": "disponible" if has_plan else "prerequis_manquant",
            "skill": "assemble_pdf",
            "params": {"template_name": "esg_full"},
            "note": None if has_plan else "Plan d'action requis. Utilisez manage_action_plan d'abord.",
        },
    ]
    documents_requis.extend(_auto_docs)

    # Documents à fournir par l'entreprise (non générables)
    _external_docs = [
        {"nom": "États financiers", "statut": "manquant", "note": "À fournir par l'entreprise"},
        {"nom": "Registre de commerce (RCCM)", "statut": "manquant", "note": "À fournir par l'entreprise"},
        {"nom": "Pièce d'identité du dirigeant", "statut": "manquant", "note": "À fournir par l'entreprise"},
    ]
    documents_requis.extend(_external_docs)

    # Ajouter les documents spécifiques de l'intermédiaire
    if intermediaire and intermediaire.documents_requis:
        noms_existants = {d["nom"].lower() for d in documents_requis}
        for doc in intermediaire.documents_requis:
            nom = doc if isinstance(doc, str) else doc.get("nom", str(doc))
            if nom.lower() not in noms_existants:
                documents_requis.append({
                    "nom": nom,
                    "statut": "manquant",
                    "note": f"Requis par {intermediaire.nom}",
                })

    dossier_complet_possible = all(
        d["statut"] != "prerequis_manquant"
        for d in documents_requis
        if d.get("skill")
    )

    return {
        "fonds": fonds.nom,
        "intermediaire": intermediaire.nom if intermediaire else None,
        "documents_requis": documents_requis,
        "dossier_complet_possible": dossier_complet_possible,
        "action_generer_tout": "generate_dossier_candidature",
    }


# ── Action : lancer_soumission ─────────────────────────────────────


async def _action_lancer_soumission(params: dict, context: dict) -> dict:
    db: AsyncSession = context["db"]
    entreprise_id = params.get("entreprise_id") or context.get("entreprise_id")

    if not entreprise_id:
        return {"error": "entreprise_id requis"}

    fonds = await _load_fonds(db, params)
    if not fonds:
        return {"error": "Fonds introuvable. Précisez fonds_id ou fonds_nom."}

    # Charger intermédiaire
    intermediaire = None
    intermediaire_id = params.get("intermediaire_id")
    if intermediaire_id:
        result = await db.execute(
            select(Intermediaire).where(Intermediaire.id == intermediaire_id)
        )
        intermediaire = result.scalar_one_or_none()

    # Si pas d'intermédiaire, prendre le recommandé
    if not intermediaire:
        result = await db.execute(select(Entreprise).where(Entreprise.id == entreprise_id))
        entreprise = result.scalar_one_or_none()
        if entreprise:
            intermediaires = await _load_intermediaires_for_fund(db, fonds.id, entreprise.pays if entreprise else None)
            if intermediaires:
                intermediaire = next(
                    (i for i in intermediaires if i.est_recommande),
                    intermediaires[0],
                )

    if not intermediaire:
        return {
            "error": "Aucun intermédiaire trouvé pour ce fonds. "
                     "Utilisez guide_candidature avec action='lister_intermediaires' pour voir les options.",
        }

    type_soumission = intermediaire.type_soumission or "inconnu"
    url = intermediaire.url_formulaire or intermediaire.site_web

    # Formulaire en ligne ou portail dédié
    if type_soumission in ("formulaire_en_ligne", "portail_dedie"):
        return {
            "type_soumission": type_soumission,
            "intermediaire": intermediaire.nom,
            "url": url,
            "extension_action": {
                "type": "OPEN_FUND_APPLICATION",
                "fonds_id": str(fonds.id),
                "url": url,
                "intermediaire_id": str(intermediaire.id),
            },
            "instructions": intermediaire.instructions_soumission
                or f"L'extension Chrome va vous guider sur le site de {intermediaire.nom}.",
        }

    # Soumission par email
    if type_soumission == "email":
        return {
            "type_soumission": "email",
            "intermediaire": intermediaire.nom,
            "email": intermediaire.email,
            "instructions": intermediaire.instructions_soumission
                or f"Envoyez votre dossier complet à {intermediaire.email}.",
            "documents_a_joindre": intermediaire.documents_requis or [],
        }

    # Soumission physique
    return {
        "type_soumission": type_soumission,
        "intermediaire": intermediaire.nom,
        "adresse": intermediaire.adresse,
        "telephone": intermediaire.telephone,
        "instructions": intermediaire.instructions_soumission
            or f"Déposez votre dossier physique auprès de {intermediaire.nom}.",
        "documents_a_joindre": intermediaire.documents_requis or [],
    }
