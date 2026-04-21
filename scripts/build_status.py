from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


TZ = ZoneInfo("America/New_York")
ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / "data" / "runtime"


def now_iso() -> str:
    return datetime.now(TZ).isoformat()


class BuildStatusReporter:
    def __init__(self, phase: str, *, min_interval_seconds: float = 0.5) -> None:
        self.phase = phase
        self.path = RUNTIME_DIR / f"{phase}.json"
        self.min_interval_seconds = min_interval_seconds
        self.current: int | None = None
        self.total: int | None = None
        self.last_output_file: str | None = None
        self._last_write_at = 0.0

    def _payload(self, status: str) -> dict[str, Any]:
        percent = None
        if self.current is not None and self.total:
            percent = round((self.current / self.total) * 100, 2)
        return {
            "phase_name": self.phase,
            "status": status,
            "current_count": self.current,
            "total_count": self.total,
            "percent_complete": percent,
            "last_output_file": self.last_output_file,
            "timestamp": now_iso(),
        }

    def _write(self, status: str, *, force: bool = False) -> None:
        now = time.monotonic()
        if not force and (now - self._last_write_at) < self.min_interval_seconds:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._payload(status)
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        temp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temp_path.replace(self.path)
        self._last_write_at = now

    def waiting(self, *, total: int | None = None) -> None:
        self.current = 0
        self.total = total
        self._write("waiting", force=True)

    def start(self, *, total: int | None = None) -> None:
        self.current = 0
        self.total = total
        self._write("running", force=True)

    def update(
        self,
        *,
        current: int | None = None,
        total: int | None = None,
        last_output_file: str | Path | None = None,
        status: str = "running",
        force: bool = False,
    ) -> None:
        if current is not None:
            self.current = current
        if total is not None:
            self.total = total
        if last_output_file is not None:
            self.last_output_file = str(last_output_file)
        self._write(status, force=force)

    def done(self, *, current: int | None = None, total: int | None = None, last_output_file: str | Path | None = None) -> None:
        self.update(current=current, total=total, last_output_file=last_output_file, status="done", force=True)

    def error(self, *, current: int | None = None, total: int | None = None, last_output_file: str | Path | None = None) -> None:
        self.update(current=current, total=total, last_output_file=last_output_file, status="error", force=True)
