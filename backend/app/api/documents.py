"""API endpoints pour la gestion des documents (upload, liste, détail, suppression)."""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.document import DocChunk, Document
from app.models.entreprise import Entreprise
from app.models.user import User
from app.rag.chunker import chunk_text
from app.rag.embeddings import get_embeddings_batch
from app.rag.text_extractor import extract_text_from_file
from app.schemas.document import DocumentDetailResponse, DocumentResponse

router = APIRouter(prefix="/api/documents", tags=["documents"])

UPLOAD_DIR = Path("/app/uploads")

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


async def _verify_entreprise_access(
    entreprise_id: uuid.UUID, user: User, db: AsyncSession
) -> Entreprise:
    """Vérifie que l'entreprise existe et appartient à l'utilisateur."""
    result = await db.execute(
        select(Entreprise).where(
            Entreprise.id == entreprise_id,
            Entreprise.user_id == user.id,
        )
    )
    entreprise = result.scalar_one_or_none()
    if not entreprise:
        raise HTTPException(status_code=404, detail="Entreprise introuvable")
    return entreprise


async def _verify_document_access(
    document_id: uuid.UUID, user: User, db: AsyncSession
) -> Document:
    """Vérifie que le document existe et appartient à une entreprise de l'utilisateur."""
    result = await db.execute(
        select(Document)
        .join(Entreprise, Entreprise.id == Document.entreprise_id)
        .where(Document.id == document_id, Entreprise.user_id == user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    return doc


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    entreprise_id: uuid.UUID = Form(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload un document (PDF, image, Word, Excel).
    Extrait le texte, crée les chunks et embeddings pour le RAG.
    """
    # Vérifier l'accès à l'entreprise
    await _verify_entreprise_access(entreprise_id, user, db)

    # Valider le type MIME
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non supporté : {file.content_type}. "
            f"Types acceptés : PDF, PNG, JPEG, DOCX, XLSX",
        )

    # Créer le répertoire d'upload
    upload_path = UPLOAD_DIR / str(entreprise_id)
    upload_path.mkdir(parents=True, exist_ok=True)

    # Sauvegarder le fichier avec un nom unique
    file_ext = Path(file.filename or "document").suffix
    unique_name = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_path / unique_name

    content = await file.read()
    file_path.write_bytes(content)

    # Extraire le texte
    try:
        texte = await extract_text_from_file(str(file_path), file.content_type)
    except Exception:
        texte = None

    # Créer le document en BDD
    doc = Document(
        entreprise_id=entreprise_id,
        nom_fichier=file.filename or "document",
        type_mime=file.content_type,
        chemin_stockage=str(file_path),
        taille=len(content),
        texte_extrait=texte,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Créer les chunks + embeddings (synchrone pour le MVP)
    if texte and texte.strip():
        await _create_chunks(doc.id, texte, db)

    return doc


@router.get("/entreprise/{entreprise_id}", response_model=list[DocumentResponse])
async def list_documents(
    entreprise_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Liste les documents d'une entreprise."""
    await _verify_entreprise_access(entreprise_id, user, db)

    result = await db.execute(
        select(Document)
        .where(Document.entreprise_id == entreprise_id)
        .order_by(Document.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Détail d'un document (métadonnées + nombre de chunks)."""
    doc = await _verify_document_access(document_id, user, db)

    # Compter les chunks
    result = await db.execute(
        select(func.count()).select_from(DocChunk).where(DocChunk.document_id == doc.id)
    )
    chunk_count = result.scalar() or 0

    return DocumentDetailResponse(
        id=doc.id,
        entreprise_id=doc.entreprise_id,
        nom_fichier=doc.nom_fichier,
        type_mime=doc.type_mime,
        taille=doc.taille,
        metadata_json=doc.metadata_json,
        created_at=doc.created_at,
        texte_extrait=doc.texte_extrait,
        chunk_count=chunk_count,
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Supprime un document, ses chunks, et le fichier physique."""
    doc = await _verify_document_access(document_id, user, db)

    # Supprimer le fichier physique
    file_path = Path(doc.chemin_stockage)
    if file_path.exists():
        file_path.unlink()

    # Supprimer en BDD (les chunks sont supprimés en cascade)
    await db.delete(doc)
    await db.commit()


async def _create_chunks(document_id: uuid.UUID, texte: str, db: AsyncSession):
    """Crée les chunks + embeddings pour un document."""
    chunks = chunk_text(texte, chunk_size=800, overlap=200)
    if not chunks:
        return

    # Générer les embeddings en batch
    texts = [c["text"] for c in chunks]
    embeddings = await get_embeddings_batch(texts)

    # Insérer les chunks
    for chunk, embedding in zip(chunks, embeddings):
        doc_chunk = DocChunk(
            document_id=document_id,
            contenu=chunk["text"],
            embedding=embedding,
            page_number=chunk.get("page"),
            chunk_index=chunk["index"],
        )
        db.add(doc_chunk)

    await db.commit()
