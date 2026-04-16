from pathlib import Path
from urllib.request import urlopen

import cv2
import mediapipe as mp


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)
MODEL_PATH = Path(__file__).resolve().parent / "models" / "hand_landmarker.task"


def ensure_model() -> Path:
    if MODEL_PATH.exists():
        return MODEL_PATH

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    print("Downloading hand landmark model...")
    with urlopen(MODEL_URL) as response, MODEL_PATH.open("wb") as model_file:
        model_file.write(response.read())
    print(f"Model saved to {MODEL_PATH}")
    return MODEL_PATH


def main() -> None:
    model_path = ensure_model()

    base_options = mp.tasks.BaseOptions(model_asset_path=str(model_path))
    options = mp.tasks.vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    drawing_utils = mp.tasks.vision.drawing_utils
    drawing_styles = mp.tasks.vision.drawing_styles
    hand_connections = mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS
    landmark_style = drawing_styles.get_default_hand_landmarks_style()
    connection_style = drawing_styles.get_default_hand_connections_style()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam (camera index 0).")

    timestamp_ms = 0
    with mp.tasks.vision.HandLandmarker.create_from_options(options) as hand_tracker:
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            results = hand_tracker.detect_for_video(mp_image, timestamp_ms)
            timestamp_ms += 33

            if results.hand_landmarks:
                h, w, _ = frame.shape
                for hand_landmarks in results.hand_landmarks:
                    drawing_utils.draw_landmarks(
                        frame,
                        hand_landmarks,
                        hand_connections,
                        landmark_drawing_spec=landmark_style,
                        connection_drawing_spec=connection_style,
                    )

                    for idx, landmark in enumerate(hand_landmarks):
                        cx, cy = int(landmark.x * w), int(landmark.y * h)
                        print(f"Point {idx}: ({cx}, {cy})")

            cv2.imshow("Hand Tracking", frame)
            if cv2.waitKey(30) & 0xFF == ord("p"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
