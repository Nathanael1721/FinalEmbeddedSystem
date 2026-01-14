# Raspberry Pi Pico 2 W - Smart Parking Gate Controller

MicroPython code for Raspberry Pi Pico 2 W to control the smart parking gate system.

## 🎯 Overview

This MicroPython application runs on Raspberry Pi Pico 2 W and provides:
- **WiFi connectivity** for MQTT communication
- **Servo motor control** for gate automation
- **Ultrasonic sensor** for vehicle detection
- **MQTT client** for real-time messaging

## 📁 Files

```
pico2w/
├── main.py           # Main MicroPython application
├── config.py         # Configuration file (create this)
└── README.md         # This file
```

## 🔌 Hardware Connection

### Pin Configuration

| Component | Pico 2 W Pin | Description |
|-----------|-------------|-------------|
| Servo Signal | GPIO0 | PWM control signal |
| Servo VCC | 5V/VSYS | Servo power |
| Servo GND | GND | Common ground |
| HC-SR04 Trig | GPIO1 | Trigger pin |
| HC-SR04 Echo | GPIO2 | Echo pin |
| HC-SR04 VCC | 5V | Sensor power |
| HC-SR04 GND | GND | Common ground |

### Wiring Diagram

```
Raspberry Pi Pico 2 W
├── GP0  → Servo Signal (Orange/Yellow)
├── GP1  → HC-SR04 Trig
├── GP2  → HC-SR04 Echo
├── 5V   → Servo VCC (Red) + HC-SR04 VCC
└── GND  → Servo GND (Brown/Black) + HC-SR04 GND
```

## ⚙️ Configuration

### 1. Create `config.py` file:

```python
# WiFi Configuration
WIFI_SSID = "YourWiFiName"
WIFI_PASSWORD = "YourWiFiPassword"

# MQTT Configuration
MQTT_BROKER = "10.126.168.211"  # Your MQTT broker IP
MQTT_PORT = 1884
MQTT_USER = ""
MQTT_PASS = ""

# Sensor Configuration
TRIGGER_DISTANCE_CM = 30  # Distance to trigger detection (cm)
```

### 2. Edit `main.py`:

Update the configuration section at the top of `main.py` with your WiFi and MQTT settings.

## 🚀 Installation & Setup

### Prerequisites

1. **Raspberry Pi Pico 2 W**
2. **MicroPython Firmware** - Install latest MicroPython for Pico 2 W
3. **Thonny IDE** or **ampy** for uploading files

### Step 1: Install MicroPython

1. Download latest MicroPython UF2 for Pico 2 W from:
   https://www.raspberrypi.com/documentation/microcontrollers/micropython.html

2. Hold BOOTSEL button while connecting USB to put Pico in bootloader mode

3. Copy UF2 file to RPI-RP2 drive

### Step 2: Upload Code

#### Using Thonny IDE:

1. Open Thonny IDE
2. Connect Pico 2 W via USB
3. Select "MicroPython (Raspberry Pi Pico 2 W)" interpreter
3. Open `main.py` and click "Run" or "Upload to /"

#### Using ampy (Command Line):

```bash
# Install ampy
pip install adafruit-ampy

# Upload main.py
ampy --port COM3 put main.py

# Upload config.py (if created)
ampy --port COM3 put config.py
```

#### Using rshell:

```bash
# Install rshell
pip install rshell

# Connect and upload
rshell --port COM3
> cp main.py /pyboard/main.py
> cp config.py /pyboard/config.py
```

### Step 3: Run the Application

Pico 2 W will automatically run `main.py` on boot. To manually run:

```python
# In Thonny or serial console
import main
```

## 📡 MQTT Topics

### Topics Used:

- **`parking/trigger`** (Publish)
  - Publishes when vehicle detected
  - Payload: `{"event": "vehicle_detected", "seq": 1, "ts": 12345}`

- **`parking/cmd`** (Subscribe)
  - Receives gate control commands
  - Commands: `OPEN`, `CLOSE`
  - Payload: `{"cmd": "OPEN", "seq": 1}`

- **`parking/status`** (Publish)
  - Publishes device status
  - Payload: `{"status": "ready", "device": "pico2w_xxx"}`

## 🔧 Troubleshooting

### WiFi Connection Issues

```python
# Check WiFi status
import network
wlan = network.WLAN(network.STA_IF)
print(wlan.ifconfig())
```

### MQTT Connection Issues

1. Verify MQTT broker is running:
   ```bash
   # On your server
   mosquitto -c mosquitto/mosquitto.conf
   ```

2. Check firewall settings (port 1884)

3. Verify broker IP address in config

### Servo Not Working

1. Check servo power connection (5V from Pico or external supply)
2. Verify PWM signal on GP0
3. Test servo angles in code:
   ```python
   from machine import Pin, PWM
   servo = PWM(Pin(0))
   servo.freq(50)
   servo.duty_u16(3000)  # ~90 degrees
   ```

### Ultrasonic Sensor Issues

1. Check wiring (Trig → GP1, Echo → GP2)
2. Verify 5V power supply
3. Test distance reading:
   ```python
   from main import measure_distance
   print(measure_distance())
   ```

## 📊 Serial Monitor

Use Thonny IDE or serial monitor to view debug output:

```
[INIT] Servo initialized
[INIT] Ultrasonic sensor initialized
[INIT] All hardware initialized
[WIFI] Connecting to YourWiFi...
[WIFI] Connected! IP: 192.168.1.100
[MQTT] Connected to broker
[SYSTEM] Ready! Starting main loop...
[SENSOR] Distance: 45.2 cm
[SENSOR] Distance: 30.1 cm
[DETECT] Vehicle detected!
[MQTT] Trigger published (seq=1)
```

## 🔋 Power Requirements

- **Pico 2 W**: ~200mA
- **Servo (SG90)**: ~200-500mA (when moving)
- **HC-SR04**: ~15mA
- **Total**: ~400-700mA peak

**Recommendation**: Use 5V 2A power supply for reliable operation.

## 📝 Notes

- Default trigger distance: 30cm
- Cooldown period: 5 seconds between triggers
- Gate auto-closes 5 seconds after OPEN command
- Built-in error handling for sensor failures
- Automatic reconnection for WiFi/MQTT

## 🎓 Course Information

- **Course:** Embedded System
- **Institution:** Taipei Tech
- **Semester:** S2 - 1st Semester
- **Project:** Smart Parking Access Control System

---

**For main project documentation, see [../README.md](../README.md)**
