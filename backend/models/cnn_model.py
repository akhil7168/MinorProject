"""
1D CNN Model for IDS
====================
Architecture:
  Input: (num_features, 1) — reshape 1D feature vector for Conv1D
  Block 1: Conv1D(64, 3) → BatchNorm → MaxPool1D(2)
  Block 2: Conv1D(128, 3) → BatchNorm → MaxPool1D(2)
  Block 3: Conv1D(64, 3) → BatchNorm
  GlobalAveragePooling1D → Dense(128) → Dropout → Dense(64) → Dense(num_classes)

Why GlobalAveragePooling over Flatten?
→ Reduces params significantly, prevents overfitting, better generalization.
"""
import numpy as np
import tensorflow as tf
from models.base_model import BaseIDSModel


class CNNModel(BaseIDSModel):
    MODEL_TYPE = "cnn"

    def build(
        self,
        input_shape: tuple,
        num_classes: int,
        filters: list = None,
        kernel_size: int = 3,
        dropout_rate: float = 0.4,
        use_batch_norm: bool = True,
        **kwargs,
    ) -> None:
        """Build 1D CNN model."""
        if filters is None:
            filters = [64, 128, 64]

        self.num_classes = num_classes
        self.input_shape = input_shape

        # Input expects (num_features,) — we reshape to (num_features, 1) for Conv1D
        inp = tf.keras.layers.Input(shape=input_shape)

        # Reshape if needed: (features,) → (features, 1)
        if len(input_shape) == 1:
            x = tf.keras.layers.Reshape((input_shape[0], 1))(inp)
        else:
            x = inp

        # Block 1
        x = tf.keras.layers.Conv1D(filters[0], kernel_size, padding="same", activation="relu")(x)
        if use_batch_norm:
            x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.MaxPool1D(pool_size=2)(x)

        # Block 2
        x = tf.keras.layers.Conv1D(filters[1], kernel_size, padding="same", activation="relu")(x)
        if use_batch_norm:
            x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.MaxPool1D(pool_size=2)(x)

        # Block 3
        x = tf.keras.layers.Conv1D(filters[2], kernel_size, padding="same", activation="relu")(x)
        if use_batch_norm:
            x = tf.keras.layers.BatchNormalization()(x)

        # GlobalAveragePooling — more parameter-efficient than Flatten
        x = tf.keras.layers.GlobalAveragePooling1D()(x)

        # Dense head
        x = tf.keras.layers.Dense(128, activation="relu")(x)
        x = tf.keras.layers.Dropout(dropout_rate)(x)
        x = tf.keras.layers.Dense(64, activation="relu")(x)
        x = tf.keras.layers.Dropout(dropout_rate * 0.75)(x)

        # Output
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
        """Train the CNN model."""
        from training.losses import get_loss_function

        epochs = config.get("epochs", 50)
        batch_size = config.get("batch_size", 256)
        lr = config.get("learning_rate", 0.001)
        loss_fn = config.get("loss_fn", "focal")

        # Convert labels to one-hot
        y_train_oh = tf.keras.utils.to_categorical(y_train, self.num_classes)
        y_val_oh = tf.keras.utils.to_categorical(y_val, self.num_classes)

        # Compile
        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=lr),
            loss=get_loss_function(loss_fn, self.num_classes),
            metrics=["accuracy"],
        )

        # Callbacks
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

        # Train
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
