from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES_PATH = ROOT / "data" / "runtime" / "anchor_seat_overrides.json"
TARGETS = [
    ROOT / "docs" / "data" / "schedule_future.json",
    ROOT / "docs" / "data" / "admin_schedule.json",
]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def apply(payload: dict[str, Any], overrides: dict[str, Any]) -> int:
    sessions = payload.get("sessions")
    if not isinstance(sessions, list):
        return 0
    changed = 0
    for session in sessions:
        if not isinstance(session, dict):
            continue
        session_id = str(session.get("session_id") or session.get("id") or "").strip()
        override = overrides.get(session_id)
        if not isinstance(override, dict):
            continue
        count = int(override.get("registered_count", 0))
        if count < 1:
            continue
        session["registered_count"] = count
        session["confirmed_seated"] = True
        session["seat_count_source"] = "anchor_seat_override"
        if override.get("appointment_class_id"):
            session["appointment_class_id"] = str(override["appointment_class_id"])
        changed += 1
    return changed


def run() -> dict[str, int]:
    config = load(OVERRIDES_PATH) if OVERRIDES_PATH.exists() else {"sessions": {}}
    overrides = config.get("sessions", {}) if isinstance(config, dict) else {}
    results: dict[str, int] = {}
    for path in TARGETS:
        if not path.exists():
            results[str(path.relative_to(ROOT))] = 0
            continue
        payload = load(path)
        results[str(path.relative_to(ROOT))] = apply(payload, overrides)
        write(path, payload)
    return results


def main() -> int:
    print(json.dumps(run(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
