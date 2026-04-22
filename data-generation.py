# Importing Libraries
import cv2
from mediapipe.tasks import python
import mediapipe as mp
from mediapipe.tasks.python import vision
import os
import csv

# ── Setup MediaPipe for 2 hands ───────────────────────────────────
base_options = python.BaseOptions(model_asset_path='models/hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2  # Changed from 1 to 2
)

detector = vision.HandLandmarker.create_from_options(options)

# ── CSV Setup — 126 points (2 hands × 21 landmarks × 3 coords) ───
output_file = 'data.csv'

header = ["label"]
for hand in ["left", "right"]:
    for i in range(21):
        header += [f"{hand}_x{i}", f"{hand}_y{i}", f"{hand}_z{i}"]

with open(output_file, mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)

print("CSV created with header")
print(f"Total Columns: {len(header)}")  # Should be 127 (1 label + 126 points)

# ── Placeholder for missing hand ──────────────────────────────────
# -1 means hand not present in frame
MISSING_HAND = [-1.0] * 63  # 21 landmarks × 3 coords

# ── Process Dataset ───────────────────────────────────────────────
dataset_path = "Indian"
skipped = 0
processed = 0

with open(output_file, mode='a', newline='') as f:
    writer = csv.writer(f)

    for label in os.listdir(dataset_path):
        label_folder = os.path.join(dataset_path, label)
        if not os.path.isdir(label_folder):
            continue

        for image in os.listdir(label_folder):
            img_path = os.path.join(label_folder, image)

            try:
                mp_image = mp.Image.create_from_file(img_path)
                result = detector.detect(mp_image)

                # ── Initialize both hands as missing ──────────────
                left_hand  = MISSING_HAND.copy()
                right_hand = MISSING_HAND.copy()

                # ── Fill whichever hands are detected ─────────────
                for i, hand_landmarks in enumerate(result.hand_landmarks):
                    # Get handedness label (Left or Right)
                    handedness = result.handedness[i][0].display_name

                    coords = []
                    for landmark in hand_landmarks:
                        coords += [
                            round(landmark.x, 4),
                            round(landmark.y, 4),
                            round(landmark.z, 4)
                        ]

                    if handedness == "Left":
                        left_hand = coords
                    else:
                        right_hand = coords

                # ── Skip if both hands missing ────────────────────
                if left_hand == MISSING_HAND and right_hand == MISSING_HAND:
                    skipped += 1
                    continue

                # ── Write row ─────────────────────────────────────
                row = [label] + left_hand + right_hand
                writer.writerow(row)
                processed += 1

            except Exception as e:
                print(f"Error on {img_path}: {e}")
                skipped += 1

print(f"Done. Processed: {processed} | Skipped: {skipped}")