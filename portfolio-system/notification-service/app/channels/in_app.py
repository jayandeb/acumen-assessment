from uuid import UUID

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.notification import Notification, NotificationChannel, NotificationStatus


def send_in_app(
    db: Session,
    user_id: str,
    transaction_id: str,
    message: str,
) -> Notification:
    notification = Notification(
        user_id=UUID(user_id),
        transaction_id=UUID(transaction_id),
        channel=NotificationChannel.IN_APP,
        message=message,
        status=NotificationStatus.SENT,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    logger.info(
        "in_app_notification_saved",
        user_id=user_id,
        transaction_id=transaction_id,
        notification_id=str(notification.id),
    )
    return notification
