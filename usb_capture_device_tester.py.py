import cv2
from pyusbcameraindex import enumerate_usb_video_devices_windows
import time

# -----------------------------------
# ENUMERATE DEVICES
# -----------------------------------
devices = enumerate_usb_video_devices_windows()

print("\n[INFO] Enumerated video devices:\n")
for d in devices:
    print(f"{d.index} == {d.name} (VID: {d.vid}, PID: {d.pid}, Path: {d.path})")

# -----------------------------------
# ONLY TEST REAL USB CAPTURE DEVICES
# -----------------------------------
print("\n[INFO] Testing OpenCV access with multiple resolutions and FPS:\n")

# Resolutions to try
resolutions = [
    (640, 480),
    (1280, 720),
    (1920, 1080)
]

# FPS to try
fps_to_try = [15, 24, 25, 30, 50, 60, 75, 120]

for d in devices:

    # Skip virtual / non-USB devices
    if not d.path or not d.path.lower().startswith(r"\\?\usb#"):
        print(f"[SKIP] {d.name} (index {d.index}) → virtual / non-USB")
        continue

    cap = cv2.VideoCapture(d.index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print(f"[SKIP] {d.name} (index {d.index}) → cannot open")
        cap.release()
        continue

    print(f"[OK] {d.name} → index {d.index} resolutions:")

    for w_req, h_req in resolutions:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w_req)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h_req)

        ret, frame = cap.read()
        if not ret or frame is None:
            print(f"  Requested {w_req}x{h_req} → No frame")
            continue

        h, w = frame.shape[:2]
        print(f"  Requested {w_req}x{h_req} → Got {w}x{h}")

        # Test FPS for this resolution
        supported_fps = []
        print(f"    [INFO] Testing supported FPS for {w}x{h}...")

        for fps in fps_to_try:
            cap.set(cv2.CAP_PROP_FPS, fps)
            # Capture 30 frames to measure actual FPS
            frame_count = 30
            start = time.time()
            success = True
            for _ in range(frame_count):
                ret, _ = cap.read()
                if not ret:
                    success = False
                    break
            end = time.time()
            if not success:
                continue

            elapsed = end - start
            actual_fps = frame_count / elapsed if elapsed > 0 else 0

            # Consider it supported if actual FPS >= 90% of requested
            if actual_fps >= 0.9 * fps:
                supported_fps.append(fps)
                print(f"      [OK] Supported FPS: {fps}")

        print(f"    [INFO] Supported FPS: {supported_fps}\n")

    cap.release()

