"""
Data Preprocessor
=================
Handles the complete preprocessing pipeline for IDS datasets.

ORDER OF OPERATIONS (critical — wrong order = data leakage):
1. clean()      — remove inf, NaN, constant cols, duplicates
2. encode()     — string labels → integer
3. split()      — BEFORE scaling to prevent data leakage
4. scale()      — fit scaler on train ONLY, apply to all splits
5. balance()    — on TRAIN split ONLY
"""
import logging
from pathlib import Path
from typing import Literal, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.utils.class_weight import compute_class_weight

logger = logging.getLogger("deepshield.data.preprocessor")


def clean(X: np.ndarray, feature_names: list[str]) -> tuple[np.ndarray, list[str]]:
    """
    Clean feature matrix:
    - Replace inf/-inf with NaN
    - Drop columns that are all NaN or constant (std == 0)
    - Replace remaining NaN with 0
    """
    df = pd.DataFrame(X, columns=feature_names)

    # Replace infinities
    df = df.replace([np.inf, -np.inf], np.nan)

    # Remove constant columns (zero variance)
    stds = df.std()
    constant_cols = stds[stds == 0].index.tolist()
    if constant_cols:
        logger.info(f"Removing {len(constant_cols)} constant columns")
        df = df.drop(columns=constant_cols)

    # Remove columns that are all NaN
    all_nan_cols = df.columns[df.isnull().all()].tolist()
    if all_nan_cols:
        df = df.drop(columns=all_nan_cols)

    # Fill remaining NaN with 0
    df = df.fillna(0)

    remaining_features = list(df.columns)
    logger.info(f"After cleaning: {len(remaining_features)} features remain (from {len(feature_names)})")

    return df.values.astype(np.float32), remaining_features


def encode_labels(y: np.ndarray, mode: Literal["binary", "multiclass"] = "multiclass") -> np.ndarray:
    """
    Encode labels.
    - binary: 0=benign, 1=attack (any non-zero class)
    - multiclass: preserve all classes
    """
    if mode == "binary":
        return (y > 0).astype(np.int32)
    return y.astype(np.int32)


def split(
    X: np.ndarray,
    y: np.ndarray,
    test_size: float = 0.2,
    val_size: float = 0.1,
    stratify: bool = True,
    time_aware: bool = False,
    random_state: int = 42,
) -> tuple:
    """
    Split data into train/val/test sets.

    Parameters:
    - time_aware: if True, preserves temporal order (no shuffle)
    - stratify: if True, preserves class distribution in splits

    Returns: (X_train, X_val, X_test, y_train, y_val, y_test)
    """
    if time_aware:
        # Temporal split: no shuffling
        n = len(X)
        test_start = int(n * (1 - test_size))
        val_start = int(test_start * (1 - val_size / (1 - test_size)))

        X_train, y_train = X[:val_start], y[:val_start]
        X_val, y_val = X[val_start:test_start], y[val_start:test_start]
        X_test, y_test = X[test_start:], y[test_start:]
    else:
        strat = y if stratify else None
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=strat
        )

        # Split remaining into train and val
        val_fraction = val_size / (1 - test_size)
        strat_temp = y_temp if stratify else None
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_fraction, random_state=random_state, stratify=strat_temp
        )

    logger.info(
        f"Split: train={len(X_train)}, val={len(X_val)}, test={len(X_test)} | "
        f"Classes in train: {np.unique(y_train, return_counts=True)}"
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def scale(
    X_train: np.ndarray,
    X_val: np.ndarray,
    X_test: np.ndarray,
    save_path: Optional[Path] = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, MinMaxScaler]:
    """
    Scale features using MinMaxScaler.
    CRITICAL: Fit on X_train ONLY, then transform all splits.
    Saves the fitted scaler for inference use.
    """
    scaler = MinMaxScaler(feature_range=(0, 1))
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    # Save scaler for inference
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(scaler, save_path)
        logger.info(f"Scaler saved to {save_path}")

    return (
        X_train_scaled.astype(np.float32),
        X_val_scaled.astype(np.float32),
        X_test_scaled.astype(np.float32),
        scaler,
    )


def compute_class_weights_dict(y: np.ndarray) -> dict:
    """
    Compute balanced class weights for handling class imbalance.
    Returns dict suitable for Keras class_weight parameter.
    """
    classes = np.unique(y)
    weights = compute_class_weight("balanced", classes=classes, y=y)
    weight_dict = {int(c): float(w) for c, w in zip(classes, weights)}
    logger.info(f"Class weights: {weight_dict}")
    return weight_dict


def handle_imbalance(
    X: np.ndarray,
    y: np.ndarray,
    strategy: Literal["smote", "undersample", "class_weight"] = "class_weight",
) -> tuple[np.ndarray, np.ndarray, Optional[dict]]:
    """
    Handle class imbalance in the TRAINING set.

    Strategies:
    - smote: SMOTE oversampling for minority + undersampling majority
    - undersample: RandomUnderSampler only
    - class_weight: Return weights dict, do NOT resample

    Returns: (X_balanced, y_balanced, class_weights_or_None)
    """
    if strategy == "class_weight":
        weights = compute_class_weights_dict(y)
        return X, y, weights

    try:
        if strategy == "smote":
            from imblearn.combine import SMOTETomek
            sampler = SMOTETomek(random_state=42)
            X_res, y_res = sampler.fit_resample(X, y)
        elif strategy == "undersample":
            from imblearn.under_sampling import RandomUnderSampler
            sampler = RandomUnderSampler(random_state=42)
            X_res, y_res = sampler.fit_resample(X, y)
        else:
            return X, y, None

        logger.info(f"After {strategy}: {len(X_res)} samples (was {len(X)})")
        return X_res, y_res, None

    except ImportError:
        logger.warning(f"imbalanced-learn not available. Falling back to class_weight")
        weights = compute_class_weights_dict(y)
        return X, y, weights


def full_pipeline(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list[str],
    mode: str = "multiclass",
    balance_strategy: str = "class_weight",
    scaler_path: Optional[Path] = None,
) -> dict:
    """
    Run the complete preprocessing pipeline.

    Returns dict with all preprocessed data:
    {
        X_train, X_val, X_test,
        y_train, y_val, y_test,
        feature_names, scaler, class_weights,
        num_classes, class_distribution
    }
    """
    # 1. Clean
    X_clean, clean_features = clean(X, feature_names)

    # 2. Encode labels
    y_encoded = encode_labels(y, mode=mode)
    num_classes = len(np.unique(y_encoded))

    # 3. Split (BEFORE scaling!)
    X_train, X_val, X_test, y_train, y_val, y_test = split(X_clean, y_encoded)

    # 4. Scale (fit on train only)
    X_train, X_val, X_test, scaler = scale(X_train, X_val, X_test, save_path=scaler_path)

    # 5. Handle imbalance (on train only)
    X_train, y_train, class_weights = handle_imbalance(X_train, y_train, strategy=balance_strategy)

    return {
        "X_train": X_train,
        "X_val": X_val,
        "X_test": X_test,
        "y_train": y_train,
        "y_val": y_val,
        "y_test": y_test,
        "feature_names": clean_features,
        "scaler": scaler,
        "class_weights": class_weights,
        "num_classes": num_classes,
        "num_features": X_train.shape[1],
    }
