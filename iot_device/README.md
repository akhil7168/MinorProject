# IoT Device - ESP32 Traffic Generator

This folder contains the firmware for the ESP32 IoT device that generates network traffic for testing the Intrusion Detection System.

## Hardware Requirements
- ESP32 Development Board
- USB cable for programming
- WiFi network access

## Software Requirements
- Arduino IDE (with ESP32 board support)
- OR PlatformIO

## Installation

### Arduino IDE Setup
1. Install Arduino IDE from https://www.arduino.cc/
2. Add ESP32 Board Support:
   - File → Preferences
   - Add to "Additional Board Manager URLs": 
     `https://dl.espressif.com/dl/package_esp32_index.json`
3. Tools → Board → Boards Manager → Search "ESP32" → Install
4. Install required libraries:
   - WiFi (built-in)
   - HTTPClient (built-in)

### Configuration
1. Open `firmware.ino` in Arduino IDE
2. Update WiFi credentials:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
3. Optionally update target URLs

### Upload to ESP32
1. Connect ESP32 via USB
2. Select Board: Tools → Board → ESP32 Dev Module
3. Select Port: Tools → Port → (Your ESP32 COM port)
4. Click Upload

## Usage

### Normal Mode (Default)
- ESP32 sends periodic HTTP requests every 2-5 seconds
- Simulates normal IoT sensor data upload
- LED blinks briefly on each request

### Attack Mode
- Press the BOOT button (GPIO 0) to toggle to Attack mode
- ESP32 generates 100 rapid requests (DDoS simulation)
- LED blinks rapidly during attack
- Automatically returns to waiting state after burst

### Serial Monitor
Open Serial Monitor (115200 baud) to see activity logs:
```
[IoT Device] WiFi Connected!
[IoT Device] IP Address: 192.168.1.100
[NORMAL] Sending sensor data...
[NORMAL] Response: 200
```

## Deployment Notes
- The ESP32 should be on the same network as the Raspberry Pi
- The Raspberry Pi's Edge IDS will capture this traffic
- For real testing, point `attackTarget` to a safe test server (not production!)
