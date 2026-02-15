# Prompt pour générer le Deck PDF — ESG Mefali

## Comment utiliser ce fichier

Copie-colle **tout le contenu sous "DÉBUT DU PROMPT"** dans l'un de ces outils :
- **Gamma.app** (recommandé, gratuit, génère directement des slides) → gamma.app → "Create new" → "Paste in text"
- **ChatGPT** → demande-lui de générer un Google Slides ou PowerPoint
- **Canva AI** → canva.com → "Présentation" → colle dans l'assistant IA

Ensuite exporte en PDF et upload sur Google Drive.

---

# DÉBUT DU PROMPT

Génère une présentation professionnelle de 10 slides au format 16:9 pour un pitch de startup dans le cadre d'un hackathon sur l'IA et le développement durable.

## Directives de design

- Style : moderne, épuré, professionnel, inspirant confiance
- Palette de couleurs : vert émeraude (#22C55E) comme couleur principale, bleu marine (#1E3A5F) comme couleur secondaire, fond blanc ou gris très clair (#F8FAFC), texte en gris foncé (#1E293B)
- Police : Montserrat ou Inter (sans-serif moderne)
- Icônes : utiliser des icônes plates et modernes pour illustrer chaque point
- Maximum 6 bullet points par slide, texte concis
- Chaque slide doit avoir un visuel ou un schéma, pas que du texte
- Langue : FRANÇAIS uniquement
- Le thème général est la finance verte et l'IA en Afrique

---

## SLIDE 1 — Couverture

Titre principal : **ESG Mefali**
Sous-titre : **L'intelligence artificielle au service de la finance verte pour les PME africaines**
En bas : Hackathon Francophone IA — Green Open Lab / IFDD — Février 2026
Visuel : une illustration stylisée combinant un continent africain, des feuilles vertes et des circuits numériques/IA

---

## SLIDE 2 — Le problème

Titre : **Les PME africaines sont exclues de la finance verte**

Contenu avec icônes pour chaque point :
- 📊 Moins de 10 % des financements climat en Afrique atteignent les PME
- 💰 Consultants ESG hors de prix : 5 000 à 20 000 $ par mission
- 📄 Référentiels ESG complexes, techniques, souvent en anglais
- 🔍 Aucune visibilité sur les dizaines de fonds verts disponibles (BOAD, GCF, BAD, AFD...)
- 🏦 Sans historique de crédit formel = pas d'accès au prêt bancaire

Conclusion en gras en bas de slide : **Résultat : 80 % de l'emploi africain est porté par les PME, mais elles ne reçoivent que 10 % du financement climat.**

Visuel : un schéma illustrant le fossé/gap entre "Milliards $ de fonds verts disponibles" à gauche et "PME africaines sans accès" à droite, avec un mur entre les deux

---

## SLIDE 3 — Notre solution

Titre : **ESG Mefali — Le conseiller ESG virtuel, en français**

Texte introductif : Un agent IA conversationnel qui accompagne les PME africaines de l'évaluation jusqu'au dossier de financement.

6 fonctionnalités clés, chacune avec une icône :
1. 🎯 Scoring ESG multi-référentiel — Évaluation automatique selon les cadres BCEAO (UEMOA), IFC (Banque Mondiale) et GCF, adaptés par secteur et pays
2. 🌍 Calculateur carbone contextualisé — Empreinte carbone avec facteurs d'émission spécifiques à l'Afrique de l'Ouest (mix énergétique, générateurs diesel, etc.)
3. 🔗 Matching intelligent de fonds verts — Recherche sémantique parmi 10+ fonds régionaux et internationaux, avec score de compatibilité
4. 💳 Crédit scoring alternatif — Score de crédit inclusif combinant pratiques ESG, tendances carbone et mobile money
5. 📋 Génération automatique de dossiers — PDF professionnels prêts à soumettre aux bailleurs de fonds
6. 🧩 Extension Chrome — Pré-remplissage automatique des formulaires de candidature sur les sites de fonds

---

## SLIDE 4 — Comment ça marche

Titre : **3 étapes pour accéder au financement vert**

Afficher un schéma horizontal en 3 étapes reliées par des flèches :

**Étape 1 — DIALOGUER** (icône : bulles de conversation)
L'entrepreneur discute en français avec l'agent IA. Pas de formulaires complexes. L'IA pose les bonnes questions et collecte les données par conversation naturelle.
→ Résultat : Score ESG calculé + Empreinte carbone mesurée

**Étape 2 — MATCHER** (icône : cible/radar)
L'IA croise le profil de l'entreprise avec les fonds verts disponibles. Elle identifie les fonds compatibles et propose un plan d'action pour améliorer l'éligibilité.
→ Résultat : Liste de fonds compatibles + Score de compatibilité

**Étape 3 — CANDIDATER** (icône : document avec check)
Le dossier de candidature est généré automatiquement en PDF. L'extension Chrome pré-remplit les formulaires en ligne sur les sites des fonds.
→ Résultat : Dossier complet soumis + Suivi de la candidature

---

## SLIDE 5 — L'IA au cœur de la solution

Titre : **Comment nous utilisons l'intelligence artificielle**

Afficher un tableau visuel avec 2 colonnes (Fonctionnalité | Technologie IA utilisée) :

| Fonctionnalité | Technologie IA |
|---|---|
| Collecte de données conversationnelle | Agent LLM (Claude) avec function calling — 20+ skills dynamiques |
| Recherche et matching de fonds | RAG hybride : recherche sémantique par vecteurs (pgvector, 1024 dim) + filtrage SQL |
| Évaluation ESG | NLP : extraction automatique de données quantitatives et qualitatives du langage naturel |
| Crédit scoring inclusif | Modèle hybride : score de solvabilité (0-100) + score d'impact vert (0-100) |
| Aide au remplissage de formulaires | Génération contextuelle par LLM : descriptions de projet, motivations adaptées au fonds ciblé |
| Analyse de documents entreprise | OCR (pytesseract) + chunking intelligent + embeddings vectoriels pour recherche sémantique |

En bas : Architecture technique — Vue 3 + FastAPI + PostgreSQL/pgvector + Claude via OpenRouter

---

## SLIDE 6 — Ce qui nous distingue

Titre : **ESG Mefali vs. Solutions existantes**

Afficher un tableau comparatif visuel avec deux colonnes contrastées (rouge/gris à gauche, vert à droite) :

| Solutions existantes (Refinitiv, Sustainalytics, CDP) | ESG Mefali |
|---|---|
| ❌ Conçues pour les grandes entreprises occidentales | ✅ Conçu spécifiquement pour les PME africaines |
| ❌ Abonnements à 10 000+ $/an | ✅ Modèle freemium accessible |
| ❌ Interfaces et référentiels en anglais | ✅ Entièrement en français, avec saisie vocale |
| ❌ Référentiels occidentaux uniquement (GRI, SASB) | ✅ Référentiels africains : BCEAO, IFC, GCF adaptés par pays |
| ❌ Formulaires longs et techniques | ✅ Dialogue naturel avec l'IA, zéro formulaire |
| ❌ Diagnostic seul, sans suite | ✅ De bout en bout : diagnostic → plan d'action → dossier PDF → candidature |

---

## SLIDE 7 — La plateforme en action

Titre : **Démo — ESG Mefali en action**

Disposer 4 zones de capture d'écran (placeholder) avec des légendes :

Zone 1 (en haut à gauche) : **Chat IA conversationnel**
Légende : "L'entrepreneur dialogue en français avec l'agent. L'IA pose les questions, calcule les scores et recommande des actions."

Zone 2 (en haut à droite) : **Dashboard ESG**
Légende : "Scores par pilier (Environnement, Social, Gouvernance) avec benchmark sectoriel et suivi dans le temps."

Zone 3 (en bas à gauche) : **Calculateur carbone**
Légende : "Empreinte carbone ventilée par source (énergie, transport, déchets) avec graphiques et comparaison sectorielle."

Zone 4 (en bas à droite) : **Extension Chrome**
Légende : "Accompagnement pas-à-pas directement sur les sites de fonds verts, avec pré-remplissage automatique."

Note : ces zones sont des placeholders gris avec les légendes — les vraies captures seront ajoutées manuellement après.

---

## SLIDE 8 — Impact et ODD

Titre : **Impact social et environnemental**

Partie gauche — ODD visés (avec les icônes officielles ONU des ODD) :
- ODD 8 — Travail décent et croissance économique : facilite l'accès au capital pour la croissance des PME vertes
- ODD 10 — Inégalités réduites : démocratise la finance verte, inclut les non-bancarisés via le crédit scoring alternatif
- ODD 12 — Consommation et production responsables : encourage l'économie circulaire et la gestion des déchets
- ODD 13 — Lutte contre les changements climatiques : quantifie les émissions, canalise le financement climat vers les PME
- ODD 17 — Partenariats pour les objectifs : connecte PME, fonds internationaux et banques locales

Partie droite — Chiffres d'impact visé à 3 ans (affichés en grand, style KPI) :
- **1 000** PME accompagnées en zone UEMOA
- **50 M$** de financements verts débloqués
- **10 000 tCO2e** de réductions carbone identifiées

---

## SLIDE 9 — Avancement et roadmap

Titre : **MVP fonctionnel — Prêt pour démonstration**

Partie gauche — Ce qui est réalisé (icônes check verts) :
- ✅ Base de données complète (20 tables, PostgreSQL + pgvector)
- ✅ Chat IA avec streaming en temps réel (SSE)
- ✅ Scoring ESG multi-référentiel (BCEAO, IFC, GCF)
- ✅ Calculateur d'empreinte carbone avec facteurs africains
- ✅ Matching intelligent de 10 fonds verts (BOAD, BAD, GCF, AFD...)
- ✅ Extension Chrome complète (27 tests unitaires, i18n FR/EN)
- ✅ Déploiement containerisé (Docker Compose)

Partie droite — Prochaines étapes (timeline verticale) :
- T2 2026 → Pilote avec 10 PME en Côte d'Ivoire
- T3 2026 → Partenariats avec BOAD et institutions de microfinance
- T4 2026 → Lancement commercial en zone UEMOA (8 pays)
- 2027 → Extension à toute l'Afrique francophone

---

## SLIDE 10 — Équipe et contact

Titre : **L'équipe**

Au centre :
- [PLACEHOLDER PHOTO] — Photo du fondateur
- Nom : [À COMPLÉTER]
- Rôle : Fondateur & Développeur
- [À COMPLÉTER : 1 ligne de parcours, ex: "Ingénieur logiciel passionné par la finance durable et l'IA"]

En bas :
- Email : [À COMPLÉTER]
- LinkedIn : [À COMPLÉTER]
- Projet : ESG Mefali

Texte de clôture en grand : **Merci — La finance verte, accessible à tous.**

# FIN DU PROMPT
