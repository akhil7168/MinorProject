"""
SHAP Explainer
==============
Model-agnostic explanations for IDS predictions using SHAP.
"""
import logging
import numpy as np

logger = logging.getLogger("deepshield.inference.explainer")


class SHAPExplainer:
    """SHAP-based explanation for predictions."""

    def __init__(self, predict_fn, background_data: np.ndarray, feature_names: list[str]):
        self.predict_fn = predict_fn
        self.background_data = background_data[:100]
        self.feature_names = feature_names
        self._explainer = None

    def _get_explainer(self):
        if self._explainer is None:
            try:
                import shap
                self._explainer = shap.KernelExplainer(self.predict_fn, self.background_data)
            except ImportError:
                logger.warning("SHAP not available")
                return None
        return self._explainer

    def explain(self, X: np.ndarray, top_k: int = 8) -> list[list[dict]]:
        """
        Explain predictions for batch of samples.
        Returns for each sample: list of top_k feature contributions.
        """
        explainer = self._get_explainer()
        if explainer is None:
            return [[] for _ in range(len(X))]

        try:
            import shap
            shap_values = explainer.shap_values(X)

            # Handle multi-class output
            if isinstance(shap_values, list):
                # Use the predicted class's SHAP values
                main_shap = np.abs(np.array(shap_values)).mean(axis=0)
            else:
                main_shap = np.abs(shap_values)

            results = []
            for i in range(len(X)):
                sample_shap = main_shap[i] if len(main_shap.shape) > 1 else main_shap

                feature_contributions = []
                for j, (name, shap_val) in enumerate(zip(self.feature_names, sample_shap)):
                    feature_contributions.append({
                        "feature": name,
                        "value": float(X[i][j]) if j < len(X[i]) else 0,
                        "shap_value": float(shap_val),
                        "direction": "increases_risk" if shap_val > 0 else "decreases_risk",
                    })

                # Sort by absolute SHAP value, take top_k
                feature_contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
                results.append(feature_contributions[:top_k])

            return results

        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            return [[] for _ in range(len(X))]

    def explain_single(self, x: np.ndarray) -> list[dict]:
        """Explain a single prediction."""
        results = self.explain(x.reshape(1, -1))
        return results[0] if results else []
