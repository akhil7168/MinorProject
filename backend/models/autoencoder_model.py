"""
Autoencoder Model for IDS (Anomaly Detection)
==============================================
UNSUPERVISED anomaly detection — detects zero-day attacks.
Train ONLY on benign traffic. Reconstruction error = anomaly score.

Encoder: Dense(64,relu) → Dense(32,relu) → Dense(16,relu) [bottleneck]
Decoder: Dense(32,relu) → Dense(64,relu) → Dense(input_dim, sigmoid)

Inference:
- error > threshold → ANOMALY (attack)
- error <= threshold → BENIGN
"""
import numpy as np
import tensorflow as tf
from models.base_model import BaseIDSModel
import logging

logger = logging.getLogger("deepshield.models.autoencoder")


class AutoencoderModel(BaseIDSModel):
    MODEL_TYPE = "autoencoder"

    def __init__(self):
        super().__init__()
        self.threshold = None

    def build(
        self,
        input_shape: tuple,
        num_classes: int = 2,
        bottleneck_dim: int = 16,
        **kwargs,
    ) -> None:
        """Build autoencoder for anomaly detection."""
        self.num_classes = num_classes
        self.input_shape = input_shape
        input_dim = input_shape[0] if isinstance(input_shape, tuple) else input_shape

        inp = tf.keras.layers.Input(shape=(input_dim,))

        # Encoder
        x = tf.keras.layers.Dense(64, activation="relu")(inp)
        x = tf.keras.layers.Dense(32, activation="relu")(x)
        encoded = tf.keras.layers.Dense(bottleneck_dim, activation="relu")(x)

        # Decoder
        x = tf.keras.layers.Dense(32, activation="relu")(encoded)
        x = tf.keras.layers.Dense(64, activation="relu")(x)
        decoded = tf.keras.layers.Dense(input_dim, activation="sigmoid")(x)

        self.model = tf.keras.Model(inputs=inp, outputs=decoded)

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        config: dict,
        progress_callback=None,
    ) -> dict:
        """Train autoencoder on BENIGN traffic only."""
        epochs = config.get("epochs", 50)
        batch_size = config.get("batch_size", 256)
        lr = config.get("learning_rate", 0.001)

        # Filter benign-only for training
        benign_mask = y_train == 0
        X_benign = X_train[benign_mask]

        if len(X_benign) == 0:
            logger.warning("No benign samples found! Using all training data.")
            X_benign = X_train

        logger.info(f"Training autoencoder on {len(X_benign)} benign samples")

        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=lr),
            loss="mse",
        )

        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss",
                patience=config.get("early_stopping_patience", 10),
                restore_best_weights=True,
            ),
        ]
        if progress_callback:
            callbacks.append(progress_callback)

        # Validation: use benign from validation set
        val_benign_mask = y_val == 0
        X_val_benign = X_val[val_benign_mask] if val_benign_mask.any() else X_val

        history = self.model.fit(
            X_benign, X_benign,
            validation_data=(X_val_benign, X_val_benign),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1,
        )

        # Set anomaly threshold from training data
        self.set_threshold(X_benign)

        return history.history

    def get_reconstruction_error(self, X: np.ndarray) -> np.ndarray:
        """Compute per-sample reconstruction error (MSE)."""
        reconstructed = self.model.predict(X, verbose=0)
        mse = np.mean((X - reconstructed) ** 2, axis=1)
        return mse

    def set_threshold(self, X_benign: np.ndarray, percentile: float = 95) -> float:
        """Set anomaly threshold from benign data reconstruction errors."""
        errors = self.get_reconstruction_error(X_benign)
        self.threshold = float(np.percentile(errors, percentile))
        logger.info(f"Anomaly threshold set to {self.threshold:.6f} (p{percentile})")
        return self.threshold

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return probabilities: [P(benign), P(anomaly)]."""
        errors = self.get_reconstruction_error(X)
        threshold = self.threshold or 0.1

        # Normalize errors to get confidence scores
        anomaly_scores = np.clip(errors / (threshold * 2), 0, 1)

        probs = np.column_stack([1 - anomaly_scores, anomaly_scores])
        return probs.astype(np.float32)

    def detect(self, X: np.ndarray) -> np.ndarray:
        """Binary detection: 0=benign, 1=anomaly."""
        errors = self.get_reconstruction_error(X)
        threshold = self.threshold or 0.1
        return (errors > threshold).astype(np.int32)
