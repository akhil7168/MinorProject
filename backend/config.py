"""
DeepShield Backend Configuration
================================
Uses pydantic-settings to load configuration from environment variables.
All secrets come from .env — never hardcoded.
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Supabase ──────────────────────────────────────────────
    SUPABASE_URL: str = "https://your-project.supabase.co"
    SUPABASE_ANON_KEY: str = "your-anon-key"
    SUPABASE_SERVICE_KEY: str = "your-service-role-key"

    # ── Redis (optional in dev) ───────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ── Celery (optional — falls back to sync) ────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ── Model Storage ─────────────────────────────────────────
    MODELS_DIR: Path = Path("models_saved")
    DATASETS_DIR: Path = Path("datasets")

    # ── Inference ─────────────────────────────────────────────
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.85
    WINDOW_SIZE: int = 10          # LSTM/Transformer sequence length
    NUM_FEATURES: int = 30

    # ── Alert Deduplication ───────────────────────────────────
    ALERT_DEDUPE_WINDOW_SECONDS: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
