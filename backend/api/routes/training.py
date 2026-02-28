"""
Training API Routes
===================
Endpoints for triggering model training, checking progress, and listing history.
"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional

from database import crud

logger = logging.getLogger("deepshield.api.training")
router = APIRouter()


class TrainingConfig(BaseModel):
    """Training configuration sent by frontend."""
    model_type: str = Field(..., pattern="^(cnn|lstm|autoencoder|transformer|hybrid|ensemble)$")
    dataset_id: str
    epochs: int = Field(default=50, ge=1, le=500)
    batch_size: int = Field(default=256, ge=16, le=2048)
    learning_rate: float = Field(default=0.001, ge=1e-6, le=1.0)
    loss_fn: str = Field(default="focal", pattern="^(focal|weighted_ce|standard)$")
    balance_strategy: str = Field(default="class_weight", pattern="^(smote|class_weight|undersample)$")
    mode: str = Field(default="multiclass", pattern="^(binary|multiclass)$")
    use_quantization: bool = True
    window_size: int = Field(default=10, ge=1, le=100)
    dropout_rate: float = Field(default=0.3, ge=0, le=0.9)
    early_stopping_patience: int = Field(default=10, ge=1, le=50)


@router.post("/training/start")
async def start_training(config: TrainingConfig, background_tasks: BackgroundTasks):
    """Start a model training job in the background."""
    # Create training run record
    run = await crud.create_training_run(
        config=config.model_dump(),
        model_type=config.model_type,
        dataset_id=config.dataset_id,
    )

    # Start training in background
    background_tasks.add_task(_run_training, run["id"], config.model_dump())

    return {"training_run_id": run["id"], "status": "pending"}


async def _run_training(run_id: str, config: dict):
    """Execute training in background."""
    try:
        from training.trainer import ModelTrainer
        trainer = ModelTrainer()
        await trainer.train_async(run_id, config)
    except Exception as e:
        logger.error(f"Training failed for {run_id}: {e}")
        await crud.update_training_run(run_id, {
            "status": "failed",
            "error_message": str(e),
        })


@router.get("/training/{run_id}/progress")
async def get_training_progress(run_id: str):
    """Get current training progress for a run."""
    run = await crud.get_training_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")

    return {
        "id": run["id"],
        "status": run.get("status"),
        "model_type": run.get("model_type"),
        "current_epoch": run.get("current_epoch", 0),
        "total_epochs": run.get("total_epochs"),
        "metrics": run.get("metrics"),
        "training_history": run.get("training_history", []),
        "error_message": run.get("error_message"),
    }


@router.get("/training/history")
async def list_training_history(model_type: Optional[str] = None, limit: int = 50):
    """List all training runs with their final metrics."""
    runs = await crud.list_training_runs(model_type=model_type, limit=limit)
    return {"training_runs": runs}
