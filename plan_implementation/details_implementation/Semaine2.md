# Semaine 2 — Agent Conversationnel

> **Objectif** : Le coeur du produit — l'utilisateur peut chatter avec l'agent IA qui appelle des skills dynamiquement, avec streaming en temps réel.

> **Prérequis** : Semaine 1 terminée (BDD, auth, seed skills en place)

---

## Étape 6 — SkillRegistry + handlers builtin basiques

**Fichiers concernés** : [03_systeme_skills.md](../03_systeme_skills.md) · [08_arborescence_projet.md](../08_arborescence_projet.md)

### À faire

- [x] 6.1 Créer `backend/app/skills/__init__.py`

- [x] 6.2 Créer `backend/app/skills/registry.py` — classe `SkillRegistry`
  - `__init__(db_session)` : stocke la session BDD + enregistre les builtins
  - `_register_builtins()` : mappe `handler_key` → fonctions Python importées depuis `handlers/`
  - `get_active_tools()` : charge les skills actifs depuis la table `skills`, retourne une liste de dicts `{name, description, input_schema}`
  - `execute_skill(skill_name, params, context)` : récupère le skill en BDD, dispatche vers builtin ou custom
  - `_execute_custom(code, params, context)` : exécution sandboxée du code Python custom
  - Code de référence complet dans [03_systeme_skills.md](../03_systeme_skills.md#architecture-du-skill-registry)

- [x] 6.3 Créer `backend/app/skills/validator.py`
  - `validate_skill_code(code)` → `(bool, str)` : vérifie les patterns interdits (`import os`, `exec(`, etc.)
  - Liste `FORBIDDEN_PATTERNS` depuis [03_systeme_skills.md](../03_systeme_skills.md#sécurité-des-skills-custom)

- [x] 6.4 Créer les handlers builtin basiques (versions minimales)
  - [x] `handlers/__init__.py` — importe tout
  - [x] `handlers/get_company_profile.py` — lit le profil entreprise depuis la BDD
  - [x] `handlers/update_company_profile.py` — met à jour `profil_json` de l'entreprise
  - [x] `handlers/list_referentiels.py` — liste les référentiels ESG actifs
  - [x] `handlers/search_knowledge_base.py` — placeholder (retourne un message "RAG pas encore implémenté")
  - Les autres handlers (analyze_document, calculate_esg_score, etc.) seront des stubs qui retournent `{"status": "not_implemented"}` pour l'instant → ✅ `handlers/stubs.py` créé

- [x] 6.5 Tester le registry en isolation — 18/18 tests passent
  - Charger les skills depuis la BDD (seed de la Semaine 1)
  - Vérifier que `get_active_tools()` retourne la bonne liste
  - Exécuter `get_company_profile` avec un `entreprise_id` de test

### Comment

1. Le `SkillRegistry` est le pont entre la BDD (définition des skills) et le code Python (exécution)
2. Commencer par les 2-3 handlers les plus simples (`get_company_profile`, `list_referentiels`)
3. Les autres handlers restent des stubs — ils seront développés en Semaine 3 et 4
4. Le code de référence est dans [03_systeme_skills.md](../03_systeme_skills.md)

---

## Étape 7 — AgentEngine (boucle agent + LLM API via OpenRouter)

**Fichiers concernés** : [04_agent_conversationnel.md](../04_agent_conversationnel.md) · [01_architecture_globale.md](../01_architecture_globale.md)

### À faire

- [x] 7.1 Créer `backend/app/agent/__init__.py`

- [x] 7.2 Créer `backend/app/agent/prompt_builder.py`
  - Fonction `build_system_prompt(entreprise, skills)` → str
  - 3 parties : identité/rôle fixe + contexte entreprise dynamique + liste des skills
  - Code de référence dans [04_agent_conversationnel.md](../04_agent_conversationnel.md#system-prompt-dynamique)

- [x] 7.3 Créer `backend/app/agent/engine.py` — classe `AgentEngine`
  - `__init__(db, skill_registry)` : instancie le client `AsyncOpenAI` pointé vers `LLM_BASE_URL` (OpenRouter)
  - `run(conversation_id, user_message, entreprise)` : boucle agent complète, yield des événements SSE
  - `_stream_llm(tools, messages)` : appel streaming au LLM, accumule les `tool_calls` fragmentés
  - `_load_history(conversation_id)` : charge les 20 derniers messages depuis la BDD
  - `_save_message(conv_id, role, content, tool_calls_json)` : sauvegarde en BDD
  - Code de référence complet dans [04_agent_conversationnel.md](../04_agent_conversationnel.md#boucle-agent)

- [x] 7.4 Boucle agent — logique détaillée
  - Construire les messages : `[system, ...history, user_message]`
  - Convertir les skills en format OpenAI tools (`type: "function"`)
  - Appeler le LLM en streaming
  - Si `tool_calls` → exécuter via `registry.execute_skill()` → ajouter le résultat en `role: "tool"` → relancer le LLM
  - Boucle max 10 tours (sécurité anti-boucle infinie)
  - Yield des événements : `text`, `skill_start`, `skill_result`, `done`, `error`

- [x] 7.5 Tester en isolation — 6/6 unit tests OK, 3 tests LLM skippés (clé API OpenRouter à configurer)
  - Appeler `engine.run()` avec un message simple ("Bonjour")
  - Vérifier que le LLM répond en streaming
  - Appeler avec un message qui devrait trigger un skill ("Quel est mon profil ?") → vérifier que `get_company_profile` est appelé

### Comment

1. Utiliser le SDK `openai` (AsyncOpenAI) avec `base_url` pointé vers OpenRouter
2. Headers requis par OpenRouter : `HTTP-Referer` + `X-Title`
3. Le streaming renvoie des chunks avec `delta.content` (texte) et `delta.tool_calls` (appels skills)
4. Les tool_calls arrivent fragmentés dans le stream — les accumuler avant de les exécuter
5. Tout le code de référence est dans [04_agent_conversationnel.md](../04_agent_conversationnel.md)

---

## Étape 8 — API /chat avec SSE streaming

**Fichiers concernés** : [05_api_endpoints.md](../05_api_endpoints.md#chat-endpoint-principal) · [04_agent_conversationnel.md](../04_agent_conversationnel.md#streaming-sse-vers-le-frontend)

### À faire

- [x] 8.1 Créer `backend/app/api/chat.py` — router `/api/chat`

- [x] 8.2 Endpoint `POST /api/chat/conversations`
  - Crée une nouvelle conversation liée à une entreprise
  - Body : `{ entreprise_id, titre? }`
  - Retourne la conversation créée

- [x] 8.3 Endpoint `GET /api/chat/conversations`
  - Liste les conversations de l'utilisateur (via l'entreprise liée au user)

- [x] 8.4 Endpoint `GET /api/chat/conversations/{id}`
  - Retourne l'historique complet d'une conversation (messages)

- [x] 8.5 Endpoint `POST /api/chat/conversations/{id}/message` — SSE streaming
  - Body : `{ message: string }`
  - Instancie `AgentEngine`, appelle `engine.run()`
  - Retourne un `EventSourceResponse` (sse-starlette)
  - Événements SSE : `text`, `skill_start`, `skill_result`, `done`, `error`
  - Voir [05_api_endpoints.md](../05_api_endpoints.md#chat-endpoint-principal)

- [x] 8.6 Endpoint `DELETE /api/chat/conversations/{id}`
  - Supprime une conversation et ses messages

- [x] 8.7 Créer les schemas Pydantic `backend/app/schemas/chat.py`
  - `CreateConversationRequest`, `SendMessageRequest`
  - `ConversationResponse`, `ConversationDetailResponse`, `MessageResponse`

- [x] 8.8 Ajouter le router chat dans `main.py`

- [x] 8.9 Créer `backend/app/api/entreprises.py` — CRUD basique entreprises
  - `POST /api/entreprises/` — créer une entreprise
  - `GET /api/entreprises/` — lister mes entreprises
  - `GET /api/entreprises/{id}` — détail
  - `PUT /api/entreprises/{id}` — modifier
  - Nécessaire pour que le chat puisse charger le contexte entreprise

- [x] 8.10 Tester le flux complet avec `curl` — tous endpoints OK, SSE stream OK (LLM API key à configurer)
  - Créer une entreprise → créer une conversation → envoyer un message → recevoir le stream SSE

### Comment

1. `sse-starlette` fournit `EventSourceResponse` qui gère le protocole SSE
2. L'endpoint `/message` est un `POST` qui retourne un stream (pas un WebSocket)
3. Chaque événement SSE a un `event:` (type) et un `data:` (JSON)
4. L'endpoint entreprises est simple mais nécessaire pour le contexte de l'agent

---

## Étape 9 — Frontend ChatView + composable useChat

**Fichiers concernés** : [06_frontend.md](../06_frontend.md#2-chatview-page-principale) · [06_frontend.md](../06_frontend.md#composable-sse-pour-le-chat)

### À faire

- [x] 9.1 Créer `src/composables/useChat.ts`
  - Gère la connexion SSE vers `/api/chat/conversations/{id}/message`
  - Parse les événements : `text` (ajoute au contenu), `skill_start` (indicateur), `skill_result` (terminé), `done`
  - État réactif : `messages`, `isLoading`, `currentSkills`
  - Fonctions : `sendMessage(text)`, `loadHistory()`
  - Code de référence dans [06_frontend.md](../06_frontend.md#composable-sse-pour-le-chat)

- [x] 9.2 Créer `src/stores/chat.ts` — Pinia store
  - Liste des conversations
  - Conversation active
  - Actions : `createConversation(entrepriseId)`, `loadConversations()`, `deleteConversation(id)`

- [x] 9.3 Créer `src/stores/entreprise.ts` — Pinia store
  - Entreprise active
  - Actions : `createEntreprise(data)`, `loadEntreprises()`, `selectEntreprise(id)`

- [x] 9.4 Créer les composants chat
  - [x] `src/components/chat/ChatContainer.vue` — conteneur principal, scroll auto
  - [x] `src/components/chat/MessageBubble.vue` — bulle message (user bleu à droite, assistant gris à gauche)
  - [x] `src/components/chat/MessageInput.vue` — zone de saisie + bouton envoyer
  - [x] `src/components/chat/SkillIndicator.vue` — "Analyse en cours..." / "Terminé"
  - [x] `src/components/chat/StreamingText.vue` — texte qui s'affiche progressivement (effet typewriter)
  - Maquettes dans [06_frontend.md](../06_frontend.md#2-chatview-page-principale)

- [x] 9.5 Créer `src/views/ChatView.vue`
  - Layout : sidebar conversations à gauche + zone chat à droite
  - Sélecteur d'entreprise si l'utilisateur en a plusieurs
  - Bouton "Nouvelle conversation"
  - Intègre `ChatContainer`, `MessageInput`, les composants chat

- [ ] 9.6 Tester le flow complet dans le navigateur
  - Se connecter → sélectionner/créer une entreprise → démarrer une conversation → envoyer un message → voir la réponse en streaming

### Comment

1. Le SSE se consomme avec `fetch()` + `ReadableStream` (pas besoin d'EventSource API car c'est un POST)
2. Buffer les lignes SSE (`event:` + `data:`) et parser le JSON
3. Le composant `MessageBubble` doit gérer l'état `isStreaming` (curseur clignotant pendant le stream)
4. `SkillIndicator` s'affiche dans la bulle assistant quand un skill est en cours

---

## Étape 10 — Profilage entreprise par conversation

**Fichiers concernés** : [04_agent_conversationnel.md](../04_agent_conversationnel.md) · [03_systeme_skills.md](../03_systeme_skills.md)

### À faire

- [ ] 10.1 Implémenter le handler `get_company_profile` complet
  - Charge l'entreprise depuis la BDD (infos + `profil_json`)
  - Retourne un dict structuré avec toutes les infos connues

- [ ] 10.2 Implémenter le handler `update_company_profile`
  - Met à jour `profil_json` de l'entreprise (merge, pas écrasement)
  - Exemples de clés : `pratiques_environnementales`, `certifications`, `objectifs_declares`, `risques_identifies`

- [ ] 10.3 Ajuster le system prompt
  - Ajouter une instruction : "Au fil de la conversation, enrichis le profil entreprise en utilisant `update_company_profile` quand tu apprends de nouvelles informations"
  - Vérifier que le prompt builder inclut bien les infos du profil dans le contexte

- [ ] 10.4 Tester le profilage
  - Démarrer une conversation, donner des infos sur l'entreprise ("on fait du tri sélectif", "on a 50 employés")
  - Vérifier que l'agent appelle `update_company_profile` automatiquement
  - Vérifier que les infos persistent dans `profil_json`

### Comment

1. Le LLM décide seul d'appeler `update_company_profile` — le system prompt l'y encourage
2. Le merge de `profil_json` se fait côté handler (pas d'écrasement des données existantes)
3. C'est la base de la personnalisation : plus l'entreprise discute, plus l'agent la connaît

---

## Récapitulatif Semaine 2

| # | Étape | Statut |
|---|-------|--------|
| 6 | SkillRegistry + handlers builtin basiques | ✅ |
| 7 | AgentEngine (boucle agent + LLM API) | ✅ |
| 8 | API /chat avec SSE streaming | ✅ |
| 9 | Frontend ChatView + composable useChat | ✅ |
| 10 | Profilage entreprise par conversation | ⬜ |

**Critère de fin de semaine** : Un utilisateur peut chatter avec l'agent IA en temps réel. L'agent répond en streaming, peut appeler des skills (au minimum `get_company_profile` et `list_referentiels`), et enrichit progressivement le profil de l'entreprise.

---

## Fichiers du plan à consulter

| Fichier | Quand le consulter |
|---------|-------------------|
| [03_systeme_skills.md](../03_systeme_skills.md) | Architecture SkillRegistry, handlers, validation, sécurité |
| [04_agent_conversationnel.md](../04_agent_conversationnel.md) | Prompt builder, boucle agent, streaming SSE, gestion contexte |
| [05_api_endpoints.md](../05_api_endpoints.md) | Endpoints chat, schemas, middleware |
| [06_frontend.md](../06_frontend.md) | ChatView, composable useChat, composants chat |
