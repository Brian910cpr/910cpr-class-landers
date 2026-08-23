from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "docs" / "data" / "admin_schedule.json"
OUTPUT = ROOT / "docs" / "data" / "landerware.ics"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ical_escape(value: Any) -> str:
    text = str(value or "")
    text = text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    text = re.sub(r"\r?\n", r"\\n", text)
    return text


def parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed.astimezone(timezone.utc)


def fmt_dt(value: Any) -> str | None:
    parsed = parse_dt(value)
    return parsed.strftime("%Y%m%dT%H%M%SZ") if parsed else None


def event_uid(row: dict[str, Any]) -> str:
    source = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(row.get("source") or "landerware"))
    raw = re.sub(r"[^A-Za-z0-9_.:-]+", "-", str(row.get("session_id") or ""))
    if raw:
        return f"{source}-{raw}@landerware.910cpr.com"
    start = re.sub(r"[^0-9]+", "", str(row.get("start_at") or ""))
    course = re.sub(r"[^A-Za-z0-9]+", "-", str(row.get("course_name") or "class").lower()).strip("-")
    return f"{source}-{start}-{course}@landerware.910cpr.com"


def build_ical(payload: Any) -> str:
    rows = payload.get("sessions", []) if isinstance(payload, dict) else []
    generated = fmt_dt(payload.get("generated_at")) or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//910CPR//LanderWare Canonical Schedule//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:LanderWare 910CPR",
        "X-WR-TIMEZONE:America/New_York",
    ]
    for row in rows:
        if not isinstance(row, dict):
            continue
        start = fmt_dt(row.get("start_at"))
        end = fmt_dt(row.get("end_at"))
        if not start:
            continue
        course = str(row.get("course_name") or "910CPR Class").strip() or "910CPR Class"
        source = str(row.get("source") or "landerware").strip()
        description_bits = [f"Source: {source}"]
        if row.get("hot_sync"):
            description_bits.append("Entered directly in LanderWare/HOT_SYNC")
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{ical_escape(event_uid(row))}",
            f"DTSTAMP:{generated}",
            f"DTSTART:{start}",
        ])
        if end:
            lines.append(f"DTEND:{end}")
        lines.append(f"SUMMARY:{ical_escape(course)}")
        if row.get("location_name"):
            lines.append(f"LOCATION:{ical_escape(row.get('location_name'))}")
        lines.append(f"DESCRIPTION:{ical_escape(' | '.join(description_bits))}")
        if row.get("registration_url"):
            lines.append(f"URL:{ical_escape(row.get('registration_url'))}")
        lines.append("STATUS:CONFIRMED")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def main() -> int:
    payload = read_json(INPUT)
    text = build_ical(payload)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(text, encoding="utf-8", newline="")
    count = text.count("BEGIN:VEVENT")
    print(f"Published {count} LanderWare calendar events to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
