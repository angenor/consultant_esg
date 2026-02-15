"""
Tests de l'AgentEngine et du prompt_builder.
Étape 7.5 :
  - Appeler engine.run() avec un message simple ("Bonjour")
  - Vérifier que le LLM répond en streaming
  - Appeler avec un message qui devrait trigger un skill
  - Tester le prompt_builder en isolation
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.agent.engine import AgentEngine
from app.agent.prompt_builder import build_system_prompt
from app.config import settings
from app.models.conversation import Conversation
from app.models.entreprise import Entreprise
from app.models.message import Message
from app.skills.registry import SkillRegistry


# ---- Fixtures ----


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def test_entreprise(db_session):
    result = await db_session.execute(text("SELECT id FROM users LIMIT 1"))
    user_row = result.first()
    if not user_row:
        pytest.skip("Aucun utilisateur en BDD")

    entreprise = Entreprise(
        user_id=user_row[0],
        nom="AgentTestCorp",
        secteur="agriculture",
        pays="Côte d'Ivoire",
        ville="Abidjan",
        effectifs=25,
        profil_json={"certifications": ["ISO 14001"]},
    )
    db_session.add(entreprise)
    await db_session.commit()
    await db_session.refresh(entreprise)
    yield entreprise
    await db_session.delete(entreprise)
    await db_session.commit()


@pytest_asyncio.fixture
async def test_conversation(db_session, test_entreprise):
    conv = Conversation(
        entreprise_id=test_entreprise.id,
        titre="Test conversation",
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)
    yield conv
    # Nettoyer les messages puis la conversation
    await db_session.execute(
        text("DELETE FROM messages WHERE conversation_id = :cid"),
        {"cid": str(conv.id)},
    )
    await db_session.delete(conv)
    await db_session.commit()


@pytest_asyncio.fixture
async def engine(db_session):
    registry = SkillRegistry(db_session)
    return AgentEngine(db_session, registry)


# ---- Tests du prompt_builder ----


class TestPromptBuilder:
    def test_build_without_entreprise(self):
        prompt = build_system_prompt(None, [])
        assert "ESG Mefali" in prompt
        assert "Ton rôle" in prompt

    def test_build_with_entreprise(self):
        entreprise = {
            "nom": "TestCorp",
            "secteur": "agriculture",
            "pays": "Côte d'Ivoire",
            "ville": "Abidjan",
            "effectifs": 50,
            "chiffre_affaires": 1000000,
            "devise": "XOF",
            "profil_json": {
                "certifications": ["ISO 14001"],
                "pratiques_environnementales": ["tri sélectif", "compostage"],
            },
        }
        prompt = build_system_prompt(entreprise, [])
        assert "TestCorp" in prompt
        assert "agriculture" in prompt
        assert "tri sélectif" in prompt
        assert "ISO 14001" in prompt

    def test_build_with_skills(self):
        skills = [
            {"name": "get_company_profile", "description": "Récupère le profil"},
            {"name": "list_referentiels", "description": "Liste les référentiels"},
        ]
        prompt = build_system_prompt(None, skills)
        assert "get_company_profile" in prompt
        assert "list_referentiels" in prompt

    def test_update_profile_instruction_in_prompt(self):
        prompt = build_system_prompt(None, [])
        assert "update_company_profile" in prompt


# ---- Tests de l'AgentEngine (nécessitent LLM_API_KEY) ----


def _has_llm_key() -> bool:
    return bool(settings.LLM_API_KEY)


@pytest.mark.skipif(not _has_llm_key(), reason="LLM_API_KEY non configurée")
class TestAgentEngine:
    """Tests nécessitant un accès au LLM via OpenRouter."""

    @pytest.mark.asyncio
    async def test_simple_greeting(self, engine, test_conversation):
        """Envoie 'Bonjour' et vérifie qu'on reçoit du texte en streaming."""
        events = []
        async for event in engine.run(
            conversation_id=str(test_conversation.id),
            user_message="Bonjour !",
        ):
            events.append(event)

        # Doit contenir au moins un événement text et un done
        event_types = [e["type"] for e in events]
        assert "text" in event_types, f"Pas de texte reçu. Événements: {event_types}"
        assert "done" in event_types

        # Le texte total ne doit pas être vide
        full_text = "".join(e["content"] for e in events if e["type"] == "text")
        assert len(full_text) > 0

    @pytest.mark.asyncio
    async def test_skill_trigger(self, engine, test_conversation, test_entreprise):
        """Envoie un message qui devrait trigger get_company_profile."""
        entreprise_dict = {
            "id": str(test_entreprise.id),
            "nom": test_entreprise.nom,
            "secteur": test_entreprise.secteur,
            "pays": test_entreprise.pays,
            "ville": test_entreprise.ville,
            "effectifs": test_entreprise.effectifs,
            "chiffre_affaires": None,
            "devise": "XOF",
            "profil_json": test_entreprise.profil_json,
        }

        events = []
        async for event in engine.run(
            conversation_id=str(test_conversation.id),
            user_message=f"Quel est le profil de mon entreprise ? L'ID est {test_entreprise.id}",
            entreprise=entreprise_dict,
        ):
            events.append(event)

        event_types = [e["type"] for e in events]
        assert "done" in event_types

        # On vérifie qu'il y a eu soit du texte, soit un appel skill
        has_text = "text" in event_types
        has_skill = "skill_start" in event_types
        assert has_text or has_skill, f"Ni texte ni skill. Événements: {event_types}"

    @pytest.mark.asyncio
    async def test_messages_saved_to_db(self, engine, test_conversation, db_session):
        """Vérifie que les messages sont sauvegardés en BDD."""
        async for _ in engine.run(
            conversation_id=str(test_conversation.id),
            user_message="Test de sauvegarde",
        ):
            pass

        from sqlalchemy import select, func

        result = await db_session.execute(
            select(func.count()).where(
                Message.conversation_id == test_conversation.id
            )
        )
        count = result.scalar()
        # Au moins 2 messages : user + assistant
        assert count >= 2


# ---- Tests unitaires (sans LLM) ----


class TestAgentEngineUnit:
    """Tests unitaires qui ne nécessitent pas de LLM."""

    @pytest.mark.asyncio
    async def test_load_empty_history(self, engine, test_conversation):
        """Vérifie que _load_history retourne une liste vide pour une nouvelle conversation."""
        history = await engine._load_history(str(test_conversation.id))
        assert history == []

    @pytest.mark.asyncio
    async def test_save_and_load_message(self, engine, test_conversation, db_session):
        """Sauvegarde un message puis le recharge."""
        await engine._save_message(
            str(test_conversation.id), "user", "Hello test"
        )
        history = await engine._load_history(str(test_conversation.id))
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello test"
