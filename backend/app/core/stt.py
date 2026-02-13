"""
Service Speech-to-Text — transcription audio via Whisper sur Replicate.
Utilisé par l'endpoint /api/chat/conversations/{id}/audio.
"""

import io
from typing import BinaryIO

from replicate import Client

from app.config import settings


class STTService:
    """Wrapper autour du modèle Whisper hébergé sur Replicate."""

    SUPPORTED_FORMATS = {"audio/webm", "audio/wav", "audio/mpeg", "audio/ogg", "audio/mp3"}

    def __init__(self) -> None:
        self._client = Client(api_token=settings.REPLICATE_API_TOKEN)

    async def transcribe(
        self,
        audio_data: BinaryIO,
        filename: str = "audio.webm",
        language: str = "fr",
    ) -> str:
        """
        Transcrit un fichier audio en texte via Whisper sur Replicate.

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

        output = await self._client.async_run(
            "openai/whisper:8099696689d249cf8b122d833c36ac3f75505c666a395ca40ef26f68e7d3d16e",
            input={
                "audio": audio_file,
                "language": language,
                "model": "large-v3",
                "transcription": "plain text",
            },
        )

        transcription = output.get("transcription", "") if isinstance(output, dict) else str(output)
        return transcription.strip()


# Singleton
_stt_service: STTService | None = None


def get_stt_service() -> STTService:
    """Dependency injection pour FastAPI."""
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
    return _stt_service
