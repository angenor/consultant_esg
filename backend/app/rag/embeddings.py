"""
Génération d'embeddings via Voyage AI (voyage-3-large, 1024 dimensions).
Configurable via .env : VOYAGE_API_KEY.
"""

import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
VOYAGE_MODEL = "voyage-3-large"
EMBEDDING_DIM = 1024
MAX_BATCH_SIZE = 128  # Voyage AI limite à 128 textes par requête


async def get_embedding(text: str) -> list[float]:
    """
    Génère un embedding pour un texte unique.
    Retourne un vecteur de 1024 dimensions.
    """
    if not text or not text.strip():
        return [0.0] * EMBEDDING_DIM

    results = await get_embeddings_batch([text])
    return results[0]


async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Génère des embeddings pour un batch de textes.
    Gère automatiquement le découpage en sous-batches si nécessaire.
    """
    api_key = settings.VOYAGE_API_KEY
    if not api_key:
        raise ValueError(
            "VOYAGE_API_KEY non configuré. Ajoutez-le dans le fichier .env."
        )

    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), MAX_BATCH_SIZE):
        batch = texts[i : i + MAX_BATCH_SIZE]
        embeddings = await _call_voyage_api(batch, api_key)
        all_embeddings.extend(embeddings)

    return all_embeddings


async def _call_voyage_api(texts: list[str], api_key: str) -> list[list[float]]:
    """Appel à l'API Voyage AI pour un batch de textes."""
    # Tronquer les textes trop longs (Voyage limite à ~32k tokens)
    truncated = [t[:16000] for t in texts]

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            VOYAGE_API_URL,
            json={
                "input": truncated,
                "model": VOYAGE_MODEL,
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        if response.status_code != 200:
            logger.error(
                "Erreur API Voyage (%d) : %s", response.status_code, response.text
            )
            raise RuntimeError(
                f"Erreur API Voyage AI ({response.status_code}): {response.text}"
            )

        data = response.json()
        # Trier par index pour garantir l'ordre
        sorted_data = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]
