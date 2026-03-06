import pandas as pd
import json
from datetime import datetime

INPUT_FILE = "../raw/Class Report.xlsx"
OUTPUT_FILE = "../data/schedule.json"

df = pd.read_excel(INPUT_FILE)

sessions = []

for _, row in df.iterrows():

    session = {
        "session_id": int(row["ID"]),
        "course": str(row["Course"]),
        "start": str(row["Start Date / Time"]),
        "end": str(row["End Date / Time"]),
        "location": str(row["Location"]),
        "instructor": str(row["Instructor"]),
        "students": int(row["Students"]) if not pd.isna(row["Students"]) else 0,
        "seats": int(row["Seats"]) if not pd.isna(row["Seats"]) else 0,
        "register_url": str(row["Registration Link"])
    }

    sessions.append(session)

schedule = {
    "generated": datetime.utcnow().isoformat(),
    "sessions": sessions
}

with open(OUTPUT_FILE, "w") as f:
    json.dump(schedule, f, indent=2)

print("schedule.json created:", len(sessions), "sessions")