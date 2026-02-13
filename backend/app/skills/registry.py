"""
Registre central des skills.
Charge les skills depuis la BDD et les convertit en outils (format OpenAI tools).
Dispatche l'exécution vers les handlers builtin ou le sandbox custom.
"""

import logging
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill

logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Pont entre la BDD (définition des skills) et le code Python (exécution).

    - Les skills builtin sont des fonctions async importées depuis handlers/
    - Les skills custom sont du code Python admin exécuté dans un sandbox restreint
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.builtin_handlers: dict[str, Callable] = {}
        self._register_builtins()

    def _register_builtins(self):
        """Enregistre tous les handlers builtin disponibles."""
        from app.skills.handlers import (
            analyze_document,
            calculate_esg_score,
            get_company_profile,
            list_referentiels,
            search_green_funds,
            search_knowledge_base,
            update_company_profile,
        )

        # Handlers implémentés
        self.builtin_handlers = {
            "builtin.get_company_profile": get_company_profile,
            "builtin.update_company_profile": update_company_profile,
            "builtin.list_referentiels": list_referentiels,
            "builtin.search_knowledge_base": search_knowledge_base,
            "builtin.analyze_document": analyze_document,
            "builtin.calculate_esg_score": calculate_esg_score,
            "builtin.search_green_funds": search_green_funds,
        }

        # Handlers stubs — seront développés en Semaine 3-4
        from app.skills.handlers.stubs import stub_handler

        stub_keys = [
            "builtin.calculate_carbon",
            "builtin.generate_reduction_plan",
            "builtin.simulate_funding",
            "builtin.calculate_credit_score",
            "builtin.get_sector_benchmark",
            "builtin.manage_action_plan",
            "builtin.generate_report_section",
            "builtin.assemble_pdf",
        ]
        for key in stub_keys:
            self.builtin_handlers[key] = stub_handler

    async def get_active_tools(self) -> list[dict]:
        """
        Charge les skills actifs depuis la BDD.
        Retourne une liste de dicts {name, description, input_schema}.
        La conversion au format OpenAI tools se fait dans engine.py.
        """
        result = await self.db.execute(
            select(Skill)
            .where(Skill.is_active.is_(True))
            .order_by(Skill.category, Skill.nom)
        )
        skills = result.scalars().all()

        tools = []
        for skill in skills:
            tools.append(
                {
                    "name": skill.nom,
                    "description": skill.description,
                    "input_schema": skill.input_schema,
                }
            )
        return tools

    async def execute_skill(
        self, skill_name: str, params: dict, context: dict
    ) -> dict[str, Any]:
        """
        Exécute un skill par son nom.
        - Si builtin → appelle la fonction Python enregistrée
        - Si custom  → exécute le handler_code dans un sandbox
        """
        result = await self.db.execute(
            select(Skill).where(Skill.nom == skill_name, Skill.is_active.is_(True))
        )
        skill = result.scalar_one_or_none()

        if not skill:
            return {"error": f"Skill '{skill_name}' introuvable ou inactif"}

        handler_key = skill.handler_key

        # Skill Builtin
        if handler_key.startswith("builtin."):
            handler = self.builtin_handlers.get(handler_key)
            if not handler:
                return {"error": f"Handler builtin '{handler_key}' non enregistré"}
            try:
                return await handler(params, context)
            except Exception as e:
                logger.exception("Erreur dans le handler builtin '%s'", handler_key)
                return {"error": f"Erreur d'exécution du skill: {e}"}

        # Skill Custom (code de l'admin)
        if handler_key.startswith("custom."):
            if not skill.handler_code:
                return {"error": f"Skill custom '{skill_name}' n'a pas de handler_code"}
            return await self._execute_custom(skill.handler_code, params, context)

        return {"error": f"Type de handler inconnu: {handler_key}"}

    async def _execute_custom(
        self, code: str, params: dict, context: dict
    ) -> dict[str, Any]:
        """
        Exécute le code Python d'un skill custom dans un environnement restreint.
        Le code doit définir une fonction `async def execute(params, context)`.
        """
        import json as json_mod
        import datetime as datetime_mod
        import math as math_mod

        allowed_globals = {
            "__builtins__": {
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sorted": sorted,
                "min": min,
                "max": max,
                "sum": sum,
                "abs": abs,
                "round": round,
                "isinstance": isinstance,
                "print": print,
                "None": None,
                "True": True,
                "False": False,
            },
            "params": params,
            "context": context,
            "json": json_mod,
            "datetime": datetime_mod,
            "math": math_mod,
        }

        local_vars: dict = {}
        try:
            exec(code, allowed_globals, local_vars)
            if "execute" not in local_vars:
                return {
                    "error": "Le skill custom doit définir une fonction execute(params, context)"
                }
            result = await local_vars["execute"](params, context)
            return result
        except Exception as e:
            logger.exception("Erreur d'exécution du skill custom")
            return {"error": f"Erreur d'exécution du skill custom: {e}"}
