"""
Seed de données de démo : compte admin, entreprise avec profil complet,
score ESG, empreinte carbone, plan d'action en cours.

Pour que la démo soit impressionnante dès le premier lancement.
"""

import logging
from datetime import date, datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.action_plan import ActionItem, ActionPlan
from app.models.carbon_footprint import CarbonFootprint
from app.models.entreprise import Entreprise
from app.models.esg_score import ESGScore
from app.models.referentiel_esg import ReferentielESG
from app.models.user import User

logger = logging.getLogger(__name__)

DEMO_ADMIN_EMAIL = "demo@esgadvisor.ai"
DEMO_ADMIN_PASSWORD = "demo1234"


async def seed_demo(db: AsyncSession) -> int:
    """
    Crée un compte admin de démo et une entreprise avec données pré-remplies.
    Retourne le nombre d'objets créés.
    """
    # Vérifier si le compte démo existe déjà
    result = await db.execute(select(User).where(User.email == DEMO_ADMIN_EMAIL))
    if result.scalar_one_or_none() is not None:
        logger.info("Compte démo déjà existant, skip.")
        return 0

    count = 0

    # --- 1. Créer l'utilisateur admin de démo ---
    demo_user = User(
        email=DEMO_ADMIN_EMAIL,
        password_hash=hash_password(DEMO_ADMIN_PASSWORD),
        nom_complet="Administrateur Démo",
        role="admin",
        is_active=True,
    )
    db.add(demo_user)
    await db.flush()  # Pour obtenir l'ID
    count += 1

    # --- 2. Créer l'entreprise de démo ---
    entreprise = Entreprise(
        user_id=demo_user.id,
        nom="AgroVert Côte d'Ivoire",
        secteur="agroalimentaire",
        sous_secteur="Transformation de produits agricoles",
        pays="Côte d'Ivoire",
        ville="Abidjan",
        effectifs=85,
        chiffre_affaires=450000000,  # 450 millions FCFA
        devise="XOF",
        description=(
            "AgroVert CI est une PME ivoirienne spécialisée dans la transformation "
            "et le conditionnement de produits agricoles locaux (mangues séchées, "
            "beurre de karité, jus de fruits naturels). Fondée en 2019, l'entreprise "
            "emploie 85 personnes dont 60% de femmes et exporte vers 5 pays de la sous-région."
        ),
        profil_json={
            "annee_creation": 2019,
            "forme_juridique": "SARL",
            "certifications": ["Commerce équitable", "Bio en cours"],
            "principaux_produits": [
                "Mangues séchées bio",
                "Beurre de karité premium",
                "Jus de fruits naturels",
                "Poudre de baobab",
            ],
            "marches_export": ["SEN", "MLI", "BFA", "GHA", "FRA"],
            "fournisseurs_agricoles": 120,
            "pct_femmes_effectif": 60,
            "pct_femmes_direction": 33,
            "source_energie": {
                "reseau_cie": "70%",
                "solaire": "20%",
                "groupe_electrogene": "10%",
            },
            "objectifs_esg": [
                "100% énergie solaire d'ici 2027",
                "Zéro déchet à la décharge d'ici 2026",
                "Certification bio complète d'ici 2026",
            ],
        },
    )
    db.add(entreprise)
    await db.flush()
    count += 1

    # --- 3. Charger le référentiel BCEAO ---
    result = await db.execute(
        select(ReferentielESG).where(ReferentielESG.code == "bceao_fd_2024")
    )
    referentiel = result.scalar_one_or_none()

    if referentiel:
        # --- 4. Score ESG de l'entreprise ---
        now = datetime.now(timezone.utc)

        # Score initial (il y a 6 mois)
        score_initial = ESGScore(
            entreprise_id=entreprise.id,
            referentiel_id=referentiel.id,
            score_e=38.0,
            score_s=42.0,
            score_g=35.0,
            score_global=38.5,
            details_json={
                "piliers": {
                    "environnement": {
                        "score": 38.0,
                        "criteres": {
                            "emissions_carbone": {"score": 40, "valeur": "180 tCO2e/an"},
                            "gestion_dechets": {"score": 40, "valeur": "Collecte basique organisée"},
                            "consommation_eau": {"score": 40, "valeur": "Suivi basique de la consommation"},
                            "energie_renouvelable": {"score": 40, "valeur": "15% solaire"},
                            "biodiversite_ecosystemes": {"score": 30, "valeur": "Pas d'impact négatif significatif identifié"},
                        },
                    },
                    "social": {
                        "score": 42.0,
                        "criteres": {
                            "conditions_travail": {"score": 40, "valeur": "Règles de base respectées"},
                            "egalite_genre": {"score": 70, "valeur": "33% femmes en direction"},
                            "impact_communaute": {"score": 40, "valeur": "Embauche locale + achats locaux"},
                            "formation_employes": {"score": 40, "valeur": "12h/employé/an"},
                            "protection_sociale": {"score": 30, "valeur": "Minima légaux respectés"},
                            "dialogue_social": {"score": 30, "valeur": "Canaux de communication informels"},
                        },
                    },
                    "gouvernance": {
                        "score": 35.0,
                        "criteres": {
                            "transparence": {"score": 40, "valeur": "Données disponibles sur demande"},
                            "ethique_anticorruption": {"score": 40, "valeur": "Règles informelles connues"},
                            "gouvernance_structure": {"score": 40, "valeur": "Direction collégiale"},
                            "conformite_reglementaire": {"score": 30, "valeur": "Conformité partielle en cours d'amélioration"},
                            "gestion_risques_esg": {"score": 20, "valeur": "Aucune gestion des risques ESG"},
                        },
                    },
                },
                "referentiel": "BCEAO Finance Durable 2024",
            },
            source="conversation",
            created_at=now - timedelta(days=180),
        )
        db.add(score_initial)
        count += 1

        # Score actuel (amélioré après actions)
        score_actuel = ESGScore(
            entreprise_id=entreprise.id,
            referentiel_id=referentiel.id,
            score_e=52.0,
            score_s=55.0,
            score_g=48.0,
            score_global=52.0,
            details_json={
                "piliers": {
                    "environnement": {
                        "score": 52.0,
                        "criteres": {
                            "emissions_carbone": {"score": 40, "valeur": "155 tCO2e/an (réduit de 14%)"},
                            "gestion_dechets": {"score": 70, "valeur": "Tri sélectif en place + valorisation partielle"},
                            "consommation_eau": {"score": 70, "valeur": "Suivi et objectifs de réduction documentés"},
                            "energie_renouvelable": {"score": 40, "valeur": "20% solaire (en cours d'extension)"},
                            "biodiversite_ecosystemes": {"score": 40, "valeur": "Pas d'impact négatif significatif identifié"},
                        },
                    },
                    "social": {
                        "score": 55.0,
                        "criteres": {
                            "conditions_travail": {"score": 70, "valeur": "Politique formelle + formation régulière"},
                            "egalite_genre": {"score": 70, "valeur": "35% femmes en direction"},
                            "impact_communaute": {"score": 70, "valeur": "Actions ponctuelles documentées"},
                            "formation_employes": {"score": 40, "valeur": "18h/employé/an"},
                            "protection_sociale": {"score": 40, "valeur": "Couverture santé et retraite"},
                            "dialogue_social": {"score": 40, "valeur": "Délégués du personnel + réunions périodiques"},
                        },
                    },
                    "gouvernance": {
                        "score": 48.0,
                        "criteres": {
                            "transparence": {"score": 70, "valeur": "Reporting interne structuré + KPIs suivis"},
                            "ethique_anticorruption": {"score": 70, "valeur": "Code éthique documenté et diffusé"},
                            "gouvernance_structure": {"score": 40, "valeur": "Direction collégiale"},
                            "conformite_reglementaire": {"score": 40, "valeur": "Conformité totale vérifiée"},
                            "gestion_risques_esg": {"score": 30, "valeur": "Conscience des risques sans formalisation"},
                        },
                    },
                },
                "referentiel": "BCEAO Finance Durable 2024",
                "evolution": "+13.5 points en 6 mois",
            },
            source="conversation",
            created_at=now - timedelta(days=5),
        )
        db.add(score_actuel)
        count += 1

        # --- 5. Plan d'action ESG ---
        plan = ActionPlan(
            entreprise_id=entreprise.id,
            titre="Plan d'amélioration ESG — AgroVert CI 2025",
            horizon="12_mois",
            referentiel_id=referentiel.id,
            score_initial=38.5,
            score_cible=65.0,
            created_at=now - timedelta(days=150),
        )
        db.add(plan)
        await db.flush()
        count += 1

        # Actions du plan
        actions = [
            ActionItem(
                plan_id=plan.id,
                titre="Installer 30 kWc de panneaux solaires supplémentaires",
                description="Extension de l'installation solaire existante pour atteindre 50% d'énergie renouvelable. Devis obtenu auprès de Solar Africa CI.",
                priorite="moyen_terme",
                pilier="environnement",
                critere_id="energie_renouvelable",
                statut="en_cours",
                echeance=date(2025, 6, 30),
                impact_score_estime=15.0,
                cout_estime=25000000,
                benefice_estime=4000000,
            ),
            ActionItem(
                plan_id=plan.id,
                titre="Mettre en place le tri sélectif et le compostage",
                description="Installer des bacs de tri dans tous les ateliers. Partenariat avec EcoRecycle CI pour la collecte. Composteur pour les déchets organiques de production.",
                priorite="quick_win",
                pilier="environnement",
                critere_id="gestion_dechets",
                statut="fait",
                echeance=date(2025, 3, 31),
                impact_score_estime=10.0,
                cout_estime=2000000,
                benefice_estime=1500000,
            ),
            ActionItem(
                plan_id=plan.id,
                titre="Système de récupération d'eau de pluie",
                description="Installation de cuves de récupération (20 m³) pour le nettoyage des équipements et l'irrigation du jardin de l'entreprise.",
                priorite="moyen_terme",
                pilier="environnement",
                critere_id="consommation_eau",
                statut="en_cours",
                echeance=date(2025, 9, 30),
                impact_score_estime=8.0,
                cout_estime=3500000,
                benefice_estime=800000,
            ),
            ActionItem(
                plan_id=plan.id,
                titre="Programme de formation SST pour tous les employés",
                description="Formation en santé-sécurité au travail de 16h pour tous les employés. Partenaire : FDFP (Fonds de Développement de la Formation Professionnelle).",
                priorite="quick_win",
                pilier="social",
                critere_id="conditions_travail",
                statut="fait",
                echeance=date(2025, 2, 28),
                impact_score_estime=10.0,
                cout_estime=1200000,
                benefice_estime=0,
            ),
            ActionItem(
                plan_id=plan.id,
                titre="Couverture santé complémentaire pour tous les employés",
                description="Souscription d'une mutuelle santé couvrant les employés et leurs familles. Négociation en cours avec NSIA Assurances.",
                priorite="quick_win",
                pilier="social",
                critere_id="protection_sociale",
                statut="en_cours",
                echeance=date(2025, 4, 30),
                impact_score_estime=8.0,
                cout_estime=6000000,
                benefice_estime=0,
            ),
            ActionItem(
                plan_id=plan.id,
                titre="Programme de mentorat et promotion des femmes",
                description="Objectif : 40% de femmes en postes de direction d'ici fin 2025. Formation en leadership pour 10 collaboratrices identifiées.",
                priorite="moyen_terme",
                pilier="social",
                critere_id="egalite_genre",
                statut="en_cours",
                echeance=date(2025, 12, 31),
                impact_score_estime=5.0,
                cout_estime=1500000,
                benefice_estime=0,
            ),
            ActionItem(
                plan_id=plan.id,
                titre="Rédaction et diffusion du code éthique",
                description="Code éthique incluant politique anti-corruption, canal d'alerte confidentiel, formation de tous les managers.",
                priorite="quick_win",
                pilier="gouvernance",
                critere_id="ethique_anticorruption",
                statut="fait",
                echeance=date(2025, 1, 31),
                impact_score_estime=10.0,
                cout_estime=500000,
                benefice_estime=0,
            ),
            ActionItem(
                plan_id=plan.id,
                titre="Cartographie des risques ESG",
                description="Identification et priorisation des risques ESG avec l'appui d'un consultant. Mise en place d'un tableau de bord de suivi trimestriel.",
                priorite="moyen_terme",
                pilier="gouvernance",
                critere_id="gestion_risques_esg",
                statut="a_faire",
                echeance=date(2025, 8, 31),
                impact_score_estime=12.0,
                cout_estime=3000000,
                benefice_estime=0,
            ),
            ActionItem(
                plan_id=plan.id,
                titre="Premier rapport ESG annuel",
                description="Publication d'un rapport ESG suivant les recommandations BCEAO. Indicateurs standardisés et objectifs chiffrés.",
                priorite="long_terme",
                pilier="gouvernance",
                critere_id="transparence",
                statut="a_faire",
                echeance=date(2025, 12, 31),
                impact_score_estime=10.0,
                cout_estime=2000000,
                benefice_estime=0,
            ),
        ]

        for action in actions:
            db.add(action)
            count += 1

    # --- 6. Empreinte carbone (plusieurs mois) ---
    carbon_data = [
        {"annee": 2024, "mois": 10, "energie": 5.8, "transport": 3.2, "dechets": 1.5, "achats": 2.1, "total_tco2e": 12.6},
        {"annee": 2024, "mois": 11, "energie": 5.5, "transport": 3.0, "dechets": 1.4, "achats": 2.3, "total_tco2e": 12.2},
        {"annee": 2024, "mois": 12, "energie": 6.2, "transport": 3.5, "dechets": 1.6, "achats": 2.8, "total_tco2e": 14.1},
        {"annee": 2025, "mois": 1, "energie": 5.2, "transport": 2.8, "dechets": 1.2, "achats": 2.0, "total_tco2e": 11.2},
        {"annee": 2025, "mois": 2, "energie": 4.8, "transport": 2.6, "dechets": 1.0, "achats": 1.9, "total_tco2e": 10.3},
    ]

    for cd in carbon_data:
        carbon = CarbonFootprint(
            entreprise_id=entreprise.id,
            annee=cd["annee"],
            mois=cd["mois"],
            energie=cd["energie"],
            transport=cd["transport"],
            dechets=cd["dechets"],
            achats=cd["achats"],
            total_tco2e=cd["total_tco2e"],
            details_json={
                "sources_energie": {
                    "reseau_cie": f"{cd['energie'] * 0.7:.1f} tCO2e",
                    "groupe_electrogene": f"{cd['energie'] * 0.2:.1f} tCO2e",
                    "solaire": "0.0 tCO2e",
                },
                "sources_transport": {
                    "camion_livraison": f"{cd['transport'] * 0.6:.1f} tCO2e",
                    "vehicules_service": f"{cd['transport'] * 0.3:.1f} tCO2e",
                    "deplacement_employes": f"{cd['transport'] * 0.1:.1f} tCO2e",
                },
                "tendance": "baisse" if cd["mois"] >= 1 else "stable",
            },
            source="conversation",
            created_at=datetime(cd["annee"], cd["mois"], 28, tzinfo=timezone.utc),
        )
        db.add(carbon)
        count += 1

    await db.commit()
    logger.info("Données de démo créées : %d objets.", count)
    return count
