"""Handler builtin : recherche dans la base de connaissances via RAG."""

import logging

from app.rag.search import semantic_search

logger = logging.getLogger(__name__)


async def search_knowledge_base(params: dict, context: dict) -> dict:
    """
    Recherche sémantique dans la base de connaissances (documents ou fonds).
    Utilise pgvector + HNSW pour la similarité cosine.

    Params:
        query (str) : texte de recherche
        source (str) : "documents", "fonds", ou "all" (défaut)
        top_k (int) : nombre de résultats (défaut 5)
        entreprise_id (str) : filtrer par entreprise (optionnel)
    """
    db = context.get("db")
    if not db:
        return {"error": "Session base de données non disponible"}

    query = params.get("query", "")
    if not query.strip():
        return {"error": "La requête de recherche est vide"}

    source = params.get("source", "all")
    top_k = params.get("top_k", 5)
    entreprise_id = context.get("entreprise_id")

    results = {"query": query, "source": source, "resultats": []}

    try:
        # Recherche dans les documents
        if source in ("documents", "all"):
            filters = {}
            if entreprise_id:
                filters["entreprise_id"] = str(entreprise_id)

            doc_results = await semantic_search(
                query=query,
                db=db,
                table="doc_chunks",
                filters=filters if filters else None,
                top_k=top_k,
            )

            for r in doc_results:
                results["resultats"].append({
                    "source": "document",
                    "contenu": r["contenu"],
                    "nom_fichier": r.get("nom_fichier"),
                    "page": r.get("page_number"),
                    "similarity": round(float(r.get("similarity", 0)), 4),
                })

        # Recherche dans les fonds verts
        if source in ("fonds", "all"):
            fonds_results = await semantic_search(
                query=query,
                db=db,
                table="fonds_chunks",
                top_k=top_k,
            )

            for r in fonds_results:
                results["resultats"].append({
                    "source": "fonds",
                    "contenu": r["contenu"],
                    "fonds_nom": r.get("fonds_nom"),
                    "type_info": r.get("type_info"),
                    "similarity": round(float(r.get("similarity", 0)), 4),
                })

        # Trier par similarité décroissante
        results["resultats"].sort(key=lambda x: x["similarity"], reverse=True)
        results["nombre_resultats"] = len(results["resultats"])

    except Exception as e:
        logger.exception("Erreur lors de la recherche RAG")
        return {"error": f"Erreur de recherche : {e}", "query": query}

    return results
