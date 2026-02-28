"""
Custom Keras Callbacks
======================
Callbacks for publishing training progress to WebSocket clients and database.
"""
import logging
import asyncio
import tensorflow as tf

logger = logging.getLogger("deepshield.training.callbacks")


class ProgressCallback(tf.keras.callbacks.Callback):
    """
    Custom callback that publishes epoch metrics to:
    1. Database (training_runs.training_history)
    2. WebSocket clients (via broadcast_training_progress)
    """

    def __init__(self, run_id: str):
        super().__init__()
        self.run_id = run_id

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}

        epoch_data = {
            "epoch": epoch + 1,
            "loss": round(float(logs.get("loss", 0)), 4),
            "val_loss": round(float(logs.get("val_loss", 0)), 4),
            "accuracy": round(float(logs.get("accuracy", 0)), 4),
            "val_accuracy": round(float(logs.get("val_accuracy", 0)), 4),
        }

        # Update database
        try:
            from database import crud
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(crud.append_epoch_to_history(self.run_id, epoch_data))
            else:
                loop.run_until_complete(crud.append_epoch_to_history(self.run_id, epoch_data))
        except Exception as e:
            logger.debug(f"Could not update DB: {e}")

        # Broadcast to WebSocket
        try:
            from api.routes.websocket import broadcast_training_progress
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(broadcast_training_progress(self.run_id, epoch_data))
        except Exception as e:
            logger.debug(f"Could not broadcast: {e}")

        logger.info(
            f"Epoch {epoch_data['epoch']}: "
            f"loss={epoch_data['loss']}, val_loss={epoch_data['val_loss']}, "
            f"acc={epoch_data['accuracy']}, val_acc={epoch_data['val_accuracy']}"
        )
