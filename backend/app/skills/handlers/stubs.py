"""
Handlers stub pour les skills builtin pas encore implémentés.
Chaque stub retourne un message indiquant que le skill sera disponible ultérieurement.
"""


async def stub_handler(params: dict, context: dict) -> dict:
    """Handler générique pour les skills pas encore implémentés."""
    return {
        "status": "not_implemented",
        "message": "Ce skill n'est pas encore implémenté. Il sera disponible dans une version ultérieure.",
        "params_received": params,
    }
