/*
 * IoT Traffic Generator for ESP32
 * 
 * This firmware generates network traffic patterns for IoT IDS testing.
 * 
 * Modes:
 * - NORMAL: Periodic HTTP requests simulating sensor data upload
 * - ATTACK: High-frequency request bursts simulating DDoS attack
 * 
 * Hardware:
 * - ESP32 Development Board
 * - Button on GPIO 0 (built-in BOOT button) to toggle modes
 * - LED on GPIO 2 (built-in LED) for status indication
 */

#include <WiFi.h>
#include <HTTPClient.h>

// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Target Server
const char* normalTarget = "http://httpbin.org/get";  // Normal traffic target
const char* attackTarget = "http://192.168.1.1";      // Attack simulation target

// GPIO Pins
const int BUTTON_PIN = 0;  // Built-in BOOT button
const int LED_PIN = 2;     // Built-in LED

// Operating Mode
enum Mode { NORMAL, ATTACK };
Mode currentMode = NORMAL;
bool buttonPressed = false;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 200;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Initialize GPIO
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Connect to WiFi
  Serial.println("\n[IoT Device] Starting...");
  Serial.print("[IoT Device] Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    digitalWrite(LED_PIN, !digitalRead(LED_PIN)); // Blink while connecting
  }
  
  Serial.println("\n[IoT Device] WiFi Connected!");
  Serial.print("[IoT Device] IP Address: ");
  Serial.println(WiFi.localIP());
  
  digitalWrite(LED_PIN, HIGH); // Solid LED when connected
  delay(1000);
  digitalWrite(LED_PIN, LOW);
}

void loop() {
  // Check button for mode toggle
  checkButton();
  
  // Execute traffic based on current mode
  if (currentMode == NORMAL) {
    generateNormalTraffic();
  } else {
    generateAttackTraffic();
  }
}

void checkButton() {
  int reading = digitalRead(BUTTON_PIN);
  
  if (reading == LOW && !buttonPressed) {
    unsigned long currentTime = millis();
    if (currentTime - lastDebounceTime > debounceDelay) {
      // Toggle mode
      currentMode = (currentMode == NORMAL) ? ATTACK : NORMAL;
      buttonPressed = true;
      lastDebounceTime = currentTime;
      
      // Visual feedback
      for (int i = 0; i < 3; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(100);
        digitalWrite(LED_PIN, LOW);
        delay(100);
      }
      
      Serial.print("\n[IoT Device] Mode switched to: ");
      Serial.println(currentMode == NORMAL ? "NORMAL" : "ATTACK");
      Serial.println("-----------------------------------\n");
    }
  }
  
  if (reading == HIGH) {
    buttonPressed = false;
  }
}

void generateNormalTraffic() {
  static unsigned long lastRequest = 0;
  unsigned long interval = random(2000, 5000); // Random delay 2-5 seconds
  
  if (millis() - lastRequest > interval) {
    Serial.println("[NORMAL] Sending sensor data...");
    
    HTTPClient http;
    http.begin(normalTarget);
    int httpCode = http.GET();
    
    if (httpCode > 0) {
      Serial.printf("[NORMAL] Response: %d\n", httpCode);
    } else {
      Serial.printf("[NORMAL] Error: %s\n", http.errorToString(httpCode).c_str());
    }
    
    http.end();
    lastRequest = millis();
    
    // Brief LED blink
    digitalWrite(LED_PIN, HIGH);
    delay(50);
    digitalWrite(LED_PIN, LOW);
  }
}

void generateAttackTraffic() {
  Serial.println("[ATTACK] !!! Launching DDoS Attack Simulation !!!");
  
  // Rapid burst of 100 requests
  for (int i = 0; i < 100; i++) {
    HTTPClient http;
    http.begin(attackTarget);
    http.setTimeout(100); // Short timeout for flooding
    
    int httpCode = http.GET();
    
    if (i % 10 == 0) {
      Serial.printf("[ATTACK] Packet flood: %d/100\n", i);
    }
    
    http.end();
    
    // Very short delay
    delay(10);
    
    // Fast LED blink during attack
    digitalWrite(LED_PIN, i % 2);
  }
  
  Serial.println("[ATTACK] Attack burst complete!");
  Serial.println("[ATTACK] Press button to return to NORMAL mode\n");
  
  digitalWrite(LED_PIN, LOW);
  
  // Stay in attack mode until button is pressed
  while (currentMode == ATTACK) {
    checkButton();
    delay(100);
  }
}
