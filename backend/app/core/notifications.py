"""Service de création de notifications."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification

logger = logging.getLogger(__name__)


async def create_notification(
    db: AsyncSession,
    user_id: uuid.UUID | str,
    type: str,
    titre: str,
    contenu: str | None = None,
    lien: str | None = None,
) -> Notification:
    """
    Crée une notification en BDD.

    Types supportés :
    - rappel_action : rappel d'échéance d'une action
    - echeance_fonds : échéance d'un fonds vert
    - nouveau_fonds : nouveau fonds vert disponible
    - progres_score : progression du score ESG
    - action_completee : action du plan d'action terminée
    """
    notif = Notification(
        user_id=uuid.UUID(str(user_id)),
        type=type,
        titre=titre,
        contenu=contenu,
        lien=lien,
    )
    db.add(notif)
    await db.flush()
    return notif
