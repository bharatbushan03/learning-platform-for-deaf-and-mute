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
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7,
    running_mode=vision.RunningMode.VIDEO
)
detector = vision.HandLandmarker.create_from_options(options)

# ── Webcam ────────────────────────────────────────────────────────
cap = cv2.VideoCapture(0)

# ── State ─────────────────────────────────────────────────────────
word_buffer    = []
last_prediction = ""
stable_count   = 0
stable_threshold = 15  # frames sign must be stable before capturing

print("ISL Real-Time Prediction Started")
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

    # MediaPipe expects timestamp in milliseconds
    timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )

    detection_result = detector.detect_for_video(mp_image, timestamp_ms)

    prediction  = ""
    confidence  = 0.0

    if detection_result.hand_landmarks:
        for hand_landmarks in detection_result.hand_landmarks:

            # ── Draw landmarks using MediaPipe drawing utils ───────
            h, w, _ = frame.shape
            points = []
            for lm in hand_landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                points.append((cx, cy))
                cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)

            # Draw connections using new tasks API
            HAND_CONNECTIONS = [
                (0, 1), (1, 2), (2, 3), (3, 4),
                (0, 5), (5, 6), (6, 7), (7, 8),
                (0, 9), (9, 10), (10, 11), (11, 12),
                (0, 13), (13, 14), (14, 15), (15, 16),
                (0, 17), (17, 18), (18, 19), (19, 20),
                (5, 9), (9, 13), (13, 17)
            ]
            for connection in HAND_CONNECTIONS:
                start = points[connection[0]]
                end   = points[connection[1]]
                cv2.line(frame, start, end, (0, 200, 200), 2)

            # ── Extract 63 numbers ────────────────────────────────
            row = []
            for lm in hand_landmarks:
                row.extend([lm.x, lm.y, lm.z])

            # ── Predict ───────────────────────────────────────────
            input_data  = np.array(row).reshape(1, -1)
            pred_encoded = model.predict(input_data)[0]
            confidence  = max(model.predict_proba(input_data)[0])
            prediction  = le.inverse_transform([pred_encoded])[0]

            # ── Display prediction ────────────────────────────────
            if confidence > 0.80:
                cv2.putText(frame, f"Sign: {prediction}", (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                            (0, 255, 0), 3)
                cv2.putText(frame, f"Confidence: {confidence*100:.1f}%",
                            (10, 95),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                            (0, 255, 255), 2)

                # ── Stability filter ──────────────────────────────
                if prediction == last_prediction:
                    stable_count += 1
                else:
                    stable_count   = 0
                    last_prediction = prediction

                # ── Capture after stable threshold ────────────────
                if stable_count == stable_threshold:
                    word_buffer.append(prediction)
                    print(f"Captured: {prediction} | Buffer: {''.join(word_buffer)}")
                    stable_count = 0

            else:
                # Low confidence — show warning
                cv2.putText(frame, f"Low confidence: {confidence*100:.1f}%",
                            (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                            (0, 165, 255), 2)

    else:
        # No hand detected
        cv2.putText(frame, "No Hand Detected", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 0, 255), 2)
        stable_count    = 0
        last_prediction = ""

    # ── Word buffer display ───────────────────────────────────────
    current_word = "".join(word_buffer[-20:])
    cv2.putText(frame, f"Word: {current_word}", (10, 140),
                cv2.FONT_HERSHEY_SIMPLEX, 1,
                (255, 255, 0), 2)

    # ── Stable progress bar ───────────────────────────────────────
    bar_width = int((stable_count / stable_threshold) * 200)
    cv2.rectangle(frame, (10, 160), (210, 180), (50, 50, 50), -1)
    cv2.rectangle(frame, (10, 160), (10 + bar_width, 180), (0, 255, 0), -1)
    cv2.putText(frame, "Stability", (10, 175),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                (255, 255, 255), 1)

    # ── Controls ──────────────────────────────────────────────────
    cv2.putText(frame, "SPACE=clear | Q=quit",
                (10, frame.shape[0] - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (180, 180, 180), 1)

    # ── Show frame ────────────────────────────────────────────────
    cv2.imshow("ISL Real-Time Prediction", frame)

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