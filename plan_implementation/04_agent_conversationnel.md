# 04 - Agent Conversationnel

## System Prompt Dynamique

Le system prompt est **assemblé** à chaque requête. Il n'est pas statique.

```python
# === backend/app/agent/prompt_builder.py ===

def build_system_prompt(entreprise: dict | None, skills: list[dict]) -> str:
    """Construit le system prompt en fonction du contexte."""

    # --- Partie fixe : identité et rôle ---
    prompt = """Tu es ESG Mefali, un conseiller expert en finance durable et conformité ESG
pour les PME africaines francophones.

## Ton rôle
- Aider les PME à comprendre et améliorer leur conformité ESG
- Les guider vers les financements verts adaptés à leur profil
- Calculer leur empreinte carbone de manière simplifiée
- Générer des rapports et dossiers de candidature professionnels

## Ton style
- Tu parles en français courant, professionnel mais accessible
- Tu utilises des exemples concrets adaptés au contexte africain
- Tu poses des questions pour mieux comprendre avant de recommander
- Tu expliques toujours le "pourquoi" de tes recommandations

## Règles importantes
- Si tu as besoin d'informations sur l'entreprise, utilise le skill get_company_profile
- Si l'utilisateur mentionne un document uploadé, utilise analyze_document
- Avant de calculer un score, assure-toi d'avoir suffisamment de données
- Ne génère un rapport que si l'utilisateur le demande explicitement
- Si tu ne sais pas, dis-le plutôt que d'inventer
"""

    # --- Partie dynamique : contexte entreprise ---
    if entreprise:
        prompt += f"""
## Entreprise actuelle
- Nom : {entreprise['nom']}
- Secteur : {entreprise['secteur']}
- Pays : {entreprise['pays']}, Ville : {entreprise['ville']}
- Effectifs : {entreprise['effectifs']}
- CA : {entreprise['chiffre_affaires']} {entreprise['devise']}
"""
        if entreprise.get("profil_json"):
            profil = entreprise["profil_json"]
            if profil.get("pratiques_environnementales"):
                prompt += f"- Pratiques vertes connues : {', '.join(profil['pratiques_environnementales'])}\n"
            if profil.get("objectifs_declares"):
                prompt += f"- Objectifs déclarés : {', '.join(profil['objectifs_declares'])}\n"

    # --- Partie dynamique : skills disponibles ---
    prompt += """
## Tes outils (skills)
Tu disposes des outils suivants. Utilise-les quand c'est pertinent :
"""
    for skill in skills:
        prompt += f"- **{skill['name']}** : {skill['description']}\n"

    return prompt
```

> **Note architecture** : Le system prompt est passé en tant que message `role: "system"` au format OpenAI,
> ce qui est compatible avec tous les modèles via OpenRouter (Claude, GPT, Llama, Mistral, etc.).

## Boucle Agent

```python
# === backend/app/agent/engine.py ===

from openai import AsyncOpenAI
from app.skills.registry import SkillRegistry
from app.config import settings

class AgentEngine:
    """
    Moteur agent utilisant le SDK OpenAI pointé vers OpenRouter.
    Changer de modèle = changer LLM_MODEL dans .env
    Changer de provider = changer LLM_BASE_URL dans .env

    Exemples de configuration :
      - OpenRouter + Claude : LLM_BASE_URL=https://openrouter.ai/api/v1  LLM_MODEL=anthropic/claude-sonnet-4-5-20250514
      - OpenRouter + GPT-4o : LLM_BASE_URL=https://openrouter.ai/api/v1  LLM_MODEL=openai/gpt-4o
      - OpenRouter + Llama  : LLM_BASE_URL=https://openrouter.ai/api/v1  LLM_MODEL=meta-llama/llama-3.1-70b-instruct
      - Anthropic direct    : LLM_BASE_URL=https://api.anthropic.com/v1  LLM_MODEL=claude-sonnet-4-5-20250514
      - OpenAI direct       : LLM_BASE_URL=https://api.openai.com/v1    LLM_MODEL=gpt-4o
    """

    def __init__(self, db, skill_registry: SkillRegistry):
        self.client = AsyncOpenAI(
            base_url=settings.LLM_BASE_URL,       # ex: "https://openrouter.ai/api/v1"
            api_key=settings.LLM_API_KEY,          # ex: clé OpenRouter
            default_headers={
                "HTTP-Referer": settings.APP_URL,  # Requis par OpenRouter
                "X-Title": "ESG Advisor AI",       # Identifiant app sur OpenRouter
            },
        )
        self.model = settings.LLM_MODEL            # ex: "anthropic/claude-sonnet-4-5-20250514"
        self.db = db
        self.registry = skill_registry

    async def run(
        self,
        conversation_id: str,
        user_message: str,
        entreprise: dict | None = None,
    ):
        """
        Boucle agent complète.
        Yield des événements SSE au fur et à mesure.
        """

        # 1. Charger l'historique
        history = await self._load_history(conversation_id)

        # 2. Charger les skills actifs (format OpenAI tools)
        tools = await self.registry.get_active_tools()

        # 3. Construire le system prompt
        system_prompt = build_system_prompt(entreprise, tools)

        # 4. Ajouter le message utilisateur
        messages = [
            {"role": "system", "content": system_prompt},
        ] + history + [
            {"role": "user", "content": user_message},
        ]

        # 5. Sauvegarder le message utilisateur en BDD
        await self._save_message(conversation_id, "user", user_message)

        # 6. Boucle agent
        max_turns = 10  # Sécurité anti-boucle infinie
        full_response = ""
        tool_calls_log = []

        for turn in range(max_turns):

            # Appel LLM avec streaming (format OpenAI)
            tool_calls_in_turn = []
            async for event in self._stream_llm(tools, messages):
                if event["type"] == "text_delta":
                    full_response += event["text"]
                    yield {"type": "text", "content": event["text"]}
                elif event["type"] == "tool_call":
                    tool_calls_in_turn.append(event["tool_call"])

            # Pas d'appel de skill → fin de la boucle
            if not tool_calls_in_turn:
                break

            # Exécuter les skills demandés
            yield {"type": "status", "content": "Exécution des outils..."}

            # Ajouter la réponse assistant avec les tool_calls
            messages.append({
                "role": "assistant",
                "content": full_response if full_response else None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["arguments"],
                        },
                    }
                    for tc in tool_calls_in_turn
                ],
            })

            for tc in tool_calls_in_turn:
                yield {
                    "type": "skill_start",
                    "skill": tc["name"],
                    "params": json.loads(tc["arguments"]),
                }

                # Exécuter le skill via le registry
                context = {
                    "db": self.db,
                    "rag": self.rag,
                    "entreprise_id": entreprise["id"] if entreprise else None,
                }
                result = await self.registry.execute_skill(
                    tc["name"], json.loads(tc["arguments"]), context
                )

                yield {
                    "type": "skill_result",
                    "skill": tc["name"],
                    "result_preview": _truncate(str(result), 200),
                }

                # Ajouter le résultat au format OpenAI tool message
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result, ensure_ascii=False),
                })

                tool_calls_log.append({"name": tc["name"], "input": json.loads(tc["arguments"])})

            # Reset full_response pour le prochain tour de boucle
            full_response = ""

        # 7. Sauvegarder la réponse complète
        await self._save_message(
            conversation_id, "assistant", full_response,
            tool_calls_json=json.dumps(tool_calls_log) if tool_calls_log else None
        )

        yield {"type": "done"}

    async def _stream_llm(self, tools, messages):
        """
        Stream la réponse du LLM via le SDK OpenAI (compatible OpenRouter).
        Format unifié : fonctionne avec Claude, GPT, Llama, Mistral, etc.
        """
        # Convertir les skills au format OpenAI tools
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
            for t in tools
        ] if tools else None

        stream = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=4096,
            messages=messages,
            tools=openai_tools,
            stream=True,
        )

        # Accumuler les tool_calls fragmentés dans le stream
        tool_calls_acc: dict[int, dict] = {}

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            # Texte
            if delta.content:
                yield {"type": "text_delta", "text": delta.content}

            # Tool calls (arrivent en fragments dans le stream)
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls_acc:
                        tool_calls_acc[idx] = {
                            "id": tc_delta.id or "",
                            "name": "",
                            "arguments": "",
                        }
                    if tc_delta.id:
                        tool_calls_acc[idx]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_calls_acc[idx]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_calls_acc[idx]["arguments"] += tc_delta.function.arguments

        # Émettre les tool_calls complètes à la fin du stream
        for idx in sorted(tool_calls_acc.keys()):
            yield {"type": "tool_call", "tool_call": tool_calls_acc[idx]}

    async def _load_history(self, conversation_id: str) -> list[dict]:
        """Charge les N derniers messages de la conversation."""
        rows = await self.db.fetch_all(
            """SELECT role, content FROM messages
               WHERE conversation_id = $1
               ORDER BY created_at DESC
               LIMIT 20""",  # Garde les 20 derniers messages (10 échanges)
            conversation_id,
        )
        # Inverser pour ordre chronologique
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    async def _save_message(self, conv_id, role, content, tool_calls_json=None):
        await self.db.execute(
            """INSERT INTO messages (conversation_id, role, content, tool_calls_json)
               VALUES ($1, $2, $3, $4)""",
            conv_id, role, content, tool_calls_json,
        )
```

## Gestion du Contexte (fenêtre limitée)

```
┌────────────────────────────────────────────────────┐
│              Fenêtre de contexte LLM                  │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  System Prompt (~1500 tokens)                 │   │
│  │  = rôle + entreprise + liste skills           │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  Historique conversation (20 derniers msgs)    │   │
│  │  = ~4000-8000 tokens                          │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  Tool results (résultats des skills)          │   │
│  │  = variable, ~2000-5000 tokens par tour       │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  Message utilisateur actuel                    │   │
│  │  = ~100-500 tokens                            │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  TOTAL : ~8000-15000 tokens par requête              │
│  Bien dans la limite des ~200K                       │
│                                                      │
│  Budget restant pour la réponse : ~4000 tokens       │
└────────────────────────────────────────────────────┘
```

### Stratégies pour rester dans les limites

| Stratégie | Détail |
|-----------|--------|
| **Historique limité** | 20 derniers messages, pas toute la conversation |
| **Résumé de contexte** | Si conversation longue, résumer les anciens échanges |
| **RAG ciblé** | Les skills ne retournent que les données pertinentes |
| **Réponses tronquées** | Les tool_result sont limités en taille |
| **Profil entreprise** | Résumé compact dans le system prompt |

```python
# Résumé automatique si la conversation est longue
async def summarize_old_messages(conversation_id: str, db, client: AsyncOpenAI) -> str:
    """Si > 20 messages, résumer les anciens."""
    old_messages = await db.fetch_all(
        """SELECT role, content FROM messages
           WHERE conversation_id = $1
           ORDER BY created_at ASC
           OFFSET 0 LIMIT (
               (SELECT COUNT(*) FROM messages WHERE conversation_id = $1) - 20
           )""",
        conversation_id,
    )

    if not old_messages:
        return None

    text = "\n".join(f"{m['role']}: {m['content'][:200]}" for m in old_messages)

    response = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"Résume cette conversation en 3-10 points clés :\n{text}"
        }]
    )
    return response.choices[0].message.content
```

## Streaming SSE vers le Frontend

```python
# === backend/app/api/chat.py ===

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

router = APIRouter()

@router.post("/chat/{conversation_id}/message")
async def send_message(conversation_id: str, body: ChatMessageRequest):
    """Envoie un message et stream la réponse."""

    async def event_generator():
        async for event in agent_engine.run(
            conversation_id=conversation_id,
            user_message=body.message,
            entreprise=body.entreprise,
        ):
            yield {
                "event": event["type"],
                "data": json.dumps(event, ensure_ascii=False),
            }

    return EventSourceResponse(event_generator())
```

Le frontend reçoit les événements au fur et à mesure :
```
event: text          → afficher le texte progressivement
event: skill_start   → afficher "Analyse du document en cours..."
event: skill_result  → afficher un indicateur de progression
event: done          → fin du streaming
```
