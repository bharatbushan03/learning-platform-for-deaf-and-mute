import cv2
import mediapipe as mp
import numpy as np
import csv
import os
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ── MediaPipe Setup ───────────────────────────────────────────────
base_options = python.BaseOptions(
    model_asset_path=r'models/hand_landmarker.task'
)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7,
    running_mode=vision.RunningMode.VIDEO
)
detector = vision.HandLandmarker.create_from_options(options)

# ── Missing hand placeholder ──────────────────────────────────────
MISSING_HAND = [-1.0] * 63

# ── Hand connections ──────────────────────────────────────────────
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17)
]

# ── CSV Setup ─────────────────────────────────────────────────────
output_file = "data2.csv"

if not os.path.exists(output_file):
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ["label"]
        for hand in ["left", "right"]:
            for i in range(21):
                header += [f"{hand}_x{i}", f"{hand}_y{i}", f"{hand}_z{i}"]
        writer.writerow(header)
    print("CSV created.")

# ── Webcam ────────────────────────────────────────────────────────
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# ── State ─────────────────────────────────────────────────────────
target_samples = 50
sample_count   = 0

print("Instructions:")
print("1. Enter sign label and press Enter")
print("2. Make the sign in front of camera")
print("3. Press SPACE to capture one sample")
print("4. Capture 50 samples per sign")
print("5. Press Q to quit")

current_sign = input("Enter sign label to start (e.g. A, B, 1): ").upper()
os.makedirs("Indian-2", exist_ok = True)
os.makedirs(f"Indian-2/{current_sign}", exist_ok = True)

# ── Main Loop ─────────────────────────────────────────────────────
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = rgb.copy()

    timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )

    detection_result = detector.detect_for_video(mp_image, timestamp_ms)

    # ── Initialize both hands as missing ──────────────────────────
    left_hand  = MISSING_HAND.copy()
    right_hand = MISSING_HAND.copy()
    hand_detected = False

    if detection_result.hand_landmarks:
        h, w, _ = frame.shape

        for i, hand_landmarks in enumerate(detection_result.hand_landmarks):
            handedness = detection_result.handedness[i][0].display_name

            # Draw landmarks
            points = []
            for lm in hand_landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                points.append((cx, cy))
                color = (255, 0, 0) if handedness == "Left" else (0, 0, 255)
                cv2.circle(frame, (cx, cy), 6, color, -1)

            for connection in HAND_CONNECTIONS:
                start = points[connection[0]]
                end   = points[connection[1]]
                line_color = (255, 0, 255) if handedness == "Left" else (0, 255, 255)
                cv2.line(frame, start, end, line_color, 2)

            # Extract coords
            coords = []
            for lm in hand_landmarks:
                coords += [round(lm.x, 4), round(lm.y, 4), round(lm.z, 4)]

            # Assign — swapped to fix mirror issue
            if handedness == "Left":
                right_hand = coords
            else:
                left_hand = coords

            hand_detected = True

    # ── Display info ──────────────────────────────────────────────
    cv2.putText(frame, f"Sign: {current_sign}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
    cv2.putText(frame, f"Samples: {sample_count}/{target_samples}", (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

    if hand_detected:
        cv2.putText(frame, "Hand Detected — Press SPACE to capture", (10, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "No Hand Detected", (10, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv2.putText(frame, "Blue=Left | Red=Right | SPACE=capture | Q=quit",
                (10, frame.shape[0] - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

    cv2.imshow("ISL Data Collection — 126 Points", frame)
    cv2.resizeWindow("ISL Data Collection — 126 Points", 1280, 720)

    key = cv2.waitKey(1) & 0xFF

    # ── SPACE = capture ───────────────────────────────────────────
    if key == ord(' ') and hand_detected:
        with open(output_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([current_sign] + left_hand + right_hand)
        cv2.imwrite(f"Indian-2/{current_sign}/{sample_count}.jpg")

        sample_count += 1
        print(f"Captured {sample_count}/50 for sign '{current_sign}'")

        if sample_count >= target_samples:
            print(f"Done! 50 samples collected for '{current_sign}'")
            next_sign = input("Enter next sign label (or Q to quit): ").upper()
            if next_sign == 'Q':
                break
            current_sign = next_sign
            sample_count = 0

    if key == ord('q'):
        break

# ── Cleanup ───────────────────────────────────────────────────────
cap.release()
cv2.destroyAllWindows()
detector.close()
print(f"Collection complete. Saved to {output_file}")