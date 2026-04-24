from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import gradio as gr
import mediapipe as mp
import numpy as np
import pickle
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


ROOT_DIR = Path(__file__).resolve().parent
MODELS_DIR = ROOT_DIR / "models"
MODEL_FILE = MODELS_DIR / "isl-model.pkl"
ENCODER_FILE = MODELS_DIR / "label-encoder.pkl"
LANDMARKER_FILE = MODELS_DIR / "hand_landmarker.task"

MISSING_HAND = [-1.0] * 63
# Frames a sign must remain stable before adding it to the word buffer.
STABLE_THRESHOLD = 15
# Minimum classifier confidence to consider a prediction valid.
CONFIDENCE_THRESHOLD = 0.80
# Keep buffered output short to avoid overflowing the UI.
MAX_DISPLAY_WORDS = 20
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17),
]


with MODEL_FILE.open("rb") as model_file:
    model = pickle.load(model_file)

with ENCODER_FILE.open("rb") as encoder_file:
    label_encoder = pickle.load(encoder_file)

base_options = python.BaseOptions(model_asset_path=str(LANDMARKER_FILE))
detector_options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7,
    running_mode=vision.RunningMode.IMAGE,
)
detector = vision.HandLandmarker.create_from_options(detector_options)


def _default_state() -> dict[str, Any]:
    return {"word_buffer": [], "last_prediction": "", "stable_count": 0}


def _draw_hand(frame: np.ndarray, hand_landmarks: list[Any], handedness: str) -> None:
    h, w, _ = frame.shape
    points: list[tuple[int, int]] = []
    point_color = (255, 0, 0) if handedness == "Left" else (0, 0, 255)
    line_color = (255, 0, 255) if handedness == "Left" else (0, 255, 255)

    for lm in hand_landmarks:
        cx, cy = int(lm.x * w), int(lm.y * h)
        points.append((cx, cy))
        cv2.circle(frame, (cx, cy), 4, point_color, -1)

    for start_idx, end_idx in HAND_CONNECTIONS:
        cv2.line(frame, points[start_idx], points[end_idx], line_color, 2)

    wrist = points[0]
    cv2.putText(
        frame,
        handedness,
        (wrist[0] - 20, wrist[1] + 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        point_color,
        2,
    )


def predict_sign(frame: np.ndarray | None, state: dict[str, Any]) -> tuple[np.ndarray | None, str, str, str, int, dict[str, Any]]:
    if frame is None:
        return None, "No input", "0.0%", "", 0, state

    if state is None:
        state = _default_state()

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    detection_result = detector.detect(mp_image)

    prediction = "No sign"
    confidence = 0.0
    left_hand = MISSING_HAND.copy()
    right_hand = MISSING_HAND.copy()

    if detection_result.hand_landmarks:
        for index, hand_landmarks in enumerate(detection_result.hand_landmarks):
            handedness = detection_result.handedness[index][0].display_name
            _draw_hand(frame, hand_landmarks, handedness)

            coords: list[float] = []
            for lm in hand_landmarks:
                coords.extend([round(lm.x, 4), round(lm.y, 4), round(lm.z, 4)])

            if handedness == "Left":
                left_hand = coords
            else:
                right_hand = coords

        features = np.array(left_hand + right_hand).reshape(1, -1)
        predicted_encoded = model.predict(features)[0]
        confidence = float(max(model.predict_proba(features)[0]))
        prediction = str(label_encoder.inverse_transform([predicted_encoded])[0])

        if confidence > CONFIDENCE_THRESHOLD:
            if prediction == state["last_prediction"]:
                state["stable_count"] += 1
            else:
                state["stable_count"] = 0
                state["last_prediction"] = prediction

            if state["stable_count"] >= STABLE_THRESHOLD:
                state["word_buffer"].append(prediction)
                state["stable_count"] = 0
        else:
            state["stable_count"] = 0
    else:
        state["stable_count"] = 0
        state["last_prediction"] = ""

    word_text = "".join(state["word_buffer"][-MAX_DISPLAY_WORDS:])
    hands_count = len(detection_result.hand_landmarks) if detection_result.hand_landmarks else 0

    cv2.putText(frame, f"Sign: {prediction}", (12, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    cv2.putText(frame, f"Confidence: {confidence * 100:.1f}%", (12, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.putText(frame, f"Word: {word_text}", (12, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    return frame, prediction, f"{confidence * 100:.1f}%", word_text, hands_count, state


def clear_buffer(state: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    state = _default_state() if state is None else state
    state["word_buffer"] = []
    state["last_prediction"] = ""
    state["stable_count"] = 0
    return "", state


with gr.Blocks(title="ISL Learning Platform UI") as app:
    gr.Markdown(
        """
        # ISL Learning Platform UI
        Upload an image or use your webcam to detect ISL signs using the trained model.
        """
    )

    state = gr.State(_default_state())

    with gr.Row():
        image_input = gr.Image(
            label="Input (Image/Webcam)",
            sources=["upload", "webcam"],
            type="numpy",
        )
        image_output = gr.Image(label="Annotated Output", type="numpy")

    with gr.Row():
        prediction_output = gr.Textbox(label="Predicted Sign", interactive=False)
        confidence_output = gr.Textbox(label="Confidence", interactive=False)
        hands_output = gr.Number(label="Hands Detected", interactive=False)

    word_output = gr.Textbox(label="Buffered Word", interactive=False)

    with gr.Row():
        detect_button = gr.Button("Detect Sign", variant="primary")
        clear_button = gr.Button("Clear Buffer")

    detect_button.click(
        fn=predict_sign,
        inputs=[image_input, state],
        outputs=[image_output, prediction_output, confidence_output, word_output, hands_output, state],
    )

    clear_button.click(
        fn=clear_buffer,
        inputs=[state],
        outputs=[word_output, state],
    )


if __name__ == "__main__":
    app.launch()
