import pandas as pd
import numpy as np
import os

def generate_dummy_data(output_path="data", num_samples=1000):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    print(f"Generating {num_samples} dummy samples...")
    
    # CICIDS2017 features (subset for demonstration)
    # We will generate random data for ~78 columns typically found in CICIDS2017
    # For simplicity, we'll name them generally as in the dataset
    
    columns = [
        "Destination Port", "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
        "Total Length of Fwd Packets", "Total Length of Bwd Packets", "Fwd Packet Length Max",
        "Fwd Packet Length Min", "Fwd Packet Length Mean", "Fwd Packet Length Std",
        "Bwd Packet Length Max", "Bwd Packet Length Min", "Bwd Packet Length Mean",
        "Bwd Packet Length Std", "Flow Bytes/s", "Flow Packets/s", "Flow IAT Mean",
        "Flow IAT Std", "Flow IAT Max", "Flow IAT Min", "Fwd IAT Total", "Fwd IAT Mean",
        "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min", "Bwd IAT Total", "Bwd IAT Mean",
        "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min", "Fwd PSH Flags", "Bwd PSH Flags",
        "Fwd URG Flags", "Bwd URG Flags", "Fwd Header Length", "Bwd Header Length",
        "Fwd Packets/s", "Bwd Packets/s", "Min Packet Length", "Max Packet Length",
        "Packet Length Mean", "Packet Length Std", "Packet Length Variance",
        "FIN Flag Count", "SYN Flag Count", "RST Flag Count", "PSH Flag Count",
        "ACK Flag Count", "URG Flag Count", "CWE Flag Count", "ECE Flag Count",
        "Down/Up Ratio", "Average Packet Size", "Avg Fwd Segment Size",
        "Avg Bwd Segment Size", "Fwd Header Length.1", "Fwd Avg Bytes/Bulk",
        "Fwd Avg Packets/Bulk", "Fwd Avg Bulk Rate", "Bwd Avg Bytes/Bulk",
        "Bwd Avg Packets/Bulk", "Bwd Avg Bulk Rate", "Subflow Fwd Packets",
        "Subflow Fwd Bytes", "Subflow Bwd Packets", "Subflow Bwd Bytes",
        "Init_Win_bytes_forward", "Init_Win_bytes_backward", "act_data_pkt_fwd",
        "min_seg_size_forward", "Active Mean", "Active Std", "Active Max",
        "Active Min", "Idle Mean", "Idle Std", "Idle Max", "Idle Min", "Label"
    ]
    
    data = np.random.rand(num_samples, len(columns) - 1) # All features random float
    
    # Generate labels (Benign and Attack)
    labels = np.random.choice(["BENIGN", "PortScan", "DDoS", "Bot"], size=num_samples)
    
    df = pd.DataFrame(data, columns=columns[:-1])
    df["Label"] = labels
    
    output_file = os.path.join(output_path, "dummy_cicids2017.csv")
    df.to_csv(output_file, index=False)
    print(f"Dummy data saved to {output_file}")

if __name__ == "__main__":
    generate_dummy_data(output_path=os.path.join(os.path.dirname(__file__), "data"))
