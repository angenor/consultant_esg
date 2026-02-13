"""
Seed des fonds_chunks : textes descriptifs détaillés + embeddings pour chaque fonds vert.
Permet la recherche RAG fine sur les critères d'éligibilité.
"""

import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fonds_vert import FondsVert, FondsChunk
from app.rag.chunker import chunk_text
from app.rag.embeddings import get_embeddings_batch

logger = logging.getLogger(__name__)

# Descriptions détaillées des fonds, indexées par nom
FONDS_DESCRIPTIONS: dict[str, list[dict[str, str]]] = {
    "Facilité Verte BOAD-PME": [
        {
            "type_info": "eligibilite",
            "contenu": (
                "La Facilité Verte BOAD-PME est un mécanisme de prêt à taux préférentiel "
                "de la Banque Ouest Africaine de Développement (BOAD) destiné aux PME de "
                "l'espace UEMOA. Montants entre 50 millions et 2 milliards de FCFA. "
                "Taux d'intérêt bonifié : 4-6% contre 8-12% pour un crédit classique. "
                "Durée de remboursement : 5 à 10 ans avec possibilité de différé de 2 ans."
            ),
        },
        {
            "type_info": "criteres",
            "contenu": (
                "Critères d'éligibilité Facilité Verte BOAD-PME : "
                "1. Score ESG minimum de 40/100 selon le référentiel BCEAO Finance Durable 2024. "
                "2. Entreprise enregistrée dans un pays UEMOA (Côte d'Ivoire, Sénégal, Mali, "
                "Burkina Faso, Togo, Bénin, Niger, Guinée-Bissau). "
                "3. Ancienneté minimum de 12 mois d'activité. "
                "4. Secteurs éligibles : agriculture durable, énergie renouvelable, recyclage "
                "et gestion des déchets, agroalimentaire, transport propre. "
                "5. Chiffre d'affaires minimum : 10 millions FCFA/an. "
                "6. Plan d'investissement vert documenté."
            ),
        },
        {
            "type_info": "processus",
            "contenu": (
                "Processus de candidature BOAD-PME : "
                "Phase 1 (2 semaines) : Pré-qualification en ligne, soumission du profil ESG. "
                "Phase 2 (4 semaines) : Due diligence environnementale et sociale. "
                "Phase 3 (2 semaines) : Comité de crédit et décision. "
                "Phase 4 (2 semaines) : Signature et décaissement. "
                "Délai total estimé : 8 à 12 semaines. "
                "Documents requis : états financiers des 2 derniers exercices, "
                "rapport ESG ou auto-évaluation, plan d'affaires vert, "
                "registre de commerce et statuts."
            ),
        },
    ],
    "Programme d'Adaptation Climatique BAD": [
        {
            "type_info": "eligibilite",
            "contenu": (
                "Le Programme d'Adaptation Climatique de la Banque Africaine de Développement "
                "(BAD) offre des subventions de 100 000 à 5 000 000 USD pour des projets "
                "d'adaptation au changement climatique en Afrique. Focus sur l'agriculture "
                "résiliente, la gestion de l'eau, les énergies renouvelables et les "
                "infrastructures climatiques. Subvention non remboursable couvrant jusqu'à "
                "70% du coût du projet."
            ),
        },
        {
            "type_info": "criteres",
            "contenu": (
                "Critères d'éligibilité Programme BAD Adaptation Climatique : "
                "1. Score ESG minimum de 30/100 selon les standards GCF. "
                "2. Projet démontrant un impact mesurable sur l'adaptation climatique. "
                "3. Pays éligibles : Côte d'Ivoire, Sénégal, Cameroun, Ghana, Kenya, "
                "Tanzanie, Éthiopie. "
                "4. Secteurs prioritaires : agriculture résiliente, gestion de l'eau, "
                "énergie renouvelable, infrastructure adaptée au climat. "
                "5. Composante genre obligatoire : au moins 30% des bénéficiaires doivent "
                "être des femmes. "
                "6. Plan de suivi-évaluation avec indicateurs climatiques."
            ),
        },
        {
            "type_info": "processus",
            "contenu": (
                "Processus de candidature BAD Adaptation : "
                "1. Note conceptuelle (5 pages max) soumise en ligne. "
                "2. Si présélectionné : proposition complète avec budget détaillé. "
                "3. Évaluation technique par un panel d'experts climat. "
                "4. Validation par le Comité de pilotage BAD. "
                "Appel à propositions : deux fois par an (mars et septembre). "
                "Durée des projets : 2 à 4 ans. "
                "Reporting : rapports semestriels avec indicateurs d'impact climatique."
            ),
        },
    ],
    "Green Climate Fund - PME Afrique de l'Ouest": [
        {
            "type_info": "eligibilite",
            "contenu": (
                "Le Green Climate Fund (GCF) finance des projets à fort impact climatique "
                "en Afrique de l'Ouest. Subventions de 500 000 à 10 000 000 USD. "
                "Le GCF est le plus grand fonds mondial dédié au climat, avec un portefeuille "
                "de plus de 12 milliards USD. Les PME accèdent via des entités accréditées "
                "nationales (banques de développement, ONG accréditées)."
            ),
        },
        {
            "type_info": "criteres",
            "contenu": (
                "Critères d'éligibilité Green Climate Fund : "
                "1. Score ESG minimum de 50/100 selon les standards GCF. "
                "2. Plan de réduction carbone chiffré et vérifié. "
                "3. Impact climatique démontrable : réduction d'au moins 100 tCO2e/an "
                "ou adaptation bénéficiant à plus de 1000 personnes. "
                "4. Pays éligibles : tous les pays d'Afrique de l'Ouest (CEDEAO + UEMOA). "
                "5. Secteurs : énergie renouvelable, transport durable, agriculture "
                "climato-intelligente, gestion des déchets. "
                "6. Co-financement requis : au moins 20% d'apport propre ou de co-financeur. "
                "7. Politique de sauvegarde environnementale et sociale conforme aux "
                "standards IFC/ESS."
            ),
        },
        {
            "type_info": "processus",
            "contenu": (
                "Processus de candidature GCF : "
                "1. Identification d'une Entité Nationale Accréditée (ENA) partenaire. "
                "2. Soumission d'une note conceptuelle via l'ENA. "
                "3. Développement de la proposition complète (funding proposal). "
                "4. Revue technique par le Secrétariat GCF. "
                "5. Validation par le Board du GCF (réunion trimestrielle). "
                "Délai total : 6 à 18 mois selon la complexité. "
                "Reporting : rapports annuels de performance + audit indépendant."
            ),
        },
    ],
    "Ligne de Crédit Vert IFC": [
        {
            "type_info": "eligibilite",
            "contenu": (
                "La Ligne de Crédit Vert de l'IFC (International Finance Corporation, "
                "groupe Banque Mondiale) propose des prêts de 200 000 à 3 000 000 USD "
                "via des banques locales partenaires. Taux d'intérêt compétitifs avec "
                "une composante d'assistance technique gratuite. Focus sur la transition "
                "énergétique, l'efficacité des ressources et les bâtiments verts."
            ),
        },
        {
            "type_info": "criteres",
            "contenu": (
                "Critères d'éligibilité Ligne de Crédit Vert IFC : "
                "1. Score ESG minimum de 45/100 selon les IFC Performance Standards. "
                "2. Conformité aux 8 standards de performance IFC obligatoire. "
                "3. Pays éligibles : Côte d'Ivoire, Sénégal, Cameroun, Ghana, Kenya, Nigeria. "
                "4. Secteurs : énergie et efficacité énergétique, industrie manufacturière "
                "propre, bâtiments verts, transport durable. "
                "5. Projet d'investissement vert identifié (équipements, technologies). "
                "6. États financiers audités des 3 derniers exercices. "
                "7. Pas de liste d'exclusion IFC (tabac, armement, jeux)."
            ),
        },
        {
            "type_info": "processus",
            "contenu": (
                "Processus de candidature IFC Green Credit : "
                "1. Contacter une banque partenaire IFC dans votre pays. "
                "2. Soumettre le dossier de crédit standard + complément vert. "
                "3. Évaluation E&S par la banque (critères IFC simplifiés). "
                "4. Accord de crédit avec composante verte. "
                "5. Assistance technique IFC pour le projet vert (gratuite). "
                "Délai : 4 à 8 semaines via la banque partenaire. "
                "Banques partenaires en CI : Société Générale CI, BICICI, Ecobank."
            ),
        },
    ],
    "Fonds de Garantie Verte FAGACE": [
        {
            "type_info": "eligibilite",
            "contenu": (
                "Le Fonds de Garantie Verte FAGACE offre des garanties partielles de crédit "
                "de 10 millions à 500 millions FCFA pour les PME vertes de la zone franc. "
                "La garantie couvre 50 à 70% du montant du prêt, facilitant l'accès au "
                "crédit bancaire classique. Aucun coût direct pour l'entreprise — la "
                "commission de garantie est prise en charge par le FAGACE."
            ),
        },
        {
            "type_info": "criteres",
            "contenu": (
                "Critères d'éligibilité Garantie Verte FAGACE : "
                "1. Score ESG minimum de 35/100 selon le référentiel BCEAO. "
                "2. Entreprise dans la zone franc (UEMOA ou CEMAC). "
                "3. Secteurs : agriculture durable, énergie renouvelable, recyclage, "
                "gestion de l'eau. "
                "4. Engagement ESG démontré : politique environnementale documentée "
                "ou certification en cours. "
                "5. Pas d'incidents de paiement majeurs sur les 12 derniers mois. "
                "6. Capacité de remboursement démontrée (ratio dette/fonds propres < 3)."
            ),
        },
        {
            "type_info": "processus",
            "contenu": (
                "Processus de candidature FAGACE Garantie Verte : "
                "1. L'entreprise sollicite un crédit auprès de sa banque habituelle. "
                "2. La banque soumet la demande de garantie au FAGACE. "
                "3. Évaluation du profil ESG et du projet par le FAGACE (2-3 semaines). "
                "4. Émission de la lettre de garantie. "
                "5. La banque accorde le crédit avec la garantie FAGACE. "
                "Avantage clé : réduit le risque pour la banque → facilite l'obtention "
                "du crédit et peut réduire le taux d'intérêt de 1 à 2 points."
            ),
        },
    ],
}


async def seed_fonds_chunks(db: AsyncSession) -> int:
    """
    Peuple la table fonds_chunks avec les descriptions détaillées des fonds.
    Génère les embeddings via Voyage AI.
    """
    # Vérifier si déjà peuplé
    result = await db.execute(select(func.count(FondsChunk.id)))
    existing_count = result.scalar()
    if existing_count and existing_count > 0:
        logger.info("fonds_chunks déjà peuplé (%d chunks), skip.", existing_count)
        return 0

    # Charger les fonds depuis la BDD
    result = await db.execute(select(FondsVert))
    fonds_list = result.scalars().all()
    fonds_by_nom = {f.nom: f for f in fonds_list}

    # Préparer tous les chunks
    all_chunks: list[tuple[FondsVert, str, str]] = []  # (fonds, contenu, type_info)

    for nom, descriptions in FONDS_DESCRIPTIONS.items():
        fonds = fonds_by_nom.get(nom)
        if not fonds:
            logger.warning("Fonds '%s' non trouvé en BDD, skip.", nom)
            continue

        for desc in descriptions:
            text_content = desc["contenu"]
            type_info = desc["type_info"]

            # Découper si le texte est long
            chunks = chunk_text(text_content, chunk_size=600, overlap=100)
            if chunks:
                for chunk in chunks:
                    all_chunks.append((fonds, chunk["text"], type_info))
            else:
                all_chunks.append((fonds, text_content, type_info))

    if not all_chunks:
        logger.warning("Aucun chunk à insérer.")
        return 0

    # Générer les embeddings en batch
    texts = [c[1] for c in all_chunks]
    logger.info("Génération des embeddings pour %d chunks de fonds...", len(texts))
    embeddings = await get_embeddings_batch(texts)

    # Insérer en BDD
    count = 0
    for (fonds, contenu, type_info), embedding in zip(all_chunks, embeddings):
        chunk = FondsChunk(
            fonds_id=fonds.id,
            contenu=contenu,
            embedding=embedding,
            type_info=type_info,
        )
        db.add(chunk)
        count += 1

    await db.commit()
    logger.info("%d chunks de fonds insérés avec embeddings.", count)
    return count
