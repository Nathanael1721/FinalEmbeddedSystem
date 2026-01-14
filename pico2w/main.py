"""
Smart Parking Gate Control - Raspberry Pi Pico 2 W
Main MicroPython Code for ESP32/Pico2W Parking Gate System

Hardware:
- Raspberry Pi Pico 2 W
- Servo Motor (SG90/MG996R) - Gate control
- Ultrasonic Sensor (HC-SR04) - Distance detection
- MQTT Client over WiFi

Author: Nathanael Tjahyadi
Course: Embedded System - Taipei Tech
"""

import machine
import time
import network
import ubinascii
import umqtt.simple
import ujson
from machine import Pin, PWM

# =========================
# CONFIGURATION
# =========================

# WiFi Configuration
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# MQTT Configuration
MQTT_BROKER = "10.126.168.211"  # IP address MQTT broker
MQTT_PORT = 1884
MQTT_CLIENT_ID = f"pico2w_{ubinascii.hexlify(machine.unique_id()).decode()}"
MQTT_USER = ""
MQTT_PASS = ""

# MQTT Topics
TOPIC_TRIGGER = "parking/trigger"
TOPIC_CMD = "parking/cmd"
TOPIC_STATUS = "parking/status"

# Hardware Pins
SERVO_PIN = 0        # GPIO0 for Servo
TRIG_PIN = 1         # GPIO1 for Ultrasonic Trigger
ECHO_PIN = 2         # GPIO2 for Ultrasonic Echo

# Servo Configuration
SERVO_OPEN_ANGLE = 90    # Open gate angle
SERVO_CLOSED_ANGLE = 0   # Closed gate angle
SERVO_FREQ = 50         # 50Hz PWM frequency

# Ultrasonic Configuration
MAX_DISTANCE_CM = 200    # Maximum detection distance
TRIGGER_DISTANCE_CM = 30 # Distance to trigger detection

# Timing
MEASUREMENT_INTERVAL_MS = 500  # Distance measurement interval
COOLDOWN_MS = 5000             # Cooldown after triggering

# =========================
# GLOBAL VARIABLES
# =========================

servo = None
trig_pin = None
echo_pin = None
mqtt_client = None
wifi_connected = False
last_trigger_time = 0
sequence_number = 0

# =========================
# HARDWARE INITIALIZATION
# =========================

def init_servo():
    """Initialize servo motor for gate control"""
    global servo
    servo = PWM(Pin(SERVO_PIN))
    servo.freq(SERVO_FREQ)
    close_gate()
    print("[INIT] Servo initialized")

def init_ultrasonic():
    """Initialize ultrasonic sensor pins"""
    global trig_pin, echo_pin
    trig_pin = Pin(TRIG_PIN, Pin.OUT)
    echo_pin = Pin(ECHO_PIN, Pin.IN)
    trig_pin.value(0)
    print("[INIT] Ultrasonic sensor initialized")

def init_hardware():
    """Initialize all hardware components"""
    init_servo()
    init_ultrasonic()
    print("[INIT] All hardware initialized")

# =========================
# SERVO CONTROL
# =========================

def set_servo_angle(angle):
    """
    Set servo angle (0-180 degrees)

    Args:
        angle: Angle in degrees (0-180)
    """
    # Convert angle to duty cycle (0-65535)
    # Servo typically uses 1-2ms pulse, at 50Hz = 20ms period
    # 0° = 1ms (5% duty), 180° = 2ms (10% duty)
    duty = int((angle / 180) * 65535 * 0.1)  # 0.1 = 10% max duty
    servo.duty_u16(duty)

def open_gate():
    """Open the parking gate"""
    print("[GATE] Opening gate...")
    set_servo_angle(SERVO_OPEN_ANGLE)
    time.sleep(0.5)  # Wait for servo to reach position
    print("[GATE] Gate opened")

def close_gate():
    """Close the parking gate"""
    print("[GATE] Closing gate...")
    set_servo_angle(SERVO_CLOSED_ANGLE)
    time.sleep(0.5)  # Wait for servo to reach position
    print("[GATE] Gate closed")

# =========================
# ULTRASONIC SENSOR
# =========================

def measure_distance():
    """
    Measure distance using ultrasonic sensor

    Returns:
        Distance in cm, or None if measurement failed
    """
    # Send trigger pulse
    trig_pin.value(0)
    time.sleep_us(2)
    trig_pin.value(1)
    time.sleep_us(10)
    trig_pin.value(0)

    # Wait for echo start
    timeout = time.ticks_ms() + 100  # 100ms timeout
    while echo_pin.value() == 0:
        if time.ticks_ms() > timeout:
            return None
        time.sleep_us(1)

    # Measure echo duration
    start = time.ticks_us()
    timeout = time.ticks_ms() + 100
    while echo_pin.value() == 1:
        if time.ticks_ms() > timeout:
            return None
        time.sleep_us(1)

    duration = time.ticks_diff(time.ticks_us(), start)

    # Calculate distance (speed of sound = 343 m/s)
    distance_cm = (duration * 343) / 10000 / 2

    return distance_cm

# =========================
# MQTT CALLBACKS
# =========================

def on_mqtt_connect(client):
    """Callback when MQTT connection is established"""
    print("[MQTT] Connected to broker")
    client.subscribe(TOPIC_CMD)

def on_mqtt_message(topic, msg):
    """
    Callback when MQTT message is received

    Args:
        topic: MQTT topic
        msg: Message payload (bytes)
    """
    global last_trigger_time

    try:
        topic_str = topic.decode()
        msg_str = msg.decode()

        print(f"[MQTT] Received: {topic_str} = {msg_str}")

        if topic_str == TOPIC_CMD:
            data = ujson.loads(msg_str)
            cmd = data.get("cmd")

            if cmd == "OPEN":
                open_gate()
                # Auto-close after 5 seconds
                time.sleep(5)
                close_gate()

            elif cmd == "CLOSE":
                close_gate()

    except Exception as e:
        print(f"[ERROR] MQTT message handling: {e}")

def on_mqtt_disconnect():
    """Callback when MQTT connection is lost"""
    print("[MQTT] Disconnected from broker")

# =========================
# MQTT FUNCTIONS
# =========================

def connect_mqtt():
    """Connect to MQTT broker"""
    global mqtt_client

    try:
        mqtt_client = umqtt.simple.MQTTClient(
            MQTT_CLIENT_ID,
            MQTT_BROKER,
            MQTT_PORT,
            MQTT_USER,
            MQTT_PASS
        )

        mqtt_client.set_callback(on_mqtt_message)
        mqtt_client.connect()
        on_mqtt_connect(mqtt_client)

        return True

    except Exception as e:
        print(f"[ERROR] MQTT connection failed: {e}")
        return False

def publish_trigger():
    """Publish vehicle detection trigger to MQTT"""
    global sequence_number

    try:
        sequence_number += 1

        trigger_msg = {
            "event": "vehicle_detected",
            "seq": sequence_number,
            "ts": time.ticks_ms(),
            "device": MQTT_CLIENT_ID
        }

        mqtt_client.publish(
            TOPIC_TRIGGER,
            ujson.dumps(trigger_msg)
        )

        print(f"[MQTT] Trigger published (seq={sequence_number})")

    except Exception as e:
        print(f"[ERROR] Failed to publish trigger: {e}")

def publish_status(status, reason=None):
    """
    Publish system status to MQTT

    Args:
        status: Status message
        reason: Optional reason for status
    """
    try:
        status_msg = {
            "status": status,
            "device": MQTT_CLIENT_ID,
            "ts": time.ticks_ms()
        }

        if reason:
            status_msg["reason"] = reason

        mqtt_client.publish(
            TOPIC_STATUS,
            ujson.dumps(status_msg)
        )

        print(f"[MQTT] Status published: {status}")

    except Exception as e:
        print(f"[ERROR] Failed to publish status: {e}")

# =========================
# WIFI CONNECTION
# =========================

def connect_wifi():
    """Connect to WiFi network"""
    global wifi_connected

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print(f"[WIFI] Connecting to {WIFI_SSID}...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        # Wait for connection with timeout
        timeout = time.ticks_ms() + 10000  # 10 second timeout
        while not wlan.isconnected():
            if time.ticks_ms() > timeout:
                print("[WIFI] Connection timeout")
                return False
            time.sleep(0.5)

    wifi_connected = True
    ip, subnet, gateway, dns = wlan.ifconfig()
    print(f"[WIFI] Connected! IP: {ip}")
    return True

# =========================
# MAIN APPLICATION
# =========================

def check_vehicle_detection():
    """
    Check for vehicle presence using ultrasonic sensor
    Publish trigger if vehicle detected
    """
    global last_trigger_time

    try:
        distance = measure_distance()

        if distance is None:
            return

        print(f"[SENSOR] Distance: {distance:.1f} cm")

        # Check if vehicle detected within trigger distance
        if distance < TRIGGER_DISTANCE_CM:
            current_time = time.ticks_ms()

            # Check cooldown to prevent multiple triggers
            if time.ticks_diff(current_time, last_trigger_time) > COOLDOWN_MS:
                print("[DETECT] Vehicle detected!")
                publish_trigger()
                last_trigger_time = current_time
            else:
                remaining = COOLDOWN_MS - time.ticks_diff(current_time, last_trigger_time)
                print(f"[COOLDOWN] {remaining}ms remaining")

    except Exception as e:
        print(f"[ERROR] Detection check failed: {e}")

def main():
    """Main application loop"""
    global mqtt_client

    print("=" * 50)
    print("Smart Parking Gate Control - Pico 2W")
    print("=" * 50)

    # Initialize hardware
    init_hardware()

    # Connect to WiFi
    if not connect_wifi():
        print("[ERROR] Failed to connect to WiFi")
        return

    # Connect to MQTT broker
    if not connect_mqtt():
        print("[ERROR] Failed to connect to MQTT broker")
        return

    print("[SYSTEM] Ready! Starting main loop...")
    publish_status("ready")

    # Main loop
    while True:
        try:
            # Check for incoming MQTT messages
            mqtt_client.check_msg()

            # Check for vehicle detection
            check_vehicle_detection()

            # Small delay
            time.sleep_ms(MEASUREMENT_INTERVAL_MS)

        except KeyboardInterrupt:
            print("\n[SYSTEM] Interrupted by user")
            break

        except Exception as e:
            print(f"[ERROR] Main loop error: {e}")
            time.sleep(1)

    # Cleanup
    print("[SYSTEM] Shutting down...")
    close_gate()
    if mqtt_client:
        mqtt_client.disconnect()
    publish_status("shutdown")
    print("[SYSTEM] Goodbye!")

# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    main()
