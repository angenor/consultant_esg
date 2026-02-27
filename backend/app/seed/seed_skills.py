from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill

BUILTIN_SKILLS = [
    {
        "nom": "analyze_document",
        "description": (
            "Analyse un document uploadé par l'entreprise. Extrait le texte (OCR si image/scan), "
            "découpe en chunks avec embedding, et retourne les données ESG pertinentes extraites."
        ),
        "category": "document",
        "handler_key": "builtin.analyze_document",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "ID du document à analyser"},
                "analysis_type": {
                    "type": "string",
                    "default": "esg_compliance",
                    "description": "Type d'analyse : esg_compliance, carbon_data, financial_data",
                },
            },
            "required": ["document_id"],
        },
    },
    {
        "nom": "calculate_esg_score",
        "description": (
            "Calcule le score ESG d'une entreprise selon un ou plusieurs référentiels. "
            "La grille de notation vient de la BDD. Retourne scores E, S, G et global."
        ),
        "category": "esg",
        "handler_key": "builtin.calculate_esg_score",
        "input_schema": {
            "type": "object",
            "properties": {
                "entreprise_id": {"type": "string", "description": "ID de l'entreprise"},
                "data": {
                    "type": "object",
                    "description": "Réponses aux critères, clé = critere_id, valeur = réponse",
                },
                "referentiel_codes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Codes des référentiels à utiliser (si vide, utilise le défaut)",
                },
            },
            "required": ["entreprise_id", "data"],
        },
    },
    {
        "nom": "list_referentiels",
        "description": (
            "Liste les référentiels ESG disponibles dans le système. "
            "Permet au LLM de savoir quels référentiels existent et recommander le bon selon le fonds visé."
        ),
        "category": "esg",
        "handler_key": "builtin.list_referentiels",
        "input_schema": {
            "type": "object",
            "properties": {
                "region": {"type": "string", "description": "Filtrer par région (UEMOA, International, Europe)"},
                "fonds_id": {"type": "string", "description": "ID d'un fonds pour trouver son référentiel associé"},
                "include_criteres": {
                    "type": "boolean",
                    "default": False,
                    "description": (
                        "Si true, inclut les critères détaillés de chaque pilier "
                        "(id, label, type, poids, question_collecte, options/unité). "
                        "Utile pour poser les bonnes questions à l'utilisateur."
                    ),
                },
            },
        },
    },
    {
        "nom": "search_green_funds",
        "description": (
            "Recherche les fonds verts compatibles avec le profil de l'entreprise. "
            "Filtrage SQL rapide puis RAG sur les fonds filtrés pour une précision fine."
        ),
        "category": "finance",
        "handler_key": "builtin.search_green_funds",
        "input_schema": {
            "type": "object",
            "properties": {
                "secteur": {"type": "string", "description": "Secteur d'activité"},
                "pays": {"type": "string", "default": "CIV", "description": "Code pays ISO 3"},
                "montant_recherche": {"type": "number", "description": "Montant recherché"},
                "score_esg": {"type": "number", "description": "Score ESG actuel de l'entreprise"},
            },
        },
    },
    {
        "nom": "calculate_carbon",
        "description": (
            "Calcule l'empreinte carbone annuelle d'une entreprise à partir des données collectées "
            "par conversation ou documents. Utilise les facteurs d'émission par pays et par source."
        ),
        "category": "carbon",
        "handler_key": "builtin.calculate_carbon",
        "input_schema": {
            "type": "object",
            "properties": {
                "entreprise_id": {"type": "string", "description": "ID de l'entreprise"},
                "data": {
                    "type": "object",
                    "description": "Données de consommation",
                    "properties": {
                        "electricite_kwh": {"type": "number"},
                        "generateur_litres": {"type": "number"},
                        "vehicules_km": {"type": "number"},
                        "type_carburant": {"type": "string", "default": "diesel"},
                        "dechets_tonnes": {"type": "number"},
                        "achats_montant": {"type": "number"},
                    },
                },
            },
            "required": ["entreprise_id", "data"],
        },
    },
    {
        "nom": "generate_reduction_plan",
        "description": (
            "Génère un plan de RÉDUCTION CARBONE priorisé à partir de l'empreinte carbone calculée. "
            "À UTILISER UNIQUEMENT pour réduire les émissions de CO2/GES. "
            "Prérequis : avoir déjà calculé l'empreinte carbone avec calculate_carbon. "
            "Identifie les sources les plus émettrices et propose des actions classées en "
            "quick_win, moyen_terme, long_terme avec coûts et économies estimées en XOF. "
            "NE PAS utiliser pour améliorer le score ESG global — utiliser manage_action_plan à la place."
        ),
        "category": "carbon",
        "handler_key": "builtin.generate_reduction_plan",
        "input_schema": {
            "type": "object",
            "properties": {
                "entreprise_id": {"type": "string", "description": "ID de l'entreprise"},
            },
            "required": ["entreprise_id"],
        },
    },
    {
        "nom": "simulate_funding",
        "description": (
            "Simule l'éligibilité et le montant potentiel pour un fonds vert donné. "
            "Charge le fonds et son référentiel, vérifie les critères d'éligibilité, "
            "et calcule un montant estimé avec ROI vert."
        ),
        "category": "finance",
        "handler_key": "builtin.simulate_funding",
        "input_schema": {
            "type": "object",
            "properties": {
                "entreprise_id": {"type": "string", "description": "ID de l'entreprise"},
                "fonds_id": {"type": "string", "description": "ID du fonds vert"},
                "montant_demande": {"type": "number", "description": "Montant demandé (optionnel)"},
            },
            "required": ["entreprise_id", "fonds_id"],
        },
    },
    {
        "nom": "calculate_credit_score",
        "description": (
            "Calcule le score de crédit vert alternatif. Combine données financières et engagement ESG "
            "pour un score inclusif. Trois composantes : solvabilité, impact vert, score combiné."
        ),
        "category": "finance",
        "handler_key": "builtin.calculate_credit_score",
        "input_schema": {
            "type": "object",
            "properties": {
                "entreprise_id": {"type": "string", "description": "ID de l'entreprise"},
                "donnees_financieres": {
                    "type": "object",
                    "description": "Données financières déclaratives",
                    "properties": {
                        "regularite": {"type": "number"},
                        "volume": {"type": "number"},
                        "anciennete": {"type": "number"},
                    },
                },
                "donnees_declaratives": {
                    "type": "object",
                    "description": "Pratiques vertes et programmes",
                    "properties": {
                        "pratiques_vertes": {"type": "array", "items": {"type": "string"}},
                        "programmes": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "required": ["entreprise_id"],
        },
    },
    {
        "nom": "get_sector_benchmark",
        "description": (
            "Récupère les moyennes sectorielles pour comparer les performances de l'entreprise. "
            "Retourne moyennes E/S/G, score global moyen, empreinte carbone moyenne du secteur."
        ),
        "category": "utils",
        "handler_key": "builtin.get_sector_benchmark",
        "input_schema": {
            "type": "object",
            "properties": {
                "secteur": {"type": "string", "description": "Secteur d'activité"},
                "pays": {"type": "string", "description": "Code pays"},
                "referentiel_code": {"type": "string", "description": "Code du référentiel"},
            },
            "required": ["secteur"],
        },
    },
    {
        "nom": "manage_action_plan",
        "description": (
            "Crée ou met à jour un plan d'action d'AMÉLIORATION ESG pour l'entreprise. "
            "Fonctionne avec TOUS les référentiels disponibles : BCEAO Finance Durable, "
            "Green Climate Fund (GCF), IFC Performance Standards, etc. "
            "Utilise le paramètre referentiel_code pour cibler un référentiel précis "
            "(ex: 'gcf_standards', 'bceao_fd_2024', 'ifc_standards'). "
            "Analyse les lacunes du dernier score ESG et génère des actions priorisées. "
            "Actions supportées : create (nouveau plan ESG), add_item (ajouter une action), "
            "update_status (changer le statut d'une action). "
            "NE PAS utiliser pour la réduction carbone — utiliser generate_reduction_plan à la place."
        ),
        "category": "utils",
        "handler_key": "builtin.manage_action_plan",
        "input_schema": {
            "type": "object",
            "properties": {
                "entreprise_id": {"type": "string", "description": "ID de l'entreprise"},
                "action": {
                    "type": "string",
                    "enum": ["create", "add_item", "update_status"],
                    "description": "Action à effectuer",
                },
                "referentiel_code": {
                    "type": "string",
                    "description": (
                        "Code du référentiel ESG ciblé (ex: 'gcf_standards', 'bceao_fd_2024', 'ifc_standards'). "
                        "Si omis, utilise le dernier score ESG disponible."
                    ),
                },
                "horizon": {
                    "type": "string",
                    "enum": ["6_mois", "12_mois", "24_mois"],
                    "description": "Horizon temporel du plan (défaut: 12_mois)",
                },
                "score_cible": {
                    "type": "number",
                    "description": "Score ESG cible à atteindre (0-100). Si omis, score actuel + 15.",
                },
                "plan_id": {"type": "string", "description": "ID du plan (pour add_item, update_status)"},
                "titre": {"type": "string", "description": "Titre du plan ou de l'action"},
                "item_id": {"type": "string", "description": "ID de l'action item (pour update_status)"},
                "statut": {"type": "string", "description": "Nouveau statut (a_faire, en_cours, fait)"},
            },
            "required": ["entreprise_id", "action"],
        },
    },
    {
        "nom": "generate_report_section",
        "description": (
            "Génère une section individuelle de rapport (résumé, analyse E/S/G, etc.). "
            "N'utilise ce skill que pour générer UNE section isolée. "
            "Pour un rapport complet, utilise assemble_pdf à la place."
        ),
        "category": "reporting",
        "handler_key": "builtin.generate_report_section",
        "input_schema": {
            "type": "object",
            "properties": {
                "entreprise_id": {"type": "string", "description": "ID de l'entreprise"},
                "template_name": {
                    "type": "string",
                    "enum": ["esg_full", "carbon", "funding_application"],
                    "description": "Nom du template de rapport",
                },
                "section_id": {"type": "string", "description": "ID de la section à générer"},
            },
            "required": ["entreprise_id", "template_name", "section_id"],
        },
    },
    {
        "nom": "assemble_pdf",
        "description": (
            "Génère un rapport PDF professionnel complet pour l'entreprise. "
            "À UTILISER quand l'utilisateur demande un rapport, un PDF, un document ESG, "
            "un bilan carbone PDF, ou un dossier de candidature pour un fonds vert. "
            "Trois types de rapports disponibles : "
            "'esg_full' (rapport ESG complet avec scores, analyses, radar, historique), "
            "'carbon' (rapport empreinte carbone avec répartition, évolution, plan de réduction), "
            "'funding_application' (dossier de candidature pour un fonds vert avec éligibilité, budget). "
            "Le rapport est généré automatiquement avec graphiques, analyses LLM et mise en page professionnelle. "
            "Retourne un lien de téléchargement du PDF."
        ),
        "category": "reporting",
        "handler_key": "builtin.assemble_pdf",
        "input_schema": {
            "type": "object",
            "properties": {
                "entreprise_id": {"type": "string", "description": "ID de l'entreprise"},
                "template_name": {
                    "type": "string",
                    "enum": ["esg_full", "carbon", "funding_application"],
                    "description": (
                        "Type de rapport à générer : "
                        "'esg_full' pour un rapport ESG complet, "
                        "'carbon' pour un rapport empreinte carbone, "
                        "'funding_application' pour un dossier de candidature fonds vert"
                    ),
                    "default": "esg_full",
                },
            },
            "required": ["entreprise_id"],
        },
    },
    {
        "nom": "search_knowledge_base",
        "description": (
            "Recherche dans la base de connaissances (documents et fonds) par similarité vectorielle. "
            "Retourne les passages les plus pertinents pour la requête."
        ),
        "category": "knowledge",
        "handler_key": "builtin.search_knowledge_base",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Requête de recherche"},
                "entreprise_id": {"type": "string", "description": "ID de l'entreprise (pour filtrer ses documents)"},
                "source": {
                    "type": "string",
                    "enum": ["documents", "fonds", "all"],
                    "default": "all",
                    "description": "Source de recherche",
                },
                "top_k": {"type": "integer", "default": 5, "description": "Nombre de résultats"},
            },
            "required": ["query"],
        },
    },
    {
        "nom": "get_action_plans",
        "description": (
            "Récupère les plans d'action EXISTANTS de l'entreprise (ESG et/ou carbone). "
            "Retourne le dernier plan de chaque type avec ses actions, leur statut et la progression. "
            "À UTILISER quand l'utilisateur demande où en est son plan d'action, "
            "quelles actions sont en cours, ou veut consulter un plan existant. "
            "Paramètre type_plan : 'esg' pour le plan ESG, 'carbone' pour le plan de réduction carbone, "
            "ou ne pas spécifier pour récupérer tous les plans."
        ),
        "category": "utils",
        "handler_key": "builtin.get_action_plans",
        "input_schema": {
            "type": "object",
            "properties": {
                "entreprise_id": {"type": "string", "description": "ID de l'entreprise"},
                "type_plan": {
                    "type": "string",
                    "enum": ["esg", "carbone"],
                    "description": "Type de plan à récupérer. Omettre pour récupérer tous les plans.",
                },
            },
            "required": ["entreprise_id"],
        },
    },
    {
        "nom": "get_company_profile",
        "description": (
            "Récupère le profil complet d'une entreprise : informations générales, "
            "dernier score ESG, empreinte carbone, plans d'action en cours."
        ),
        "category": "profile",
        "handler_key": "builtin.get_company_profile",
        "input_schema": {
            "type": "object",
            "properties": {
                "entreprise_id": {"type": "string", "description": "ID de l'entreprise"},
            },
            "required": ["entreprise_id"],
        },
    },
    {
        "nom": "update_company_profile",
        "description": (
            "Met à jour le profil d'une entreprise avec de nouvelles informations "
            "collectées lors de la conversation. Utilise ce skill dès que l'utilisateur "
            "mentionne des informations sur son entreprise."
        ),
        "category": "profile",
        "handler_key": "builtin.update_company_profile",
        "input_schema": {
            "type": "object",
            "properties": {
                "entreprise_id": {"type": "string", "description": "ID de l'entreprise"},
                "updates": {
                    "type": "object",
                    "description": (
                        "Clés à mettre à jour dans le profil. Clés possibles : "
                        "pratiques_environnementales (list), certifications (list), "
                        "objectifs_declares (list), risques_identifies (list), "
                        "pratiques_sociales (list), gouvernance (dict), "
                        "energie (dict), dechets (dict), eau (dict), "
                        "chaine_approvisionnement (dict), effectifs_details (dict), "
                        "et toute autre clé pertinente."
                    ),
                },
            },
            "required": ["entreprise_id", "updates"],
        },
    },
    {
        "nom": "generate_document",
        "description": (
            "Génère un document Word (.docx) professionnel pour l'entreprise. "
            "À UTILISER quand l'utilisateur demande un document Word, une lettre, "
            "une note de présentation, un plan d'affaires, ou un budget prévisionnel. "
            "Types disponibles : "
            "'lettre_motivation' (lettre de candidature pour un fonds vert), "
            "'note_presentation' (profil entreprise complet pour un bailleur), "
            "'plan_affaires' (business plan vert avec stratégie ESG), "
            "'engagement_esg' (lettre d'engagement ESG formelle), "
            "'budget_previsionnel' (budget détaillé pour un projet vert). "
            "Le paramètre fonds_id permet de cibler un fonds vert spécifique "
            "(utile pour lettre_motivation et budget_previsionnel). "
            "Retourne un lien de téléchargement du fichier Word."
        ),
        "category": "reporting",
        "handler_key": "builtin.generate_document",
        "input_schema": {
            "type": "object",
            "properties": {
                "entreprise_id": {"type": "string", "description": "ID de l'entreprise"},
                "document_type": {
                    "type": "string",
                    "enum": [
                        "lettre_motivation",
                        "note_presentation",
                        "plan_affaires",
                        "engagement_esg",
                        "budget_previsionnel",
                    ],
                    "description": (
                        "Type de document à générer : "
                        "'lettre_motivation' pour une candidature fonds vert, "
                        "'note_presentation' pour un profil entreprise, "
                        "'plan_affaires' pour un business plan vert, "
                        "'engagement_esg' pour une lettre d'engagement, "
                        "'budget_previsionnel' pour un budget de projet"
                    ),
                },
                "fonds_id": {
                    "type": "string",
                    "description": "ID du fonds vert ciblé (optionnel, pour personnaliser le document)",
                },
                "instructions": {
                    "type": "string",
                    "description": "Instructions spécifiques de l'utilisateur pour personnaliser le contenu",
                },
            },
            "required": ["entreprise_id", "document_type"],
        },
    },
    {
        "nom": "get_intermediaires",
        "description": (
            "Liste les intermédiaires disponibles pour un fonds vert donné, "
            "filtrés par pays et type. Retourne les contacts, URLs de formulaires, "
            "et instructions de soumission pour chaque intermédiaire."
        ),
        "category": "finance",
        "handler_key": "builtin.get_intermediaires",
        "input_schema": {
            "type": "object",
            "properties": {
                "fonds_id": {"type": "string", "description": "ID du fonds vert"},
                "pays": {"type": "string", "description": "Filtrer par pays (nom ou code ISO)"},
                "type": {
                    "type": "string",
                    "enum": ["banque_partenaire", "entite_accreditee", "agence_nationale", "bmd"],
                    "description": "Filtrer par type d'intermédiaire",
                },
            },
            "required": ["fonds_id"],
        },
    },
    {
        "nom": "guide_candidature",
        "description": (
            "Guide l'utilisateur dans le processus de candidature à un fonds vert. "
            "Analyse le mode d'accès, identifie les intermédiaires adaptés au pays de l'entreprise, "
            "et propose les prochaines étapes (préparation de dossier, formulaire en ligne, etc.). "
            "4 actions possibles : 'analyser' (défaut, analyse complète), "
            "'lister_intermediaires' (liste les intermédiaires du fonds), "
            "'preparer_dossier' (identifie les documents à préparer), "
            "'lancer_soumission' (URL ou instructions pour soumettre)."
        ),
        "category": "finance",
        "handler_key": "builtin.guide_candidature",
        "input_schema": {
            "type": "object",
            "properties": {
                "entreprise_id": {"type": "string", "description": "ID de l'entreprise"},
                "fonds_id": {"type": "string", "description": "ID du fonds vert ciblé"},
                "fonds_nom": {
                    "type": "string",
                    "description": "Nom du fonds (si ID inconnu, recherche par nom)",
                },
                "action": {
                    "type": "string",
                    "enum": ["analyser", "lister_intermediaires", "preparer_dossier", "lancer_soumission"],
                    "default": "analyser",
                    "description": "Action à effectuer",
                },
                "intermediaire_id": {
                    "type": "string",
                    "description": "ID de l'intermédiaire choisi (pour preparer_dossier et lancer_soumission)",
                },
            },
            "required": ["entreprise_id"],
        },
    },
    {
        "nom": "generate_dossier_candidature",
        "description": (
            "Génère un dossier complet de candidature pour un fonds vert. "
            "Produit les documents nécessaires : page de garde, checklist, lettre de motivation, "
            "fiche projet vert, plan d'affaires, budget prévisionnel, note d'impact ESG, "
            "engagement ESG, rapport ESG complet, bilan carbone — en Word et/ou PDF, "
            "adaptés au fonds et à l'intermédiaire avec des prompts spécifiques. "
            "Supporte deux modes : 'complet' (pré-rempli avec les données) et 'template_vierge' "
            "(structure avec placeholders [À COMPLÉTER]). "
            "Crée un fichier ZIP regroupant tous les documents avec nomenclature ordonnée. "
            "Le paramètre 'documents' permet de ne générer qu'une partie du dossier."
        ),
        "category": "document",
        "handler_key": "builtin.generate_dossier_candidature",
        "input_schema": {
            "type": "object",
            "properties": {
                "entreprise_id": {"type": "string", "description": "ID de l'entreprise"},
                "fonds_id": {"type": "string", "description": "ID du fonds vert ciblé"},
                "intermediaire_id": {
                    "type": "string",
                    "description": "ID de l'intermédiaire (optionnel, pour adapter les documents)",
                },
                "format": {
                    "type": "string",
                    "enum": ["word", "pdf", "both"],
                    "default": "both",
                    "description": "Format de sortie des documents",
                },
                "type_dossier": {
                    "type": "string",
                    "enum": ["complet", "template_vierge"],
                    "default": "complet",
                    "description": "complet = pré-rempli avec données entreprise, template_vierge = structure avec placeholders à remplir",
                },
                "documents": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Liste des documents à générer. Si vide, génère le dossier complet. "
                        "Types possibles : page_garde, checklist_documents, lettre_motivation, "
                        "fiche_projet, plan_affaires, budget_previsionnel, note_impact_esg, "
                        "engagement_esg, note_presentation, rapport_esg_complet, bilan_carbone"
                    ),
                },
                "instructions": {
                    "type": "string",
                    "description": "Instructions spécifiques pour personnaliser la génération",
                },
            },
            "required": ["entreprise_id", "fonds_id"],
        },
    },
]


async def seed_skills(db: AsyncSession) -> int:
    count = 0
    for skill_data in BUILTIN_SKILLS:
        result = await db.execute(select(Skill).where(Skill.nom == skill_data["nom"]))
        existing = result.scalar_one_or_none()
        if existing is None:
            db.add(Skill(**skill_data))
            count += 1
        else:
            # Update description and input_schema for builtin skills
            existing.description = skill_data["description"]
            existing.input_schema = skill_data["input_schema"]
    await db.commit()
    return count
