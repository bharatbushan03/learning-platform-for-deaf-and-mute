import cv2
import mediapipe as mp
import numpy as np
import pickle
import base64
import json
import os
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import UploadFile, File, HTTPException
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ── App Setup ─────────────────────────────────────────────────────
app = FastAPI(title="ISL Recognition API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Load Model & Encoder ──────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = Path(BASE_DIR).parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_DIST = FRONTEND_DIR / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"

with open(os.path.join(BASE_DIR, "models/isl-model.pkl"), "rb") as f:
    model = pickle.load(f)

with open(os.path.join(BASE_DIR, "models/label-encoder.pkl"), "rb") as f:
    le = pickle.load(f)

# ── MediaPipe Setup ───────────────────────────────────────────────
base_options = python.BaseOptions(
    model_asset_path=os.path.join(BASE_DIR, "models/hand_landmarker.task")
)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7,
    running_mode=vision.RunningMode.IMAGE
)
detector = vision.HandLandmarker.create_from_options(options)

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# ── Missing hand placeholder ──────────────────────────────────────
MISSING_HAND = [-1.0] * 63

# ── Hand connections for drawing ──────────────────────────────────
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
    (5,9),(9,13),(13,17)
]

# ── Helper: Process Frame ─────────────────────────────────────────
def process_frame(frame_bytes: bytes):
    # Decode base64 image from frontend
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        return None, None, None, []

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )

    result = detector.detect(mp_image)

    # Initialize both hands as missing
    left_hand  = MISSING_HAND.copy()
    right_hand = MISSING_HAND.copy()
    landmarks_for_drawing = []
    hand_detected = False

    if result.hand_landmarks:
        h, w, _ = frame.shape

        for i, hand_landmarks in enumerate(result.hand_landmarks):
            handedness = result.handedness[i][0].display_name

            # Extract points for drawing
            points = []
            for lm in hand_landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                points.append({"x": cx, "y": cy, "hand": handedness})

            landmarks_for_drawing.append({
                "handedness": handedness,
                "points": points
            })

            # Extract coords
            coords = []
            for lm in hand_landmarks:
                coords += [round(lm.x, 4), round(lm.y, 4), round(lm.z, 4)]

            # Swapped to fix mirror issue
            if handedness == "Left":
                right_hand = coords
            else:
                left_hand = coords

            hand_detected = True

    prediction = None
    confidence = 0.0

    if hand_detected:
        row = left_hand + right_hand
        input_data = np.array(row).reshape(1, -1)
        pred_encoded = model.predict(input_data)[0]
        confidence   = float(max(model.predict_proba(input_data)[0]))
        prediction   = le.inverse_transform([pred_encoded])[0]

    return prediction, confidence, hand_detected, landmarks_for_drawing


# ── REST Endpoint — Health Check ──────────────────────────────────
@app.get("/")
def root():
    if FRONTEND_INDEX.exists():
        return FileResponse(FRONTEND_INDEX)
    return {
        "status": "ISL API Running",
        "frontend": "Build the Vite app in frontend/ and serve frontend/dist/index.html",
    }


@app.get("/health")
def health_check():
    return {"status": "ISL API Running"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    # Read image bytes
    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="Empty upload")
    
    # Process frame
    prediction, confidence, hand_detected, landmarks = process_frame(contents)
    
    if not hand_detected:
        return {
            "prediction": None,
            "confidence": 0.0,
            "hand_detected": False,
            "landmarks": []
        }
    
    return {
        "prediction": prediction,
        "confidence": round(confidence * 100, 1),
        "hand_detected": hand_detected,
        "landmarks": landmarks
    }

# ── WebSocket Endpoint — Real-Time Prediction ─────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    try:
        while True:
            # Receive frame from frontend as base64 string
            data = await websocket.receive_text()
            payload = json.loads(data)

            # Decode base64 image
            img_data = base64.b64decode(payload["frame"])

            # Process frame
            prediction, confidence, hand_detected, landmarks = process_frame(img_data)

            # Send response back to frontend
            response = {
                "prediction":   prediction,
                "confidence":   round(confidence * 100, 1),
                "hand_detected": hand_detected,
                "landmarks":    landmarks
            }

            await websocket.send_text(json.dumps(response))

    except WebSocketDisconnect:
        print("Client disconnected")

    except Exception as e:
        print(f"Error: {e}")
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except:
            pass
        finally:
            await websocket.close()
