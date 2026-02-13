"""Handler builtin : analyse d'un document uploadé via RAG."""

import logging
import uuid

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import DocChunk, Document
from app.rag.chunker import chunk_text
from app.rag.embeddings import get_embedding, get_embeddings_batch
from app.rag.search import semantic_search

logger = logging.getLogger(__name__)

# Requêtes de recherche par type d'analyse
ANALYSIS_QUERIES = {
    "esg_compliance": [
        "pratiques environnementales gestion déchets énergie renouvelable",
        "conditions de travail employés formation diversité",
        "gouvernance transparence éthique conformité anti-corruption",
    ],
    "financial": [
        "chiffre d'affaires revenus bénéfices résultats financiers",
        "dépenses investissements budget coûts",
    ],
    "carbon": [
        "consommation énergie électricité carburant générateur",
        "transport logistique véhicules flotte",
        "déchets émissions pollution recyclage",
    ],
}


async def analyze_document(params: dict, context: dict) -> dict:
    """
    Analyse un document uploadé.
    1. Récupère le document et vérifie les chunks
    2. Si pas encore chunké → lance la pipeline RAG
    3. Recherche sémantique par type d'analyse
    4. Retourne les passages pertinents extraits
    """
    db: AsyncSession = context.get("db")
    if not db:
        return {"error": "Session base de données non disponible"}

    document_id = params.get("document_id")
    if not document_id:
        return {"error": "document_id est requis"}

    analysis_type = params.get("analysis_type", "esg_compliance")

    try:
        doc_uuid = uuid.UUID(str(document_id))
    except ValueError:
        return {"error": f"document_id invalide : {document_id}"}

    # 1. Récupérer le document
    result = await db.execute(select(Document).where(Document.id == doc_uuid))
    doc = result.scalar_one_or_none()

    if not doc:
        return {"error": f"Document introuvable (id: {document_id})"}

    # 2. Vérifier / créer les chunks
    count_result = await db.execute(
        select(func.count()).select_from(DocChunk).where(DocChunk.document_id == doc_uuid)
    )
    chunk_count = count_result.scalar() or 0

    if chunk_count == 0:
        # Pas encore chunké → lancer la pipeline RAG
        texte = doc.texte_extrait
        if not texte:
            return {
                "error": "Le document n'a pas de texte extrait. Essayez de le réuploader."
            }

        chunks = chunk_text(texte, chunk_size=800, overlap=200)
        if not chunks:
            return {"error": "Impossible de découper le document en chunks."}

        texts = [c["text"] for c in chunks]
        embeddings = await get_embeddings_batch(texts)

        for chunk_data, embedding in zip(chunks, embeddings):
            doc_chunk = DocChunk(
                document_id=doc_uuid,
                contenu=chunk_data["text"],
                embedding=embedding,
                page_number=chunk_data.get("page"),
                chunk_index=chunk_data["index"],
            )
            db.add(doc_chunk)
        await db.commit()
        chunk_count = len(chunks)

    # 3. Recherche sémantique par type d'analyse
    queries = ANALYSIS_QUERIES.get(analysis_type, ANALYSIS_QUERIES["esg_compliance"])

    all_results = []
    for query in queries:
        results = await semantic_search(
            query=query,
            db=db,
            table="doc_chunks",
            filters={"document_id": str(doc_uuid)},
            top_k=5,
        )
        all_results.extend(results)

    # 4. Déduplique et trie par similarité
    seen = set()
    unique_results = []
    for r in sorted(all_results, key=lambda x: float(x.get("similarity", 0)), reverse=True):
        contenu = r["contenu"]
        if contenu not in seen:
            seen.add(contenu)
            unique_results.append({
                "contenu": contenu,
                "page_number": r.get("page_number"),
                "similarity": round(float(r.get("similarity", 0)), 4),
            })

    # Limiter à 15 résultats
    unique_results = unique_results[:15]

    return {
        "document": doc.nom_fichier,
        "analysis_type": analysis_type,
        "extracted_passages": unique_results,
        "total_chunks": chunk_count,
        "total_pages": (doc.metadata_json or {}).get("pages", "inconnu"),
    }
