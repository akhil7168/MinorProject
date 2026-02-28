"""
Hybrid CNN + LSTM Model for IDS
================================
CNN extracts local feature interactions, LSTM captures temporal dynamics.

Architecture:
  Input: (window_size, num_features)
  → Conv1D(64, 3, relu) + BatchNorm → MaxPool1D(2)
  → Conv1D(32, 3, relu)
  → LSTM(64, return_sequences=False, dropout=0.3)
  → Dense(64, relu) + Dropout(0.4)
  → Dense(num_classes, softmax)
"""
import numpy as np
import tensorflow as tf
from models.base_model import BaseIDSModel


class HybridCNNLSTM(BaseIDSModel):
    MODEL_TYPE = "hybrid"

    def build(
        self,
        input_shape: tuple,
        num_classes: int,
        dropout_rate: float = 0.4,
        **kwargs,
    ) -> None:
        """Build CNN+LSTM hybrid model."""
        self.num_classes = num_classes
        self.input_shape = input_shape

        inp = tf.keras.layers.Input(shape=input_shape)

        # CNN feature extraction
        x = tf.keras.layers.Conv1D(64, 3, padding="same", activation="relu")(inp)
        x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.MaxPool1D(pool_size=2)(x)
        x = tf.keras.layers.Conv1D(32, 3, padding="same", activation="relu")(x)

        # LSTM temporal processing
        x = tf.keras.layers.LSTM(64, return_sequences=False, dropout=0.3)(x)

        # Dense classifier
        x = tf.keras.layers.Dense(64, activation="relu")(x)
        x = tf.keras.layers.Dropout(dropout_rate)(x)
        out = tf.keras.layers.Dense(num_classes, activation="softmax")(x)

        self.model = tf.keras.Model(inputs=inp, outputs=out)

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        config: dict,
        progress_callback=None,
    ) -> dict:
        """Train hybrid model."""
        from training.losses import get_loss_function

        epochs = config.get("epochs", 50)
        batch_size = config.get("batch_size", 256)
        lr = config.get("learning_rate", 0.001)

        y_train_oh = tf.keras.utils.to_categorical(y_train, self.num_classes)
        y_val_oh = tf.keras.utils.to_categorical(y_val, self.num_classes)

        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=lr),
            loss=get_loss_function(config.get("loss_fn", "focal"), self.num_classes),
            metrics=["accuracy"],
        )

        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss",
                patience=config.get("early_stopping_patience", 10),
                restore_best_weights=True,
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6
            ),
        ]
        if progress_callback:
            callbacks.append(progress_callback)

        history = self.model.fit(
            X_train, y_train_oh,
            validation_data=(X_val, y_val_oh),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            class_weight=config.get("class_weights"),
            verbose=1,
        )

        return history.history
