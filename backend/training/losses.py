"""
Loss Functions for IDS Training
================================
Custom TensorFlow-compatible loss functions optimized for
imbalanced network intrusion detection datasets.
"""
import tensorflow as tf
import numpy as np


def focal_loss(gamma: float = 2.0, alpha: float = 0.25):
    """
    Focal Loss — reduces weight of easy examples, focuses on hard ones.
    Especially effective for CICIDS-2017 with severe class imbalance.

    FL(pt) = -alpha * (1-pt)^gamma * log(pt)

    Higher gamma → more focus on hard examples.
    """
    def loss_fn(y_true, y_pred):
        y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)
        cross_entropy = -y_true * tf.math.log(y_pred)
        weight = alpha * y_true * tf.math.pow(1 - y_pred, gamma)
        return tf.reduce_mean(tf.reduce_sum(weight * cross_entropy, axis=-1))
    return loss_fn


def label_smoothing_crossentropy(smoothing: float = 0.1):
    """
    Label smoothing — prevents overconfident predictions, improves calibration.
    Replaces hard labels (0/1) with soft labels (smoothing/(n_classes), 1-smoothing).
    """
    def loss_fn(y_true, y_pred):
        n_classes = tf.cast(tf.shape(y_true)[-1], tf.float32)
        y_true_smooth = y_true * (1 - smoothing) + smoothing / n_classes
        return tf.keras.losses.categorical_crossentropy(y_true_smooth, y_pred)
    return loss_fn


def weighted_categorical_crossentropy(class_weights: dict):
    """
    Standard weighted categorical cross-entropy.
    Weights dict from compute_class_weights().
    """
    weights = np.array([class_weights.get(i, 1.0) for i in sorted(class_weights.keys())])
    weights_tensor = tf.constant(weights, dtype=tf.float32)

    def loss_fn(y_true, y_pred):
        y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)
        sample_weights = tf.reduce_sum(y_true * weights_tensor, axis=-1)
        ce = -tf.reduce_sum(y_true * tf.math.log(y_pred), axis=-1)
        return tf.reduce_mean(sample_weights * ce)
    return loss_fn


def get_loss_function(name: str, num_classes: int = 6, class_weights: dict = None):
    """Get loss function by name."""
    if name == "focal":
        return focal_loss(gamma=2.0, alpha=0.25)
    elif name == "weighted_ce" and class_weights:
        return weighted_categorical_crossentropy(class_weights)
    elif name == "label_smoothing":
        return label_smoothing_crossentropy(smoothing=0.1)
    else:
        return "categorical_crossentropy"
