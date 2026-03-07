import json
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "schedule.json"
OUTPUT_FILE = ROOT / "docs" / "data" / "public_schedule.json"

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)


def is_public_listing_location(location: str) -> bool:
    return str(location or "").strip().startswith("::")


def clean_location_display(location: str) -> str:
    value = str(location or "").strip()
    if value.startswith("::"):
        value = value[2:].strip()
    return value


with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

sessions = data["sessions"]

public_sessions = []

for s in sessions:
    location = str(s.get("location", "")).strip()

    if not is_public_listing_location(location):
        continue

    public_sessions.append(
        {
            "session_id": s.get("session_id"),
            "course": s.get("course"),
            "start": s.get("start"),
            "location": clean_location_display(location),
            "register_url": s.get("register_url"),
        }
    )

public_sessions.sort(key=lambda x: str(x.get("start", "")))

output = {
    "generated": datetime.now(UTC).isoformat(),
    "sessions": public_sessions,
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print(f"Public schedule written: {OUTPUT_FILE}")
print(f"Sessions: {len(public_sessions)}")