# 08 - Arborescence du Projet

## Structure Complète

```
consultant_esg/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      ← Point d'entrée FastAPI
│   │   ├── config.py                    ← Settings (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, etc.)
│   │   │
│   │   ├── api/                         ← Routes API
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                  ← /api/auth/*
│   │   │   ├── chat.py                  ← /api/chat/* (SSE streaming)
│   │   │   ├── entreprises.py           ← /api/entreprises/*
│   │   │   ├── documents.py             ← /api/documents/*
│   │   │   ├── reports.py               ← /api/reports/*
│   │   │   ├── carbon.py               ← /api/carbon/*
│   │   │   ├── credit_score.py         ← /api/credit-score/*
│   │   │   ├── action_plans.py         ← /api/action-plans/*
│   │   │   ├── notifications.py        ← /api/notifications/*
│   │   │   ├── benchmark.py            ← /api/benchmark/*
│   │   │   └── admin/
│   │   │       ├── __init__.py
│   │   │       ├── skills.py            ← /api/admin/skills/*
│   │   │       ├── referentiels.py      ← /api/admin/referentiels/*  NOUVEAU
│   │   │       ├── fonds.py             ← /api/admin/fonds/*
│   │   │       ├── templates.py         ← /api/admin/templates/*
│   │   │       └── stats.py             ← /api/admin/stats/*
│   │   │
│   │   ├── agent/                       ← Moteur de l'agent IA
│   │   │   ├── __init__.py
│   │   │   ├── engine.py               ← Boucle agent (appel LLM via OpenRouter + skills)
│   │   │   └── prompt_builder.py       ← Construction dynamique du system prompt
│   │   │
│   │   ├── skills/                      ← Système de skills
│   │   │   ├── __init__.py
│   │   │   ├── registry.py             ← SkillRegistry (chargement BDD → tools)
│   │   │   ├── validator.py            ← Validation du code Python custom
│   │   │   ├── sandbox.py              ← Exécution sandboxée des skills custom
│   │   │   └── handlers/               ← Skills builtin (code Python)
│   │   │       ├── __init__.py
│   │   │       ├── analyze_document.py
│   │   │       ├── calculate_esg_score.py  ← v2 multi-référentiel
│   │   │       ├── list_referentiels.py    ← NOUVEAU
│   │   │       ├── search_green_funds.py
│   │   │       ├── calculate_carbon.py
│   │   │       ├── generate_reduction_plan.py     ← plan de réduction carbone
│   │   │       ├── simulate_funding.py            ← simulateur de financement
│   │   │       ├── calculate_credit_score.py      ← scoring crédit vert (Module 5)
│   │   │       ├── get_sector_benchmark.py        ← moyennes sectorielles
│   │   │       ├── manage_action_plan.py          ← gestion plan d'action (Module 6)
│   │   │       ├── generate_report_section.py
│   │   │       ├── assemble_pdf.py
│   │   │       ├── search_knowledge_base.py
│   │   │       ├── get_company_profile.py
│   │   │       └── update_company_profile.py
│   │   │
│   │   ├── rag/                         ← Moteur RAG
│   │   │   ├── __init__.py
│   │   │   ├── chunker.py              ← Découpage de texte en chunks
│   │   │   ├── embeddings.py           ← Appels API embeddings
│   │   │   ├── search.py               ← Recherche sémantique pgvector
│   │   │   └── text_extractor.py       ← Extraction texte (PDF, OCR, Word)
│   │   │
│   │   ├── reports/                     ← Génération de rapports PDF
│   │   │   ├── __init__.py
│   │   │   ├── generator.py            ← Assemblage HTML → PDF (WeasyPrint)
│   │   │   ├── charts.py              ← Graphiques matplotlib
│   │   │   └── templates/              ← Templates HTML/CSS Jinja2
│   │   │       ├── rapport_esg.html
│   │   │       ├── rapport_carbone.html
│   │   │       ├── dossier_candidature.html
│   │   │       └── base.html           ← Template de base commun
│   │   │
│   │   ├── models/                      ← Modèles SQLAlchemy (ou queries brutes)
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── entreprise.py
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   ├── document.py
│   │   │   ├── skill.py
│   │   │   ├── referentiel_esg.py      ← NOUVEAU
│   │   │   ├── esg_score.py
│   │   │   ├── carbon_footprint.py        ← empreinte carbone
│   │   │   ├── credit_score.py            ← scoring crédit vert
│   │   │   ├── action_plan.py             ← plans d'action + items
│   │   │   ├── notification.py            ← notifications
│   │   │   ├── sector_benchmark.py        ← moyennes sectorielles
│   │   │   ├── fonds_vert.py
│   │   │   └── report_template.py
│   │   │
│   │   ├── schemas/                     ← Pydantic schemas (request/response)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── entreprise.py
│   │   │   ├── document.py
│   │   │   ├── skill.py
│   │   │   ├── referentiel.py          ← NOUVEAU
│   │   │   ├── carbon.py
│   │   │   ├── credit_score.py
│   │   │   ├── action_plan.py
│   │   │   ├── notification.py
│   │   │   └── report.py
│   │   │
│   │   ├── core/                        ← Utilitaires et configuration
│   │   │   ├── __init__.py
│   │   │   ├── database.py             ← Connexion PostgreSQL
│   │   │   ├── security.py             ← JWT, hashing password
│   │   │   ├── dependencies.py         ← Dépendances FastAPI (auth, db)
│   │   │   └── stt.py                  ← Service Speech-to-Text (Whisper/Google)
│   │   │
│   │   └── seed/                        ← Données initiales
│   │       ├── __init__.py
│   │       ├── seed_skills.py          ← Insertion des skills builtin
│   │       ├── seed_referentiels.py   ← Insertion des référentiels ESG initiaux  NOUVEAU
│   │       ├── seed_fonds.py           ← Insertion des fonds verts (+ lien référentiel)
│   │       ├── seed_benchmarks.py     ← Insertion moyennes sectorielles initiales
│   │       └── seed_knowledge.py       ← Insertion base de connaissances ESG
│   │
│   ├── migrations/                      ← Migrations Alembic
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 001_initial.py
│   │       └── ...
│   │
│   ├── data/                            ← Données statiques
│   │   ├── fonds_verts.json            ← Catalogue des fonds verts
│   │   ├── referentiels_esg.json       ← Référentiels ESG initiaux (BCEAO, GCF, IFC...)
│   │   ├── facteurs_emission.json      ← Facteurs d'émission carbone (par pays/source)
│   │   ├── sector_benchmarks.json     ← Moyennes sectorielles initiales (données estimées)
│   │   └── knowledge_base/             ← Documents de la base de connaissances
│   │       ├── reglementations_uemoa.md
│   │       ├── taxonomie_verte_bceao.md
│   │       ├── guide_esg_pme.md
│   │       └── ...
│   │
│   ├── uploads/                         ← Stockage local des fichiers uploadés
│   │   └── .gitkeep
│   │
│   ├── tests/
│   │   ├── test_agent.py
│   │   ├── test_skills.py
│   │   ├── test_rag.py
│   │   └── test_api.py
│   │
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   │
│   │   ├── views/
│   │   │   ├── LoginView.vue
│   │   │   ├── RegisterView.vue
│   │   │   ├── ChatView.vue
│   │   │   ├── DashboardView.vue
│   │   │   ├── DocumentsView.vue
│   │   │   ├── CarbonView.vue              ← Empreinte carbone + réduction
│   │   │   ├── CreditScoreView.vue         ← Score crédit vert (Module 5)
│   │   │   ├── ActionPlanView.vue          ← Suivi plan d'action (Module 6)
│   │   │   └── admin/
│   │   │       ├── AdminLayout.vue
│   │   │       ├── SkillsListView.vue
│   │   │       ├── SkillEditView.vue
│   │   │       ├── ReferentielsListView.vue   ← NOUVEAU
│   │   │       ├── ReferentielEditView.vue    ← NOUVEAU
│   │   │       ├── FondsListView.vue
│   │   │       ├── FondEditView.vue           ← NOUVEAU
│   │   │       ├── TemplatesListView.vue
│   │   │       └── StatsView.vue
│   │   │
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── ChatContainer.vue
│   │   │   │   ├── MessageBubble.vue
│   │   │   │   ├── MessageInput.vue
│   │   │   │   ├── SkillIndicator.vue
│   │   │   │   ├── StreamingText.vue
│   │   │   │   ├── FileUploadButton.vue
│   │   │   │   └── AudioRecordButton.vue   ← Enregistrement vocal (STT)
│   │   │   │
│   │   │   ├── carbon/                     ← Composants empreinte carbone
│   │   │   │   ├── CarbonSummary.vue
│   │   │   │   ├── CarbonEvolution.vue
│   │   │   │   ├── CarbonBySource.vue
│   │   │   │   ├── ReductionPlan.vue
│   │   │   │   └── SectorComparison.vue
│   │   │   │
│   │   │   ├── credit/                     ← Composants crédit vert
│   │   │   │   ├── CreditScoreGauge.vue
│   │   │   │   ├── ScoreBreakdown.vue
│   │   │   │   └── ShareScoreButton.vue
│   │   │   │
│   │   │   ├── actions/                    ← Composants plan d'action
│   │   │   │   ├── ActionPlanTimeline.vue
│   │   │   │   ├── ActionItemCard.vue
│   │   │   │   └── ProgressTracker.vue
│   │   │   │
│   │   │   ├── dashboard/
│   │   │   │   ├── ScoreCard.vue
│   │   │   │   ├── RadarChart.vue
│   │   │   │   ├── ScoreHistory.vue
│   │   │   │   ├── FundsMatchList.vue
│   │   │   │   └── ActionPlan.vue
│   │   │   │
│   │   │   ├── admin/
│   │   │   │   ├── SkillForm.vue
│   │   │   │   ├── SkillCodeEditor.vue
│   │   │   │   ├── SkillTestPanel.vue
│   │   │   │   ├── SchemaBuilder.vue
│   │   │   │   ├── ReferentielForm.vue        ← NOUVEAU
│   │   │   │   ├── GrilleEditor.vue           ← NOUVEAU (éditeur visuel grille ESG)
│   │   │   │   └── ScoringSimulator.vue       ← NOUVEAU (test scoring)
│   │   │   │
│   │   │   └── common/
│   │   │       ├── AppSidebar.vue
│   │   │       ├── AppHeader.vue
│   │   │       ├── NotificationBell.vue    ← Cloche notifications
│   │   │       ├── LoadingSpinner.vue
│   │   │       └── ConfirmDialog.vue
│   │   │
│   │   ├── composables/
│   │   │   ├── useChat.ts
│   │   │   ├── useAuth.ts
│   │   │   ├── useApi.ts
│   │   │   ├── useAudioRecorder.ts     ← MediaRecorder + envoi audio
│   │   │   └── useNotifications.ts     ← Polling notifications
│   │   │
│   │   ├── stores/
│   │   │   ├── auth.ts
│   │   │   ├── chat.ts
│   │   │   ├── entreprise.ts
│   │   │   ├── notifications.ts        ← Pinia store notifications
│   │   │   └── admin.ts
│   │   │
│   │   ├── router/
│   │   │   └── index.ts
│   │   │
│   │   └── assets/
│   │       ├── logo.svg
│   │       └── styles/
│   │           └── main.css           ← TailwindCSS imports
│   │
│   ├── public/
│   │   └── favicon.ico
│   │
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── Dockerfile
│
├── docker-compose.yml                   ← PostgreSQL + Backend + Frontend
├── .env.example
├── .gitignore
└── README.md
```

## docker-compose.yml

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: esg_advisor
      POSTGRES_USER: esg
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://esg:${DB_PASSWORD}@db:5432/esg_advisor
      # --- LLM (via OpenRouter par défaut) ---
      LLM_BASE_URL: ${LLM_BASE_URL:-https://openrouter.ai/api/v1}
      LLM_API_KEY: ${LLM_API_KEY}
      LLM_MODEL: ${LLM_MODEL:-anthropic/claude-sonnet-4-5-20250514}
      APP_URL: ${APP_URL:-http://localhost:3000}
      JWT_SECRET: ${JWT_SECRET}
    depends_on:
      - db
    volumes:
      - ./backend/uploads:/app/uploads

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  pgdata:
```

## .env.example

```env
# Base de données
DB_PASSWORD=changeme_in_production

# === LLM (via OpenRouter — compatible OpenAI SDK) ===
# Pour changer de modèle, il suffit de modifier LLM_MODEL ci-dessous.
# Pour changer de provider, modifier LLM_BASE_URL et LLM_API_KEY.
#
# Exemples de configurations :
#   OpenRouter + Claude  : LLM_BASE_URL=https://openrouter.ai/api/v1  LLM_MODEL=anthropic/claude-sonnet-4-5-20250514
#   OpenRouter + GPT-4o  : LLM_BASE_URL=https://openrouter.ai/api/v1  LLM_MODEL=openai/gpt-4o
#   OpenRouter + Llama 3 : LLM_BASE_URL=https://openrouter.ai/api/v1  LLM_MODEL=meta-llama/llama-3.1-70b-instruct
#   OpenRouter + Mistral : LLM_BASE_URL=https://openrouter.ai/api/v1  LLM_MODEL=mistralai/mistral-large-latest
#   Anthropic direct     : LLM_BASE_URL=https://api.anthropic.com/v1  LLM_MODEL=claude-sonnet-4-5-20250514
#   OpenAI direct        : LLM_BASE_URL=https://api.openai.com/v1    LLM_MODEL=gpt-4o
#
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-...                                    # Clé API OpenRouter
LLM_MODEL=anthropic/claude-sonnet-4-5-20250514            # Modèle par défaut

# URL de l'application (requis par OpenRouter pour identification)
APP_URL=http://localhost:3000

# JWT
JWT_SECRET=changeme_random_secret_64chars

# Embeddings (au choix)
VOYAGE_API_KEY=...        # Si Voyage AI
# ou utiliser les embeddings locaux

# Speech-to-Text (pour le support vocal)
OPENAI_API_KEY=...        # Si Whisper API (OpenAI)
# ou GOOGLE_STT_CREDENTIALS=... pour Google Cloud Speech
```

## Ordre d'Implémentation Recommandé

```
Semaine 1 : Fondations
├── 1. docker-compose + PostgreSQL + pgvector
├── 2. Backend FastAPI : config, database, auth
├── 3. Modèles BDD + migrations Alembic (incluant referentiels_esg)
├── 4. Seed : skills builtin + référentiels ESG initiaux + fonds verts
└── 5. Frontend : setup Vue.js + router + auth

Semaine 2 : Agent Conversationnel
├── 6. SkillRegistry + handlers builtin basiques
├── 7. AgentEngine (boucle agent + Claude API)
├── 8. API /chat avec SSE streaming
├── 9. Frontend ChatView + composable useChat
└── 10. Profilage entreprise par conversation

Semaine 3 : Modules Métier (ESG + Carbone + Financement)
├── 11. RAG : chunker, embeddings (Voyage 3.5), search (HNSW)
├── 12. Upload documents + analyse
├── 13. Score ESG multi-référentiel (skill v2 + list_referentiels)
├── 14. Recherche fonds verts (SQL + RAG + lien référentiel)
├── 15. Calculateur carbone (skill calculate_carbon + table carbon_footprints)
├── 16. Plan de réduction carbone (skill generate_reduction_plan)
├── 17. Simulateur de financement (skill simulate_funding)
└── 18. Benchmarking sectoriel (skill get_sector_benchmark + table sector_benchmarks)

Semaine 4 : Crédit Vert + Plans d'Action + Rapports
├── 19. Scoring crédit vert alternatif (skill calculate_credit_score + table credit_scores)
├── 20. Plan d'action et suivi (skill manage_action_plan + tables action_plans/items)
├── 21. Système de notifications (table + API + NotificationBell frontend)
├── 22. Templates HTML rapports (avec section multi-référentiel)
├── 23. Génération PDF (WeasyPrint + charts)
├── 24. Frontend : CarbonView + CreditScoreView + ActionPlanView
└── 25. Dashboard entreprise (multi-référentiel + comparaison + benchmarks)

Semaine 5 : Admin + Support Vocal + Polish
├── 26. Admin CRUD skills (API + Frontend)
├── 27. Admin CRUD référentiels ESG (éditeur grille + simulateur)
├── 28. Support vocal : AudioRecordButton + API /audio + STT (Whisper)
├── 29. Seed données réalistes (référentiels, benchmarks, fonds)
├── 30. UX/UI polish + tests de bout en bout
├── 31. Vidéo pitch + deck
└── 32. Déploiement démo
```
