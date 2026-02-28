"""
DeepShield CRUD Operations
==========================
All database operations are centralized here.
Routes NEVER touch the database directly — they call these functions.
Each function handles errors and returns typed results.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from database.supabase_client import get_client

logger = logging.getLogger("deepshield.crud")


# ═══════════════════════════════════════════════════════════════
# DATASETS
# ═══════════════════════════════════════════════════════════════

async def get_all_datasets() -> list[dict]:
    """Get all datasets with their metadata and status."""
    try:
        client = get_client()
        result = client.table("datasets").select("*").order("created_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to fetch datasets: {e}")
        return []


async def get_dataset(dataset_id: str) -> Optional[dict]:
    """Get a single dataset by ID."""
    try:
        client = get_client()
        result = client.table("datasets").select("*").eq("id", dataset_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Failed to fetch dataset {dataset_id}: {e}")
        return None


async def upsert_dataset(data: dict) -> dict:
    """Create or update a dataset record."""
    try:
        client = get_client()
        if "id" not in data:
            data["id"] = str(uuid4())
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = client.table("datasets").upsert(data).execute()
        return result.data[0] if result.data else data
    except Exception as e:
        logger.error(f"Failed to upsert dataset: {e}")
        return data


async def update_dataset_status(dataset_id: str, status: str, progress: int = None):
    """Update dataset download status and progress."""
    try:
        client = get_client()
        updates = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
        if progress is not None:
            updates["download_progress"] = progress
        client.table("datasets").update(updates).eq("id", dataset_id).execute()
    except Exception as e:
        logger.error(f"Failed to update dataset status: {e}")


# ═══════════════════════════════════════════════════════════════
# TRAINING RUNS
# ═══════════════════════════════════════════════════════════════

async def create_training_run(config: dict, model_type: str, dataset_id: str) -> dict:
    """Create a new training run record."""
    try:
        client = get_client()
        data = {
            "id": str(uuid4()),
            "model_type": model_type,
            "dataset_id": dataset_id,
            "status": "pending",
            "config": config,
            "current_epoch": 0,
            "total_epochs": config.get("epochs", 50),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        result = client.table("training_runs").insert(data).execute()
        return result.data[0] if result.data else data
    except Exception as e:
        logger.error(f"Failed to create training run: {e}")
        raise


async def update_training_run(run_id: str, updates: dict) -> dict:
    """Update a training run with new data."""
    try:
        client = get_client()
        result = client.table("training_runs").update(updates).eq("id", run_id).execute()
        return result.data[0] if result.data else updates
    except Exception as e:
        logger.error(f"Failed to update training run {run_id}: {e}")
        return updates


async def get_training_run(run_id: str) -> Optional[dict]:
    """Get a single training run by ID."""
    try:
        client = get_client()
        result = client.table("training_runs").select("*").eq("id", run_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Failed to fetch training run {run_id}: {e}")
        return None


async def list_training_runs(model_type: str = None, limit: int = 50) -> list[dict]:
    """List training runs, optionally filtered by model type."""
    try:
        client = get_client()
        query = client.table("training_runs").select("*").order("created_at", desc=True).limit(limit)
        if model_type:
            query = query.eq("model_type", model_type)
        result = query.execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to list training runs: {e}")
        return []


async def append_epoch_to_history(run_id: str, epoch_data: dict):
    """Append epoch metrics to training history."""
    try:
        run = await get_training_run(run_id)
        if run:
            history = run.get("training_history") or []
            history.append(epoch_data)
            await update_training_run(run_id, {
                "training_history": history,
                "current_epoch": epoch_data.get("epoch", 0),
            })
    except Exception as e:
        logger.error(f"Failed to append epoch to history: {e}")


# ═══════════════════════════════════════════════════════════════
# MODEL REGISTRY
# ═══════════════════════════════════════════════════════════════

async def register_model(training_run_id: str, name: str, model_type: str, paths: dict, metrics: dict = None) -> dict:
    """Register a trained model in the registry."""
    try:
        client = get_client()
        data = {
            "id": str(uuid4()),
            "name": name,
            "model_type": model_type,
            "training_run_id": training_run_id,
            "is_active": True,
            "version": 1,
            "model_path": paths.get("model_path", ""),
            "tflite_path": paths.get("tflite_path"),
            "scaler_path": paths.get("scaler_path"),
            "metrics": metrics,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        result = client.table("model_registry").insert(data).execute()
        return result.data[0] if result.data else data
    except Exception as e:
        logger.error(f"Failed to register model: {e}")
        raise


async def get_active_model(model_type: str) -> Optional[dict]:
    """Get the active model for a given type."""
    try:
        client = get_client()
        result = (client.table("model_registry")
                  .select("*")
                  .eq("model_type", model_type)
                  .eq("is_active", True)
                  .limit(1)
                  .execute())
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Failed to fetch active model for {model_type}: {e}")
        return None


async def set_model_active(model_id: str):
    """Set a model as active, deactivating others of the same type."""
    try:
        client = get_client()
        # Get the model to find its type
        model = client.table("model_registry").select("*").eq("id", model_id).execute()
        if model.data:
            model_type = model.data[0]["model_type"]
            # Deactivate all of same type
            client.table("model_registry").update({"is_active": False}).eq("model_type", model_type).execute()
            # Activate this one
            client.table("model_registry").update({"is_active": True}).eq("id", model_id).execute()
    except Exception as e:
        logger.error(f"Failed to set model active: {e}")


async def list_models() -> list[dict]:
    """List all registered models."""
    try:
        client = get_client()
        result = client.table("model_registry").select("*").order("created_at", desc=True).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        return []


# ═══════════════════════════════════════════════════════════════
# ANALYSIS SESSIONS
# ═══════════════════════════════════════════════════════════════

async def create_session(session_type: str, filename: str = None) -> dict:
    """Create a new analysis session."""
    try:
        client = get_client()
        data = {
            "id": str(uuid4()),
            "session_type": session_type,
            "filename": filename,
            "status": "pending",
            "total_flows": 0,
            "benign_count": 0,
            "attack_count": 0,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        result = client.table("analysis_sessions").insert(data).execute()
        return result.data[0] if result.data else data
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise


async def update_session(session_id: str, updates: dict):
    """Update an analysis session."""
    try:
        client = get_client()
        client.table("analysis_sessions").update(updates).eq("id", session_id).execute()
    except Exception as e:
        logger.error(f"Failed to update session {session_id}: {e}")


async def get_session(session_id: str) -> Optional[dict]:
    """Get an analysis session by ID."""
    try:
        client = get_client()
        result = client.table("analysis_sessions").select("*").eq("id", session_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Failed to fetch session {session_id}: {e}")
        return None


async def list_sessions(limit: int = 20) -> list[dict]:
    """List analysis sessions."""
    try:
        client = get_client()
        result = (client.table("analysis_sessions")
                  .select("*")
                  .order("started_at", desc=True)
                  .limit(limit)
                  .execute())
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        return []


# ═══════════════════════════════════════════════════════════════
# FLOW DETECTIONS
# ═══════════════════════════════════════════════════════════════

async def bulk_insert_detections(detections: list[dict]):
    """Bulk insert flow detection results."""
    try:
        client = get_client()
        # Add IDs if missing
        for d in detections:
            if "id" not in d:
                d["id"] = str(uuid4())
            if "detected_at" not in d:
                d["detected_at"] = datetime.now(timezone.utc).isoformat()
        # Insert in batches of 500
        batch_size = 500
        for i in range(0, len(detections), batch_size):
            batch = detections[i:i + batch_size]
            client.table("flow_detections").insert(batch).execute()
        logger.info(f"Inserted {len(detections)} flow detections")
    except Exception as e:
        logger.error(f"Failed to bulk insert detections: {e}")


async def get_session_detections(session_id: str, page: int = 1, limit: int = 100) -> list[dict]:
    """Get paginated flow detections for a session."""
    try:
        client = get_client()
        offset = (page - 1) * limit
        result = (client.table("flow_detections")
                  .select("*")
                  .eq("session_id", session_id)
                  .order("detected_at", desc=True)
                  .limit(limit)
                  .execute())
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to fetch detections for session {session_id}: {e}")
        return []


async def get_attack_breakdown(session_id: str) -> dict:
    """Get attack type counts for a session."""
    try:
        detections = await get_session_detections(session_id, limit=10000)
        breakdown = {}
        for d in detections:
            if d.get("is_attack") or d.get("predicted_class", "BENIGN") != "BENIGN":
                attack_type = d.get("predicted_class", "Unknown")
                breakdown[attack_type] = breakdown.get(attack_type, 0) + 1
        return breakdown
    except Exception as e:
        logger.error(f"Failed to get attack breakdown: {e}")
        return {}


# ═══════════════════════════════════════════════════════════════
# ALERTS
# ═══════════════════════════════════════════════════════════════

async def create_alert(alert_data: dict) -> dict:
    """Create a new alert."""
    try:
        client = get_client()
        if "id" not in alert_data:
            alert_data["id"] = str(uuid4())
        if "created_at" not in alert_data:
            alert_data["created_at"] = datetime.now(timezone.utc).isoformat()
        result = client.table("alerts").insert(alert_data).execute()
        return result.data[0] if result.data else alert_data
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        raise


async def get_alerts(
    severity: str = None,
    status: str = None,
    attack_type: str = None,
    limit: int = 50,
    page: int = 1,
) -> list[dict]:
    """Get alerts with optional filters."""
    try:
        client = get_client()
        query = client.table("alerts").select("*").order("created_at", desc=True).limit(limit)
        if severity:
            query = query.eq("severity", severity)
        if status:
            query = query.eq("status", status)
        if attack_type:
            query = query.eq("attack_type", attack_type)
        result = query.execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Failed to fetch alerts: {e}")
        return []


async def update_alert_status(alert_id: str, status: str, notes: str = None):
    """Update alert status and optionally add notes."""
    try:
        client = get_client()
        updates = {"status": status}
        if notes:
            updates["notes"] = notes
        if status == "acknowledged":
            updates["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
        elif status == "resolved":
            updates["resolved_at"] = datetime.now(timezone.utc).isoformat()
        client.table("alerts").update(updates).eq("id", alert_id).execute()
    except Exception as e:
        logger.error(f"Failed to update alert {alert_id}: {e}")


async def get_alert_stats() -> dict:
    """Get alert summary statistics."""
    try:
        alerts = await get_alerts(limit=10000)
        stats = {
            "total": len(alerts),
            "open": len([a for a in alerts if a.get("status") == "open"]),
            "critical": len([a for a in alerts if a.get("severity") == "critical"]),
            "high": len([a for a in alerts if a.get("severity") == "high"]),
            "medium": len([a for a in alerts if a.get("severity") == "medium"]),
            "low": len([a for a in alerts if a.get("severity") == "low"]),
            "acknowledged": len([a for a in alerts if a.get("status") == "acknowledged"]),
            "resolved": len([a for a in alerts if a.get("status") == "resolved"]),
        }
        return stats
    except Exception as e:
        logger.error(f"Failed to get alert stats: {e}")
        return {"total": 0, "open": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}


# ═══════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════

async def get_dashboard_stats() -> dict:
    """Get dashboard summary statistics."""
    try:
        client = get_client()
        # Get recent sessions
        sessions = await list_sessions(limit=100)
        total_flows = sum(s.get("total_flows", 0) for s in sessions)
        total_attacks = sum(s.get("attack_count", 0) for s in sessions)

        # Get alert stats
        alert_stats = await get_alert_stats()

        # Get active models count
        models = await list_models()
        active_models = [m for m in models if m.get("is_active")]

        # Compute average accuracy from active models
        accuracies = [m.get("metrics", {}).get("accuracy", 0) for m in active_models if m.get("metrics")]
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0

        return {
            "total_flows_24h": total_flows,
            "total_attacks_24h": total_attacks,
            "attack_rate_percent": round((total_attacks / total_flows * 100) if total_flows > 0 else 0, 2),
            "active_models": len(active_models),
            "open_alerts": alert_stats.get("open", 0),
            "critical_alerts": alert_stats.get("critical", 0),
            "model_ensemble_accuracy": round(avg_accuracy, 4),
        }
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        return {
            "total_flows_24h": 0,
            "total_attacks_24h": 0,
            "attack_rate_percent": 0,
            "active_models": 0,
            "open_alerts": 0,
            "critical_alerts": 0,
            "model_ensemble_accuracy": 0,
        }


async def get_traffic_timeline(hours: int = 24) -> list[dict]:
    """Get hourly traffic data for timeline chart."""
    try:
        # Generate hourly buckets with counts from sessions
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        timeline = []
        for i in range(hours, 0, -1):
            hour = now - timedelta(hours=i)
            timeline.append({
                "hour": hour.strftime("%H:%M"),
                "timestamp": hour.isoformat(),
                "total_flows": 0,
                "attack_flows": 0,
                "benign_flows": 0,
            })
        return timeline
    except Exception as e:
        logger.error(f"Failed to get traffic timeline: {e}")
        return []


async def get_attack_distribution() -> list[dict]:
    """Get attack type distribution across all sessions."""
    try:
        sessions = await list_sessions(limit=100)
        distribution = {}
        for s in sessions:
            breakdown = s.get("attack_breakdown") or {}
            for attack_type, count in breakdown.items():
                distribution[attack_type] = distribution.get(attack_type, 0) + count

        return [{"type": k, "count": v} for k, v in distribution.items()]
    except Exception as e:
        logger.error(f"Failed to get attack distribution: {e}")
        return []


# ═══════════════════════════════════════════════════════════════
# MODEL COMPARISON
# ═══════════════════════════════════════════════════════════════

async def save_model_comparison(name: str, dataset_id: str, results: list[dict]) -> dict:
    """Save a model comparison result."""
    try:
        client = get_client()
        data = {
            "id": str(uuid4()),
            "name": name,
            "dataset_id": dataset_id,
            "results": results,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        result = client.table("model_comparison").insert(data).execute()
        return result.data[0] if result.data else data
    except Exception as e:
        logger.error(f"Failed to save model comparison: {e}")
        raise
