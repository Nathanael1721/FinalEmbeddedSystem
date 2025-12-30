import torch

# Memuat model
model = torch.load('E:\One Drive\OneDrive\College\S2 - Taipei Tech\1st Semester\Embedded System\FinalEmbeddedSystem\yolov12n-face.pt')

# Jika model disimpan dalam format biasa
print(model)

# Jika model disimpan dengan atribut kelas (misalnya daftar kelas)
if hasattr(model, 'classes'):
    print(model.classes)
else:
    print("Tidak ada atribut kelas dalam model.")

# from flask import Flask, Response, render_template, jsonify, request
# from datetime import datetime
# import json
# import os
# import queue
# import threading
# import time
# import socket
# import struct

# import cv2
# import paho.mqtt.client as mqtt
# from ultralytics import YOLO

# app = Flask(__name__, template_folder="Templates")

# # =========================
# # Action Log (in-memory)
# # =========================
# action_log = []
# next_id = 1
# log_lock = threading.Lock()

# def add_log(content: str):
#     global next_id
#     with log_lock:
#         action_log.append({
#             "id": next_id,
#             "timestamp": datetime.now().isoformat(timespec="seconds"),
#             "content": content,
#         })
#         next_id += 1
#         if len(action_log) > 200:
#             action_log.pop(0)

# # =========================
# # Latest frame + signaling
# # =========================
# latest_jpeg = None
# latest_frame = None
# frame_id = 0
# last_frame_ts = 0.0
# frame_cv = threading.Condition()

# # =========================
# # Video Source Settings
# # =========================
# USE_TCP_STREAM = False  # False = use local camera; True = receive JPEGs via TCP
# STREAM_FPS = 10
# STREAM_ACTIVE_S = 5.0

# # =========================
# # TCP Receiver Settings
# # =========================
# TCP_HOST = "0.0.0.0"
# TCP_PORT = 9999
# MAX_FRAME_BYTES = 20_000_000  # 20 MB safety limit

# # =========================
# # MQTT + Detection Settings
# # =========================
# MQTT_HOST = "10.126.168.211"
# MQTT_PORT = 1884
# MQTT_USER = ""
# MQTT_PASS = ""

# TOPIC_TRIGGER = "parking/trigger"
# TOPIC_CMD = "parking/cmd"
# TOPIC_STATUS = "parking/status"
# TARGET_CLASS = "face"
# #TARGET_CLASS = "toy car"
# CONF_THRESH = 0.70

# FRAMES_TO_CHECK = 10
# DETECTION_TIMEOUT_S = 3.0

# # =========================
# # System Status Tracking
# # =========================
# system_status = {
#     "door_status": "CLOSED",  # CLOSED, OPEN
#     "last_detection": "None",  # None, silver_car, etc.
#     "detection_confidence": 0.0,
#     "last_detection_time": None,
#     "mqtt_connected": False,
#     "total_detections": 0,
#     "access_granted": 0,
#     "access_denied": 0,
# }
# status_lock = threading.Lock()

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
# #MODEL_PATH = os.path.join(REPO_ROOT, "server", "best.pt")
# MODEL_PATH = os.path.join(REPO_ROOT, "server", "E:\One Drive\OneDrive\College\S2 - Taipei Tech\1st Semester\Embedded System\FinalEmbeddedSystem\yolov12n-face.pt")

# camera_lock = threading.Lock()
# current_camera_index = 0

# model_lock = threading.Lock()
# model = None
# model_load_error = None

# trigger_q = queue.Queue(maxsize=50)
# mqtt_client = None

# stream_lock = threading.Lock()
# stream_active_until = 0.0


# def set_stream_active(duration_s: float) -> None:
#     global stream_active_until
#     if duration_s <= 0:
#         return
#     with stream_lock:
#         until = time.time() + duration_s
#         if until > stream_active_until:
#             stream_active_until = until
#     with frame_cv:
#         frame_cv.notify_all()


# def is_stream_active() -> bool:
#     with stream_lock:
#         return time.time() < stream_active_until


# def get_camera_index() -> int:
#     with camera_lock:
#         return current_camera_index


# def set_camera_index(idx: int) -> None:
#     global current_camera_index
#     with camera_lock:
#         current_camera_index = idx


# def open_camera(index: int):
#     if os.name == "nt":
#         return cv2.VideoCapture(index, cv2.CAP_DSHOW)
#     return cv2.VideoCapture(index)


# def get_model():
#     global model, model_load_error
#     with model_lock:
#         if model is not None or model_load_error is not None:
#             return model
#         try:
#             if not os.path.exists(MODEL_PATH):
#                 raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
#             model = YOLO(MODEL_PATH)
#             add_log(f"Model loaded: {MODEL_PATH}")
#         except Exception as e:
#             model_load_error = str(e)
#             add_log(f"Model load error: {e}")
#         return model


# def detect_with_model(frame):
#     m = get_model()
#     if m is None:
#         return None, 0.0

#     results = m.predict(source=frame, verbose=False)
#     if not results:
#         return None, 0.0

#     r0 = results[0]
#     best_class = None
#     best_conf = 0.0
#     names = getattr(r0, "names", {})

#     if getattr(r0, "boxes", None) is None:
#         return None, 0.0

#     for box in r0.boxes:
#         try:
#             cls_id = int(box.cls[0])
#             conf = float(box.conf[0])
#         except Exception:
#             continue
#         name = names.get(cls_id, str(cls_id))
#         if conf > best_conf:
#             best_conf = conf
#             best_class = name

#     return best_class, best_conf


# def recv_exact(conn: socket.socket, n: int) -> bytes:
#     """Read exactly n bytes from conn, otherwise raise ConnectionError."""
#     buf = bytearray()
#     while len(buf) < n:
#         chunk = conn.recv(n - len(buf))
#         if not chunk:
#             raise ConnectionError("Client disconnected")
#         buf.extend(chunk)
#     return bytes(buf)


# def tcp_receiver():
#     """
#     Protocol:
#       Repeated frames over one persistent TCP connection:
#         [4 bytes big-endian length][JPEG bytes...]
#     """
#     global latest_jpeg, latest_frame, frame_id, last_frame_ts

#     srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     srv.bind((TCP_HOST, TCP_PORT))
#     srv.listen(1)

#     print(f"[TCP] Listening on {TCP_HOST}:{TCP_PORT}", flush=True)
#     add_log(f"TCP receiver listening on {TCP_HOST}:{TCP_PORT}")

#     while True:
#         conn, addr = srv.accept()
#         print(f"[TCP] client connected {addr}", flush=True)
#         add_log(f"TCP client connected: {addr}")

#         try:
#             conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

#             # Keep this connection open and receive many frames
#             while True:
#                 header = recv_exact(conn, 4)
#                 (length,) = struct.unpack("!I", header)

#                 if length <= 0 or length > MAX_FRAME_BYTES:
#                     raise ValueError(f"Invalid frame length: {length}")

#                 jpg = recv_exact(conn, length)

#                 with frame_cv:
#                     latest_jpeg = jpg
#                     latest_frame = None
#                     frame_id += 1
#                     last_frame_ts = time.time()
#                     frame_cv.notify_all()

#         except ConnectionError:
#             print(f"[TCP] client disconnected {addr}", flush=True)
#             add_log(f"TCP client disconnected: {addr}")
#         except Exception as e:
#             print(f"[TCP] error {addr}: {e}", flush=True)
#             add_log(f"TCP client error {addr}: {e}")
#         finally:
#             try:
#                 conn.close()
#             except Exception:
#                 pass


# def camera_streamer():
#     global latest_jpeg, latest_frame, frame_id, last_frame_ts
#     cap = None
#     active_cam_index = None
#     last_tick = 0.0

#     while True:
#         if not is_stream_active():
#             if cap is not None:
#                 try:
#                     cap.release()
#                 except Exception:
#                     pass
#                 cap = None
#                 active_cam_index = None
#             time.sleep(0.1)
#             continue

#         cam_index = get_camera_index()
#         if cap is None or active_cam_index != cam_index:
#             if cap is not None:
#                 try:
#                     cap.release()
#                 except Exception:
#                     pass
#             cap = open_camera(cam_index)
#             active_cam_index = cam_index
#             if not cap.isOpened():
#                 add_log(f"Camera {cam_index} not available for stream")
#                 try:
#                     cap.release()
#                 except Exception:
#                     pass
#                 cap = None
#                 time.sleep(0.5)
#                 continue
#             add_log(f"Camera {cam_index} opened for stream")

#         ok, frame = cap.read()
#         if not ok:
#             time.sleep(0.05)
#             continue

#         ok, buf = cv2.imencode(".jpg", frame)
#         if not ok:
#             continue

#         jpg = buf.tobytes()
#         with frame_cv:
#             latest_frame = frame.copy()
#             latest_jpeg = jpg
#             frame_id += 1
#             last_frame_ts = time.time()
#             frame_cv.notify_all()

#         now = time.time()
#         dt = now - last_tick
#         if dt < 1.0 / STREAM_FPS:
#             time.sleep((1.0 / STREAM_FPS) - dt)
#         last_tick = time.time()


# # Start video source thread
# if USE_TCP_STREAM:
#     threading.Thread(target=tcp_receiver, daemon=True).start()
# else:
#     threading.Thread(target=camera_streamer, daemon=True).start()

# # =========================
# # MQTT + Detection Worker
# # =========================
# def detection_worker(client: mqtt.Client):
#     global system_status
#     while True:
#         item = trigger_q.get()
#         if item is None:
#             break

#         seq = item.get("seq")
#         t_start = time.time()
#         best_class = None
#         best_conf = 0.0

#         set_stream_active(max(STREAM_ACTIVE_S, DETECTION_TIMEOUT_S + 1.0))
#         last_seen = -1
#         got_frame = False

#         for _ in range(FRAMES_TO_CHECK):
#             with frame_cv:
#                 frame_cv.wait_for(lambda: frame_id != last_seen and latest_frame is not None, timeout=0.5)
#                 if latest_frame is None or frame_id == last_seen:
#                     if time.time() - t_start > DETECTION_TIMEOUT_S:
#                         break
#                     continue
#                 frame = latest_frame.copy()
#                 last_seen = frame_id
#                 got_frame = True

#             pred, conf = detect_with_model(frame)
#             if conf > best_conf:
#                 best_conf = conf
#                 best_class = pred

#             if time.time() - t_start > DETECTION_TIMEOUT_S:
#                 break

#         if not got_frame:
#             status = {"gate": "DENIED", "seq": seq, "reason": "no_frame", "ts": int(time.time())}
#             client.publish(TOPIC_STATUS, json.dumps(status), qos=0)
#             add_log("DENIED (no_frame)")
#             with status_lock:
#                 system_status["total_detections"] += 1
#                 system_status["access_denied"] += 1
#             trigger_q.task_done()
#             continue

#         if best_class == TARGET_CLASS and best_conf >= CONF_THRESH:
#             cmd = {"cmd": "OPEN", "seq": seq, "ts": int(time.time())}
#             client.publish(TOPIC_CMD, json.dumps(cmd), qos=1)
#             add_log(f"OPEN sent (seq={seq}, conf={best_conf:.2f})")
#             with status_lock:
#                 system_status["door_status"] = "OPEN"
#                 system_status["last_detection"] = best_class
#                 system_status["detection_confidence"] = best_conf
#                 system_status["last_detection_time"] = datetime.now().isoformat(timespec="seconds")
#                 system_status["total_detections"] += 1
#                 system_status["access_granted"] += 1
#         else:
#             reason = f"{best_class}:{best_conf:.2f}"
#             status = {"gate": "DENIED", "seq": seq, "reason": reason, "ts": int(time.time())}
#             client.publish(TOPIC_STATUS, json.dumps(status), qos=0)
#             add_log(f"DENIED (seq={seq}, reason={reason})")
#             with status_lock:
#                 system_status["door_status"] = "CLOSED"
#                 system_status["last_detection"] = best_class if best_class else "None"
#                 system_status["detection_confidence"] = best_conf
#                 system_status["last_detection_time"] = datetime.now().isoformat(timespec="seconds")
#                 system_status["total_detections"] += 1
#                 system_status["access_denied"] += 1

#         trigger_q.task_done()


# def on_connect(client, userdata, flags, rc):
#     client.subscribe(TOPIC_TRIGGER, qos=0)
#     add_log(f"MQTT connected rc={rc}")
#     with status_lock:
#         system_status["mqtt_connected"] = True


# def on_message(client, userdata, msg):
#     if msg.topic != TOPIC_TRIGGER:
#         return
#     try:
#         data = json.loads(msg.payload.decode("utf-8"))
#     except Exception:
#         return
#     if data.get("event") != "vehicle_detected":
#         return

#     try:
#         set_stream_active(STREAM_ACTIVE_S)
#         trigger_q.put_nowait(data)
#         add_log(f"Trigger received (seq={data.get('seq')})")
#     except queue.Full:
#         add_log("Trigger queue full, dropped")


# def start_mqtt():
#     global mqtt_client
#     client = mqtt.Client(client_id="parking_web_app")
#     if MQTT_USER:
#         client.username_pw_set(MQTT_USER, MQTT_PASS)

#     client.on_connect = on_connect
#     client.on_message = on_message

#     try:
#         client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
#     except Exception as e:
#         add_log(f"MQTT connect error: {e}")
#         return None

#     t = threading.Thread(target=client.loop_forever, daemon=True)
#     t.start()

#     w = threading.Thread(target=detection_worker, args=(client,), daemon=True)
#     w.start()

#     mqtt_client = client
#     return client


# start_mqtt()

# # =========================
# # Flask routes
# # =========================
# @app.route("/")
# def index():
#     add_log("Page opened.")
#     return render_template("index.html")


# def generate_mjpeg():
#     """
#     MJPEG stream of the latest received JPEG.
#     Sends only when a new frame arrives.
#     """
#     last_sent = 0
#     while True:
#         with frame_cv:
#             frame_cv.wait_for(lambda: frame_id != last_sent, timeout=5.0)
#             if latest_jpeg is None:
#                 continue
#             jpg = latest_jpeg
#             last_sent = frame_id

#         yield (
#             b"--frame\r\n"
#             b"Content-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
#         )


# @app.route("/video_feed")
# def video_feed():
#     return Response(
#         generate_mjpeg(),
#         mimetype="multipart/x-mixed-replace; boundary=frame",
#     )


# @app.route("/log")
# def log():
#     with log_lock:
#         return jsonify(action_log[-50:])


# @app.route("/status")
# def status():
#     with frame_cv:
#         has_frame = latest_jpeg is not None
#         age = None if not has_frame else round(time.time() - last_frame_ts, 3)
#         fid = frame_id
#         size = None if not has_frame else len(latest_jpeg)

#     return jsonify({
#         "has_frame": has_frame,
#         "frame_id": fid,
#         "frame_age_seconds": age,
#         "jpeg_bytes": size,
#         "use_tcp_stream": USE_TCP_STREAM,
#         "stream_active": is_stream_active(),
#         "tcp_host": TCP_HOST,
#         "tcp_port": TCP_PORT,
#         "camera_index": get_camera_index(),
#         "model_path": MODEL_PATH,
#         "model_loaded": model is not None,
#         "model_error": model_load_error
#     })


# @app.route("/system_status")
# def system_status_endpoint():
#     """Return system status including door, detection, and MQTT status"""
#     with status_lock:
#         status_copy = system_status.copy()

#     # Add additional system info
#     status_copy["model_loaded"] = model is not None
#     status_copy["stream_active"] = is_stream_active()
#     status_copy["camera_index"] = get_camera_index()

#     return jsonify(status_copy)


# @app.route("/cameras")
# def cameras():
#     available = []
#     for idx in range(6):
#         cap = open_camera(idx)
#         if cap.isOpened():
#             available.append(idx)
#         try:
#             cap.release()
#         except Exception:
#             pass
#     return jsonify({"available": available, "current": get_camera_index()})


# @app.route("/set_camera", methods=["POST"])
# def set_camera():
#     data = request.get_json(silent=True) or {}
#     try:
#         idx = int(data.get("index"))
#     except Exception:
#         return jsonify({"ok": False, "error": "invalid_index"}), 400

#     if idx < 0 or idx > 10:
#         return jsonify({"ok": False, "error": "out_of_range"}), 400

#     set_camera_index(idx)
#     add_log(f"Camera selected: {idx}")
#     return jsonify({"ok": True, "current": idx})


# if __name__ == "__main__":
#     # Important: debug=False to avoid the reloader running twice
#     app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
