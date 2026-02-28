"""
Live Capture (optional)
=======================
Real-time packet sniffing using scapy.
Requires elevated privileges on most systems.
"""
import logging

logger = logging.getLogger("deepshield.capture.live")


class LiveCapture:
    """Optional live packet capture using scapy."""

    def __init__(self, interface: str = None):
        self.interface = interface
        self.running = False

    async def start(self, callback=None):
        """Start live capture (requires admin/root privileges)."""
        try:
            from scapy.all import sniff, IP, TCP, UDP
        except ImportError:
            logger.error("Scapy not available for live capture")
            return

        self.running = True
        logger.info(f"Starting live capture on {self.interface or 'default interface'}")

        def process_packet(pkt):
            if not self.running or IP not in pkt:
                return

            packet_info = {
                "src_ip": pkt[IP].src,
                "dst_ip": pkt[IP].dst,
                "size": len(pkt),
                "timestamp": float(pkt.time),
                "protocol": "TCP" if TCP in pkt else "UDP" if UDP in pkt else "OTHER",
                "src_port": pkt[TCP].sport if TCP in pkt else pkt[UDP].sport if UDP in pkt else 0,
                "dst_port": pkt[TCP].dport if TCP in pkt else pkt[UDP].dport if UDP in pkt else 0,
                "direction": "fwd",
                "flags": "",
                "header_length": pkt[IP].ihl * 4,
                "window_size": pkt[TCP].window if TCP in pkt else 0,
            }

            if TCP in pkt:
                f = pkt[TCP].flags
                if f & 0x02: packet_info["flags"] += "S"
                if f & 0x10: packet_info["flags"] += "A"
                if f & 0x01: packet_info["flags"] += "F"
                if f & 0x04: packet_info["flags"] += "R"

            if callback:
                callback(packet_info)

        sniff(
            iface=self.interface,
            prn=process_packet,
            store=False,
            stop_filter=lambda _: not self.running,
        )

    def stop(self):
        """Stop live capture."""
        self.running = False
        logger.info("Live capture stopped")
