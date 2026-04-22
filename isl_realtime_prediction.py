import cv2
import mediapipe as mp
import numpy as np
import pickle
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ── Load Model & Encoder ──────────────────────────────────────────
with open(r"models/isl-model.pkl", "rb") as f:
    model = pickle.load(f)

with open(r"models/label-encoder.pkl", "rb") as f:
    le = pickle.load(f)

# ── MediaPipe v0.10+ Setup ────────────────────────────────────────
base_options = python.BaseOptions(
    model_asset_path=r'models/hand_landmarker.task'
)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,                          # Changed to 2
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7,
    running_mode=vision.RunningMode.VIDEO
)
detector = vision.HandLandmarker.create_from_options(options)

# ── Webcam ────────────────────────────────────────────────────────
cap = cv2.VideoCapture(0)

# ── Increase window size ──────────────────────────────────────────
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# ── Hand connections ──────────────────────────────────────────────
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17)
]

# ── Missing hand placeholder ──────────────────────────────────────
MISSING_HAND = [-1.0] * 63  # 21 landmarks × 3 coords

# ── State ─────────────────────────────────────────────────────────
word_buffer      = []
last_prediction  = ""
stable_count     = 0
stable_threshold = 15

print("ISL Real-Time Prediction Started — Both Hands")
print("SPACE = clear buffer | Q = quit")

# ── Main Loop ─────────────────────────────────────────────────────
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Camera error.")
        break

    # Mirror flip
    frame = cv2.flip(frame, 1)
    rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Timestamp
    timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )

    detection_result = detector.detect_for_video(mp_image, timestamp_ms)

    prediction = ""
    confidence = 0.0

    # ── Initialize both hands as missing ──────────────────────────
    left_hand  = MISSING_HAND.copy()
    right_hand = MISSING_HAND.copy()

    if detection_result.hand_landmarks:
        h, w, _ = frame.shape

        for i, hand_landmarks in enumerate(detection_result.hand_landmarks):

            # ── Get handedness ────────────────────────────────────
            handedness = detection_result.handedness[i][0].display_name

            # ── Draw landmarks ────────────────────────────────────
            points = []
            for lm in hand_landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                points.append((cx, cy))

                # Different color per hand
                color = (255, 0, 0) if handedness == "Left" else (0, 0, 255)
                cv2.circle(frame, (cx, cy), 6, color, -1)

            # Draw connections
            line_color = (255, 0, 255) if handedness == "Left" else (0, 255, 255)
            for connection in HAND_CONNECTIONS:
                start = points[connection[0]]
                end   = points[connection[1]]
                cv2.line(frame, start, end, line_color, 3)

            # ── Hand label on screen ──────────────────────────────
            wrist = points[0]
            cv2.putText(frame, handedness, (wrist[0] - 30, wrist[1] + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            # ── Extract coords ────────────────────────────────────
            coords = []
            for lm in hand_landmarks:
                coords += [
                    round(lm.x, 4),
                    round(lm.y, 4),
                    round(lm.z, 4)
                ]

            # ── Assign to correct hand slot ───────────────────────
            if handedness == "Left":
                left_hand = coords
            else:
                right_hand = coords

        # ── Build 126-point input ─────────────────────────────────
        row        = left_hand + right_hand
        input_data = np.array(row).reshape(1, -1)

        # ── Predict ───────────────────────────────────────────────
        pred_encoded = model.predict(input_data)[0]
        confidence   = max(model.predict_proba(input_data)[0])
        prediction   = le.inverse_transform([pred_encoded])[0]

        # ── Display prediction ────────────────────────────────────
        color = (0, 255, 0) if confidence > 0.80 else (0, 165, 255)
        cv2.putText(frame, f"Sign: {prediction}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.0, color, 4)
        cv2.putText(frame, f"Confidence: {confidence*100:.1f}%", (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

        # ── Stability filter ──────────────────────────────────────
        if confidence > 0.80:
            if prediction == last_prediction:
                stable_count += 1
            else:
                stable_count    = 0
                last_prediction = prediction

            if stable_count == stable_threshold:
                word_buffer.append(prediction)
                print(f"Captured: {prediction} | Buffer: {''.join(word_buffer)}")
                stable_count = 0

    else:
        # No hands detected
        cv2.putText(frame, "No Hand Detected", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
        stable_count    = 0
        last_prediction = ""

    # ── Word buffer display ───────────────────────────────────────
    current_word = "".join(word_buffer[-20:])
    cv2.putText(frame, f"Word: {current_word}", (10, 160),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 2)

    # ── Hands detected count ──────────────────────────────────────
    hands_count = len(detection_result.hand_landmarks) if detection_result.hand_landmarks else 0
    cv2.putText(frame, f"Hands: {hands_count}/2", (10, 200),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)

    # ── Stability progress bar ────────────────────────────────────
    bar_width = int((stable_count / stable_threshold) * 300)
    cv2.rectangle(frame, (10, 220), (310, 245), (50, 50, 50), -1)
    cv2.rectangle(frame, (10, 220), (10 + bar_width, 245), (0, 255, 0), -1)
    cv2.putText(frame, "Stability", (10, 240),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # ── Hand legend ───────────────────────────────────────────────
    cv2.putText(frame, "Blue = Left | Red = Right", (10, frame.shape[0] - 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

    # ── Controls ──────────────────────────────────────────────────
    cv2.putText(frame, "SPACE = clear | Q = quit",
                (10, frame.shape[0] - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 180), 2)

    # ── Show frame ────────────────────────────────────────────────
    cv2.imshow("ISL Real-Time Prediction", frame)
    cv2.resizeWindow("ISL Real-Time Prediction", 1280, 720)

    # ── Key controls ──────────────────────────────────────────────
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break

    if key == ord(' '):
        word_buffer = []
        print("Buffer cleared.")

# ── Cleanup ───────────────────────────────────────────────────────
cap.release()
cv2.destroyAllWindows()
detector.close()
print("Session ended.")