"""Analysis background tasks."""
import logging

logger = logging.getLogger("deepshield.tasks.analysis")

try:
    from tasks.celery_app import celery_app

    if celery_app:
        @celery_app.task(bind=True, name="analyze_file")
        def analyze_file_task(self, session_id: str, file_path: str, model_list: list, ext: str):
            """Celery task for file analysis."""
            import asyncio
            from api.routes.inference import _run_analysis
            asyncio.run(_run_analysis(session_id, file_path, model_list, ext))

except Exception:
    pass
