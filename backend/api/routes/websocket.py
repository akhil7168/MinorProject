"""
WebSocket Routes
================
Real-time alert streaming and training progress via WebSocket.
Uses in-memory pub/sub when Redis is unavailable.
"""
import asyncio
import json
import logging
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("deepshield.ws")
router = APIRouter()

# ── In-memory connection tracking ──────────────────────────────
alert_connections: Set[WebSocket] = set()
training_connections: dict[str, Set[WebSocket]] = {}


@router.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time alert streaming."""
    await websocket.accept()
    alert_connections.add(websocket)
    logger.info(f"Alert WebSocket connected. Total: {len(alert_connections)}")

    try:
        while True:
            # Keep connection alive, listen for ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        alert_connections.discard(websocket)
        logger.info(f"Alert WebSocket disconnected. Total: {len(alert_connections)}")


@router.websocket("/ws/training/{run_id}")
async def ws_training(websocket: WebSocket, run_id: str):
    """WebSocket endpoint for training progress streaming."""
    await websocket.accept()

    if run_id not in training_connections:
        training_connections[run_id] = set()
    training_connections[run_id].add(websocket)
    logger.info(f"Training WS connected for {run_id}")

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        training_connections.get(run_id, set()).discard(websocket)
        logger.info(f"Training WS disconnected for {run_id}")


# ── Broadcast functions (called by alert_manager/trainer) ──────

async def broadcast_alert(alert_data: dict):
    """Broadcast a new alert to all connected WebSocket clients."""
    message = json.dumps({"type": "new_alert", "data": alert_data})
    disconnected = set()
    for ws in alert_connections:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add(ws)
    alert_connections.difference_update(disconnected)


async def broadcast_training_progress(run_id: str, data: dict):
    """Broadcast training progress to clients watching a specific run."""
    message = json.dumps({"type": "epoch_complete", "data": data})
    connections = training_connections.get(run_id, set())
    disconnected = set()
    for ws in connections:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add(ws)
    connections.difference_update(disconnected)


async def broadcast_training_complete(run_id: str, metrics: dict):
    """Broadcast training completion."""
    message = json.dumps({"type": "training_complete", "data": {"metrics": metrics}})
    connections = training_connections.get(run_id, set())
    for ws in connections:
        try:
            await ws.send_text(message)
        except Exception:
            pass
    # Clean up
    training_connections.pop(run_id, None)
