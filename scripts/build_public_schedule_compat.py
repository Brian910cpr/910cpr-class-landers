import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "schedule.json"
OUTPUT = ROOT / "docs" / "data" / "public_schedule.json"

def parse_dt(value):
    if not value:
        return None
    text = str(value).strip()
    for candidate in (
        text,
        text.replace("Z", "+00:00"),
        text[:19],
        text[:16],
        text[:10],
    ):
        try:
            return datetime.fromisoformat(candidate)
        except Exception:
            pass
    return None

def pick(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] not in (None, ""):
            return d[k]
    return default

def main():
    if not INPUT.exists():
        raise SystemExit(f"Missing input: {INPUT}")

    raw = json.loads(INPUT.read_text(encoding="utf-8"))

    if isinstance(raw, dict):
        sessions = raw.get("sessions") or raw.get("shifts") or raw.get("data") or []
    elif isinstance(raw, list):
        sessions = raw
    else:
        sessions = []

    now = datetime.now()
    public_sessions = []

    for s in sessions:
        if not isinstance(s, dict):
            continue

        start_raw = pick(
            s,
            "start",
            "start_time",
            "startTime",
            "datetime",
            "date_time",
            "session_start",
            "session_datetime",
            "date",
            default=""
        )
        dt = parse_dt(start_raw)
        if not dt:
            continue
        if dt < now:
            continue

        is_public = pick(
            s,
            "public",
            "is_public",
            "isPublic",
            "published",
            "is_published",
            default=True
        )

        if isinstance(is_public, str):
            is_public = is_public.strip().lower() in {"1", "true", "yes", "y", "public", "published"}

        if not bool(is_public):
            continue

        session_id = pick(s, "id", "session_id", "class_id", "classSchedId", "sched_id", default="")
        course_name = pick(s, "course_name", "course", "title", "name", default="")
        location = pick(s, "location", "venue", "address", default="")
        price = pick(s, "price", "cost", default="")
        register_url = pick(s, "register_url", "registerUrl", "url", "enroll_url", default="")

        public_sessions.append({
            "id": session_id,
            "title": course_name,
            "course": course_name,
            "start": dt.isoformat(),
            "location": location,
            "price": price,
            "register_url": register_url,
            "public": True
        })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(public_sessions, indent=2), encoding="utf-8")

    print(f"Total sessions in schedule.json: {len(sessions)}")
    print(f"Public sessions to build: {len(public_sessions)}")
    print(f"Wrote: {OUTPUT}")

if __name__ == "__main__":
    main()