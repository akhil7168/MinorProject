import time
import random
import requests
import threading

# Configuration
TARGET_URL = "http://google.com" # Target for normal traffic
ATTACK_TARGET_IP = "192.168.1.1" # Example target for attack

def generate_normal_traffic():
    """Simulate normal IoT behavior: Periodic MQTT/HTTP requests"""
    print("[IOT] Starting Normal Traffic Simulation...")
    while True:
        try:
            # Simulate sensor data upload
            print("[IOT] Sending sensor data (Normal)...")
            # requests.get(TARGET_URL) 
            time.sleep(random.uniform(1.0, 5.0)) # Random delay 1-5s
        except Exception as e:
            print(f"[IOT] Error: {e}")

def generate_attack_traffic():
    """Simulate attack behavior: Rapid request bursts (DoS)"""
    print("[IOT] !!! STARTING ATTACK SIMULATION !!!")
    # Simulate a burst of 100 requests
    for i in range(100):
        try:
            # In a real attack, this would be a high-frequency packet flood
            # Here we just print to simulate the event for the IDS to pick up
            if i % 10 == 0:
                print(f"[IOT] !!! ATTACK PACKET FLOOD {i} !!!")
            time.sleep(0.01) # Very fast
        except:
            pass
    print("[IOT] Attack burst finished.")

if __name__ == "__main__":
    print("1. Normal Traffic")
    print("2. Attack Simulation")
    choice = input("Select mode (1/2): ")
    
    if choice == '1':
        generate_normal_traffic()
    elif choice == '2':
        generate_attack_traffic()
    else:
        print("Invalid choice")
