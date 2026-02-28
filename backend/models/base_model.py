"""
Base IDS Model
==============
Abstract base class for all deep learning IDS models.
Defines the interface that all model implementations must follow.
"""
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional

import numpy as np

logger = logging.getLogger("deepshield.models")


class BaseIDSModel(ABC):
    """
    Abstract base class for IDS deep learning models.
    All models (CNN, LSTM, Autoencoder, Transformer, Hybrid) inherit from this.
    """

    MODEL_TYPE: str = "base"

    def __init__(self):
        self.model = None
        self.num_classes = None
        self.input_shape = None

    @abstractmethod
    def build(self, input_shape: tuple, num_classes: int, **kwargs) -> None:
        """Build the Keras model. Store as self.model."""
        pass

    @abstractmethod
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        config: dict,
        progress_callback: Optional[Callable] = None,
    ) -> dict:
        """
        Train the model.
        Returns training history dict.
        """
        pass

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return class probability array shape (N, num_classes)."""
        if self.model is None:
            raise RuntimeError("Model not built or loaded")
        return self.model.predict(X, verbose=0)

    def predict_class(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Return integer class predictions."""
        probs = self.predict(X)
        if probs.shape[1] == 1:
            return (probs[:, 0] > threshold).astype(int)
        return np.argmax(probs, axis=1)

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """Return comprehensive metrics dict."""
        from training.metrics import compute_all_metrics

        y_pred_probs = self.predict(X_test)
        return compute_all_metrics(y_test, y_pred_probs)

    def get_model_summary(self) -> dict:
        """Return model architecture summary."""
        if self.model is None:
            return {}

        total_params = self.model.count_params()
        trainable = sum(
            int(np.prod(w.shape)) for w in self.model.trainable_weights
        )

        return {
            "total_params": total_params,
            "trainable_params": trainable,
            "non_trainable_params": total_params - trainable,
            "layer_count": len(self.model.layers),
        }

    def save(self, path: Path) -> None:
        """Save Keras model to .h5 file."""
        if self.model is None:
            raise RuntimeError("No model to save")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(str(path))
        logger.info(f"Model saved to {path}")

    def load(self, path: Path) -> None:
        """Load Keras model from .h5 file."""
        import tensorflow as tf
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")
        self.model = tf.keras.models.load_model(str(path), compile=False)
        logger.info(f"Model loaded from {path}")

    def export_tflite(self, path: Path, quantize: bool = True) -> float:
        """Convert to TFLite with optional quantization. Returns size in MB."""
        import tensorflow as tf

        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)

        if quantize:
            converter.optimizations = [tf.lite.Optimize.DEFAULT]

        tflite_model = converter.convert()

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(tflite_model)

        size_mb = len(tflite_model) / (1024 * 1024)
        logger.info(f"TFLite exported to {path} ({size_mb:.2f} MB)")
        return size_mb
