"""
Models API Routes
=================
Endpoints for managing the model registry: listing, comparison, activation.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import crud

router = APIRouter()


@router.get("/models")
async def list_models():
    """List all registered models with their metrics."""
    models = await crud.list_models()
    return {"models": models}


@router.get("/models/{model_id}")
async def get_model(model_id: str):
    """Get a specific model's details."""
    models = await crud.list_models()
    model = next((m for m in models if m.get("id") == model_id), None)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.patch("/models/{model_id}/activate")
async def activate_model(model_id: str):
    """Set a model as the active model for its type."""
    await crud.set_model_active(model_id)
    return {"status": "activated", "model_id": model_id}


class CompareRequest(BaseModel):
    model_ids: list[str] = []
    dataset_id: Optional[str] = None


@router.post("/models/compare")
async def compare_models(request: CompareRequest):
    """Compare metrics across models."""
    models = await crud.list_models()

    if request.model_ids:
        models = [m for m in models if m.get("id") in request.model_ids]

    # Build comparison table
    comparison = []
    for m in models:
        metrics = m.get("metrics", {}) or {}
        comparison.append({
            "model_id": m.get("id"),
            "model_type": m.get("model_type"),
            "name": m.get("name"),
            "accuracy": metrics.get("accuracy", 0),
            "f1_macro": metrics.get("f1_macro", 0),
            "auc_roc_macro": metrics.get("auc_roc_macro", 0),
            "detection_rate": metrics.get("detection_rate", 0),
            "false_alarm_rate": metrics.get("false_alarm_rate", 0),
            "is_active": m.get("is_active", False),
        })

    return {"comparison": comparison}
