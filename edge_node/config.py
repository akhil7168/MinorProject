import os

# Backend API Configuration
BACKEND_URL = "http://localhost:8002/predict"  # Replace localhost with your Laptop's IP when running on Pi
API_ENDPOINT = BACKEND_URL

# Network Configuration
INTERFACE = "Wi-Fi"  # Change to "wlan0" on Raspberry Pi or "eth0"
CAPTURE_DURATION = 10  # Seconds to capture before processing

# Feature Extraction
# CICIDS2017 feature count
FEATURE_COUNT = 78
