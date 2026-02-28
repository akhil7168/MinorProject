"""
Inference Engine
================
Singleton that holds all active models in memory for fast inference.
Loaded at app startup from model registry.
"""
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import joblib

from config import get_settings

logger = logging.getLogger("deepshield.inference.engine")
settings = get_settings()


class InferenceEngine:
    """
    Singleton inference engine.
    Holds all active models in memory for fast prediction.
    """

    def __init__(self):
        self.models = {}      # name → model instance
        self.scalers = {}     # name → fitted scaler
        self.ensemble = None
        self._loaded = False

    async def load_active_models(self) -> None:
        """Load all active models from the model registry."""
        from database import crud
        from models.cnn_model import CNNModel
        from models.lstm_model import LSTMModel
        from models.autoencoder_model import AutoencoderModel
        from models.transformer_model import TransformerIDSModel
        from models.hybrid_model import HybridCNNLSTM
        from models.ensemble import EnsembleIDS

        model_classes = {
            "cnn": CNNModel,
            "lstm": LSTMModel,
            "autoencoder": AutoencoderModel,
            "transformer": TransformerIDSModel,
            "hybrid": HybridCNNLSTM,
        }

        registered_models = await crud.list_models()
        active_models = [m for m in registered_models if m.get("is_active")]

        for model_info in active_models:
            model_type = model_info.get("model_type")
            model_path = model_info.get("model_path")
            scaler_path = model_info.get("scaler_path")

            if not model_path or not Path(model_path).exists():
                logger.warning(f"Model file not found: {model_path}")
                continue

            try:
                ModelClass = model_classes.get(model_type)
                if ModelClass is None:
                    continue

                model = ModelClass()
                model.load(Path(model_path))
                self.models[model_type] = model

                # Load scaler
                if scaler_path and Path(scaler_path).exists():
                    self.scalers[model_type] = joblib.load(scaler_path)

                logger.info(f"Loaded model: {model_type} from {model_path}")

            except Exception as e:
                logger.error(f"Failed to load {model_type}: {e}")

        # Build ensemble from loaded models
        if self.models:
            self.ensemble = EnsembleIDS()
            for name, model in self.models.items():
                self.ensemble.add_model(name, model)
            logger.info(f"Ensemble built with {len(self.models)} models")

        self._loaded = True

    async def infer_single(self, features: dict) -> dict:
        """
        Run inference on a single flow's features.
        Returns prediction with per-model breakdown.
        """
        from data.loader import CLASS_NAMES

        # Convert features dict to array
        feature_values = np.array(list(features.values()), dtype=np.float32).reshape(1, -1)

        # Scale features
        scaler = next(iter(self.scalers.values()), None)
        if scaler:
            feature_values = scaler.transform(feature_values)

        if self.ensemble and len(self.models) > 1:
            results = self.ensemble.predict_with_explanation(feature_values)
            return results[0]
        elif self.models:
            # Use first available model
            name, model = next(iter(self.models.items()))
            probs = model.predict(feature_values)
            predicted_label = int(np.argmax(probs[0]))
            return {
                "predicted_class": CLASS_NAMES.get(predicted_label, f"Class_{predicted_label}"),
                "predicted_label": predicted_label,
                "confidence": float(probs[0][predicted_label]),
                "per_model": {name: {"class": CLASS_NAMES.get(predicted_label, ""), "confidence": float(probs[0][predicted_label])}},
                "disagreement_score": 0,
                "is_reliable": True,
            }
        else:
            raise RuntimeError("No models loaded for inference")

    async def infer_batch(self, X: np.ndarray) -> list[dict]:
        """Efficient batch inference for CSV/PCAP uploads."""
        from data.loader import CLASS_NAMES

        # Scale
        scaler = next(iter(self.scalers.values()), None)
        if scaler:
            X = scaler.transform(X)

        if self.ensemble and len(self.models) > 1:
            return self.ensemble.predict_with_explanation(X)
        elif self.models:
            name, model = next(iter(self.models.items()))
            probs = model.predict(X)
            results = []
            for i in range(len(X)):
                label = int(np.argmax(probs[i]))
                results.append({
                    "predicted_class": CLASS_NAMES.get(label, f"Class_{label}"),
                    "predicted_label": label,
                    "confidence": float(probs[i][label]),
                    "model_votes": {name: {"class": CLASS_NAMES.get(label, ""), "confidence": float(probs[i][label])}},
                })
            return results
        else:
            raise RuntimeError("No models loaded")

    def get_model_status(self) -> dict:
        """Which models are loaded and ready."""
        return {
            "loaded_models": list(self.models.keys()),
            "has_ensemble": self.ensemble is not None,
            "has_scalers": list(self.scalers.keys()),
            "is_ready": self._loaded and len(self.models) > 0,
        }


# Singleton instance
inference_engine = InferenceEngine()
