"""
Bidirectional LSTM Model for IDS
================================
Architecture:
  Input: (window_size, num_features) — sequences of consecutive flows
  BiLSTM(64, return_sequences=True, dropout=0.3)
  BiLSTM(32, dropout=0.3)
  Dense(64, relu) + Dropout(0.3)
  Dense(num_classes, softmax)

Why Bidirectional?
→ Captures both past and future context in a traffic sequence.
→ A SYN flood followed by RSTs is recognizable forward and backward.
"""
import numpy as np
import tensorflow as tf
from models.base_model import BaseIDSModel


class LSTMModel(BaseIDSModel):
    MODEL_TYPE = "lstm"

    @staticmethod
    def create_sequences(
        X: np.ndarray, y: np.ndarray, window: int = 10, step: int = 1
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Reshape flat data into sliding window sequences.
        Label of each sequence = label of the last flow in window.

        For training: step=1 (overlapping windows)
        For inference: step=window_size (non-overlapping)
        """
        sequences = []
        labels = []
        for i in range(0, len(X) - window + 1, step):
            sequences.append(X[i: i + window])
            labels.append(y[i + window - 1])

        return np.array(sequences, dtype=np.float32), np.array(labels, dtype=np.int32)

    def build(
        self,
        input_shape: tuple,
        num_classes: int,
        lstm_units: list = None,
        dropout_rate: float = 0.3,
        recurrent_dropout: float = 0.2,
        **kwargs,
    ) -> None:
        """Build Bidirectional LSTM model."""
        if lstm_units is None:
            lstm_units = [64, 32]

        self.num_classes = num_classes
        self.input_shape = input_shape

        inp = tf.keras.layers.Input(shape=input_shape)

        x = tf.keras.layers.Bidirectional(
            tf.keras.layers.LSTM(
                lstm_units[0], return_sequences=True,
                dropout=dropout_rate, recurrent_dropout=recurrent_dropout,
            )
        )(inp)

        x = tf.keras.layers.Bidirectional(
            tf.keras.layers.LSTM(
                lstm_units[1],
                dropout=dropout_rate,
            )
        )(x)

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
        """Train the LSTM model on sequenced data."""
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
