"""
PCAP Reader
===========
Parse uploaded PCAP files into flow-level features for analysis.
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("deepshield.capture.pcap")


class PcapReader:
    """Read and parse PCAP files into network flow features."""

    def read_pcap(self, file_path: str) -> list[dict]:
        """
        Read a PCAP file and extract flow-level features.
        Returns list of feature dicts, one per flow.
        """
        try:
            from scapy.all import rdpcap, IP, TCP, UDP
        except ImportError:
            logger.warning("Scapy not available — using fallback PCAP parser")
            return self._fallback_parse(file_path)

        try:
            packets = rdpcap(str(file_path))
            flows = {}

            for pkt in packets:
                if IP not in pkt:
                    continue

                src = pkt[IP].src
                dst = pkt[IP].dst
                proto = "TCP" if TCP in pkt else "UDP" if UDP in pkt else "OTHER"
                sport = pkt[TCP].sport if TCP in pkt else pkt[UDP].sport if UDP in pkt else 0
                dport = pkt[TCP].dport if TCP in pkt else pkt[UDP].dport if UDP in pkt else 0

                # 5-tuple flow key
                flow_key = (src, dst, sport, dport, proto)

                if flow_key not in flows:
                    flows[flow_key] = {
                        "src_ip": src, "dst_ip": dst,
                        "src_port": sport, "dst_port": dport,
                        "protocol": proto, "packets": [],
                    }

                flags = ""
                if TCP in pkt:
                    f = pkt[TCP].flags
                    if f & 0x02: flags += "S"
                    if f & 0x10: flags += "A"
                    if f & 0x01: flags += "F"
                    if f & 0x04: flags += "R"
                    if f & 0x08: flags += "P"
                    if f & 0x20: flags += "U"

                flows[flow_key]["packets"].append({
                    "size": len(pkt),
                    "timestamp": float(pkt.time),
                    "direction": "fwd",
                    "flags": flags,
                    "header_length": pkt[IP].ihl * 4 if IP in pkt else 20,
                    "window_size": pkt[TCP].window if TCP in pkt else 0,
                })

            # Convert flows to feature dicts
            from data.feature_engineer import engineer_flow_features
            result = []
            for flow_key, flow_data in flows.items():
                features = engineer_flow_features(flow_data["packets"])
                features["src_ip"] = flow_data["src_ip"]
                features["dst_ip"] = flow_data["dst_ip"]
                features["protocol"] = flow_data["protocol"]
                result.append(features)

            logger.info(f"Parsed {len(result)} flows from PCAP")
            return result

        except Exception as e:
            logger.error(f"PCAP parsing failed: {e}")
            return []

    def _fallback_parse(self, file_path: str) -> list[dict]:
        """Fallback parser when scapy is not available."""
        logger.warning(f"Cannot parse PCAP without scapy: {file_path}")
        return []
