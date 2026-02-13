# 01 - Architecture Globale

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vue.js 3)                       │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌────────────────┐  │
│  │   Chat    │  │Dashboard │  │  Upload   │  │ Admin Skills   │  │
│  │Interface  │  │Entreprise│  │ Documents │  │   (CRUD)       │  │
│  └─────┬────┘  └────┬─────┘  └─────┬─────┘  └───────┬────────┘  │
│        └─────────────┴──────────────┴────────────────┘           │
│                              │ API REST + WebSocket (SSE)        │
└──────────────────────────────┼───────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────┐
│                        BACKEND (FastAPI)                          │
│                              │                                    │
│  ┌───────────────────────────▼──────────────────────────────┐    │
│  │                    API Gateway (Routers)                   │    │
│  │  /auth  /chat  /documents  /reports  /admin/skills        │    │
│  └───────────────────────────┬──────────────────────────────┘    │
│                              │                                    │
│  ┌───────────────────────────▼──────────────────────────────┐    │
│  │                  AGENT ENGINE (cœur)                       │    │
│  │                                                            │    │
│  │  ┌─────────────┐    ┌──────────────────────────────────┐  │    │
│  │  │ Agent Loop   │───▶│   Skill Registry (dynamique)    │  │    │
│  │  │ (LLM API    │    │                                  │  │    │
│  │  │  OpenRouter) │    │  Skills chargés depuis la BDD :  │  │    │
│  │  │ system_prompt│    │  ┌────────────────────────────┐  │  │    │
│  │  │ + tools      │    │  │ analyze_document           │  │  │    │
│  │  │ + messages   │    │  │ calculate_esg_score        │  │  │    │
│  │  │              │    │  │ search_green_funds         │  │  │    │
│  │  │              │◀───│  │ calculate_carbon           │  │  │    │
│  │  │              │    │  │ generate_report_section    │  │  │    │
│  │  │              │    │  │ assemble_pdf               │  │  │    │
│  │  │              │    │  │ ... (ajoutés par l'admin)  │  │  │    │
│  │  └─────────────┘    └──────────────────────────────────┘  │    │
│  └───────────────────────────────────────────────────────────┘    │
│                              │                                    │
│  ┌───────────────┐  ┌───────▼───────┐  ┌──────────────────────┐  │
│  │  RAG Engine   │  │ Skill Runner  │  │  Report Generator    │  │
│  │  (pgvector)   │  │ (exécute le   │  │  (Jinja2+WeasyPrint) │  │
│  │               │  │  code Python  │  │                      │  │
│  │  - chunking   │  │  du skill)    │  │  - templates HTML    │  │
│  │  - embedding  │  │               │  │  - charts matplotlib │  │
│  │  - search     │  │               │  │  - PDF output        │  │
│  └───────┬───────┘  └───────┬───────┘  └──────────┬───────────┘  │
│          └──────────────────┼─────────────────────┘              │
│                              │                                    │
└──────────────────────────────┼───────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────┐
│                         DONNÉES                                   │
│                              │                                    │
│  ┌──────────────────┐  ┌────▼──────────┐  ┌───────────────────┐  │
│  │   PostgreSQL      │  │  Stockage     │  │  LLM API          │  │
│  │   + pgvector      │  │  Local.       │  │  (via OpenRouter)  │  │
│  │                   │  │               │  │                   │  │
│  │ - users           │  │ - documents   │  │ - chat/completions│  │
│  │ - entreprises     │  │ - rapports    │  │ - tool_use        │  │
│  │ - conversations   │  │ - images      │  │                   │  │
│  │ - skills (config) │  │               │  │ Modèle configurable│  │
│  │ - fonds_verts     │  │               │  │ (Claude, GPT, etc)│  │
│  │ - scores          │  │               │  │                   │  │
│  │ - doc_chunks      │  │               │  │                   │  │
│  └──────────────────┘  └───────────────┘  └───────────────────┘  │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Flux Principal : Message Utilisateur → Réponse

```
1. Utilisateur envoie un message via le chat
   │
2. POST /api/chat/message  (ou WebSocket)
   │
3. Backend charge :
   │  a. Historique conversation (BDD)
   │  b. Profil entreprise (BDD)
   │  c. Skills actifs (BDD → Skill Registry)
   │  d. System prompt construit dynamiquement
   │
4. Appel LLM API (via OpenRouter, format OpenAI) avec :
   │  - system: prompt système + contexte entreprise
   │  - tools: skills actifs convertis en format OpenAI tools
   │  - messages: historique conversation
   │
5. Le LLM répond :
   │
   ├─► finish_reason = "stop"
   │   → Réponse textuelle directe → renvoyée au frontend
   │
   └─► finish_reason = "tool_calls"
       → Le LLM veut utiliser un skill
       │
       6. Skill Runner exécute le skill :
       │   - Lit la config du skill en BDD
       │   - Exécute la fonction Python associée
       │   - Retourne le résultat
       │
       7. Résultat renvoyé au LLM (tool result message)
       │
       8. Retour à l'étape 5 (boucle agent)
          → Jusqu'à finish_reason = "stop"
```

## Principes Architecturaux

### 1. Skills = Source de Vérité en BDD
Les skills ne sont PAS codés en dur. Ils sont stockés en base de données avec :
- Leur définition (nom, description, paramètres JSON Schema)
- Leur code d'exécution Python (ou référence à une fonction)
- Leur statut (actif/inactif)
- Leurs permissions

L'admin peut les créer, modifier, activer/désactiver depuis l'interface.

### 2. System Prompt Dynamique
Le system prompt est construit à chaque requête en assemblant :
- Un prompt de base (rôle du conseiller ESG)
- Le contexte entreprise (si connecté)
- Les instructions spécifiques aux skills actifs

### 3. LLM Interchangeable via OpenRouter
Le backend utilise le SDK OpenAI pointé vers **OpenRouter** (`base_url = "https://openrouter.ai/api/v1"`).
Changer de modèle = changer une variable d'env (`LLM_MODEL`), aucune modification de code.
Modèle par défaut : `anthropic/claude-sonnet-4-5-20250514` via OpenRouter.

### 4. Streaming SSE
Les réponses longues du LLM sont streamées au frontend via Server-Sent Events (SSE) pour une UX réactive.

### 5. Sécurité des Skills
Les skills exécutent du code Python. On utilise un système de fonctions enregistrées (pas d'eval/exec arbitraire) avec validation des entrées/sorties.

### 6. Support Vocal (Speech-to-Text)
Le chat accepte des messages audio en plus du texte. Le flux est :
1. L'utilisateur enregistre un message vocal depuis le frontend (MediaRecorder API)
2. Le fichier audio est envoyé à `POST /api/chat/conversations/{id}/audio`
3. Le backend transcrit l'audio via un service STT (Whisper API ou Google Cloud Speech)
4. Le texte transcrit est injecté dans la boucle agent comme un message texte classique
5. La réponse reste en texte (pas de TTS pour le MVP)

### 7. Système de Notifications
Un système de notifications internes gère :
- Les rappels d'actions planifiées (échéances du plan d'action)
- Les alertes sur les nouveaux appels à projets / fonds verts
- Les notifications de progression (score amélioré, action complétée)

Les notifications sont stockées en BDD et consultables via le frontend (icône cloche dans le header).

### 8. Skills additionnels (non listés dans le diagramme ci-dessus)
En plus des skills du diagramme, le registry contient aussi :
- `generate_reduction_plan` — génère un plan de réduction carbone priorisé
- `simulate_funding` — simule le montant éligible, ROI vert et timeline
- `calculate_credit_score` — scoring crédit vert alternatif (Module 5)
- `get_sector_benchmark` — récupère les moyennes sectorielles pour comparaison
- `manage_action_plan` — crée/met à jour le plan d'action et ses items
