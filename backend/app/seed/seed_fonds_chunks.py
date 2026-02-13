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
    "Fonds Climat BCEAO": [
        {
            "type_info": "eligibilite",
            "contenu": (
                "Le Fonds Climat BCEAO est une ligne de refinancement à taux bonifié mise en place "
                "par la Banque Centrale des États de l'Afrique de l'Ouest. Montants entre 25 millions "
                "et 1 milliard de FCFA. Taux préférentiel de 3,5% à 5,5% selon la notation ESG de "
                "l'entreprise (contre 8-14% pour un crédit classique). Durée de 3 à 8 ans avec "
                "possibilité de différé de 18 mois. La BCEAO refinance les banques commerciales "
                "qui accordent des prêts verts conformes à sa directive sur la finance durable."
            ),
        },
        {
            "type_info": "criteres",
            "contenu": (
                "Critères d'éligibilité Fonds Climat BCEAO : "
                "1. Score ESG minimum de 35/100 selon le référentiel BCEAO Finance Durable 2024. "
                "2. Entreprise enregistrée dans un pays UEMOA avec au moins 6 mois d'activité. "
                "3. Tous les secteurs sont éligibles (agriculture, énergie, recyclage, agroalimentaire, "
                "BTP vert, transport propre, services). "
                "4. Projet d'investissement vert identifié et chiffré. "
                "5. Chiffre d'affaires minimum : 5 millions FCFA/an. "
                "6. Compte bancaire actif dans une banque partenaire de l'UEMOA. "
                "7. Pas d'incidents de paiement non régularisés à la Centrale des Risques."
            ),
        },
        {
            "type_info": "processus",
            "contenu": (
                "Processus de candidature Fonds Climat BCEAO : "
                "1. L'entreprise contacte sa banque commerciale habituelle. "
                "2. La banque évalue le dossier de crédit classique + profil ESG. "
                "3. La banque soumet la demande de refinancement à la BCEAO. "
                "4. La BCEAO valide l'éligibilité verte du projet (2-3 semaines). "
                "5. La banque accorde le prêt au taux bonifié BCEAO. "
                "Délai total estimé : 3 à 6 semaines. "
                "Avantage clé : le taux de refinancement BCEAO est inférieur au taux directeur, "
                "permettant aux banques d'offrir des conditions très compétitives."
            ),
        },
    ],
    "Programme SUNREF Afrique de l'Ouest": [
        {
            "type_info": "eligibilite",
            "contenu": (
                "Le Programme SUNREF (Sustainable Use of Natural Resources and Energy Finance) "
                "de l'Agence Française de Développement (AFD) offre des prêts verts via des "
                "banques locales partenaires. Montants entre 10 millions et 750 millions FCFA. "
                "Le programme inclut une prime d'investissement de 10 à 15% remboursée après "
                "réalisation du projet, ainsi qu'un audit énergétique gratuit réalisé par des "
                "experts certifiés. Focus sur l'efficacité énergétique et les énergies renouvelables."
            ),
        },
        {
            "type_info": "criteres",
            "contenu": (
                "Critères d'éligibilité Programme SUNREF : "
                "1. Score ESG minimum de 30/100 selon le référentiel BCEAO. "
                "2. Pays éligibles : Côte d'Ivoire, Sénégal, Cameroun, Burkina Faso. "
                "3. Secteurs prioritaires : efficacité énergétique dans l'industrie et le bâtiment, "
                "énergie solaire et biomasse, froid commercial et climatisation performante, "
                "agroalimentaire (séchage solaire, froid solaire). "
                "4. Investissement minimum : 10 millions FCFA. "
                "5. Réduction d'énergie ou d'émissions démontrable par l'audit. "
                "6. Entreprise formelle avec au moins 2 ans d'existence."
            ),
        },
        {
            "type_info": "processus",
            "contenu": (
                "Processus de candidature SUNREF : "
                "1. Contact avec une banque partenaire SUNREF (Société Générale, Ecobank, BICICI). "
                "2. Audit énergétique gratuit réalisé par un expert SUNREF agréé. "
                "3. L'expert identifie les investissements éligibles et le potentiel d'économies. "
                "4. La banque monte le dossier de crédit avec le rapport d'audit. "
                "5. Accord de prêt aux conditions SUNREF. "
                "6. Après réalisation : vérification et versement de la prime (10-15%). "
                "Délai : 4 à 10 semaines selon la complexité de l'audit. "
                "La prime d'investissement peut couvrir une partie significative de l'apport personnel."
            ),
        },
    ],
    "Fonds Paysan Résilient FIDA": [
        {
            "type_info": "eligibilite",
            "contenu": (
                "Le Fonds Paysan Résilient du FIDA (Fonds International de Développement Agricole) "
                "offre des subventions de 50 000 à 2 000 000 USD pour renforcer la résilience "
                "climatique des petits producteurs agricoles en Afrique de l'Ouest. Subvention "
                "non remboursable couvrant jusqu'à 80% du coût du projet. Priorité aux coopératives "
                "agricoles, aux femmes entrepreneures et aux jeunes agriculteurs. "
                "Durée des projets : 2 à 5 ans."
            ),
        },
        {
            "type_info": "criteres",
            "contenu": (
                "Critères d'éligibilité Fonds Paysan Résilient FIDA : "
                "1. Score ESG minimum de 25/100 selon les standards GCF. "
                "2. Pays UEMOA éligibles : tous les 8 pays membres. "
                "3. Secteurs : agriculture résiliente, agroalimentaire, gestion de l'eau agricole. "
                "4. Au moins 40% des bénéficiaires doivent être des femmes. "
                "5. Projet démontrant un impact sur l'adaptation climatique des exploitations. "
                "6. Statut juridique : coopérative, GIE, PME agricole, ou organisation paysanne. "
                "7. Apport propre minimum de 20% (en nature ou numéraire). "
                "8. Engagement de formation des bénéficiaires en pratiques agricoles durables."
            ),
        },
        {
            "type_info": "processus",
            "contenu": (
                "Processus de candidature FIDA Paysan Résilient : "
                "1. Appel à propositions publié sur le site FIDA (2 fenêtres par an : avril et octobre). "
                "2. Soumission d'une note conceptuelle (3-5 pages) via le portail en ligne. "
                "3. Présélection et invitation à soumettre une proposition complète. "
                "4. Atelier de formulation avec l'équipe FIDA pays. "
                "5. Évaluation technique et approbation par le comité régional. "
                "6. Signature de la convention de subvention. "
                "Délai total : 3 à 6 mois. "
                "Suivi : rapports trimestriels + mission de supervision FIDA annuelle."
            ),
        },
    ],
    "Ligne Verte BEI-Proparco": [
        {
            "type_info": "eligibilite",
            "contenu": (
                "La Ligne Verte BEI-Proparco est un co-financement de la Banque Européenne "
                "d'Investissement et de Proparco (filiale de l'AFD) pour les PME en croissance "
                "engagées dans la transition climatique. Prêts de 500 000 à 5 000 000 EUR "
                "à moyen-long terme (5-12 ans). Possibilité de conversion en devises locales "
                "(FCFA) pour limiter le risque de change. Composante d'assistance technique "
                "gratuite pour l'accompagnement ESG et la structuration de projet."
            ),
        },
        {
            "type_info": "criteres",
            "contenu": (
                "Critères d'éligibilité Ligne Verte BEI-Proparco : "
                "1. Score ESG minimum de 40/100 selon les IFC Performance Standards. "
                "2. Pays éligibles : Côte d'Ivoire, Sénégal, Cameroun, Ghana, Kenya, Tanzanie. "
                "3. Secteurs : énergie renouvelable, transport durable, industrie propre, "
                "bâtiments verts et efficacité énergétique, services à valeur ajoutée. "
                "4. Chiffre d'affaires annuel entre 500 000 et 50 000 000 EUR. "
                "5. Effectif : 10 à 500 employés (définition PME européenne). "
                "6. Projet d'investissement vert identifié avec business plan. "
                "7. États financiers audités des 2 derniers exercices. "
                "8. Engagement de reporting ESG annuel pendant la durée du prêt."
            ),
        },
        {
            "type_info": "processus",
            "contenu": (
                "Processus de candidature BEI-Proparco : "
                "1. Expression d'intérêt via le portail BEI ou contact Proparco local. "
                "2. Diagnostic ESG préliminaire (gratuit, réalisé par un consultant BEI). "
                "3. Soumission du dossier complet : business plan + plan d'investissement vert. "
                "4. Due diligence financière et environnementale (4-6 semaines). "
                "5. Comité d'investissement BEI/Proparco. "
                "6. Négociation des termes et signature. "
                "Délai : 2 à 4 mois selon la taille du projet. "
                "L'assistance technique inclut : conseil en management ESG, formation équipe, "
                "mise en place d'un système de reporting."
            ),
        },
    ],
    "Programme SREP - Énergie Renouvelable": [
        {
            "type_info": "eligibilite",
            "contenu": (
                "Le Programme SREP (Scaling Up Renewable Energy Program) des Climate Investment "
                "Funds (CIF) finance la mise à échelle des énergies renouvelables dans les pays "
                "à faible revenu. Subventions et prêts concessionnels de 200 000 à 8 000 000 USD. "
                "Focus exclusif sur les projets d'énergie renouvelable : solaire photovoltaïque, "
                "solaire thermique, éolien, biomasse, mini-hydroélectricité. "
                "Le SREP combine subventions (jusqu'à 50%) et prêts à taux très bas (1-3%)."
            ),
        },
        {
            "type_info": "criteres",
            "contenu": (
                "Critères d'éligibilité Programme SREP : "
                "1. Score ESG minimum de 35/100 selon les standards GCF. "
                "2. Pays éligibles SREP en Afrique : Mali, Burkina Faso, Niger, Éthiopie, "
                "Kenya, Tanzanie, Ghana (pays pilotes SREP). "
                "3. Projet 100% énergie renouvelable (solaire, éolien, biomasse, mini-hydro). "
                "4. Impact démontrable : nombre de personnes/entreprises ayant accès à l'énergie. "
                "5. Viabilité financière du projet démontrée sur 10 ans minimum. "
                "6. Partenariat avec une entité locale (gouvernement, ONG, coopérative). "
                "7. Plan de maintenance et de durabilité post-projet."
            ),
        },
        {
            "type_info": "processus",
            "contenu": (
                "Processus de candidature SREP : "
                "1. Le projet doit s'inscrire dans le Plan d'Investissement SREP du pays. "
                "2. Soumission via une Banque Multilatérale de Développement partenaire "
                "(Banque Mondiale, BAD, BID, BERD). "
                "3. Évaluation technique par les experts CIF (6-8 semaines). "
                "4. Validation par le sous-comité SREP (réunion semestrielle). "
                "5. Approbation finale par la BMD partenaire. "
                "Délai total : 6 à 12 mois. "
                "Reporting : rapports semestriels de performance incluant la production "
                "d'énergie, les réductions d'émissions et le nombre de bénéficiaires."
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
