"""
Ensemble IDS
============
Weighted soft voting ensemble of all trained models.
Each model contributes a weighted probability vector.
Disagreement score measures model agreement.
"""
import logging
from typing import Optional

import numpy as np
from models.base_model import BaseIDSModel

logger = logging.getLogger("deepshield.models.ensemble")


class EnsembleIDS:
    """
    Weighted soft voting ensemble.
    Combines predictions from multiple models for maximum accuracy.
    """

    def __init__(self):
        self.models: dict[str, tuple[BaseIDSModel, float]] = {}
        self.num_classes = None

    def add_model(self, name: str, model: BaseIDSModel, weight: float = 1.0):
        """Add a model to the ensemble."""
        self.models[name] = (model, weight)
        if model.num_classes and self.num_classes is None:
            self.num_classes = model.num_classes

    def remove_model(self, name: str):
        """Remove a model from the ensemble."""
        self.models.pop(name, None)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Weighted soft voting prediction.
        Returns averaged probability array shape (N, num_classes).
        """
        if not self.models:
            raise RuntimeError("No models in ensemble")

        weighted_preds = []
        total_weight = 0

        for name, (model, weight) in self.models.items():
            try:
                probs = model.predict(X)
                weighted_preds.append(probs * weight)
                total_weight += weight
            except Exception as e:
                logger.warning(f"Model {name} prediction failed: {e}")

        if not weighted_preds:
            raise RuntimeError("All models failed prediction")

        # Weighted average
        ensemble_probs = np.sum(weighted_preds, axis=0) / total_weight
        return ensemble_probs

    def predict_class(self, X: np.ndarray) -> np.ndarray:
        """Return class predictions from ensemble."""
        probs = self.predict(X)
        return np.argmax(probs, axis=1)

    def predict_with_explanation(self, X: np.ndarray) -> list[dict]:
        """
        Full prediction with per-model breakdown.
        Returns list of dicts with class, confidence, per-model votes, disagreement score.
        """
        from data.loader import CLASS_NAMES

        if not self.models:
            raise RuntimeError("No models in ensemble")

        all_probs = {}
        weights = {}

        for name, (model, weight) in self.models.items():
            try:
                probs = model.predict(X)
                all_probs[name] = probs
                weights[name] = weight
            except Exception as e:
                logger.warning(f"Model {name} failed: {e}")

        if not all_probs:
            raise RuntimeError("All models failed")

        # Ensemble prediction
        total_weight = sum(weights.values())
        ensemble_probs = sum(
            probs * weights[name] for name, probs in all_probs.items()
        ) / total_weight

        results = []
        for i in range(len(X)):
            predicted_label = int(np.argmax(ensemble_probs[i]))
            predicted_class = CLASS_NAMES.get(predicted_label, f"Class_{predicted_label}")
            confidence = float(ensemble_probs[i][predicted_label])

            # Per-model votes
            per_model = {}
            confidences_per_model = []
            for name, probs in all_probs.items():
                model_label = int(np.argmax(probs[i]))
                model_conf = float(probs[i][model_label])
                per_model[name] = {
                    "class": CLASS_NAMES.get(model_label, f"Class_{model_label}"),
                    "confidence": round(model_conf, 4),
                }
                confidences_per_model.append(model_conf)

            # Disagreement: std of per-model max confidences
            disagreement = float(np.std(confidences_per_model))

            results.append({
                "predicted_class": predicted_class,
                "predicted_label": predicted_label,
                "confidence": round(confidence, 4),
                "per_model": per_model,
                "disagreement_score": round(disagreement, 4),
                "is_reliable": disagreement < 0.1,
            })

        return results

    def auto_weight(self, X_val: np.ndarray, y_val: np.ndarray):
        """
        Automatically set weights based on each model's validation F1 score.
        Better models get higher weights in the ensemble.
        """
        from sklearn.metrics import f1_score

        for name, (model, _) in list(self.models.items()):
            try:
                y_pred = model.predict_class(X_val)
                f1 = f1_score(y_val, y_pred, average="macro")
                self.models[name] = (model, max(f1, 0.01))
                logger.info(f"Ensemble weight for {name}: {f1:.4f}")
            except Exception as e:
                logger.warning(f"Could not compute weight for {name}: {e}")
                self.models[name] = (model, 0.5)
