# IoT Guardian - Edge Node Deployment

This folder contains the code to run the Intrusion Detection System (IDS) on a Raspberry Pi.

## Prerequisites
- Raspberry Pi 4 (Recommended)
- Python 3.7+
- Network Interface (Wi-Fi/Ethernet) in monitor mode (optional, for real capture)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure the Backend URL in `config.py`:
```python
BACKEND_URL = "http://<YOUR_LAPTOP_IP>:8000/predict"
```

## Running the Edge IDS

Run the main IDS script:
```bash
python edge_ids.py
```
This script will:
1. Simulate packet capture (or capture real packets if configured).
2. Extract features (78 features compatible with CICIDS2017).
3. Send data to the Backend API.
4. Log any detected attacks.

## simulating Traffic

To test the IDS without real attacks, run the traffic generator in a separate terminal:
```bash
python traffic_generator.py
```
Select "2" to simulate a DDoS attack burst. The `edge_ids.py` script should detect the high traffic volume and alert the backend.
