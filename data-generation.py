import cv2
import mediapipe as mp
import csv
import os

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=True,  # True for images, not video
    max_num_hands=1,
    min_detection_confidence=0.5  # Lower threshold for black background
)

dataset_path = "path/to/kaggle/dataset"  # folder with A, B, C... subfolders
output_csv = "kaggle_landmarks.csv"

with open(output_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    header = ['label'] + [f'{axis}{i}' for i in range(21) for axis in ['x','y','z']]
    writer.writerow(header)

    for sign_folder in os.listdir(dataset_path):
        sign_path = os.path.join(dataset_path, sign_folder)
        if not os.path.isdir(sign_path):
            continue

        success = 0
        fail = 0

        for img_file in os.listdir(sign_path):
            img_path = os.path.join(sign_path, img_file)
            image = cv2.imread(img_path)
            if image is None:
                continue

            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            if result.multi_hand_landmarks:
                row = [sign_folder]
                for lm in result.multi_hand_landmarks[0].landmark:
                    row.extend([lm.x, lm.y, lm.z])
                writer.writerow(row)
                success += 1
            else:
                fail += 1  # MediaPipe couldn't detect hand

        print(f"{sign_folder}: {success} success, {fail} failed")

print(f"Done. Saved to {output_csv}")
