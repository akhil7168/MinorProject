"""
Training Metrics
================
Comprehensive metrics for evaluating IDS model performance.
"""
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    roc_auc_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report,
    average_precision_score,
)


def compute_all_metrics(y_true: np.ndarray, y_pred_probs: np.ndarray) -> dict:
    """
    Compute comprehensive metrics for IDS model evaluation.

    Returns:
    {
        accuracy, f1_macro, f1_weighted, auc_roc_macro,
        detection_rate, false_alarm_rate,
        per_class: {class_name: {precision, recall, f1, support}},
        confusion_matrix, classification_report
    }
    """
    # Get class predictions
    if y_pred_probs.ndim == 1 or y_pred_probs.shape[1] == 1:
        y_pred = (y_pred_probs.ravel() > 0.5).astype(int)
    else:
        y_pred = np.argmax(y_pred_probs, axis=1)

    num_classes = y_pred_probs.shape[1] if y_pred_probs.ndim > 1 else 2
    from data.loader import CLASS_NAMES

    # Basic metrics
    accuracy = float(accuracy_score(y_true, y_pred))
    f1_macro = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    f1_weighted = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    # AUC-ROC (handle multiclass)
    try:
        if num_classes <= 2:
            auc_roc = float(roc_auc_score(y_true, y_pred_probs[:, 1] if y_pred_probs.ndim > 1 else y_pred_probs))
        else:
            from sklearn.preprocessing import label_binarize
            y_true_bin = label_binarize(y_true, classes=list(range(num_classes)))
            auc_roc = float(roc_auc_score(y_true_bin, y_pred_probs, multi_class="ovr", average="macro"))
    except Exception:
        auc_roc = 0.0

    # Detection Rate (True Positive Rate for attacks)
    # Attack = any class > 0
    y_true_binary = (y_true > 0).astype(int)
    y_pred_binary = (y_pred > 0).astype(int)

    tp = np.sum((y_pred_binary == 1) & (y_true_binary == 1))
    fn = np.sum((y_pred_binary == 0) & (y_true_binary == 1))
    fp = np.sum((y_pred_binary == 1) & (y_true_binary == 0))
    tn = np.sum((y_pred_binary == 0) & (y_true_binary == 0))

    detection_rate = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    false_alarm_rate = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    # Per-class metrics
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, zero_division=0
    )

    per_class = {}
    for i in range(len(precision)):
        class_name = CLASS_NAMES.get(i, f"Class_{i}")
        per_class[class_name] = {
            "precision": round(float(precision[i]), 4),
            "recall": round(float(recall[i]), 4),
            "f1": round(float(f1[i]), 4),
            "support": int(support[i]),
        }

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred).tolist()

    # Classification report
    report = classification_report(y_true, y_pred, zero_division=0)

    return {
        "accuracy": round(accuracy, 4),
        "f1_macro": round(f1_macro, 4),
        "f1_weighted": round(f1_weighted, 4),
        "auc_roc_macro": round(auc_roc, 4),
        "detection_rate": round(detection_rate, 4),
        "false_alarm_rate": round(false_alarm_rate, 4),
        "per_class": per_class,
        "confusion_matrix": cm,
        "classification_report": report,
    }
