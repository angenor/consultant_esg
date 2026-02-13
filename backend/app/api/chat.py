"""
Router /api/chat — Conversations et messagerie SSE.
Endpoints : CRUD conversations + envoi de message avec streaming SSE.
"""

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.agent.engine import AgentEngine
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.stt import STTService, get_stt_service
from app.models.conversation import Conversation
from app.models.entreprise import Entreprise
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import (
    ConversationDetailResponse,
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
    SendMessageRequest,
)
from app.skills.registry import SkillRegistry

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ---- Helpers ----


async def _get_entreprise_dict(entreprise_id: uuid.UUID, db: AsyncSession) -> dict:
    """Charge une entreprise et la retourne sous forme de dict pour l'agent."""
    result = await db.execute(select(Entreprise).where(Entreprise.id == entreprise_id))
    entreprise = result.scalar_one_or_none()
    if not entreprise:
        raise HTTPException(status_code=404, detail="Entreprise introuvable")
    return {
        "id": str(entreprise.id),
        "nom": entreprise.nom,
        "secteur": entreprise.secteur,
        "sous_secteur": entreprise.sous_secteur,
        "pays": entreprise.pays,
        "ville": entreprise.ville,
        "effectifs": entreprise.effectifs,
        "chiffre_affaires": float(entreprise.chiffre_affaires) if entreprise.chiffre_affaires else None,
        "devise": entreprise.devise,
        "description": entreprise.description,
        "profil_json": entreprise.profil_json,
    }


async def _verify_conversation_access(
    conversation_id: uuid.UUID, user: User, db: AsyncSession
) -> Conversation:
    """Vérifie que la conversation existe et appartient à l'utilisateur."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable")

    # Vérifier que l'entreprise de la conversation appartient à l'utilisateur
    result = await db.execute(
        select(Entreprise).where(
            Entreprise.id == conv.entreprise_id,
            Entreprise.user_id == user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Accès non autorisé à cette conversation")

    return conv


# ---- Endpoints ----


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    body: CreateConversationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Crée une nouvelle conversation liée à une entreprise."""
    # Vérifier que l'entreprise appartient à l'utilisateur
    result = await db.execute(
        select(Entreprise).where(
            Entreprise.id == body.entreprise_id,
            Entreprise.user_id == user.id,
        )
    )
    entreprise = result.scalar_one_or_none()
    if not entreprise:
        raise HTTPException(status_code=404, detail="Entreprise introuvable")

    conv = Conversation(
        entreprise_id=body.entreprise_id,
        titre=body.titre or f"Conversation avec {entreprise.nom}",
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Liste les conversations de l'utilisateur (via ses entreprises)."""
    result = await db.execute(
        select(Conversation)
        .join(Entreprise, Conversation.entreprise_id == Entreprise.id)
        .where(Entreprise.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Récupère l'historique complet d'une conversation."""
    conv = await _verify_conversation_access(conversation_id, user, db)

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()

    return ConversationDetailResponse(
        id=conv.id,
        entreprise_id=conv.entreprise_id,
        titre=conv.titre,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[MessageResponse.model_validate(m) for m in messages],
    )


@router.post("/conversations/{conversation_id}/message")
async def send_message(
    conversation_id: uuid.UUID,
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Envoie un message et stream la réponse via SSE.

    Events SSE :
    - event: text         -> Texte de la réponse (streaming mot par mot)
    - event: skill_start  -> Un skill commence (nom + params)
    - event: skill_result -> Un skill a fini (résumé du résultat)
    - event: done         -> Fin de la réponse
    - event: error        -> Erreur
    """
    conv = await _verify_conversation_access(conversation_id, user, db)

    # Charger le contexte entreprise
    entreprise_dict = await _get_entreprise_dict(conv.entreprise_id, db)

    # Instancier le registry et l'engine
    registry = SkillRegistry(db)
    engine = AgentEngine(db, registry)

    async def event_generator():
        try:
            async for event in engine.run(
                conversation_id=str(conversation_id),
                user_message=body.message,
                entreprise=entreprise_dict,
            ):
                yield {
                    "event": event["type"],
                    "data": json.dumps(event, ensure_ascii=False, default=str),
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"type": "error", "content": str(e)}),
            }

    return EventSourceResponse(event_generator())


ALLOWED_AUDIO_TYPES = {
    "audio/webm",
    "audio/wav",
    "audio/mpeg",
    "audio/ogg",
    "audio/mp3",
    "audio/x-m4a",
    "audio/mp4",
    "video/webm",  # MediaRecorder peut produire video/webm avec codec audio
}


@router.post("/conversations/{conversation_id}/audio")
async def send_audio_message(
    conversation_id: uuid.UUID,
    audio: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    stt: STTService = Depends(get_stt_service),
):
    """
    Reçoit un fichier audio, le transcrit via Whisper (STT),
    puis injecte le texte dans la boucle agent comme un message classique.

    Formats acceptés : webm, wav, mp3, ogg (sortie MediaRecorder).
    Retourne un SSE stream identique à /message, précédé d'un event `transcript`.
    """
    # Valider le type MIME (ignorer les paramètres comme ;codecs=opus)
    content_type = (audio.content_type or "").split(";")[0].strip()
    if content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Format audio non supporté : {content_type}. "
            f"Formats acceptés : webm, wav, mp3, ogg.",
        )

    conv = await _verify_conversation_access(conversation_id, user, db)

    # Transcrire l'audio en texte
    transcript = await stt.transcribe(
        audio_data=audio.file,
        filename=audio.filename or "audio.webm",
        language="fr",
    )

    if not transcript.strip():
        raise HTTPException(
            status_code=400,
            detail="Impossible de transcrire l'audio. Veuillez réessayer.",
        )

    # Charger le contexte entreprise
    entreprise_dict = await _get_entreprise_dict(conv.entreprise_id, db)

    # Instancier le registry et l'engine
    registry = SkillRegistry(db)
    engine = AgentEngine(db, registry)

    async def event_generator():
        # Envoyer d'abord la transcription au frontend
        yield {
            "event": "transcript",
            "data": json.dumps({"type": "transcript", "text": transcript}, ensure_ascii=False),
        }
        # Puis lancer l'agent normalement avec le texte transcrit
        try:
            async for event in engine.run(
                conversation_id=str(conversation_id),
                user_message=transcript,
                entreprise=entreprise_dict,
            ):
                yield {
                    "event": event["type"],
                    "data": json.dumps(event, ensure_ascii=False, default=str),
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"type": "error", "content": str(e)}),
            }

    return EventSourceResponse(event_generator())


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Supprime une conversation et ses messages."""
    conv = await _verify_conversation_access(conversation_id, user, db)
    await db.delete(conv)
    await db.commit()
