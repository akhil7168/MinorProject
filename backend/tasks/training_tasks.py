"""Training background tasks."""
import logging

logger = logging.getLogger("deepshield.tasks.training")

try:
    from tasks.celery_app import celery_app

    if celery_app:
        @celery_app.task(bind=True, name="train_model")
        def train_model_task(self, run_id: str, config: dict):
            """Celery task for model training."""
            import asyncio
            from training.trainer import ModelTrainer
            trainer = ModelTrainer()
            asyncio.run(trainer.train_async(run_id, config))

except Exception:
    pass
