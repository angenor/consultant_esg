"""
Module RAG (Retrieval-Augmented Generation).
Pipeline : extraction texte → chunking → embeddings → recherche sémantique.
"""

from app.rag.chunker import chunk_text
from app.rag.embeddings import get_embedding
from app.rag.search import semantic_search
from app.rag.text_extractor import extract_text_from_file

__all__ = [
    "extract_text_from_file",
    "chunk_text",
    "get_embedding",
    "semantic_search",
]
