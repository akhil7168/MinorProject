"""
Model Optimizer
===============
TFLite export, quantization, pruning, and inference benchmarking.
"""
import logging
import time
from pathlib import Path

import numpy as np

logger = logging.getLogger("deepshield.training.optimizer")


def export_tflite_float32(model, output_path: Path) -> float:
    """Export TFLite without quantization. Returns file size in MB."""
    import tensorflow as tf

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(tflite_model)

    size_mb = len(tflite_model) / (1024 * 1024)
    logger.info(f"TFLite (float32) exported: {size_mb:.2f} MB")
    return size_mb


def export_tflite_int8(model, representative_data: np.ndarray, output_path: Path) -> float:
    """INT8 quantization. ~4x smaller, ~2-3x faster on CPU."""
    import tensorflow as tf

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    def representative_dataset():
        for i in range(min(200, len(representative_data))):
            yield [representative_data[i:i+1].astype(np.float32)]

    converter.representative_dataset = representative_dataset
    # converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]

    tflite_model = converter.convert()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(tflite_model)

    size_mb = len(tflite_model) / (1024 * 1024)
    logger.info(f"TFLite (INT8) exported: {size_mb:.2f} MB")
    return size_mb


def benchmark_inference_latency(model_path: Path, X_sample: np.ndarray, n_runs: int = 100) -> dict:
    """
    Benchmark model inference latency.
    Returns: {mean_ms, std_ms, p95_ms, p99_ms}
    """
    import tensorflow as tf

    # Load TFLite model
    interpreter = tf.lite.Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    latencies = []
    for i in range(n_runs):
        sample = X_sample[i % len(X_sample)].reshape(1, -1).astype(np.float32)
        interpreter.set_tensor(input_details[0]["index"], sample)

        start = time.perf_counter()
        interpreter.invoke()
        elapsed = (time.perf_counter() - start) * 1000  # ms

        latencies.append(elapsed)

    latencies = np.array(latencies)
    return {
        "mean_ms": round(float(np.mean(latencies)), 3),
        "std_ms": round(float(np.std(latencies)), 3),
        "p95_ms": round(float(np.percentile(latencies, 95)), 3),
        "p99_ms": round(float(np.percentile(latencies, 99)), 3),
    }
