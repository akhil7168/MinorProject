"""
Lightweight Transformer for IDS
================================
Keeps params under 200K for fast CPU inference.

embed_dim=32, num_heads=2, ff_dim=64, num_blocks=2

Architecture:
  Input: (window_size, num_features)
  → Dense(32) [linear projection]
  → PositionalEncoding [sinusoidal]
  → TransformerBlock × 2
  → GlobalAveragePooling1D
  → Dense(32, relu) + Dropout
  → Dense(num_classes, softmax)

Why GELU in FFN? → Smoother gradient flow, better for transformers.
"""
import numpy as np
import tensorflow as tf
from models.base_model import BaseIDSModel


class PositionalEncoding(tf.keras.layers.Layer):
    """Sinusoidal positional encoding — fixed, not learned (saves params)."""

    def __init__(self, max_len: int = 100, embed_dim: int = 32, **kwargs):
        super().__init__(**kwargs)
        self.max_len = max_len
        self.embed_dim = embed_dim

    def build(self, input_shape):
        positions = np.arange(self.max_len)[:, np.newaxis]
        dims = np.arange(self.embed_dim)[np.newaxis, :]

        angles = positions / np.power(10000, (2 * (dims // 2)) / self.embed_dim)
        angles[:, 0::2] = np.sin(angles[:, 0::2])
        angles[:, 1::2] = np.cos(angles[:, 1::2])

        self.pos_encoding = tf.constant(angles[np.newaxis, :, :], dtype=tf.float32)
        super().build(input_shape)

    def call(self, x):
        seq_len = tf.shape(x)[1]
        return x + self.pos_encoding[:, :seq_len, :]

    def get_config(self):
        config = super().get_config()
        config.update({"max_len": self.max_len, "embed_dim": self.embed_dim})
        return config


class TransformerBlock(tf.keras.layers.Layer):
    """Single transformer block: MHA + FFN + LayerNorm + residual."""

    def __init__(self, embed_dim: int = 32, num_heads: int = 2,
                 ff_dim: int = 64, dropout: float = 0.1, **kwargs):
        super().__init__(**kwargs)
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.dropout_rate = dropout

    def build(self, input_shape):
        self.att = tf.keras.layers.MultiHeadAttention(
            num_heads=self.num_heads, key_dim=self.embed_dim // self.num_heads
        )
        self.ffn = tf.keras.Sequential([
            tf.keras.layers.Dense(self.ff_dim, activation="gelu"),
            tf.keras.layers.Dense(self.embed_dim),
        ])
        self.layernorm1 = tf.keras.layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = tf.keras.layers.LayerNormalization(epsilon=1e-6)
        self.dropout1 = tf.keras.layers.Dropout(self.dropout_rate)
        self.dropout2 = tf.keras.layers.Dropout(self.dropout_rate)
        super().build(input_shape)

    def call(self, inputs, training=False):
        # Multi-Head Attention + Residual + LayerNorm
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output, training=training)
        x = self.layernorm1(inputs + attn_output)

        # Feed-Forward + Residual + LayerNorm
        ffn_output = self.ffn(x)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(x + ffn_output)

    def get_config(self):
        config = super().get_config()
        config.update({
            "embed_dim": self.embed_dim,
            "num_heads": self.num_heads,
            "ff_dim": self.ff_dim,
            "dropout": self.dropout_rate,
        })
        return config


class TransformerIDSModel(BaseIDSModel):
    MODEL_TYPE = "transformer"

    def build(
        self,
        input_shape: tuple,
        num_classes: int,
        embed_dim: int = 32,
        num_heads: int = 2,
        ff_dim: int = 64,
        num_blocks: int = 2,
        dropout_rate: float = 0.3,
        **kwargs,
    ) -> None:
        """Build lightweight transformer model."""
        self.num_classes = num_classes
        self.input_shape = input_shape

        inp = tf.keras.layers.Input(shape=input_shape)

        # Linear projection to embedding space
        x = tf.keras.layers.Dense(embed_dim)(inp)

        # Positional encoding
        x = PositionalEncoding(max_len=input_shape[0], embed_dim=embed_dim)(x)

        # Transformer blocks
        for _ in range(num_blocks):
            x = TransformerBlock(embed_dim, num_heads, ff_dim, dropout_rate)(x)

        # Pool and classify
        x = tf.keras.layers.GlobalAveragePooling1D()(x)
        x = tf.keras.layers.Dense(32, activation="relu")(x)
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
        """Train transformer model."""
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
