from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def _items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("offers", "selected", "rows"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _is_august(item: dict[str, Any]) -> bool:
    date_value = _clean(item.get("date") or item.get("start_date") or item.get("offer_date"))
    start_value = _clean(item.get("start") or item.get("start_datetime") or item.get("start_time_iso"))
    return date_value.startswith("2026-08") or start_value.startswith("2026-08")


def _is_bls(item: dict[str, Any]) -> bool:
    text = " ".join(
        _clean(item.get(key))
        for key in (
            "course_key",
            "course_family",
            "family",
            "course_name",
            "course",
            "title",
            "normalized_course_name",
        )
    ).lower()
    return "bls" in text or _clean(item.get("courseId") or item.get("course_id")) in {"209806", "359474", "210549"}


def _is_selected(item: dict[str, Any]) -> bool:
    source = _clean(item.get("row_source") or item.get("render_source") or item.get("source"))
    status = _clean(item.get("status") or item.get("offer_status"))
    return "selected" in source.lower() or status.lower() == "selected"


def build_summary(preview_path: Path, *, kind: str, repo_root: Path) -> dict[str, Any]:
    payload = json.loads(preview_path.read_text(encoding="utf-8"))
    items = _items(payload)
    august = [item for item in items if _is_august(item)]
    bls = [item for item in items if _is_bls(item)]
    august_bls = [item for item in august if _is_bls(item)]
    selected = [item for item in items if _is_selected(item)]
    reasons = Counter(
        _clean(item.get("rejection_reason") or item.get("hidden_reason") or item.get("reason") or item.get("blocker"))
        for item in items
        if _clean(item.get("rejection_reason") or item.get("hidden_reason") or item.get("reason") or item.get("blocker"))
    )
    try:
        full_preview_path = str(preview_path.relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        full_preview_path = str(preview_path)
    return {
        "kind": kind,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "full_preview_path": full_preview_path,
        "full_preview_size_bytes": preview_path.stat().st_size,
        "total_count": len(items),
        "august_count": len(august),
        "bls_count": len(bls),
        "august_bls_count": len(august_bls),
        "selected_seed_count": len(selected),
        "top_rejection_or_hidden_reasons": [
            {"reason": reason, "count": count}
            for reason, count in reasons.most_common(20)
        ],
    }


def write_summary(preview_path: Path, summary_json_path: Path, summary_md_path: Path, *, kind: str, repo_root: Path) -> dict[str, Any]:
    summary = build_summary(preview_path, kind=kind, repo_root=repo_root)
    summary_json_path.parent.mkdir(parents=True, exist_ok=True)
    summary_json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# {kind.replace('_', ' ').title()} Summary",
        "",
        f"- Full generated preview: `{summary['full_preview_path']}`",
        f"- Full preview size: {summary['full_preview_size_bytes']} bytes",
        f"- Total rows: {summary['total_count']}",
        f"- August rows: {summary['august_count']}",
        f"- BLS rows: {summary['bls_count']}",
        f"- August BLS rows: {summary['august_bls_count']}",
        f"- Selected seed rows detected: {summary['selected_seed_count']}",
        "",
        "## Top Rejection Or Hidden Reasons",
    ]
    if summary["top_rejection_or_hidden_reasons"]:
        lines.extend(f"- {row['reason']}: {row['count']}" for row in summary["top_rejection_or_hidden_reasons"])
    else:
        lines.append("- None recorded in this preview.")
    summary_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary
