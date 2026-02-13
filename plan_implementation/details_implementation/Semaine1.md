# Semaine 1 — Fondations

> **Objectif** : Mettre en place l'infrastructure (Docker, BDD, backend, frontend) pour que tout le reste puisse se construire dessus.

---

## Étape 1 — Docker Compose + PostgreSQL + pgvector

**Fichiers concernés** : [08_arborescence_projet.md](../08_arborescence_projet.md) · [01_architecture_globale.md](../01_architecture_globale.md)

### À faire

- [x] 1.1 Créer le fichier `docker-compose.yml` à la racine
  - Service `db` : image `pgvector/pgvector:pg16`, port 5432, volume `pgdata`
  - Service `backend` : build `./backend`, port 8000, depends_on `db`
  - Service `frontend` : build `./frontend`, port 3000, depends_on `backend`
  - Variables d'env injectées depuis `.env`

- [x] 1.2 Créer `.env` à partir de `.env.example`
  - `DB_PASSWORD`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `JWT_SECRET`, `APP_URL`
  - Voir le template complet dans [08_arborescence_projet.md](../08_arborescence_projet.md#docker-composeyml)

- [x] 1.3 Créer `.gitignore`
  - `.env`, `__pycache__`, `node_modules`, `uploads/*`, `pgdata`, `.venv`

- [x] 1.4 Vérifier que `docker compose up db` lance PostgreSQL avec pgvector (port 5433 externe, pgvector v0.8.1)
  - Tester : `docker compose exec db psql -U esg -d esg_advisor -c "CREATE EXTENSION IF NOT EXISTS vector;"`

### Comment

1. Copier le `docker-compose.yml` du plan ([08_arborescence_projet.md](../08_arborescence_projet.md))
2. Créer `.env` en copiant `.env.example` et en remplissant les clés
3. `docker compose up -d db` → vérifier que la BDD tourne

---

## Étape 2 — Backend FastAPI : config, database, auth

**Fichiers concernés** : [08_arborescence_projet.md](../08_arborescence_projet.md) · [05_api_endpoints.md](../05_api_endpoints.md) · [01_architecture_globale.md](../01_architecture_globale.md)

### À faire

- [x] 2.1 Créer l'arborescence backend
  ```
  backend/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── config.py
  │   ├── api/
  │   │   ├── __init__.py
  │   │   └── auth.py
  │   ├── core/
  │   │   ├── __init__.py
  │   │   ├── database.py
  │   │   ├── security.py
  │   │   └── dependencies.py
  │   ├── models/
  │   │   └── __init__.py
  │   └── schemas/
  │       ├── __init__.py
  │       └── auth.py
  ├── requirements.txt
  ├── Dockerfile
  └── .env.example
  ```

- [x] 2.2 `requirements.txt` — dépendances initiales (bcrypt direct au lieu de passlib[bcrypt] pour compat bcrypt 5.x)
  - `fastapi`, `uvicorn[standard]`, `asyncpg`, `sqlalchemy[asyncio]`, `alembic`
  - `python-jose[cryptography]`, `bcrypt`, `python-multipart`
  - `pydantic-settings`, `sse-starlette`, `openai`, `pgvector`

- [x] 2.3 `app/config.py` — Settings via pydantic-settings
  - Charger depuis `.env` : `DATABASE_URL`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `JWT_SECRET`, `APP_URL`

- [x] 2.4 `app/core/database.py` — Connexion async PostgreSQL
  - Pool de connexions via `asyncpg` ou `SQLAlchemy async`
  - Fonction `get_db()` pour l'injection de dépendance FastAPI

- [x] 2.5 `app/core/security.py` — JWT + hashing
  - `hash_password(password)` → bcrypt
  - `verify_password(plain, hashed)` → bool
  - `create_access_token(user_id)` → JWT signé HS256
  - `decode_token(token)` → payload

- [x] 2.6 `app/core/dependencies.py` — Dépendances FastAPI
  - `get_current_user(token)` : décode le JWT, charge le user, vérifie `is_active`
  - `require_admin(user)` : vérifie `role == 'admin'`
  - Voir [05_api_endpoints.md](../05_api_endpoints.md#middleware-et-dépendances)

- [x] 2.7 `app/api/auth.py` — Endpoints d'authentification
  - `POST /api/auth/register` → crée user + retourne JWT
  - `POST /api/auth/login` → vérifie credentials + retourne JWT
  - `GET /api/auth/me` → retourne profil user connecté
  - Schemas Pydantic : `RegisterRequest`, `LoginRequest`, `TokenResponse`
  - Voir [05_api_endpoints.md](../05_api_endpoints.md#auth)

- [x] 2.8 `app/main.py` — Point d'entrée FastAPI
  - Inclure le router auth
  - CORS middleware (allow origins: `http://localhost:3000`)
  - Event startup : connexion BDD

- [x] 2.9 `Dockerfile` backend
  - `FROM python:3.12-slim`
  - `COPY requirements.txt` → `pip install`
  - `COPY app/ /app/app/`
  - `CMD uvicorn app.main:app --host 0.0.0.0 --port 8000`

- [x] 2.10 Tester : `docker compose up backend` → `POST /api/auth/register` fonctionne

### Comment

1. Créer les fichiers un par un en suivant l'arborescence
2. Commencer par `config.py` + `database.py` (connexion BDD)
3. Puis `security.py` (JWT + bcrypt)
4. Puis `dependencies.py` (injection auth)
5. Puis `auth.py` (routes register/login/me)
6. Puis `main.py` (assemble tout)
7. Tester avec `curl` ou Postman

---

## Étape 3 — Modèles BDD + migrations Alembic

**Fichiers concernés** : [02_modeles_donnees.md](../02_modeles_donnees.md) · [08_arborescence_projet.md](../08_arborescence_projet.md)

### À faire

- [x] 3.1 Initialiser Alembic
  - `alembic init migrations`
  - Configurer `env.py` pour utiliser `DATABASE_URL` depuis les settings
  - Configurer pour le mode async si SQLAlchemy async

- [x] 3.2 Créer les modèles SQLAlchemy dans `app/models/`
  - [x] `user.py` — table `users` (id UUID, email, password_hash, nom_complet, role, is_active)
  - [x] `entreprise.py` — table `entreprises` (id, user_id FK, nom, secteur, pays, ville, effectifs, chiffre_affaires, devise, profil_json JSONB)
  - [x] `conversation.py` — table `conversations` (id, entreprise_id FK, titre, timestamps)
  - [x] `message.py` — table `messages` (id, conversation_id FK, role, content, tool_calls_json JSONB) + index
  - [x] `skill.py` — table `skills` (id, nom UNIQUE, description, category, input_schema JSONB, handler_key, handler_code, is_active, version)
  - [x] `document.py` — tables `documents` + `doc_chunks` (avec colonne `vector(1024)` pour pgvector)
  - [x] `referentiel_esg.py` — table `referentiels_esg` (id, nom, code UNIQUE, institution, grille_json JSONB, is_active)
  - [x] `esg_score.py` — table `esg_scores` (id, entreprise_id FK, referentiel_id FK, scores E/S/G, details_json)
  - [x] `fonds_vert.py` — tables `fonds_verts` + `fonds_chunks` (avec referentiel_id FK)
  - [x] `carbon_footprint.py` — table `carbon_footprints` (id, entreprise_id FK, annee, sources, total_tco2e)
  - [x] `credit_score.py` — table `credit_scores` (scores solvabilité, impact vert, combiné, facteurs)
  - [x] `action_plan.py` — tables `action_plans` + `action_items`
  - [x] `notification.py` — table `notifications`
  - [x] `sector_benchmark.py` — table `sector_benchmarks`
  - [x] `report_template.py` — table `report_templates`
  - Tout le SQL de référence est dans [02_modeles_donnees.md](../02_modeles_donnees.md)

- [x] 3.3 Créer la première migration Alembic
  - `alembic revision --autogenerate -m "initial tables"`
  - Vérifier le fichier généré (pgvector extension, indexes HNSW)
  - Ajouter manuellement `CREATE EXTENSION IF NOT EXISTS vector` en haut de la migration

- [x] 3.4 Appliquer la migration
  - `alembic upgrade head`
  - Vérifier avec `\dt` dans psql que toutes les tables existent

### Comment

1. Utiliser SQLAlchemy 2.0 avec `DeclarativeBase` et `mapped_column`
2. Pour les colonnes `vector(1024)`, utiliser le package `pgvector` pour SQLAlchemy
3. S'inspirer des CREATE TABLE dans [02_modeles_donnees.md](../02_modeles_donnees.md) pour les types et contraintes
4. Un modèle par fichier, un `__init__.py` qui importe tout (nécessaire pour autogenerate Alembic)

---

## Étape 4 — Seed : skills builtin + référentiels ESG + fonds verts

**Fichiers concernés** : [03_systeme_skills.md](../03_systeme_skills.md) · [02_modeles_donnees.md](../02_modeles_donnees.md) · [08_arborescence_projet.md](../08_arborescence_projet.md)

### À faire

- [x] 4.1 Créer `app/seed/seed_skills.py`
  - Insérer les skills builtin dans la table `skills` :
    - `analyze_document`, `calculate_esg_score`, `list_referentiels`, `search_green_funds`
    - `calculate_carbon`, `generate_reduction_plan`, `simulate_funding`
    - `calculate_credit_score`, `get_sector_benchmark`, `manage_action_plan`
    - `generate_report_section`, `assemble_pdf`, `search_knowledge_base`
    - `get_company_profile`, `update_company_profile`
  - Pour chaque skill : nom, description (pour le LLM), category, input_schema (JSON Schema), handler_key (`builtin.xxx`)
  - Les descriptions et schemas sont dans [03_systeme_skills.md](../03_systeme_skills.md)

- [x] 4.2 Créer `data/referentiels_esg.json` + `app/seed/seed_referentiels.py`
  - 3 référentiels : BCEAO Finance Durable 2024, Green Climate Fund, IFC Standards
  - Chaque référentiel a sa `grille_json` complète (piliers, critères, poids, seuils)

- [x] 4.3 Créer `data/fonds_verts.json` + `app/seed/seed_fonds.py`
  - 5 fonds verts : BOAD, BAD, GCF, IFC, FAGACE — liés aux référentiels

- [x] 4.4 Créer `data/facteurs_emission.json`
  - 6 pays (CIV, SEN, CMR, MLI, BFA, GHA) avec facteurs électricité, diesel, transport, déchets

- [x] 4.5 Créer `data/sector_benchmarks.json` + `app/seed/seed_benchmarks.py`
  - 7 benchmarks : agriculture, énergie, recyclage, agroalimentaire, transport (CIV + SEN)

- [x] 4.6 Créer un script principal `app/seed/__main__.py`
  - `python -m app.seed` exécute tous les seeds dans l'ordre
  - Idempotent : vérifie l'existence avant insertion (0 doublons au 2e run)

- [x] 4.7 Exécuter le seed et vérifier en BDD (15 skills, 3 réf., 5 fonds, 7 benchmarks)

### Comment

1. Commencer par les skills (c'est le coeur du système)
2. Pour les référentiels, s'inspirer de l'exemple `grille_json` dans [02_modeles_donnees.md](../02_modeles_donnees.md#referentiels_esg-nouveau)
3. Pour les fonds verts, mettre des données réalistes (montants en USD/XOF, secteurs pertinents)
4. Le seed doit être rejouable sans erreur (idempotent)

---

## Étape 5 — Frontend : setup Vue.js + router + auth

**Fichiers concernés** : [06_frontend.md](../06_frontend.md) · [08_arborescence_projet.md](../08_arborescence_projet.md)

### À faire

- [x] 5.1 Initialiser le projet Vue.js (Vite + vue-ts, vue-router, pinia, tailwindcss v4, @tailwindcss/vite)
  - `npm create vite@latest frontend -- --template vue-ts`
  - Installer les dépendances : `vue-router`, `pinia`, `tailwindcss`, `@tailwindcss/vite`

- [x] 5.2 Configurer TailwindCSS v4 (plugin Vite, `@import "tailwindcss"` dans main.css)
  - Tailwind v4 : pas de `tailwind.config.js`, utilise `@tailwindcss/vite` plugin
  - `src/assets/styles/main.css` avec `@import "tailwindcss"`

- [x] 5.3 Configurer le router (`src/router/index.ts`)
  - 11 routes lazy-loaded + guard auth + guard admin
  - `/` → redirect `/chat`, `/login`, `/register`, `/chat`, `/chat/:conversationId`
  - `/dashboard`, `/documents`, `/carbon`, `/credit-score`, `/action-plan`
  - `/admin/*` : skills, referentiels, fonds, templates, stats (requiresAdmin)
  - Guard `beforeEach` : vérifie token localStorage + rôle admin via authStore

- [x] 5.4 Créer le store auth (`src/stores/auth.ts`)
  - Pinia composition API (setup store) avec `user`, `token`, `isAuthenticated`, `isAdmin`
  - Actions : `login`, `register`, `logout`, `fetchMe`, `init`
  - Token persisté dans `localStorage`, session restaurée au démarrage via `init()`

- [x] 5.5 Créer le composable API (`src/composables/useApi.ts`)
  - `get<T>`, `post<T>`, `put<T>`, `del<T>`, `upload<T>` (FormData)
  - Auto-injection Bearer token, gestion 401 → redirect login
  - Content-Type auto (JSON sauf FormData)

- [x] 5.6 Configurer le proxy Vite (`vite.config.ts`) — fait en même temps que 5.2
  - Proxy `/api` → `http://localhost:8000` (backend)

- [x] 5.7 Créer `LoginView.vue`
  - Formulaire email + password, loading state, gestion erreurs
  - Design emerald/green centré, redirection `/chat` après connexion

- [x] 5.8 Créer `RegisterView.vue`
  - Formulaire nom + email + password + confirmation, validation passwords match (≥6 chars)
  - Redirection `/chat` après inscription

- [x] 5.9 Créer le layout principal (`App.vue` + `AppSidebar.vue` + `AppHeader.vue`)
  - Sidebar dark (bg-gray-900) : 6 liens nav + section admin conditionnelle + user info + logout
  - Header : titre page dynamique + cloche notifications + avatar initiales
  - Layout conditionnel : pages auth sans sidebar, pages app avec sidebar

- [x] 5.10 Créer 15 vues placeholder (6 pages principales + 9 pages admin)
  - ChatView, DashboardView, DocumentsView, CarbonView, CreditScoreView, ActionPlanView
  - Admin : AdminLayout, SkillsList/Edit, ReferentielsList/Edit, FondsList/Edit, TemplatesList, Stats

- [x] 5.11 `Dockerfile` frontend + `nginx.conf`
  - Multi-stage : `node:20-alpine` (build) → `nginx:alpine` (serve port 3000)
  - nginx : SPA fallback (`try_files → /index.html`) + proxy `/api` → backend

- [x] 5.12 Tester le flow complet
  - `docker compose up` → 3 services (db, backend, frontend) UP
  - Register via API proxy : JWT + user retournés ✅
  - Login via API proxy : JWT + user retournés ✅
  - GET /me avec Bearer token : user data OK ✅
  - Test navigateur (agent-browser) : inscription → redirection → layout avec sidebar ✅
  - Navigation entre pages (Chat, Dashboard, etc.) : active-class sidebar OK ✅

### Comment

1. `npm create vite@latest` pour le scaffolding rapide
2. Installer Tailwind selon la doc officielle (PostCSS)
3. Router : définir les routes + `beforeEach` guard pour vérifier le token
4. Pinia store auth : le token va dans `localStorage`, rechargé au démarrage de l'app
5. Les pages de la Semaine 1 sont minimalistes : login, register, et le layout principal
6. Tout le reste (chat, dashboard, etc.) sera développé dans les semaines suivantes

---

## Récapitulatif Semaine 1

| # | Étape | Statut |
|---|-------|--------|
| 1 | Docker Compose + PostgreSQL + pgvector | ✅ |
| 2 | Backend FastAPI : config, database, auth | ✅ |
| 3 | Modèles BDD + migrations Alembic | ✅ |
| 4 | Seed : skills + référentiels + fonds | ✅ |
| 5 | Frontend : Vue.js + router + auth | ✅ |

**Critère de fin de semaine** : On peut lancer `docker compose up`, s'inscrire/se connecter, voir le layout principal, et la BDD contient toutes les tables + données initiales (skills, référentiels, fonds).

---

## Fichiers du plan à consulter pendant l'implémentation

| Fichier | Quand le consulter |
|---------|-------------------|
| [01_architecture_globale.md](../01_architecture_globale.md) | Vue d'ensemble, principes architecturaux, flux principal |
| [02_modeles_donnees.md](../02_modeles_donnees.md) | SQL de toutes les tables, types, contraintes, exemples JSON |
| [03_systeme_skills.md](../03_systeme_skills.md) | Descriptions des skills builtin pour le seed |
| [05_api_endpoints.md](../05_api_endpoints.md) | Code des endpoints auth, middleware, dépendances |
| [06_frontend.md](../06_frontend.md) | Structure pages, composants, stores, router |
| [08_arborescence_projet.md](../08_arborescence_projet.md) | Arborescence fichiers, docker-compose, .env |
