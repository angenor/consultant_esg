"""Handler builtin : recherche dans la base de connaissances (placeholder RAG)."""


async def search_knowledge_base(params: dict, context: dict) -> dict:
    """
    Placeholder — le moteur RAG sera implémenté en Semaine 3.
    Retourne un message informatif pour l'instant.
    """
    query = params.get("query", "")
    source = params.get("source", "all")

    return {
        "status": "not_implemented",
        "message": (
            "Le moteur de recherche vectorielle (RAG) n'est pas encore implémenté. "
            "Il sera disponible après l'intégration des embeddings en Semaine 3."
        ),
        "query": query,
        "source": source,
    }
