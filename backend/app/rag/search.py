"""
Recherche sémantique via pgvector (opérateur cosine <=>).
Supporte les tables doc_chunks et fonds_chunks.
"""

import logging
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.embeddings import get_embedding

logger = logging.getLogger(__name__)


async def semantic_search(
    query: str,
    db: AsyncSession,
    table: str = "doc_chunks",
    filters: dict | None = None,
    top_k: int = 5,
) -> list[dict]:
    """
    Recherche sémantique dans une table contenant des embeddings pgvector.

    Args:
        query: Texte de la requête de recherche
        db: Session SQLAlchemy async
        table: "doc_chunks" ou "fonds_chunks"
        filters: Filtres supplémentaires (ex: {"document_id": uuid})
        top_k: Nombre de résultats à retourner

    Returns:
        Liste de dicts avec le contenu, la similarité, et les métadonnées
    """
    if table not in ("doc_chunks", "fonds_chunks"):
        raise ValueError(f"Table non supportée : {table}")

    # Générer l'embedding de la requête
    query_embedding = await get_embedding(query)
    embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

    # Construire la requête SQL selon la table
    if table == "doc_chunks":
        sql, params = _build_doc_chunks_query(embedding_str, filters, top_k)
    else:
        sql, params = _build_fonds_chunks_query(embedding_str, filters, top_k)

    result = await db.execute(text(sql), params)
    rows = result.mappings().all()

    return [dict(row) for row in rows]


def _build_doc_chunks_query(
    embedding_str: str, filters: dict | None, top_k: int
) -> tuple[str, dict]:
    """Construit la requête de recherche pour doc_chunks."""
    where_clauses = []
    params: dict = {"embedding": embedding_str, "top_k": top_k}

    if filters:
        if "document_id" in filters:
            where_clauses.append("dc.document_id = :document_id")
            params["document_id"] = filters["document_id"]
        if "entreprise_id" in filters:
            where_clauses.append("d.entreprise_id = :entreprise_id")
            params["entreprise_id"] = filters["entreprise_id"]

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    sql = f"""
        SELECT
            dc.id,
            dc.contenu,
            dc.page_number,
            dc.chunk_index,
            dc.document_id,
            d.nom_fichier,
            1 - (dc.embedding <=> CAST(:embedding AS vector)) AS similarity
        FROM doc_chunks dc
        JOIN documents d ON d.id = dc.document_id
        {where_sql}
        ORDER BY dc.embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """
    return sql, params


def _build_fonds_chunks_query(
    embedding_str: str, filters: dict | None, top_k: int
) -> tuple[str, dict]:
    """Construit la requête de recherche pour fonds_chunks."""
    where_clauses = []
    params: dict = {"embedding": embedding_str, "top_k": top_k}

    if filters:
        if "fonds_id" in filters:
            where_clauses.append("fc.fonds_id = :fonds_id")
            params["fonds_id"] = filters["fonds_id"]
        if "type_info" in filters:
            where_clauses.append("fc.type_info = :type_info")
            params["type_info"] = filters["type_info"]

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    sql = f"""
        SELECT
            fc.id,
            fc.contenu,
            fc.fonds_id,
            fc.type_info,
            fv.nom AS fonds_nom,
            1 - (fc.embedding <=> CAST(:embedding AS vector)) AS similarity
        FROM fonds_chunks fc
        JOIN fonds_verts fv ON fv.id = fc.fonds_id
        {where_sql}
        ORDER BY fc.embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """
    return sql, params
