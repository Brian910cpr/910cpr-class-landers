import json
from datetime import datetime, UTC
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "raw" / "Class Report.xlsx"
OUTPUT_FILE = ROOT / "data" / "schedule.json"

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

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
        "register_url": str(row["Registration Link"]),
    }
    sessions.append(session)

schedule = {
    "generated": datetime.now(UTC).isoformat(),
    "sessions": sessions,
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(schedule, f, indent=2)

print(f"schedule.json created: {len(sessions)} sessions")
print(f"Wrote: {OUTPUT_FILE}")