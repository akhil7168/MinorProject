"""
Flow Aggregator
===============
5-tuple flow aggregation engine for network traffic.
"""
import logging
from collections import defaultdict
from typing import Optional

logger = logging.getLogger("deepshield.capture.flow")


class FlowAggregator:
    """Aggregate packets into flows by 5-tuple."""

    def __init__(self, timeout: float = 120.0):
        self.timeout = timeout
        self.flows = defaultdict(lambda: {"packets": [], "start_time": None})

    def add_packet(self, packet: dict) -> Optional[dict]:
        """
        Add a packet. Returns completed flow features when flow expires.
        """
        key = (
            packet.get("src_ip", ""),
            packet.get("dst_ip", ""),
            packet.get("src_port", 0),
            packet.get("dst_port", 0),
            packet.get("protocol", "TCP"),
        )

        flow = self.flows[key]
        timestamp = packet.get("timestamp", 0)

        if flow["start_time"] is None:
            flow["start_time"] = timestamp

        flow["packets"].append(packet)

        # Check for flow timeout
        if timestamp - flow["start_time"] > self.timeout:
            return self._finalize_flow(key)

        # Check for FIN/RST flag
        flags = packet.get("flags", "")
        if "F" in flags or "R" in flags:
            return self._finalize_flow(key)

        return None

    def _finalize_flow(self, key: tuple) -> dict:
        """Convert flow packets into features."""
        from data.feature_engineer import engineer_flow_features

        flow = self.flows.pop(key, None)
        if not flow:
            return {}

        features = engineer_flow_features(flow["packets"])
        features["src_ip"] = key[0]
        features["dst_ip"] = key[1]
        features["src_port"] = key[2]
        features["dst_port"] = key[3]
        features["protocol"] = key[4]

        return features

    def flush_all(self) -> list[dict]:
        """Finalize all active flows."""
        results = []
        for key in list(self.flows.keys()):
            result = self._finalize_flow(key)
            if result:
                results.append(result)
        return results
