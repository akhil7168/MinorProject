"""
Model Trainer
=============
Non-blocking training engine. The API endpoint triggers training and returns
immediately. Progress is streamed via WebSocket and database updates.
"""
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np

from config import get_settings
from database import crud
from training.callbacks import ProgressCallback

logger = logging.getLogger("deepshield.training.trainer")
settings = get_settings()


# Model factory — maps model_type string to model class
def _get_model_class(model_type: str):
    """Get model class by type string."""
    from models.cnn_model import CNNModel
    from models.lstm_model import LSTMModel
    from models.autoencoder_model import AutoencoderModel
    from models.transformer_model import TransformerIDSModel
    from models.hybrid_model import HybridCNNLSTM

    model_map = {
        "cnn": CNNModel,
        "lstm": LSTMModel,
        "autoencoder": AutoencoderModel,
        "transformer": TransformerIDSModel,
        "hybrid": HybridCNNLSTM,
    }
    return model_map.get(model_type)


class ModelTrainer:
    """Orchestrates the full training pipeline."""

    async def train_async(self, run_id: str, config: dict) -> None:
        """
        Run the complete training pipeline.
        Steps:
        1. Load + preprocess dataset
        2. Build model
        3. Train with progress callback
        4. Evaluate on test set
        5. Save model + export TFLite
        6. Register in model registry
        """
        try:
            start_time = time.time()
            await crud.update_training_run(run_id, {
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
            })

            model_type = config["model_type"]
            logger.info(f"Starting training: {model_type} (run={run_id})")

            # ── Step 1: Load and preprocess dataset ──────────────
            dataset_id = config.get("dataset_id", "")
            dataset = await crud.get_dataset(dataset_id) if dataset_id else None
            dataset_name = dataset.get("name", "NSL-KDD") if dataset else "NSL-KDD"

            logger.info(f"Loading dataset: {dataset_name}")
            from data.loader import load_dataset
            X, y, feature_names = load_dataset(dataset_name)

            from data.preprocessor import full_pipeline
            scaler_path = settings.MODELS_DIR / f"{model_type}_scaler.pkl"
            data = full_pipeline(
                X, y, feature_names,
                mode=config.get("mode", "multiclass"),
                balance_strategy=config.get("balance_strategy", "class_weight"),
                scaler_path=scaler_path,
            )

            X_train = data["X_train"]
            X_val = data["X_val"]
            X_test = data["X_test"]
            y_train = data["y_train"]
            y_val = data["y_val"]
            y_test = data["y_test"]
            num_classes = data["num_classes"]
            num_features = data["num_features"]

            # ── Step 2: Build model ──────────────────────────────
            ModelClass = _get_model_class(model_type)
            if ModelClass is None:
                raise ValueError(f"Unknown model type: {model_type}")

            model = ModelClass()

            # Determine input shape based on model type
            window_size = config.get("window_size", 10)

            if model_type in ("lstm", "transformer", "hybrid"):
                # These models need sequence input: (window_size, num_features)
                from models.lstm_model import LSTMModel
                X_train, y_train = LSTMModel.create_sequences(X_train, y_train, window=window_size)
                X_val, y_val = LSTMModel.create_sequences(X_val, y_val, window=window_size)
                X_test, y_test = LSTMModel.create_sequences(X_test, y_test, window=window_size)
                input_shape = (window_size, num_features)
            else:
                # CNN and Autoencoder: (num_features,)
                input_shape = (num_features,)

            model.build(
                input_shape=input_shape,
                num_classes=num_classes,
                dropout_rate=config.get("dropout_rate", 0.3),
            )

            logger.info(f"Model built: {model.get_model_summary()}")

            # ── Step 3: Train ────────────────────────────────────
            progress_cb = ProgressCallback(run_id)
            config["class_weights"] = data.get("class_weights")

            history = model.train(
                X_train, y_train, X_val, y_val,
                config=config,
                progress_callback=progress_cb,
            )

            # ── Step 4: Evaluate ─────────────────────────────────
            logger.info("Evaluating model on test set...")
            metrics = model.evaluate(X_test, y_test)
            logger.info(f"Test metrics: accuracy={metrics['accuracy']}, f1={metrics['f1_macro']}")

            # ── Step 5: Save model ───────────────────────────────
            model_path = settings.MODELS_DIR / f"{model_type}_model.h5"
            model.save(model_path)

            tflite_path = settings.MODELS_DIR / f"{model_type}_model.tflite"
            try:
                model.export_tflite(tflite_path, quantize=config.get("use_quantization", True))
            except Exception as e:
                logger.warning(f"TFLite export failed: {e}")
                tflite_path = None

            # ── Step 6: Register and finalize ────────────────────
            duration = int(time.time() - start_time)

            # Build training history for storage
            training_history = []
            if history:
                num_epochs = len(history.get("loss", []))
                for i in range(num_epochs):
                    training_history.append({
                        "epoch": i + 1,
                        "loss": round(history["loss"][i], 4),
                        "val_loss": round(history.get("val_loss", [0])[min(i, len(history.get("val_loss", [0])) - 1)], 4),
                        "accuracy": round(history.get("accuracy", [0])[min(i, len(history.get("accuracy", [0])) - 1)], 4),
                        "val_accuracy": round(history.get("val_accuracy", [0])[min(i, len(history.get("val_accuracy", [0])) - 1)], 4),
                    })

            await crud.update_training_run(run_id, {
                "status": "completed",
                "metrics": metrics,
                "training_history": training_history,
                "confusion_matrix": metrics.get("confusion_matrix"),
                "classification_report": metrics.get("per_class"),
                "model_path": str(model_path),
                "tflite_path": str(tflite_path) if tflite_path else None,
                "scaler_path": str(scaler_path),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": duration,
            })

            # Register in model registry
            await crud.register_model(
                training_run_id=run_id,
                name=f"{model_type}_v1",
                model_type=model_type,
                paths={
                    "model_path": str(model_path),
                    "tflite_path": str(tflite_path) if tflite_path else None,
                    "scaler_path": str(scaler_path),
                },
                metrics=metrics,
            )

            logger.info(f"✅ Training complete for {model_type}: {duration}s, accuracy={metrics['accuracy']}")

            # Broadcast completion via WebSocket
            try:
                from api.routes.websocket import broadcast_training_complete
                import asyncio
                await broadcast_training_complete(run_id, metrics)
            except Exception:
                pass

        except Exception as e:
            logger.error(f"❌ Training failed for run {run_id}: {e}", exc_info=True)
            await crud.update_training_run(run_id, {
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })
            raise
