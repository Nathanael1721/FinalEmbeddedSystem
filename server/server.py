import time
import json
import threading
import queue

import cv2
import paho.mqtt.client as mqtt

# =========================
# CONFIG
# =========================
MQTT_HOST = "10.126.168.211"
MQTT_PORT = 1884
MQTT_USER = "YOUR_USER"
MQTT_PASS = "YOUR_PASS"

TOPIC_TRIGGER = "parking/trigger"
TOPIC_CMD     = "parking/cmd"
TOPIC_STATUS  = "parking/status"

TARGET_CLASS = "silver_car"
CONF_THRESH = 0.70

CAM_INDEX = 0
FRAMES_TO_CHECK = 10
DETECTION_TIMEOUT_S = 3.0

# =========================
# DETECTION PLACEHOLDER
# =========================
def detect_silver_car(frame):
    """
    Replace this function with your model.
    Must return: (pred_class: str, conf: float)

    Placeholder: simple color-based "silver" detection (heuristic) so the system runs.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Rough "silver/gray": low saturation, mid-high value
    # (heuristic, not ML)
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]
    mask = ((s < 60) & (v > 120)).astype("uint8")

    ratio = mask.mean() / 255.0  # 0..1
    conf = min(1.0, ratio * 3.0)
    pred = TARGET_CLASS if conf >= CONF_THRESH else "other"
    return pred, float(conf)

# =========================
# WORKER
# =========================
trigger_q = queue.Queue(maxsize=50)

def camera_worker(mqtt_client):
    cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError("Webcam not available")

    while True:
        item = trigger_q.get()
        if item is None:
            break

        seq = item.get("seq")
        t_start = time.time()

        best_class = None
        best_conf = 0.0

        # Only run detection briefly
        for _ in range(FRAMES_TO_CHECK):
            ok, frame = cap.read()
            if not ok:
                continue

            pred, conf = detect_silver_car(frame)
            if conf > best_conf:
                best_conf = conf
                best_class = pred

            if time.time() - t_start > DETECTION_TIMEOUT_S:
                break

        # Decision
        if best_class == TARGET_CLASS and best_conf >= CONF_THRESH:
            cmd = {"cmd": "OPEN", "seq": seq, "ts": int(time.time())}
            mqtt_client.publish(TOPIC_CMD, json.dumps(cmd), qos=1)
        else:
            status = {"gate": "DENIED", "seq": seq, "reason": f"{best_class}:{best_conf:.2f}", "ts": int(time.time())}
            mqtt_client.publish(TOPIC_STATUS, json.dumps(status), qos=0)

        trigger_q.task_done()

# =========================
# MQTT callbacks
# =========================
def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_TRIGGER, qos=0)

def on_message(client, userdata, msg):
    if msg.topic != TOPIC_TRIGGER:
        return
    try:
        data = json.loads(msg.payload.decode("utf-8"))
    except:
        return
    if data.get("event") != "vehicle_detected":
        return

    # enqueue trigger (non-blocking)
    try:
        trigger_q.put_nowait(data)
    except queue.Full:
        pass

def main():
    client = mqtt.Client(client_id="windows_parking_server")
    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASS)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)

    t = threading.Thread(target=camera_worker, args=(client,), daemon=True)
    t.start()

    client.loop_forever()

if __name__ == "__main__":
    main()
