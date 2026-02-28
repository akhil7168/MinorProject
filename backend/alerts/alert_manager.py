"""
Alert Manager
=============
Creates, deduplicates, and publishes alerts for high-confidence attack detections.
"""
import hashlib
import logging
import time
from typing import Optional

from database import crud

logger = logging.getLogger("deepshield.alerts.manager")


class AlertManager:
    """Manages alert creation, deduplication, and publishing."""

    def __init__(self, threshold: float = 0.85, dedupe_window: int = 60):
        self.threshold = threshold
        self.dedupe_window = dedupe_window
        self._recent_fingerprints: dict[str, dict] = {}

    async def process_detection(self, detection: dict, session_id: str) -> Optional[dict]:
        """
        Process a detection result and create an alert if warranted.
        Returns the alert dict if one was created, None otherwise.
        """
        predicted_class = detection.get("predicted_class", "BENIGN")
        confidence = detection.get("confidence", 0)

        # Only alert on attacks above threshold
        if predicted_class == "BENIGN" or confidence < self.threshold:
            return None

        src_ip = detection.get("src_ip", "unknown")
        attack_type = predicted_class

        # Check deduplication
        fingerprint = self._compute_fingerprint(src_ip, attack_type)

        if fingerprint in self._recent_fingerprints:
            # Increment existing alert instead of creating new one
            existing = self._recent_fingerprints[fingerprint]
            existing["alert_count"] = existing.get("alert_count", 1) + 1
            existing["last_seen"] = __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat()
            return None

        # Create new alert
        severity = self._assign_severity(attack_type, confidence)

        alert_data = {
            "session_id": session_id,
            "severity": severity,
            "attack_type": attack_type,
            "src_ip": src_ip,
            "dst_ip": detection.get("dst_ip", "unknown"),
            "confidence": confidence,
            "status": "open",
            "fingerprint": fingerprint,
            "alert_count": 1,
            "model_votes": detection.get("per_model") or detection.get("model_votes"),
            "shap_explanation": detection.get("shap_explanation"),
            "raw_features": detection.get("features"),
        }

        alert = await crud.create_alert(alert_data)
        self._recent_fingerprints[fingerprint] = alert_data

        # Publish to WebSocket
        await self._publish_alert(alert)

        logger.info(f"🚨 Alert: {severity} {attack_type} from {src_ip} (conf={confidence:.2%})")
        return alert

    def _compute_fingerprint(self, src_ip: str, attack_type: str) -> str:
        """
        Deduplication fingerprint.
        Same src_ip + attack_type within time bucket → same fingerprint.
        """
        time_bucket = int(time.time()) // self.dedupe_window
        raw = f"{src_ip}:{attack_type}:{time_bucket}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _assign_severity(self, attack_type: str, confidence: float) -> str:
        """Map attack type + confidence → severity level."""
        critical_attacks = {"DDoS", "DoS"}
        high_attacks = {"Botnet", "R2L", "BruteForce", "Backdoor"}
        medium_attacks = {"PortScan", "Probe", "WebAttack"}

        if attack_type in critical_attacks and confidence > 0.95:
            return "critical"
        elif attack_type in critical_attacks or attack_type in high_attacks:
            return "high"
        elif attack_type in medium_attacks:
            return "medium" if confidence < 0.95 else "high"
        else:
            return "medium" if confidence > 0.9 else "low"

    async def _publish_alert(self, alert: dict):
        """Publish alert to WebSocket clients."""
        try:
            from api.routes.websocket import broadcast_alert
            await broadcast_alert(alert)
        except Exception as e:
            logger.debug(f"Could not broadcast alert: {e}")

    def cleanup_fingerprints(self):
        """Remove expired fingerprints."""
        current_bucket = int(time.time()) // self.dedupe_window
        expired = [fp for fp, data in self._recent_fingerprints.items()]
        for fp in expired:
            del self._recent_fingerprints[fp]


# Singleton instance
alert_manager = AlertManager()
