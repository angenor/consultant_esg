# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ESG Advisor AI — a conversational AI platform for sustainable finance targeting Francophone African SMEs. Combines ESG compliance analysis, green financing advice, and alternative credit scoring. Built with Vue 3 + FastAPI + PostgreSQL (pgvector) + Claude via OpenRouter.

## Commands

### Docker (full stack)
```bash
docker compose up -d          # Start all services (db, backend, frontend)
docker compose down           # Stop all services
docker compose logs -f backend  # Follow backend logs
```

### Frontend (from /frontend)
```bash
npm run dev       # Vite dev server on localhost:5173, proxies /api → localhost:8000
npm run build     # Type-check (vue-tsc) then build
npm run preview   # Preview production build
```

### Backend (from /backend)
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
python -m app.seed                           # Seed reference data
alembic upgrade head                         # Run migrations
alembic revision --autogenerate -m "msg"     # Generate new migration
```

### Database
- PostgreSQL 16 with pgvector, exposed on port **5433** (host) → 5432 (container)
- DB name: `esg_advisor`, user: `esg`

## Architecture

### Stack
- **Frontend:** Vue 3 (Composition API) + TypeScript + Pinia + TailwindCSS 4 + Vite 7
- **Backend:** FastAPI (async) + SQLAlchemy (async) + Alembic
- **Database:** PostgreSQL 16 + pgvector (HNSW indexes, Vector 1024)
- **LLM:** Claude via OpenRouter API (configurable in .env)

### Frontend structure (`frontend/src/`)
- `router/index.ts` — route definitions with auth guards and admin role checks
- `stores/auth.ts` — Pinia store: JWT in localStorage, login/register/logout
- `composables/useApi.ts` — fetch wrapper with auto JWT injection, 401 redirect
- `views/` — page components (Login, Register, Chat, Dashboard, Documents, Carbon, CreditScore, ActionPlan)
- `views/admin/` — admin CRUD views (Skills, Referentiels, Fonds, Templates, Stats)
- `components/common/` — AppHeader, AppSidebar

### Backend structure (`backend/app/`)
- `main.py` — FastAPI app with CORS, lifespan (DB check), health endpoint at `/api/health`
- `config.py` — Pydantic BaseSettings from `.env`
- `core/database.py` — async SQLAlchemy engine + session factory
- `core/security.py` — bcrypt hashing, JWT creation/verification (24h expiry)
- `core/dependencies.py` — `get_current_user()`, `require_admin()` dependencies
- `api/auth.py` — register, login, me endpoints under `/api/auth`
- `models/` — 20 SQLAlchemy models (User, Entreprise, Conversation, Message, Document, DocChunk, Skill, ReferentielESG, ESGScore, FondsVert, FondsChunk, CarbonFootprint, CreditScore, ActionPlan, ActionItem, SectorBenchmark, ReportTemplate, Notification, FundApplication, FundSiteConfig)
- `schemas/` — Pydantic request/response models
- `api/extension.py` — Chrome extension endpoints under `/api/extension` (fund-configs, applications, field-suggest, progress, fund-recommendations)
- `seed/` — data seeding scripts loading from `/data/*.json`

### Key design patterns
- **Dynamic skill registry:** Skills stored in DB with `handler_key` + `handler_code`, loaded at runtime for the LLM agent
- **RAG with pgvector:** DocChunk and FondsChunk tables hold 1024-dim embeddings with HNSW indexes for similarity search
- **Multi-referential ESG:** supports multiple ESG frameworks simultaneously (IFC, GRI, etc.)
- **SSE streaming:** planned for real-time LLM responses via `sse-starlette`

### Chrome Extension structure (`chrome-extension/`)
- **Manifest V3** extension with popup, side panel, service worker, content scripts, i18n (FR/EN)
- `_locales/` — fr/messages.json, en/messages.json (Chrome i18n with `default_locale: "fr"`)
- `src/shared/` — types.ts, constants.ts, api-client.ts, auth.ts, storage.ts, data-mapper.ts, i18n.ts
- `src/shared/stores/applications.ts` — reactive composable for candidature CRUD and progress tracking
- `src/popup/` — Vue 3 popup with LoginPanel, DashboardPanel, ApplicationCard, FundRecommendation, ApplicationDetail
- `src/sidepanel/` — Vue 3 step-by-step guide with components: NoFundDetected, ProgressBar, StepNavigator, StepContent (batch autofill), FieldHelper, DocChecklist, MiniChat
- `src/background/service-worker.ts` — message handling (12 message types), data sync, alarms (auth 30m, sync 5m, deadlines 6h), side panel opening
- `src/background/notifications.ts` — deadline alerts (J-30/J-7/J-1), inactive application reminders (3+ days), deduplication via chrome.storage.local
- `src/content/detector.ts` — FundDetector class: URL pattern matching, SPA observation (pushState/popstate), Shadow DOM detection banner
- `src/content/highlighter.ts` — FieldHighlighter class: colored field highlighting (green=auto, blue=AI, orange=manual), Shadow DOM tooltips
- `src/content/autofill.ts` — listens for AUTOFILL_FIELD/BATCH_AUTOFILL/HIGHLIGHT_FIELDS messages, fills form fields with event dispatching
- `src/content/batch-autofill.ts` — sequential multi-field filling with animation and error reporting
- `src/shared/data-mapper.ts` — DataMapper class: resolves company data paths with formatters (currency, date, percentage, case)
- `tests/` — vitest unit tests: data-mapper (13), auth (5), detector (9) = 27 tests total
- Build: `npm run build` from `chrome-extension/`, produces `dist/` + `esg-advisor-extension.zip`

### Data flow
```
Frontend (Vue 3) → /api proxy → FastAPI → PostgreSQL + pgvector
                                       → OpenRouter (Claude LLM)
Chrome Extension → /api/extension/* → FastAPI (same backend)
```

## Configuration

Environment variables in `.env` (see `.env.example`):
- `DB_PASSWORD` — PostgreSQL password
- `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` — LLM provider config
- `JWT_SECRET` — JWT signing secret
- `VOYAGE_API_KEY` — embeddings (optional)
- `REPLICATE_API_TOKEN` — speech-to-text Whisper via Replicate

## Implementation Status

Platform Week 1 complete: Docker infrastructure, database schema (all 18 tables), auth endpoints, frontend routing/auth. Most views are stubs awaiting implementation. Implementation roadmap in `plan_implementation/` with weekly guides (`details_implementation/Semaine1-5.md`).

Extension Week 1 complete: Chrome extension project initialized (Manifest V3 + Vite 7 + Vue 3 + TailwindCSS 4). Shared types/constants, API client with JWT, auth manager, storage manager, service worker, popup (login + dashboard), backend extension endpoints (fund-configs, applications CRUD, field-suggest, progress), FundApplication/FundSiteConfig models migrated, seed data for BOAD fund config.

Extension Week 2 complete: Content script FundDetector (URL pattern matching, SPA observation, Shadow DOM banner), FieldHighlighter (colored highlighting with tooltips), Side Panel guide (7 Vue components: NoFundDetected, ProgressBar, StepNavigator, StepContent, FieldHelper, DocChecklist, MiniChat), autofill integration (content script ↔ side panel communication), service worker updated with OPEN_SIDEPANEL and GET_FUND_CONFIGS handlers. Extension roadmap in `plan_implementation/details_implementation_extension/Semaine1-3.md`.

Extension Week 3 complete: DataMapper class with path resolution and formatters (currency, date, percentage, case), batch autofill with sequential animation, "Tout remplir" button in StepContent. Applications store (useApplications composable), ApplicationDetail popup component, auto-creation of candidature on fund detection, progress saving between sessions. Notifications system (deadlines J-30/J-7/J-1, inactive reminders, deduplication), 6h alarm cycle. i18n FR/EN (_locales, chrome.i18n.getMessage, components updated). Unit tests (27 tests: DataMapper 13, auth 5, detector 9). Privacy policy FR/EN, production build + zip ready for Chrome Web Store.

## Parallel Sub-agents Strategy

Use multiple sub-agents in parallel for efficiency:
- Search frontend + backend simultaneously
- Explore multiple files/folders at the same time
- Run tests + verifications in parallel after modifications
- **Avant de créer un nouveau composant** : Toujours lancer un sous-agent pour vérifier si un composant similaire existe déjà (rechercher par nom et par fonctionnalité). Évite les redondances et favorise la réutilisation.


## Auto-maintenance de ce fichier

Après chaque modification significative du projet, vérifier si CLAUDE.md reflète toujours l'état actuel et le mettre à jour si nécessaire.


## user de test
logein: test@test.com
mot de passe: test1234