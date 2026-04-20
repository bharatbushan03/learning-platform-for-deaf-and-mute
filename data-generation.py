# Importing Libraries
import cv2
from mediapipe.tasks import python
import mediapipe as mp
from mediapipe.tasks.python import vision
import os
import csv

# Load a single image & Detect hand landmarks
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options = base_options,
    num_hands = 1
)

detector = vision.HandLandmarker.create_from_options(options)

image_path = r'Indian/1/0.jpg'

mp_image = mp.Image.create_from_file(image_path)
result = detector.detect(mp_image)

print("Hands detected: ", len(result.hand_landmarks))

landmarks = result.hand_landmarks[0]

for i, landmark in enumerate(landmarks):
    print(f"Landmark {i}: x={landmark.x:.4f}, y={landmark.y:.4f}, z={landmark.z:.4f}")

output_file = 'data.csv'

header = ["label"]
for i in range(21):
    header += [f"x{i}", f"y{i}", f"z{i}"]

with open(output_file, mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)

print("CSV created with header")
print(header)
print("Total Columns: ", len(header))

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

                if len(result.hand_landmarks) == 0:
                    skipped += 1
                    continue
                landmarks = result.hand_landmarks[0]
                row = [label]
                for landmark in landmarks:
                    row += [round(landmark.x, 4), round(landmark.y, 4), round(landmark.z, 4)]
                writer.writerow(row)
                processed += 1

            except Exception as e:
                print(f"Error on {img_path}: {e}")
                skipped += 1


print(f"Done. Processed {processed} and skipped {skipped}")
