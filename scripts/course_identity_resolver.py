from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any


def strip_html_tags(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^<]*(?:(?!</style>)<[^<]*)*</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(text)


def normalize_whitespace(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_title(value: Any) -> str:
    text = strip_html_tags(value).lower()
    text = text.replace("®", "").replace("™", "")
    text = re.sub(r"\b(width|height|style|src|img|br|alt|title|longdesc)\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return normalize_whitespace(text)


def stable_course_key(value: Any, fallback: str = "needs_review") -> str:
    text = normalize_title(value).replace(" ", "_")
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:80] or fallback


def load_aliases(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"aliases": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {"aliases": []}
    aliases = payload.get("aliases")
    if not isinstance(aliases, list):
        payload["aliases"] = []
    return payload


def build_alias_indexes(aliases: dict[str, Any]) -> dict[str, dict[str, Any]]:
    exact: dict[str, dict[str, Any]] = {}
    normalized: dict[str, dict[str, Any]] = {}
    by_course_id: dict[str, dict[str, Any]] = {}
    for alias in aliases.get("aliases", []):
        if not isinstance(alias, dict):
            continue
        legacy_name = normalize_whitespace(alias.get("legacy_name"))
        normalized_name = normalize_whitespace(alias.get("normalized_name")) or normalize_title(legacy_name)
        course_id = normalize_whitespace(alias.get("course_id"))
        if legacy_name:
            exact.setdefault(legacy_name, alias)
        if normalized_name:
            normalized.setdefault(normalized_name, alias)
        if course_id:
            by_course_id.setdefault(course_id, alias)
    return {
        "exact": exact,
        "normalized": normalized,
        "by_course_id": by_course_id,
    }


def course_reference_by_id(course_reference: dict[str, Any] | None, course_id: str) -> dict[str, Any] | None:
    if not course_reference or not course_id:
        return None
    by_id = course_reference.get("courses_by_id", {}) if isinstance(course_reference, dict) else {}
    by_number = course_reference.get("courses_by_number", {}) if isinstance(course_reference, dict) else {}
    if isinstance(by_id.get(course_id), dict):
        return by_id[course_id]
    mapped_id = by_number.get(course_id)
    if mapped_id and isinstance(by_id.get(str(mapped_id)), dict):
        return by_id[str(mapped_id)]
    return None


def course_reference_title_aliases(entry: dict[str, Any]) -> list[str]:
    aliases: list[str] = []
    for key in ("official_title", "clean_title", "course_key"):
        value = normalize_whitespace(entry.get(key))
        if value:
            aliases.append(value)
    for value in entry.get("title_aliases", []) or []:
        value = normalize_whitespace(value)
        if value:
            aliases.append(value)
    return aliases


def build_course_reference_title_index(course_reference: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not course_reference:
        return {}
    by_id = course_reference.get("courses_by_id", {}) if isinstance(course_reference, dict) else {}
    index: dict[str, dict[str, Any]] = {}
    for entry in by_id.values():
        if not isinstance(entry, dict):
            continue
        if entry.get("active") is False:
            continue
        for alias in course_reference_title_aliases(entry):
            normalized = normalize_title(alias)
            if normalized:
                index.setdefault(normalized, entry)
    return index


def course_reference_by_title(course_reference: dict[str, Any] | None, raw_course: str) -> dict[str, Any] | None:
    normalized = normalize_title(raw_course)
    if not normalized:
        return None
    return build_course_reference_title_index(course_reference).get(normalized)


def hidden_metadata(raw_course: str) -> dict[str, str]:
    raw = str(raw_course or "")
    found: dict[str, str] = {}
    patterns = {
        "course_key": [
            r"\bcourse[_-]?key\s*[:=]\s*['\"]?([A-Za-z0-9_.:-]+)",
            r"\bck\s*[:=]\s*['\"]?([A-Za-z0-9_.:-]+)",
        ],
        "course_id": [
            r"\blongdesc\s*=\s*['\"][^'\"]*\br:([^|'\"]+)",
            r"\bname\s*=\s*['\"]?(\d+)",
        ],
        "course_code": [
            r"\blongdesc\s*=\s*['\"][^'\"]*\bt:([^|'\"]+)",
        ],
    }
    for key, regexes in patterns.items():
        for regex in regexes:
            match = re.search(regex, raw, flags=re.I)
            if match:
                found[key] = html.unescape(match.group(1)).strip()
                break
    return found


def alias_result(alias: dict[str, Any], method: str, confidence: str, matched_alias: str = "") -> dict[str, Any]:
    return {
        "course_key": normalize_whitespace(alias.get("course_key")) or stable_course_key(alias.get("official_course_name") or alias.get("legacy_name")),
        "official_course_name": normalize_whitespace(alias.get("official_course_name")),
        "match_method": method,
        "match_confidence": confidence,
        "matched_alias": matched_alias or normalize_whitespace(alias.get("legacy_name")),
        "alias_status": normalize_whitespace(alias.get("status")),
        "needs_review": confidence not in {"high", "medium"} or str(alias.get("status") or "").lower() == "needs_review",
    }


def reference_result(entry: dict[str, Any], method: str) -> dict[str, Any]:
    official = normalize_whitespace(entry.get("official_title") or entry.get("clean_title"))
    return {
        "course_key": normalize_whitespace(entry.get("course_key")) or stable_course_key(official or entry.get("course_id")),
        "official_course_name": official,
        "match_method": method,
        "match_confidence": "high",
        "matched_alias": "",
        "certifying_body": normalize_whitespace(entry.get("certifying_body")),
        "family": normalize_whitespace(entry.get("family")),
        "subtype": normalize_whitespace(entry.get("subtype")),
        "delivery_mode": normalize_whitespace(entry.get("delivery_mode")),
        "needs_review": False,
    }


def resolve_course_identity(
    session_or_row: dict[str, Any],
    aliases: dict[str, Any],
    course_reference: dict[str, Any] | None = None,
) -> dict[str, Any]:
    course = session_or_row.get("course") if isinstance(session_or_row.get("course"), dict) else {}
    indexes = build_alias_indexes(aliases)

    course_id = normalize_whitespace(
        session_or_row.get("course_id")
        or course.get("course_id")
        or session_or_row.get("course_number")
        or course.get("course_number")
    )
    raw_course = normalize_whitespace(
        session_or_row.get("raw_course_name")
        or session_or_row.get("course_name_raw")
        or session_or_row.get("course_name")
        or course.get("course_name_raw")
        or course.get("course_name_primary_raw")
        or course.get("course_name_primary_clean")
    )
    normalized = normalize_title(raw_course)

    if course_id:
        referenced = course_reference_by_id(course_reference, course_id)
        if referenced:
            return reference_result(referenced, "course_id")
        alias = indexes["by_course_id"].get(course_id)
        if alias:
            return alias_result(alias, "course_id", "high")

    metadata = hidden_metadata(raw_course)
    metadata_key = metadata.get("course_key")
    if metadata_key:
        for alias in aliases.get("aliases", []):
            if isinstance(alias, dict) and normalize_whitespace(alias.get("course_key")) == metadata_key:
                return alias_result(alias, "metadata", "high")
        return {
            "course_key": metadata_key,
            "official_course_name": "",
            "match_method": "metadata",
            "match_confidence": "medium",
            "matched_alias": "",
            "needs_review": True,
        }

    metadata_course_id = metadata.get("course_id")
    if metadata_course_id:
        referenced = course_reference_by_id(course_reference, metadata_course_id)
        if referenced:
            return reference_result(referenced, "metadata")
        alias = indexes["by_course_id"].get(metadata_course_id)
        if alias:
            return alias_result(alias, "metadata", "high")

    alias = indexes["exact"].get(raw_course)
    if alias:
        return alias_result(alias, "legacy_alias", "high", raw_course)

    alias = indexes["normalized"].get(normalized)
    if alias:
        return alias_result(alias, "normalized_title", "medium", normalize_whitespace(alias.get("legacy_name")))

    referenced = course_reference_by_title(course_reference, raw_course)
    if referenced:
        return reference_result(referenced, "course_title")

    return {
        "course_key": "",
        "official_course_name": "",
        "match_method": "unmatched",
        "match_confidence": "none",
        "matched_alias": "",
        "needs_review": True,
    }
