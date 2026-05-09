from celery import Celery

from app.core.config import settings

celery_app = Celery("portfolio", broker=settings.REDIS_URL)

celery_app.conf.task_routes = {
    "process_notification_event": {"queue": "notifications"}
}


@celery_app.task(name="process_notification_event")
def publish_transaction_event(event_data: dict) -> None:
    pass
