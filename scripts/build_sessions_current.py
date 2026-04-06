
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

def build_sessions_current(schedule_json: Path, output_json: Path) -> None:
    payload = json.loads(schedule_json.read_text(encoding="utf-8"))
    today = datetime.now().date()

    sessions = []
    for s in payload.get("sessions", []):
        try:
            s_date = datetime.fromisoformat(s.get("date")).date()
        except Exception:
            continue
        if s_date >= today:
            sessions.append(s)

    out = {
        "build": {
            "source_schedule": str(schedule_json),
            "session_count": len(sessions),
        },
        "sessions": sessions,
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {output_json}")
    print(json.dumps(out["build"], indent=2))

def main() -> int:
    parser = argparse.ArgumentParser(description="Filter schedule.json into future-facing sessions_current.json")
    parser.add_argument("--schedule-json", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    build_sessions_current(Path(args.schedule_json), Path(args.output))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
