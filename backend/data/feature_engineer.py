"""
Feature Engineering
===================
Feature selection, importance analysis, and flow feature extraction.
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("deepshield.data.features")


def remove_correlated(
    X: np.ndarray,
    feature_names: list[str],
    threshold: float = 0.95,
) -> tuple[np.ndarray, list[str]]:
    """
    Remove highly correlated features.
    Keeps the first of each correlated pair (lower index).
    """
    df = pd.DataFrame(X, columns=feature_names)
    corr_matrix = df.corr().abs()

    # Upper triangle mask
    upper = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    )

    # Find columns to drop
    to_drop = [col for col in upper.columns if any(upper[col] > threshold)]

    if to_drop:
        logger.info(f"Removing {len(to_drop)} correlated features (threshold={threshold})")
        df = df.drop(columns=to_drop)

    return df.values.astype(np.float32), list(df.columns)


def select_top_k_mutual_information(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list[str],
    k: int = 30,
) -> tuple[np.ndarray, list[str], list[dict]]:
    """
    Select top-k features by mutual information with the target.
    Returns (X_selected, selected_names, mi_scores).
    """
    from sklearn.feature_selection import mutual_info_classif

    mi_scores = mutual_info_classif(X, y, random_state=42)
    mi_ranking = sorted(
        zip(feature_names, mi_scores), key=lambda x: x[1], reverse=True
    )

    top_k = mi_ranking[:k]
    selected_names = [name for name, _ in top_k]
    selected_idx = [feature_names.index(name) for name in selected_names]

    scores = [{"feature": name, "mi_score": float(score)} for name, score in top_k]

    logger.info(f"Selected top {k} features by MI. Best: {top_k[0][0]} ({top_k[0][1]:.4f})")
    return X[:, selected_idx], selected_names, scores


def select_variance_threshold(
    X: np.ndarray,
    feature_names: list[str],
    threshold: float = 0.01,
) -> tuple[np.ndarray, list[str]]:
    """Remove features with variance below threshold."""
    from sklearn.feature_selection import VarianceThreshold

    selector = VarianceThreshold(threshold=threshold)
    X_selected = selector.fit_transform(X)
    mask = selector.get_support()
    selected_names = [f for f, m in zip(feature_names, mask) if m]

    logger.info(f"Variance filter: {len(selected_names)} features remain (was {len(feature_names)})")
    return X_selected, selected_names


def get_shap_feature_importance(
    model,
    X_sample: np.ndarray,
    feature_names: list[str],
    n_samples: int = 200,
) -> list[dict]:
    """
    Compute SHAP feature importance using KernelExplainer.
    Returns list of {feature, mean_abs_shap, rank}.
    """
    try:
        import shap

        # Use a subset of data as background
        background = X_sample[:min(100, len(X_sample))]
        explainer = shap.KernelExplainer(model.predict, background)
        shap_values = explainer.shap_values(X_sample[:n_samples])

        # Handle multi-output
        if isinstance(shap_values, list):
            mean_abs = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
        else:
            mean_abs = np.abs(shap_values).mean(axis=0)

        # Build ranking
        ranking = sorted(
            zip(feature_names, mean_abs), key=lambda x: x[1], reverse=True
        )

        return [
            {"feature": name, "mean_abs_shap": float(val), "rank": i + 1}
            for i, (name, val) in enumerate(ranking)
        ]

    except Exception as e:
        logger.error(f"SHAP computation failed: {e}")
        return []


def engineer_flow_features(packets: list) -> dict:
    """
    Compute 30 flow-level features from a list of raw packets.
    Used for PCAP analysis and live capture.

    Each packet should be a dict with:
    {size, timestamp, direction, protocol, flags, header_length, window_size}
    """
    if not packets:
        return _empty_features()

    sizes = [p.get("size", 0) for p in packets]
    timestamps = [p.get("timestamp", 0) for p in packets]
    fwd = [p for p in packets if p.get("direction", "fwd") == "fwd"]
    bwd = [p for p in packets if p.get("direction", "fwd") == "bwd"]
    fwd_sizes = [p.get("size", 0) for p in fwd]
    bwd_sizes = [p.get("size", 0) for p in bwd]

    # Inter-arrival times
    iats = np.diff(sorted(timestamps)) if len(timestamps) > 1 else [0]

    # Flow duration
    duration_ms = (max(timestamps) - min(timestamps)) * 1000 if len(timestamps) > 1 else 0

    # TCP flags
    all_flags = [p.get("flags", "") for p in packets]

    features = {
        # Volume features
        "total_packets": len(packets),
        "total_bytes": sum(sizes),
        "fwd_packet_count": len(fwd),
        "bwd_packet_count": len(bwd),
        "fwd_bytes_total": sum(fwd_sizes),
        "bwd_bytes_total": sum(bwd_sizes),
        # Packet length features
        "pkt_len_mean": float(np.mean(sizes)) if sizes else 0,
        "pkt_len_std": float(np.std(sizes)) if sizes else 0,
        "pkt_len_max": max(sizes) if sizes else 0,
        "pkt_len_min": min(sizes) if sizes else 0,
        "pkt_len_variance": float(np.var(sizes)) if sizes else 0,
        # Inter-arrival time features
        "iat_mean": float(np.mean(iats)) if len(iats) > 0 else 0,
        "iat_std": float(np.std(iats)) if len(iats) > 0 else 0,
        "iat_max": float(np.max(iats)) if len(iats) > 0 else 0,
        "iat_min": float(np.min(iats)) if len(iats) > 0 else 0,
        # Flow duration
        "flow_duration_ms": duration_ms,
        "flow_bytes_per_sec": sum(sizes) / (duration_ms / 1000) if duration_ms > 0 else 0,
        "flow_packets_per_sec": len(packets) / (duration_ms / 1000) if duration_ms > 0 else 0,
        # TCP flags
        "flag_syn_count": sum(1 for f in all_flags if "S" in f),
        "flag_ack_count": sum(1 for f in all_flags if "A" in f),
        "flag_fin_count": sum(1 for f in all_flags if "F" in f),
        "flag_rst_count": sum(1 for f in all_flags if "R" in f),
        "flag_psh_count": sum(1 for f in all_flags if "P" in f),
        "flag_urg_count": sum(1 for f in all_flags if "U" in f),
        # Header features
        "header_length_mean": float(np.mean([p.get("header_length", 20) for p in packets])),
        "window_size_mean": float(np.mean([p.get("window_size", 0) for p in packets])),
        # Derived ratios
        "fwd_bwd_ratio": (len(fwd) / len(bwd)) if len(bwd) > 0 else len(fwd),
        "bytes_per_packet_mean": sum(sizes) / len(packets) if packets else 0,
        "down_up_ratio": (sum(bwd_sizes) / sum(fwd_sizes)) if sum(fwd_sizes) > 0 else 0,
        "active_idle_ratio": float(np.mean(iats) / np.max(iats)) if np.max(iats) > 0 else 0,
    }

    return features


def _empty_features() -> dict:
    """Return a dict of all zero features."""
    return {
        "total_packets": 0, "total_bytes": 0, "fwd_packet_count": 0,
        "bwd_packet_count": 0, "fwd_bytes_total": 0, "bwd_bytes_total": 0,
        "pkt_len_mean": 0, "pkt_len_std": 0, "pkt_len_max": 0,
        "pkt_len_min": 0, "pkt_len_variance": 0, "iat_mean": 0,
        "iat_std": 0, "iat_max": 0, "iat_min": 0, "flow_duration_ms": 0,
        "flow_bytes_per_sec": 0, "flow_packets_per_sec": 0,
        "flag_syn_count": 0, "flag_ack_count": 0, "flag_fin_count": 0,
        "flag_rst_count": 0, "flag_psh_count": 0, "flag_urg_count": 0,
        "header_length_mean": 0, "window_size_mean": 0, "fwd_bwd_ratio": 0,
        "bytes_per_packet_mean": 0, "down_up_ratio": 0, "active_idle_ratio": 0,
    }
