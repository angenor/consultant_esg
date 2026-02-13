"""
Validation du code Python des skills custom.
Vérifie les patterns interdits avant sauvegarde en BDD.
"""

FORBIDDEN_PATTERNS = [
    # Imports système dangereux
    "import os",
    "import sys",
    "import subprocess",
    "import shutil",
    "import signal",
    "import socket",
    # Exécution de code arbitraire
    "__import__",
    "exec(",
    "eval(",
    "compile(",
    # Accès fichiers
    "open(",
    "file(",
    # Requêtes HTTP
    "requests.",
    "urllib.",
    "httpx.",
    "aiohttp.",
    # Écriture directe en BDD (les skills custom sont en lecture seule)
    "DELETE ",
    "DROP ",
    "UPDATE ",
    "INSERT ",
    "ALTER ",
    "TRUNCATE ",
]


def validate_skill_code(code: str) -> tuple[bool, str]:
    """
    Valide le code d'un skill custom.
    Retourne (True, "OK") si valide, (False, "raison") sinon.
    """
    if not code or not code.strip():
        return False, "Le code ne peut pas être vide"

    for pattern in FORBIDDEN_PATTERNS:
        if pattern in code:
            return False, f"Pattern interdit détecté: '{pattern}'"

    if "async def execute(params, context)" not in code:
        return False, "Le code doit définir : async def execute(params, context)"

    return True, "OK"
