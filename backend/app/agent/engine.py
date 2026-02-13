"""
Moteur agent utilisant le SDK OpenAI pointé vers OpenRouter.
Boucle agent complète avec streaming SSE et appels de skills.

Changer de modèle = changer LLM_MODEL dans .env
Changer de provider = changer LLM_BASE_URL dans .env
"""

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.prompt_builder import build_system_prompt
from app.config import settings
from app.models.message import Message
from app.skills.registry import SkillRegistry

logger = logging.getLogger(__name__)

MAX_AGENT_TURNS = 10


class AgentEngine:
    """
    Moteur agent : reçoit un message utilisateur, appelle le LLM en streaming,
    exécute les skills demandés, et yield des événements SSE.
    """

    def __init__(self, db: AsyncSession, skill_registry: SkillRegistry):
        self.client = AsyncOpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
            default_headers={
                "HTTP-Referer": settings.APP_URL,
                "X-Title": "ESG Advisor AI",
            },
        )
        self.model = settings.LLM_MODEL
        self.db = db
        self.registry = skill_registry

    async def run(
        self,
        conversation_id: str,
        user_message: str,
        entreprise: dict | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Boucle agent complète. Yield des événements SSE :
        - text         : fragment de texte à afficher
        - skill_start  : un skill va être exécuté
        - skill_result : résultat d'un skill
        - done         : fin du streaming
        - error        : erreur
        """
        try:
            # 1. Charger l'historique
            history = await self._load_history(conversation_id)

            # 2. Charger les skills actifs
            tools = await self.registry.get_active_tools()

            # 3. Construire le system prompt
            system_prompt = build_system_prompt(entreprise, tools)

            # 4. Assembler les messages
            messages = [
                {"role": "system", "content": system_prompt},
                *history,
                {"role": "user", "content": user_message},
            ]

            # 5. Sauvegarder le message utilisateur
            await self._save_message(conversation_id, "user", user_message)

            # 6. Boucle agent
            full_response = ""
            tool_calls_log: list[dict] = []

            for turn in range(MAX_AGENT_TURNS):
                tool_calls_in_turn: list[dict] = []

                # Stream la réponse du LLM
                async for event in self._stream_llm(tools, messages):
                    if event["type"] == "text_delta":
                        full_response += event["text"]
                        yield {"type": "text", "content": event["text"]}
                    elif event["type"] == "tool_call":
                        tool_calls_in_turn.append(event["tool_call"])

                # Pas d'appel de skill → fin de la boucle
                if not tool_calls_in_turn:
                    break

                # Ajouter la réponse assistant avec les tool_calls
                messages.append(
                    {
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
                    }
                )

                # Exécuter chaque skill demandé
                for tc in tool_calls_in_turn:
                    try:
                        tc_params = json.loads(tc["arguments"])
                    except json.JSONDecodeError:
                        tc_params = {}

                    yield {
                        "type": "skill_start",
                        "skill": tc["name"],
                        "params": tc_params,
                    }

                    context = {
                        "db": self.db,
                        "entreprise_id": entreprise.get("id") if entreprise else None,
                    }
                    result = await self.registry.execute_skill(
                        tc["name"], tc_params, context
                    )

                    yield {
                        "type": "skill_result",
                        "skill": tc["name"],
                        "result": _truncate(json.dumps(result, ensure_ascii=False, default=str), 200),
                    }

                    # Ajouter le résultat au format OpenAI tool message
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": json.dumps(result, ensure_ascii=False, default=str),
                        }
                    )

                    tool_calls_log.append({"name": tc["name"], "input": tc_params})

                # Reset pour le prochain tour
                full_response = ""

            # 7. Sauvegarder la réponse complète
            await self._save_message(
                conversation_id,
                "assistant",
                full_response,
                tool_calls_json=tool_calls_log if tool_calls_log else None,
            )

            yield {"type": "done"}

        except Exception as e:
            logger.exception("Erreur dans la boucle agent")
            yield {"type": "error", "content": str(e)}

    async def _stream_llm(
        self, tools: list[dict], messages: list[dict]
    ) -> AsyncGenerator[dict, None]:
        """
        Stream la réponse du LLM via le SDK OpenAI (compatible OpenRouter).
        Accumule les tool_calls fragmentés et les émet à la fin du stream.
        """
        # Convertir les skills au format OpenAI tools
        openai_tools = (
            [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["input_schema"],
                    },
                }
                for t in tools
            ]
            if tools
            else None
        )
        # Matérialiser le générateur en liste (le SDK attend une liste)
        openai_tools = list(openai_tools) if openai_tools else None

        stream = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=4096,
            messages=messages,
            tools=openai_tools,
            stream=True,
        )

        # Accumuler les tool_calls fragmentés
        tool_calls_acc: dict[int, dict] = {}

        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

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
        """Charge les 20 derniers messages de la conversation."""
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(20)
        )
        messages = result.scalars().all()

        # Inverser pour l'ordre chronologique
        return [
            {"role": m.role, "content": m.content}
            for m in reversed(messages)
        ]

    async def _save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        tool_calls_json: list[dict] | None = None,
    ):
        """Sauvegarde un message en BDD."""
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content or "",
            tool_calls_json=tool_calls_json,
        )
        self.db.add(msg)
        await self.db.commit()


def _truncate(text: str, max_len: int) -> str:
    """Tronque un texte à max_len caractères."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
