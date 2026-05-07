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
DEBUG_STATUS_DIR = ROOT / "debug" / "status"


def now_iso() -> str:
    return datetime.now(TZ).isoformat()


class BuildStatusReporter:
    def __init__(self, phase: str, *, min_interval_seconds: float = 0.5) -> None:
        self.phase = phase
        self.worker = phase
        self.script = f"scripts/{phase}.py"
        self.path = RUNTIME_DIR / f"{phase}.json"
        self.debug_path = DEBUG_STATUS_DIR / f"{phase}.json"
        self.min_interval_seconds = min_interval_seconds
        self.current: int | None = None
        self.total: int | None = None
        self.last_output_file: str | None = None
        self.inputs: list[str] = []
        self.outputs: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.files_needing_review: list[str] = []
        self.pages_generated: int | None = None
        self.extra_counts: dict[str, int | float | str | bool | None] = {}
        self._last_write_at = 0.0

    def _payload(self, status: str) -> dict[str, Any]:
        percent = None
        if self.current is not None and self.total:
            percent = round((self.current / self.total) * 100, 2)
        timestamp = now_iso()
        last_successful_run = timestamp if status == "done" else None
        if last_successful_run is None and self.debug_path.exists():
            try:
                previous = json.loads(self.debug_path.read_text(encoding="utf-8"))
                last_successful_run = previous.get("last_successful_run")
            except (OSError, json.JSONDecodeError):
                last_successful_run = None
        return {
            "phase_name": self.phase,
            "worker": self.worker,
            "script": self.script,
            "status": status,
            "last_run": timestamp,
            "current_count": self.current,
            "total_count": self.total,
            "percent_complete": percent,
            "last_output_file": self.last_output_file,
            "timestamp": timestamp,
            "last_successful_run": last_successful_run,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "counts": self.extra_counts,
            "pages_generated": self.pages_generated,
            "warnings": self.warnings,
            "errors": self.errors,
            "files_needing_review": self.files_needing_review,
        }

    def set_context(
        self,
        *,
        inputs: list[str | Path] | None = None,
        outputs: list[str | Path] | None = None,
    ) -> None:
        if inputs is not None:
            self.inputs = [str(path) for path in inputs]
        if outputs is not None:
            self.outputs = [str(path) for path in outputs]

    def _write_json_atomic(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temp_path.replace(path)

    def _write(self, status: str, *, force: bool = False) -> None:
        now = time.monotonic()
        if not force and (now - self._last_write_at) < self.min_interval_seconds:
            return
        payload = self._payload(status)
        self._write_json_atomic(self.path, payload)
        self._write_json_atomic(self.debug_path, payload)
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
        pages_generated: int | None = None,
        counts: dict[str, int | float | str | bool | None] | None = None,
        warnings: list[str] | None = None,
        errors: list[str] | None = None,
        files_needing_review: list[str | Path] | None = None,
        inputs: list[str | Path] | None = None,
        outputs: list[str | Path] | None = None,
        status: str = "running",
        force: bool = False,
    ) -> None:
        self.set_context(inputs=inputs, outputs=outputs)
        if current is not None:
            self.current = current
        if total is not None:
            self.total = total
        if last_output_file is not None:
            self.last_output_file = str(last_output_file)
        if pages_generated is not None:
            self.pages_generated = pages_generated
        if counts:
            self.extra_counts.update(counts)
        if warnings:
            self.warnings.extend(warnings)
        if errors:
            self.errors.extend(errors)
        if files_needing_review:
            self.files_needing_review.extend(str(path) for path in files_needing_review)
        self._write(status, force=force)

    def done(
        self,
        *,
        current: int | None = None,
        total: int | None = None,
        last_output_file: str | Path | None = None,
        pages_generated: int | None = None,
        counts: dict[str, int | float | str | bool | None] | None = None,
        warnings: list[str] | None = None,
        files_needing_review: list[str | Path] | None = None,
        inputs: list[str | Path] | None = None,
        outputs: list[str | Path] | None = None,
    ) -> None:
        self.update(
            current=current,
            total=total,
            last_output_file=last_output_file,
            pages_generated=pages_generated,
            counts=counts,
            warnings=warnings,
            files_needing_review=files_needing_review,
            inputs=inputs,
            outputs=outputs,
            status="done",
            force=True,
        )

    def error(
        self,
        *,
        current: int | None = None,
        total: int | None = None,
        last_output_file: str | Path | None = None,
        message: str | None = None,
        inputs: list[str | Path] | None = None,
        outputs: list[str | Path] | None = None,
    ) -> None:
        errors = [message] if message else None
        self.update(
            current=current,
            total=total,
            last_output_file=last_output_file,
            errors=errors,
            inputs=inputs,
            outputs=outputs,
            status="error",
            force=True,
        )
