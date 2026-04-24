import pandas as pd
import os

kaggle = pd.read_csv("data.csv")
webcam = pd.read_csv("data2.csv")

merged = pd.concat([kaggle, webcam], ignore_index=True)
merged = merged.sample(frac=1, random_state=42)  # shuffle
merged.to_csv("data_final.csv", index=False)

print(merged['label'].value_counts())
print(f"Total samples: {len(merged)}")

os.remove("data2.csv")
print("Temporary webcam data removed")
print("Haa ve Raju. Bund mra aaya.")
print("14 da ki hal ha")