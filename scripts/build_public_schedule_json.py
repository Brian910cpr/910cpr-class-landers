import pandas as pd
import json
from datetime import datetime

INPUT_FILE = "data/enrollware_export.xlsx"
OUTPUT_FILE = "docs/public_schedule.json"

df = pd.read_excel(INPUT_FILE)

sessions = []

for _, row in df.iterrows():

    start = pd.to_datetime(row["Date / Time"])

    if start < datetime.now():
        continue

    session_id = row["Class ID"]
    course_id = row["Course ID"]

    session = {
        "session_id": int(session_id),
        "course_id": int(course_id),
        "title": str(row["Course Name"]),
        "start": start.isoformat(),
        "location": str(row["Location"]),
        "seats_available": int(row["Seats Available"]),
        "register_url": f"https://coastalcprtraining.enrollware.com/enroll?id={session_id}",
        "schedule_url": f"https://coastalcprtraining.enrollware.com/schedule#ct{course_id}"
    }

    sessions.append(session)

sessions.sort(key=lambda x: x["start"])

with open(OUTPUT_FILE, "w") as f:
    json.dump(sessions, f, indent=2)

print(f"Wrote {len(sessions)} future sessions")