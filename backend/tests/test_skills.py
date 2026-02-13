"""
Tests du SkillRegistry et des handlers builtin.
Exécute les vérifications demandées à l'étape 6.5 :
  - Charger les skills depuis la BDD (seed de la Semaine 1)
  - Vérifier que get_active_tools() retourne la bonne liste
  - Exécuter get_company_profile avec un entreprise_id de test
  - Valider le validator de skills custom
"""

import asyncio
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core.database import Base
from app.models.entreprise import Entreprise
from app.models.referentiel_esg import ReferentielESG
from app.models.skill import Skill
from app.skills.registry import SkillRegistry
from app.skills.validator import validate_skill_code


# ---- Fixtures ----

@pytest_asyncio.fixture
async def db_session():
    """Crée une session BDD de test (utilise la vraie BDD)."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def registry(db_session):
    """Instancie un SkillRegistry avec la session de test."""
    return SkillRegistry(db_session)


@pytest_asyncio.fixture
async def test_entreprise(db_session):
    """Crée une entreprise de test temporaire."""
    # Récupérer un user existant pour le FK
    result = await db_session.execute(text("SELECT id FROM users LIMIT 1"))
    user_row = result.first()
    if not user_row:
        pytest.skip("Aucun utilisateur en BDD — lancez le seed d'abord")

    entreprise = Entreprise(
        user_id=user_row[0],
        nom="TestCorp ESG",
        secteur="agriculture",
        pays="Côte d'Ivoire",
        ville="Abidjan",
        effectifs=50,
        description="Entreprise de test pour les skills",
        profil_json={"certifications": ["ISO 14001"], "pratiques_vertes": ["tri sélectif"]},
    )
    db_session.add(entreprise)
    await db_session.commit()
    await db_session.refresh(entreprise)
    yield entreprise
    # Cleanup
    await db_session.delete(entreprise)
    await db_session.commit()


# ---- Tests ----

class TestSkillRegistry:
    """Tests du SkillRegistry."""

    @pytest.mark.asyncio
    async def test_get_active_tools_returns_skills(self, registry):
        """Vérifie que get_active_tools() retourne les skills seedés."""
        tools = await registry.get_active_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0, "Aucun skill actif trouvé — avez-vous lancé le seed ?"

        # Vérifier la structure de chaque tool
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool

        # Vérifier que les skills clés sont présents
        tool_names = {t["name"] for t in tools}
        assert "get_company_profile" in tool_names
        assert "list_referentiels" in tool_names
        assert "update_company_profile" in tool_names

    @pytest.mark.asyncio
    async def test_get_active_tools_has_15_builtin(self, registry):
        """Vérifie que tous les 15 skills builtin sont chargés."""
        tools = await registry.get_active_tools()
        assert len(tools) == 15, f"Attendu 15 skills, trouvé {len(tools)}"

    @pytest.mark.asyncio
    async def test_execute_get_company_profile(self, registry, test_entreprise, db_session):
        """Exécute get_company_profile et vérifie le résultat."""
        context = {"db": db_session}
        result = await registry.execute_skill(
            "get_company_profile",
            {"entreprise_id": str(test_entreprise.id)},
            context,
        )

        assert "error" not in result
        assert result["nom"] == "TestCorp ESG"
        assert result["secteur"] == "agriculture"
        assert result["pays"] == "Côte d'Ivoire"
        assert result["profil"]["certifications"] == ["ISO 14001"]

    @pytest.mark.asyncio
    async def test_execute_get_company_profile_not_found(self, registry, db_session):
        """Vérifie le comportement quand l'entreprise n'existe pas."""
        context = {"db": db_session}
        result = await registry.execute_skill(
            "get_company_profile",
            {"entreprise_id": str(uuid.uuid4())},
            context,
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_execute_update_company_profile(self, registry, test_entreprise, db_session):
        """Met à jour le profil et vérifie le merge."""
        context = {"db": db_session}
        result = await registry.execute_skill(
            "update_company_profile",
            {
                "entreprise_id": str(test_entreprise.id),
                "updates": {
                    "objectifs_declares": ["neutralité carbone 2030"],
                    "certifications": ["Fair Trade"],  # Doit s'ajouter, pas remplacer
                },
            },
            context,
        )

        assert result["status"] == "updated"
        # Vérifier le merge des listes
        assert "ISO 14001" in result["profil"]["certifications"]
        assert "Fair Trade" in result["profil"]["certifications"]
        assert result["profil"]["objectifs_declares"] == ["neutralité carbone 2030"]

    @pytest.mark.asyncio
    async def test_execute_list_referentiels(self, registry, db_session):
        """Vérifie que list_referentiels retourne les référentiels seedés."""
        context = {"db": db_session}
        result = await registry.execute_skill("list_referentiels", {}, context)

        assert "error" not in result
        assert result["nombre"] > 0, "Aucun référentiel trouvé — avez-vous lancé le seed ?"

        for ref in result["referentiels"]:
            assert "code" in ref
            assert "nom" in ref
            assert "piliers" in ref

    @pytest.mark.asyncio
    async def test_execute_list_referentiels_filter_region(self, registry, db_session):
        """Filtre les référentiels par région."""
        context = {"db": db_session}
        result = await registry.execute_skill(
            "list_referentiels", {"region": "UEMOA"}, context
        )
        for ref in result["referentiels"]:
            assert ref["region"] == "UEMOA"

    @pytest.mark.asyncio
    async def test_execute_stub_skill(self, registry, db_session):
        """Vérifie qu'un skill stub retourne not_implemented."""
        context = {"db": db_session}
        result = await registry.execute_skill(
            "calculate_esg_score",
            {"entreprise_id": "test", "data": {}},
            context,
        )
        assert result["status"] == "not_implemented"

    @pytest.mark.asyncio
    async def test_execute_unknown_skill(self, registry, db_session):
        """Vérifie le comportement pour un skill inexistant."""
        context = {"db": db_session}
        result = await registry.execute_skill("skill_inconnu", {}, context)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_search_knowledge_base_placeholder(self, registry, db_session):
        """Vérifie que search_knowledge_base retourne le placeholder."""
        context = {"db": db_session}
        result = await registry.execute_skill(
            "search_knowledge_base",
            {"query": "critères BCEAO"},
            context,
        )
        assert result["status"] == "not_implemented"
        assert "RAG" in result["message"]


class TestSkillValidator:
    """Tests du validator de skills custom."""

    def test_valid_code(self):
        code = '''
async def execute(params, context):
    result = await context["db"].execute("SELECT 1")
    return {"status": "ok"}
'''
        valid, msg = validate_skill_code(code)
        assert valid is True
        assert msg == "OK"

    def test_empty_code(self):
        valid, msg = validate_skill_code("")
        assert valid is False

    def test_missing_execute(self):
        code = '''
async def my_function(params, context):
    return {"status": "ok"}
'''
        valid, msg = validate_skill_code(code)
        assert valid is False
        assert "execute" in msg

    def test_forbidden_import_os(self):
        code = '''
import os
async def execute(params, context):
    return {"path": os.getcwd()}
'''
        valid, msg = validate_skill_code(code)
        assert valid is False
        assert "import os" in msg

    def test_forbidden_subprocess(self):
        code = '''
import subprocess
async def execute(params, context):
    return subprocess.run(["ls"])
'''
        valid, msg = validate_skill_code(code)
        assert valid is False

    def test_forbidden_exec(self):
        code = '''
async def execute(params, context):
    exec("print('hello')")
    return {}
'''
        valid, msg = validate_skill_code(code)
        assert valid is False

    def test_forbidden_open(self):
        code = '''
async def execute(params, context):
    f = open("/etc/passwd")
    return {"data": f.read()}
'''
        valid, msg = validate_skill_code(code)
        assert valid is False

    def test_forbidden_sql_write(self):
        code = '''
async def execute(params, context):
    await context["db"].execute("DELETE FROM users")
    return {}
'''
        valid, msg = validate_skill_code(code)
        assert valid is False
        assert "DELETE" in msg
