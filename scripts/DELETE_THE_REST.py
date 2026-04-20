import os
import pandas as pd

# Paths
classes_dir = r"E:\GitHub\910cpr-class-landers\docs\classes"
excel_path = r"E:\GitHub\910cpr-class-landers\Class Report (37).xlsx"

# Load Excel
df = pd.read_excel(excel_path)

# Extract valid IDs
valid_ids = set()

for link in df['Registration Link'].dropna():
    if 'id=' in link:
        valid_ids.add(link.split('id=')[-1].strip())

print(f"Valid IDs: {len(valid_ids)}")

# Scan files
deleted = 0
kept = 0

for file in os.listdir(classes_dir):
    if not file.endswith(".html"):
        continue

    name = file.replace(".html", "")

    if name not in valid_ids:
        os.remove(os.path.join(classes_dir, file))
        deleted += 1
    else:
        kept += 1

print(f"Deleted: {deleted}")
print(f"Kept: {kept}")