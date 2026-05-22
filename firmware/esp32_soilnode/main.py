"""
Famtech AgriCore — ESP32 Soilnode Firmware Template (MicroPython)
------------------------------------------------------------------
This script demonstrates how a real hardware device connects to the
AgriCore Edge Hub (or Cloud) and securely pushes JSON telemetry.

Requirements:
- MicroPython v1.19+ on ESP32
- umqtt.simple (install via upip)
"""

import time
import network
import json
import machine
from umqtt.simple import MQTTClient

# ── Configuration ─────────────────────────────────────────────────────────────
# 1. Register device via the Famtech dashboard to get these credentials
FARM_ID = "replace_with_farm_id"
DEVICE_ID = "replace_with_device_id"
API_KEY = "replace_with_api_key_shown_once_during_registration"

# 2. Network / MQTT Broker (Point this to your Edge Hub's IP address)
WIFI_SSID = "Farm_WiFi"
WIFI_PASS = "supersecret"
MQTT_SERVER = "192.168.1.100"  # IP of Raspberry Pi running Edge Hub
MQTT_PORT = 1883

# 3. Hardware config
POLL_INTERVAL_SEC = 60 * 5  # Send data every 5 minutes
SOIL_PIN = machine.ADC(machine.Pin(32))
SOIL_PIN.atten(machine.ADC.ATTN_11DB) # 3.3v range

# ── Networking ────────────────────────────────────────────────────────────────
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        while not wlan.isconnected():
            time.sleep(1)
            print(".", end="")
    print("\nWiFi Connected:", wlan.ifconfig())

# ── Sensors ───────────────────────────────────────────────────────────────────
def read_sensors():
    """Read ADC and convert to arbitrary percentage for demo."""
    raw = SOIL_PIN.read()
    # Assuming 0 (wet) to 4095 (dry) for a standard analog capacitive sensor
    moisture = 100 - (raw / 4095.0 * 100.0)
    
    # Fake a battery reading
    battery = 85.5 
    
    return moisture, battery

# ── Main Loop ─────────────────────────────────────────────────────────────────
def main():
    connect_wifi()
    
    # Use the API key as the MQTT password to authenticate
    client = MQTTClient(
        client_id=DEVICE_ID,
        server=MQTT_SERVER,
        port=MQTT_PORT,
        user=DEVICE_ID,
        password=API_KEY
    )
    
    try:
        client.connect()
        print("Connected to MQTT Broker!")
    except Exception as e:
        print("MQTT connection failed:", e)
        # Deep sleep and try again later
        machine.deepsleep(60000)

    topic = f"famtech/{FARM_ID}/{DEVICE_ID}/telemetry"

    while True:
        try:
            moisture, battery = read_sensors()
            
            payload = {
                "device_id": DEVICE_ID,
                "battery_pct": battery,
                "firmware_ver": "1.0.0",
                "readings": [
                    {
                        "metric": "soil_moisture",
                        "value": round(moisture, 2),
                        "unit": "%"
                    }
                ]
            }
            
            json_str = json.dumps(payload)
            print(f"Publishing to {topic}:\n{json_str}")
            
            # Send QOS 1 so the hub guarantees receipt
            client.publish(topic, json_str.encode(), qos=1)
            
        except Exception as e:
            print("Error publishing:", e)
            # Optional: attempt reconnect
        
        print(f"Sleeping for {POLL_INTERVAL_SEC} seconds...")
        # Deep sleep saves battery on ESP32
        # machine.deepsleep(POLL_INTERVAL_SEC * 1000) 
        time.sleep(POLL_INTERVAL_SEC)

if __name__ == "__main__":
    main()
