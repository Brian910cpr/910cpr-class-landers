from __future__ import annotations

from typing import Any


PUBLIC_CLASS_LOCATION_PREFIX = "::"


def clean_location_name(value: Any) -> str:
    return str(value or "").strip()


def is_public_class_location(location_name: Any) -> bool:
    """Return true only for canonical public class locations.

    Public publication eligibility is intentionally strict:
    trim leading/trailing whitespace, then require the exact case-sensitive
    Enrollware/public-location prefix "::".
    """
    return clean_location_name(location_name).startswith(PUBLIC_CLASS_LOCATION_PREFIX)


def session_location_candidates(session: dict[str, Any]) -> list[str]:
    location = session.get("location")
    values: list[Any] = [
        session.get("raw_location"),
        session.get("location_raw"),
        session.get("location_display"),
        session.get("location_name"),
    ]
    if isinstance(location, dict):
        values.extend(
            [
                location.get("raw_location"),
                location.get("location_raw"),
                location.get("location_display"),
                location.get("location_name"),
                location.get("name"),
            ]
        )
    else:
        values.append(location)
    return [clean_location_name(value) for value in values if clean_location_name(value)]


def session_has_public_class_location(session: dict[str, Any]) -> bool:
    return any(is_public_class_location(value) for value in session_location_candidates(session))


def public_location_rejection_reason(location_name: Any) -> str | None:
    if is_public_class_location(location_name):
        return None
    return "location_not_public_double_colon_prefix_required"
