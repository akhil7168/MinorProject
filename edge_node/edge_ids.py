"""
Real-Time IoT Intrusion Detection - Edge Node
Uses Python raw sockets for REAL packet capture on Windows (no Npcap needed).
Extracts features from live network traffic and sends to Deep Learning backend.
Falls back to simulation if Administrator privileges are missing.
"""
import socket
import struct
import time
import requests
import logging
import threading
import random
from collections import defaultdict
from statistics import mean, stdev
from config import API_ENDPOINT, FEATURE_COUNT, CAPTURE_DURATION

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [EDGE] - %(message)s')

class RealTimeIDS:
    def __init__(self):
        self.running = True
        self.flows = {}
        self.lock = threading.Lock()
        self.use_simulation = False

    def create_raw_socket(self):
        """Create a raw socket to capture ALL network packets on Windows"""
        # Get the local IP address
        hostname = socket.gethostname()
        host_ip = socket.gethostbyname(hostname)
        
        logging.info(f"Binding to host IP: {host_ip}")
        
        # Create raw socket (works on Windows without Npcap)
        # Note: This requires Administrator privileges
        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
        raw_sock.bind((host_ip, 0))
        
        # Include IP headers
        raw_sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        
        # Enable promiscuous mode (receive ALL packets)
        raw_sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
        
        return raw_sock, host_ip

    def parse_ip_header(self, data):
        """Parse IP header from raw packet data"""
        ip_header = struct.unpack('!BBHHHBBH4s4s', data[:20])
        
        version_ihl = ip_header[0]
        ihl = (version_ihl & 0xF) * 4
        total_length = ip_header[2]
        protocol = ip_header[6]
        src_ip = socket.inet_ntoa(ip_header[8])
        dst_ip = socket.inet_ntoa(ip_header[9])
        
        return {
            'ihl': ihl,
            'total_length': total_length,
            'protocol': protocol,  # 6=TCP, 17=UDP, 1=ICMP
            'src_ip': src_ip,
            'dst_ip': dst_ip
        }

    def parse_tcp_header(self, data, ihl):
        """Parse TCP header"""
        tcp_header = struct.unpack('!HHLLBBHHH', data[ihl:ihl+20])
        return {
            'src_port': tcp_header[0],
            'dst_port': tcp_header[1],
            'seq': tcp_header[2],
            'ack': tcp_header[3],
            'flags': tcp_header[5]
        }

    def parse_udp_header(self, data, ihl):
        """Parse UDP header"""
        udp_header = struct.unpack('!HHHH', data[ihl:ihl+8])
        return {
            'src_port': udp_header[0],
            'dst_port': udp_header[1],
            'length': udp_header[2]
        }

    def capture_packets(self, raw_sock):
        """Capture real network packets and group into flows"""
        logging.info("✅ REAL packet capture started! Listening to all network traffic...")
        
        while self.running:
            try:
                data, addr = raw_sock.recvfrom(65535)
                ip_info = self.parse_ip_header(data)
                
                src_port = 0
                dst_port = 0
                flags = 0
                
                if ip_info['protocol'] == 6:  # TCP
                    try:
                        tcp = self.parse_tcp_header(data, ip_info['ihl'])
                        src_port = tcp['src_port']
                        dst_port = tcp['dst_port']
                        flags = tcp['flags']
                    except Exception:
                        pass
                elif ip_info['protocol'] == 17:  # UDP
                    try:
                        udp = self.parse_udp_header(data, ip_info['ihl'])
                        src_port = udp['src_port']
                        dst_port = udp['dst_port']
                    except Exception:
                        pass

                # Create flow key
                flow_key = (ip_info['src_ip'], ip_info['dst_ip'], ip_info['protocol'])
                
                packet_info = {
                    'time': time.time(),
                    'len': ip_info['total_length'],
                    'src_port': src_port,
                    'dst_port': dst_port,
                    'flags': flags,
                    'protocol': ip_info['protocol']
                }
                
                with self.lock:
                    if flow_key not in self.flows:
                        self.flows[flow_key] = []
                    self.flows[flow_key].append(packet_info)
                    
            except Exception as e:
                if self.running:
                    logging.debug(f"Packet parse error: {e}")

    def extract_features(self, flow_packets):
        """Extract features from packets"""
        if not flow_packets:
            return [0.0] * FEATURE_COUNT

        timestamps = [p['time'] for p in flow_packets]
        lengths = [p['len'] for p in flow_packets]
        
        flow_duration = (max(timestamps) - min(timestamps)) * 1e6
        total_packets = len(flow_packets)
        total_length = sum(lengths)
        
        pkt_max = max(lengths)
        pkt_min = min(lengths)
        pkt_mean = mean(lengths)
        pkt_std = stdev(lengths) if len(lengths) > 1 else 0.0
        
        iats = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
        iat_mean = mean(iats) * 1e6 if iats else 0.0
        iat_std = stdev(iats) * 1e6 if len(iats) > 1 else 0.0
        
        syn_count = sum(1 for p in flow_packets if p['flags'] & 0x02)
        fin_count = sum(1 for p in flow_packets if p['flags'] & 0x01)
        ack_count = sum(1 for p in flow_packets if p['flags'] & 0x10)
        
        bytes_per_sec = total_length / (flow_duration / 1e6) if flow_duration > 0 else 0
        pkts_per_sec = total_packets / (flow_duration / 1e6) if flow_duration > 0 else 0
        
        features = [0.0] * FEATURE_COUNT
        features[0]  = float(flow_packets[0]['dst_port'])
        features[1]  = flow_duration
        features[2]  = float(total_packets)
        features[4]  = float(total_length)
        features[6]  = float(pkt_max)
        features[7]  = float(pkt_min)
        features[8]  = pkt_mean
        features[9]  = pkt_std
        features[14] = bytes_per_sec
        features[15] = pkts_per_sec
        features[16] = iat_mean
        features[17] = iat_std
        features[43] = float(fin_count)
        features[44] = float(syn_count)
        features[47] = float(ack_count)
        
        return features

    def simulate_traffic_analysis(self):
        """Fallback simulation logic"""
        count = random.randint(10, 100)
        features = [0.0] * FEATURE_COUNT
        
        # Simulate attack vs normal traffic
        if count > 80:
            features[0] = 80
            features[1] = 100000
            features[2] = count
            features[15] = count / 3.0
            src = "192.168.1.105"
            dst = "192.168.1.50"
            proto = 6
        else:
            features[0] = 443
            features[1] = 500
            features[2] = count
            features[15] = count / 3.0
            src = "192.168.1.101"
            dst = "192.168.1.1"
            proto = 6

        self.send_to_backend(features, (src, dst, proto))

    def processor(self):
        """Process flows"""
        logging.info(f"Processing flows every {CAPTURE_DURATION} seconds...")
        
        while self.running:
            time.sleep(CAPTURE_DURATION)
            
            if self.use_simulation:
                self.simulate_traffic_analysis()
                continue
            
            with self.lock:
                current_flows = dict(self.flows)
                self.flows.clear()
            
            if not current_flows:
                continue
            
            total_packets = sum(len(pkts) for pkts in current_flows.values())
            logging.info(f"📊 Captured {total_packets} packets across {len(current_flows)} flows")
            
            for flow_key, packets in current_flows.items():
                if len(packets) < 2: continue
                features = self.extract_features(packets)
                self.send_to_backend(features, flow_key)

    def send_to_backend(self, features, flow_key):
        """Send to API"""
        try:
            payload = {"features": features}
            response = requests.post(API_ENDPOINT, json=payload, timeout=2)
            
            src, dst, proto = flow_key
            proto_name = {6: 'TCP', 17: 'UDP', 1: 'ICMP'}.get(proto, str(proto))
            
            if response.status_code == 200:
                result = response.json()
                label = result.get("label", "Unknown")
                conf = result.get("confidence", 0)
                
                if result.get("is_attack"):
                    logging.warning(f"🚨 ATTACK [{src} -> {dst}] ({proto_name}) | {label} | Confidence: {conf:.1%}")
                else:
                    logging.info(f"✅ Normal [{src} -> {dst}] ({proto_name}) | Confidence: {conf:.1%}")
            else:
                logging.error(f"Backend Error: {response.text}")
        except Exception as e:
            logging.error(f"Connection Failed: {e}")

    def start(self):
        """Start IDS with Admin check"""
        try:
            raw_sock, host_ip = self.create_raw_socket()
            logging.info(f"🔵 Raw socket created. Monitoring ALL traffic on {host_ip}")
            
            capture_thread = threading.Thread(target=self.capture_packets, args=(raw_sock,))
            capture_thread.daemon = True
            capture_thread.start()
            
            self.processor()
            
        except PermissionError:
            logging.error("❌ Permission denied! Run as Administrator for Real Packet Capture.")
            logging.warning("⚠️  Switching to SIMULATION MODE due to lack of privileges.")
            self.use_simulation = True
            self.processor()
        except OSError as e:
            logging.error(f"❌ Socket error: {e}")
            logging.warning("⚠️  Switching to SIMULATION MODE.")
            self.use_simulation = True
            self.processor()
        except KeyboardInterrupt:
            logging.info("Stopping IDS...")
        finally:
            self.running = False

if __name__ == "__main__":
    ids = RealTimeIDS()
    logging.info("=" * 60)
    logging.info("  REAL-TIME IoT INTRUSION DETECTION SYSTEM")
    logging.info("  Using Raw Socket Capture (No Npcap Needed)")
    logging.info("  For Real Capture: Run as Administrator")
    logging.info("=" * 60)
    ids.start()
