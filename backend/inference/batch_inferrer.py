"""
Batch Inferrer
==============
Handles batch processing of CSV and PCAP files for analysis.
"""
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from database import crud

logger = logging.getLogger("deepshield.inference.batch")


class BatchInferrer:
    """Process CSV/PCAP files through the inference engine."""

    def __init__(self, engine):
        self.engine = engine

    async def analyze_csv(self, file_path: str, session_id: str) -> dict:
        """
        Analyze a CSV file containing network flow features.
        Each row is treated as one flow.
        """
        logger.info(f"Analyzing CSV: {file_path}")
        df = pd.read_csv(file_path, low_memory=False)
        df.columns = df.columns.str.strip()

        # Remove non-feature columns
        drop_cols = ["Flow ID", "Source IP", "Src IP", "Destination IP",
                     "Dst IP", "Timestamp", "Label", "label"]
        existing_drops = [c for c in drop_cols if c in df.columns]

        # Extract labels if present (for accuracy reporting)
        labels = None
        for lc in ["Label", "label"]:
            if lc in df.columns:
                labels = df[lc].values
                break

        features_df = df.drop(columns=existing_drops, errors="ignore")

        # Convert to numeric
        for col in features_df.columns:
            features_df[col] = pd.to_numeric(features_df[col], errors="coerce")
        features_df = features_df.fillna(0)
        features_df = features_df.replace([np.inf, -np.inf], 0)

        X = features_df.values.astype(np.float32)

        # Run batch inference
        results = await self.engine.infer_batch(X)

        # Build detections for DB
        detections = []
        attack_count = 0
        attack_breakdown = {}

        for i, result in enumerate(results):
            predicted_class = result.get("predicted_class", "BENIGN")
            is_attack = predicted_class != "BENIGN"

            if is_attack:
                attack_count += 1
                attack_breakdown[predicted_class] = attack_breakdown.get(predicted_class, 0) + 1

            detections.append({
                "session_id": session_id,
                "predicted_class": predicted_class,
                "predicted_label": result.get("predicted_label", 0),
                "confidence": result.get("confidence", 0),
                "model_votes": result.get("model_votes") or result.get("per_model"),
                "features": {col: float(X[i][j]) for j, col in enumerate(features_df.columns[:10])},
            })

        # Bulk insert detections (in smaller batches to avoid memory issues)
        batch_size = 1000
        for i in range(0, len(detections), batch_size):
            await crud.bulk_insert_detections(detections[i:i + batch_size])

        logger.info(f"Analysis complete: {len(results)} flows, {attack_count} attacks")
        return {
            "total_flows": len(results),
            "attack_count": attack_count,
            "benign_count": len(results) - attack_count,
            "attack_breakdown": attack_breakdown,
        }

    async def analyze_flows(self, flows: list[dict], session_id: str) -> dict:
        """Analyze pre-extracted flow features (from PCAP)."""
        if not flows:
            return {"total_flows": 0, "attack_count": 0, "benign_count": 0, "attack_breakdown": {}}

        # Convert flow dicts to numpy array
        feature_keys = list(flows[0].keys())
        X = np.array([[f.get(k, 0) for k in feature_keys] for f in flows], dtype=np.float32)

        results = await self.engine.infer_batch(X)

        attack_count = 0
        attack_breakdown = {}
        detections = []

        for i, result in enumerate(results):
            predicted_class = result.get("predicted_class", "BENIGN")
            is_attack = predicted_class != "BENIGN"
            if is_attack:
                attack_count += 1
                attack_breakdown[predicted_class] = attack_breakdown.get(predicted_class, 0) + 1

            detections.append({
                "session_id": session_id,
                "predicted_class": predicted_class,
                "predicted_label": result.get("predicted_label", 0),
                "confidence": result.get("confidence", 0),
            })

        await crud.bulk_insert_detections(detections)

        return {
            "total_flows": len(results),
            "attack_count": attack_count,
            "benign_count": len(results) - attack_count,
            "attack_breakdown": attack_breakdown,
        }
