"""
Service Speech-to-Text — transcription audio via Whisper API (OpenAI).
Utilisé par l'endpoint /api/chat/conversations/{id}/audio.
"""

import io
from typing import BinaryIO

from openai import AsyncOpenAI

from app.config import settings


class STTService:
    """Wrapper autour de l'API Whisper d'OpenAI pour la transcription audio."""

    SUPPORTED_FORMATS = {"audio/webm", "audio/wav", "audio/mpeg", "audio/ogg", "audio/mp3"}

    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def transcribe(
        self,
        audio_data: BinaryIO,
        filename: str = "audio.webm",
        language: str = "fr",
    ) -> str:
        """
        Transcrit un fichier audio en texte via Whisper.

        Args:
            audio_data: Flux binaire du fichier audio
            filename: Nom du fichier (pour déterminer le format)
            language: Code langue ISO 639-1

        Returns:
            Texte transcrit
        """
        content = audio_data.read()
        if isinstance(content, str):
            content = content.encode()

        audio_file = io.BytesIO(content)
        audio_file.name = filename

        response = await self._client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language,
            response_format="text",
        )

        return response.strip() if isinstance(response, str) else str(response).strip()


# Singleton
_stt_service: STTService | None = None


def get_stt_service() -> STTService:
    """Dependency injection pour FastAPI."""
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
    return _stt_service
