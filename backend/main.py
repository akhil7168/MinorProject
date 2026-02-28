"""
DeepShield — FastAPI Application Entry Point
=============================================
Registers all routers, configures middleware, and manages application lifespan.
The inference engine loads pre-trained models at startup for immediate use.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("deepshield")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    - On startup: create directories, load pre-trained models into memory.
    - On shutdown: cleanup resources.
    """
    logger.info("🛡️  DeepShield starting up...")

    # Ensure required directories exist
    settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    settings.DATASETS_DIR.mkdir(parents=True, exist_ok=True)

    # Load pre-trained models for inference
    try:
        from inference.engine import inference_engine
        await inference_engine.load_active_models()
        logger.info("✅ Pre-trained models loaded successfully")
    except Exception as e:
        logger.warning(f"⚠️  Could not load pre-trained models: {e}")
        logger.info("   Models can be trained via /api/v1/training/start")

    yield

    logger.info("🛡️  DeepShield shutting down...")


# ── Create FastAPI App ─────────────────────────────────────────
app = FastAPI(
    title="DeepShield",
    description="AI-Powered Network Intrusion Detection System",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Middleware ────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ───────────────────────────────────────────────
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "deepshield-backend", "version": "1.0.0"}


# ── Register API Routers ──────────────────────────────────────
from api.routes import datasets, training, inference, alerts, models, dashboard, websocket

app.include_router(datasets.router, prefix="/api/v1", tags=["Datasets"])
app.include_router(training.router, prefix="/api/v1", tags=["Training"])
app.include_router(inference.router, prefix="/api/v1", tags=["Inference"])
app.include_router(alerts.router, prefix="/api/v1", tags=["Alerts"])
app.include_router(models.router, prefix="/api/v1", tags=["Models"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])
app.include_router(websocket.router, prefix="", tags=["WebSocket"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
