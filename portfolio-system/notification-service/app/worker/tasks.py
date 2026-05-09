from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.channels import email as email_channel
from app.channels import sms as sms_channel
from app.channels import in_app as in_app_channel
from app.core.config import settings
from app.core.logger import logger
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.models.preference import NotificationPreference
from app.rules.engine import should_notify
from app.worker.celery_app import celery_app

sync_engine = create_engine(
    settings.DATABASE_URL.replace("+asyncpg", "+psycopg2"),
    echo=False,
)
SyncSession = sessionmaker(bind=sync_engine)


@celery_app.task(
    name="process_notification_event",
    bind=True,
    max_retries=3,
    default_retry_delay=2,
)
def process_notification_event(self, event_data: dict) -> None:
    try:
        logger.info("processing_notification", task_id=self.request.id, event_data=event_data)

        user_id = event_data.get("user_id")
        transaction_id = event_data.get("transaction_id")
        transaction_type = event_data.get("type")
        amount = event_data.get("amount", "0")

        message = (
            f"Transaction alert: {transaction_type} of ${amount} "
            f"(transaction ID: {transaction_id})"
        )

        with SyncSession() as db:
            preferences = (
                db.query(NotificationPreference)
                .filter(NotificationPreference.user_id == user_id)
                .all()
            )

            channel_decisions = should_notify(event_data, preferences)
            logger.info(
                "notification_rules_evaluated",
                user_id=user_id,
                decisions=channel_decisions,
            )

            for channel_name, should_send in channel_decisions.items():
                if not should_send:
                    continue

                if channel_name == NotificationChannel.EMAIL.value:
                    email_channel.send_email(user_id, transaction_id, message)
                    _save_notification(db, user_id, transaction_id, channel_name, message)
                elif channel_name == NotificationChannel.SMS.value:
                    sms_channel.send_sms(user_id, transaction_id, message)
                    _save_notification(db, user_id, transaction_id, channel_name, message)
                elif channel_name == NotificationChannel.IN_APP.value:
                    in_app_channel.send_in_app(db, user_id, transaction_id, message)

        logger.info(
            "notification_processing_complete",
            task_id=self.request.id,
            user_id=user_id,
        )

    except Exception as exc:
        logger.error("notification_failed", error=str(exc), retries=self.request.retries)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


def _save_notification(
    db: Session,
    user_id: str,
    transaction_id: str,
    channel: str,
    message: str,
) -> None:
    notification = Notification(
        user_id=UUID(user_id),
        transaction_id=UUID(transaction_id),
        channel=NotificationChannel(channel),
        message=message,
        status=NotificationStatus.SENT,
    )
    db.add(notification)
    db.commit()
