from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "private" / "runtime" / "durable_session_snapshot.json"
URL = "https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/session-workspace/projection"


def main() -> int:
    request = urllib.request.Request(URL, headers={"Accept": "application/json", "User-Agent": "910CPR-Schedule-Integrity/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        source = json.loads(response.read().decode("utf-8"))
    sessions = source.get("sessions") if isinstance(source, dict) else None
    if not isinstance(sessions, list):
        raise RuntimeError("Durable session endpoint did not return a sessions list")
    payload = {
        "available": True,
        "generated_at": datetime.now(ZoneInfo("America/New_York")).isoformat(),
        "source_url": URL,
        "sessions": sessions,
        "error": "",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Fetched {len(sessions)} durable LanderWare sessions -> {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
