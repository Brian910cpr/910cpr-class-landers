import json
import os
from datetime import datetime

DATA_FILE = "../data/schedule.json"
OUTPUT_FILE = "../docs/data/public_schedule.json"

PUBLIC_LOCATION = "Wilmington; Shipyard Blvd"
PUBLIC_SEATS_SENTINEL = 555

os.makedirs("../docs/data", exist_ok=True)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

sessions = data["sessions"]


def is_public(session):
    location = str(session.get("location", "")).strip()

    seats = session.get("seats")
    try:
        seats = int(seats)
    except:
        seats = None

    if location == PUBLIC_LOCATION:
        return True

    if seats == PUBLIC_SEATS_SENTINEL and location != PUBLIC_LOCATION:
        return True

    return False


def parse_dt(value):
    raw = str(value)

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %I:%M %p",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except:
            pass

    return None


public_sessions = []

for s in sessions:

    if not is_public(s):
        continue

    dt = parse_dt(s.get("start"))

    if dt is None:
        continue

    public_sessions.append(
        {
            "session_id": s.get("session_id"),
            "course": s.get("course"),
            "start": s.get("start"),
            "location": s.get("location"),
            "register_url": s.get("register_url"),
        }
    )

public_sessions.sort(key=lambda x: x["start"])

output = {
    "generated": datetime.utcnow().isoformat(),
    "sessions": public_sessions,
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("Public schedule written:", OUTPUT_FILE)
print("Sessions:", len(public_sessions))