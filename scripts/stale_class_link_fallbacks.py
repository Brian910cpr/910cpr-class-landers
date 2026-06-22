from __future__ import annotations

import re
from html import unescape
from pathlib import Path
from typing import Any


def strip_html(value: Any) -> str:
    value = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", unescape(value)).strip()


def infer_current_public_destination(context: Any) -> str:
    text = strip_html(context).lower()
    if not text:
        return "/classes/"
    if any(term in text for term in ("uscg", "maritime", "coast guard", "elementary first aid")):
        return "/uscg-elementary-first-aid-cpr.html"
    if any(term in text for term in ("red cross", "arc ")):
        return "/arc.html"
    if any(term in text for term in ("hsi", "ashi")):
        return "/hsi.html"
    if "acls" in text:
        return "/acls.html"
    if "pals" in text:
        return "/pals.html"
    if "bls" in text or "basic life support" in text:
        return "/bls.html"
    if any(term in text for term in ("heartsaver", "cpr aed", "cpr/aed", "first aid cpr", "pediatric")):
        return "/heartsaver.html"
    if any(term in text for term in ("group", "onsite", "on-site", "workplace", "company training")):
        return "/group-training.html"
    return "/classes/"


def safe_class_detail_href(session_id: Any, docs_dir: Path, *context_parts: Any) -> str:
    sid = strip_html(session_id)
    context = " ".join(strip_html(part) for part in context_parts if strip_html(part))
    if sid:
        class_path = docs_dir / "classes" / f"{sid}.html"
        if class_path.exists():
            return f"/classes/{sid}.html"
    return infer_current_public_destination(context)
