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
import asyncio
from capture.live_capture import LiveCapture
from capture.flow_aggregator import FlowAggregator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("deepshield")

settings = get_settings()

live_sniffer = LiveCapture()
flow_aggregator = FlowAggregator(timeout=10.0)  # 10s timeout for fast real-time response
main_loop = None

async def process_live_flow(flow: dict):
    from inference.engine import inference_engine
    if not inference_engine.get_model_status()["is_ready"]:
        return
        
    try:
        # Run inference using the default engine state
        result = await inference_engine.infer_single(flow)
        
        # Only log/alert if it's an attack (label != 0)
        if result.get("predicted_label", 0) != 0:
            from database import crud
            from api.routes.websocket import broadcast_alert
            from datetime import datetime, timezone
            
            alert_data = {
                "source_ip": str(flow.get("src_ip", "")),
                "destination_ip": str(flow.get("dst_ip", "")),
                "source_port": int(flow.get("src_port", 0)),
                "destination_port": int(flow.get("dst_port", 0)),
                "protocol": str(flow.get("protocol", "TCP")),
                "attack_type": result.get("predicted_class", "Unknown"),
                "severity": "high" if result.get("confidence", 0.0) > 0.8 else "medium",
                "status": "open",
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "confidence": result.get("confidence", 0.0),
                "details": {
                    "model_confidence": result.get("confidence", 0.0),
                    "flow_size": flow.get("Total Length of Fwd Packets", 0) + flow.get("Total Length of Bwd Packets", 0),
                }
            }
            alert = await crud.create_alert(alert_data)
            await broadcast_alert(alert)
    except Exception as e:
        logger.error(f"Live inference error: {e}")

def packet_callback(packet):
    flow = flow_aggregator.add_packet(packet)
    if flow and main_loop and main_loop.is_running():
        try:
            asyncio.run_coroutine_threadsafe(process_live_flow(flow), main_loop)
        except Exception:
            pass


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

    global main_loop
    main_loop = asyncio.get_running_loop()

    # Load pre-trained models for inference
    try:
        from inference.engine import inference_engine
        await inference_engine.load_active_models()
        logger.info("✅ Pre-trained models loaded successfully")
        
        # Start live capture now that models are ready
        live_sniffer.start(callback=packet_callback)
    except Exception as e:
        logger.warning(f"⚠️  Could not load pre-trained models: {e}")
        logger.info("   Models can be trained via /api/v1/training/start")

    yield

    logger.info("🛡️  DeepShield shutting down...")
    live_sniffer.stop()


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
