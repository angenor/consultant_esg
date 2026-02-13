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
- `models/` — 18 SQLAlchemy models (User, Entreprise, Conversation, Message, Document, DocChunk, Skill, ReferentielESG, ESGScore, FondsVert, FondsChunk, CarbonFootprint, CreditScore, ActionPlan, ActionItem, SectorBenchmark, ReportTemplate, Notification)
- `schemas/` — Pydantic request/response models
- `seed/` — data seeding scripts loading from `/data/*.json`

### Key design patterns
- **Dynamic skill registry:** Skills stored in DB with `handler_key` + `handler_code`, loaded at runtime for the LLM agent
- **RAG with pgvector:** DocChunk and FondsChunk tables hold 1024-dim embeddings with HNSW indexes for similarity search
- **Multi-referential ESG:** supports multiple ESG frameworks simultaneously (IFC, GRI, etc.)
- **SSE streaming:** planned for real-time LLM responses via `sse-starlette`

### Data flow
```
Frontend (Vue 3) → /api proxy → FastAPI → PostgreSQL + pgvector
                                       → OpenRouter (Claude LLM)
```

## Configuration

Environment variables in `.env` (see `.env.example`):
- `DB_PASSWORD` — PostgreSQL password
- `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` — LLM provider config
- `JWT_SECRET` — JWT signing secret
- `VOYAGE_API_KEY` — embeddings (optional)
- `OPENAI_API_KEY` — speech-to-text (optional)

## Implementation Status

Week 1 complete: Docker infrastructure, database schema (all 18 tables), auth endpoints, frontend routing/auth. Most views are stubs awaiting implementation. Implementation roadmap in `plan_implementation/` with weekly guides (`details_implementation/Semaine1-5.md`).


## Parallel Sub-agents Strategy

Use multiple sub-agents in parallel for efficiency:
- Search frontend + backend simultaneously
- Explore multiple files/folders at the same time
- Run tests + verifications in parallel after modifications
- **Avant de créer un nouveau composant** : Toujours lancer un sous-agent pour vérifier si un composant similaire existe déjà (rechercher par nom et par fonctionnalité). Évite les redondances et favorise la réutilisation.


## Auto-maintenance de ce fichier

Après chaque modification significative du projet, vérifier si CLAUDE.md reflète toujours l'état actuel et le mettre à jour si nécessaire.