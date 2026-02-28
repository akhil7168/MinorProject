"""
Celery App Configuration
========================
Optional — falls back to synchronous execution if Redis unavailable.
"""
import logging

logger = logging.getLogger("deepshield.tasks")

try:
    from celery import Celery
    from config import get_settings

    settings = get_settings()

    celery_app = Celery(
        "deepshield",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )

    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,    # 1 hour max per task
        worker_max_tasks_per_child=10,
    )

    logger.info("Celery configured")

except Exception as e:
    logger.warning(f"Celery not available: {e}. Background tasks will run synchronously.")
    celery_app = None
