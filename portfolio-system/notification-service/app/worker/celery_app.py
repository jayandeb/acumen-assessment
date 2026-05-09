from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "notification",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.worker.tasks"],
)

celery_app.conf.task_routes = {
    "process_notification_event": {"queue": "notifications"}
}

celery_app.conf.task_acks_late = True
celery_app.conf.task_reject_on_worker_lost = True
