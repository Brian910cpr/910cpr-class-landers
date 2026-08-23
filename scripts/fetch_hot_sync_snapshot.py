from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "private" / "runtime" / "hot_sync_snapshot.json"
DEFAULT_URL = "https://schedule.910cpr.com/admin/hot-sync"
TZ = ZoneInfo("America/New_York")


def main() -> int:
    key = str(os.environ.get("HOT_SYNC_ADMIN_KEY") or "").strip()
    url = str(os.environ.get("HOT_SYNC_API_URL") or DEFAULT_URL).strip()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    if not key:
        payload = {
            "available": False,
            "generated_at": datetime.now(TZ).isoformat(),
            "source_url": url,
            "records": [],
            "error": "HOT_SYNC_ADMIN_KEY is not configured in this runtime.",
        }
        OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print("HOT_SYNC snapshot unavailable: HOT_SYNC_ADMIN_KEY is not configured.")
        return 0

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "910CPR-LanderWare-Canonical-Schedule/1.0",
            "X-Hot-Sync-Admin-Key": key,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
        source = json.loads(raw)
        records = source.get("records", []) if isinstance(source, dict) else []
        if not isinstance(records, list):
            raise ValueError("HOT_SYNC response did not contain a records list")
        payload = {
            "available": True,
            "generated_at": datetime.now(TZ).isoformat(),
            "source_url": url,
            "records": records,
            "error": "",
        }
        OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Fetched {len(records)} HOT_SYNC records -> {OUTPUT}")
        return 0
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, ValueError) as exc:
        payload = {
            "available": False,
            "generated_at": datetime.now(TZ).isoformat(),
            "source_url": url,
            "records": [],
            "error": f"{exc.__class__.__name__}: {exc}",
        }
        OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"HOT_SYNC snapshot unavailable: {payload['error']}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
