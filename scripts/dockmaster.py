from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "lore" / "dockmaster" / "ENTRY_LEDGER.json"


def _safe_comment_text(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text.replace("--", "—").replace("<", "").replace(">", "")


def dockmaster_comment(stable_identity: str, purpose: str = "session_page") -> str:
    """Return a deterministic, valid HTML comment; lore can never break a build."""
    try:
        payload = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        entries = [item for item in payload.get("entries", []) if item.get("purpose") == purpose]
        if not entries:
            return ""
        assigned_id = str(payload.get("assignments", {}).get(stable_identity) or "")
        entry = next((item for item in entries if str(item.get("id")) == assigned_id), None)
        if entry is None:
            digest = hashlib.sha256(f"{purpose}:{stable_identity}".encode("utf-8")).digest()
            entry = entries[int.from_bytes(digest[:4], "big") % len(entries)]
        entry_id = re.sub(r"[^0-9A-Za-z_-]", "", str(entry.get("id") or ""))
        text = _safe_comment_text(entry.get("text"))
        if not entry_id or not text:
            return ""
        return f"<!--\nDockmaster’s Journal\nEntry {entry_id}\n\n{text}\n-->"
    except Exception:
        return ""
