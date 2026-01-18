import cv2
from flask import Flask, Response
import webbrowser
import threading
import time
import atexit

# =========================
# CONFIG (MANUAL SETTINGS)
# =========================
DEVICE_INDEX = 2        # USB3 Video = 2
WIDTH = 1920 
HEIGHT = 1080
FPS = 30
PORT = 5505
OPEN_BROWSER = True     # Auto open browser

# =========================
# FLASK APP
# =========================
app = Flask(__name__)
cap = None
browser_opened = False

# =========================
# CAMERA FUNCTIONS
# =========================
def open_camera():
    global cap
    cap = cv2.VideoCapture(DEVICE_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {DEVICE_INDEX}")

    # Set resolution and FPS
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    # Print actual camera settings
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = cap.get(cv2.CAP_PROP_FPS)

    print("[INFO] Camera opened")
    print(f"[INFO] Device index: {DEVICE_INDEX}")
    print(f"[INFO] Requested: {WIDTH}x{HEIGHT}@{FPS} FPS")
    print(f"[INFO] Actual: {actual_w}x{actual_h}@{actual_fps:.2f} FPS")

def release_camera():
    global cap
    if cap is not None:
        cap.release()
        cap = None
        print("[INFO] Camera released")

atexit.register(release_camera)

# =========================
# VIDEO STREAM GENERATOR
# =========================
def generate_frames():
    global cap
    while True:
        if cap is None:
            time.sleep(0.1)
            continue

        success, frame = cap.read()
        if not success or frame is None:
            continue

        ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )

# =========================
# FLASK ROUTES
# =========================
@app.route("/video")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )

@app.route("/")
def index():
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>USB Capture Feed</title>
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            background: black;
            height: 100%;
            overflow: hidden;
        }}
        img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}
        #info {{
            position: fixed;
            top: 10px;
            right: 10px;
            color: white;
            background: rgba(0,0,0,0.5);
            padding: 6px 10px;
            font-family: Arial;
            font-size: 14px;
            border-radius: 6px;
        }}
    </style>
</head>
<body>
    <div id="info">
        Device Index: {DEVICE_INDEX}<br>
        Resolution: {WIDTH}×{HEIGHT} @ {FPS} FPS
    </div>
    <img src="/video">
</body>
</html>
"""

# =========================
# OPEN BROWSER
# =========================
def open_browser_once():
    global browser_opened
    if OPEN_BROWSER and not browser_opened:
        time.sleep(1.5)
        webbrowser.open(f"http://localhost:{PORT}")
        browser_opened = True

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    open_camera()

    if OPEN_BROWSER:
        threading.Thread(target=open_browser_once, daemon=True).start()

    print(f"[INFO] Server running at http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
