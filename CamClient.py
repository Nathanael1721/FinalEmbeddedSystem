import cv2
import socket
import struct
import time

SERVER_HOST = "127.0.0.1"  # Server-IP
SERVER_PORT = 9999

VIDEO_SOURCE = 0
TARGET_W, TARGET_H = 1920, 1080
JPEG_QUALITY = 85
FPS = 25

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    s.connect((SERVER_HOST, SERVER_PORT))
    return s

cap = cv2.VideoCapture(VIDEO_SOURCE)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, TARGET_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, TARGET_H)

if not cap.isOpened():
    raise RuntimeError("Video source could not be opened")

interval = 1.0 / FPS

sock = None
while sock is None:
    try:
        sock = connect()
        print(f"Connected to {SERVER_HOST}:{SERVER_PORT}")
    except Exception as e:
        print("Connect failed, retrying:", e)
        time.sleep(1)

try:
    while True:
        t0 = time.time()

        ok, frame = cap.read()
        if not ok:
            print("Frame read failed")
            break

        if frame.shape[1] != TARGET_W or frame.shape[0] != TARGET_H:
            frame = cv2.resize(frame, (TARGET_W, TARGET_H), interpolation=cv2.INTER_AREA)

        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
        if not ok:
            continue

        jpg = buf.tobytes()
        header = struct.pack("!I", len(jpg))

        try:
            sock.sendall(header)
            sock.sendall(jpg)
        except Exception as e:
            print("Send failed, reconnecting:", e)
            try:
                sock.close()
            except Exception:
                pass
            sock = None
            while sock is None:
                try:
                    sock = connect()
                    print(f"Reconnected to {SERVER_HOST}:{SERVER_PORT}")
                except Exception as e2:
                    print("Reconnect failed, retrying:", e2)
                    time.sleep(1)

        # FPS limit
        dt = time.time() - t0
        sleep = interval - dt
        if sleep > 0:
            time.sleep(sleep)

finally:
    try:
        cap.release()
    except Exception:
        pass
    try:
        if sock:
            sock.close()
    except Exception:
        pass
