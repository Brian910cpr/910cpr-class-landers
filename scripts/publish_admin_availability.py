from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "data" / "runtime" / "calendar_snapshots"
CALENDAR_SOURCES = ROOT / "data" / "config" / "calendar_sources.json"
OUTPUT = ROOT / "docs" / "data" / "admin_availability.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    config = read_json(CALENDAR_SOURCES)
    source_cfg = {
        str(item.get("calendar_source_key")): item
        for item in config.get("calendar_sources", [])
        if isinstance(item, dict)
    }

    events: list[dict[str, Any]] = []
    source_status: list[dict[str, Any]] = []
    newest_generated = ""

    for path in sorted(SNAPSHOT_DIR.glob("*.json")):
        payload = read_json(path)
        source_key = str(payload.get("calendar_source_id") or path.stem)
        cfg = source_cfg.get(source_key, {})
        generated_at = str(payload.get("generated_at") or "")
        if generated_at > newest_generated:
            newest_generated = generated_at

        source_status.append({
            "source_key": source_key,
            "display_name": payload.get("source_display_name") or cfg.get("display_name") or source_key,
            "source_type": payload.get("source_type") or cfg.get("calendar_mode") or "unknown",
            "export_status": payload.get("export_status") or "unknown",
            "generated_at": generated_at,
            "event_count": len(payload.get("events") or []),
        })

        for row in payload.get("events") or []:
            start = row.get("start")
            if not start:
                continue
            events.append({
                "source_key": source_key,
                "display_name": payload.get("source_display_name") or cfg.get("display_name") or source_key,
                "source_type": payload.get("source_type") or cfg.get("calendar_mode") or "unknown",
                "instructor_key": cfg.get("instructor_key"),
                "title": row.get("title") or row.get("summary") or "Busy",
                "start": start,
                "end": row.get("end"),
                "location": row.get("location") or "",
                "status": row.get("status") or "",
            })

    events.sort(key=lambda item: (str(item.get("start")), str(item.get("source_key"))))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "schema_version": "1.0",
        "generated_at": newest_generated or datetime.now().astimezone().isoformat(),
        "purpose": "Read-only sanitized calendar visibility for the 910CPR admin dashboard.",
        "sources": source_status,
        "events": events,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Published {len(events)} admin availability events to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
