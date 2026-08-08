"""Shared final contract for public-safe dynamic inventory.

All source rows passed here have already gone through the existing hub loaders'
publication, policy, container, URL, and renderability gates.  This module owns
only deterministic cross-source deduplication and the versioned contract shape.
It contains no scheduling policy.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "landerware.public-dynamic-inventory.v1"


def _text(value: Any) -> str:
    return " ".join(str(value or "").split())


def merge_appointment_seed_offers(*grouped_sources: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    """Preserve the hub's source precedence and dedupe booking-equivalent rows."""
    merged: dict[str, list[dict[str, Any]]] = {}
    seen_by_hub: dict[str, set[str]] = {}
    for grouped in grouped_sources:
        for hub_slug, offers in grouped.items():
            hub_key = _text(hub_slug)
            if not hub_key:
                continue
            seen = seen_by_hub.setdefault(hub_key, set())
            for offer in offers:
                href = _text(offer.get("appointment_registration_url"))
                dedupe_key = href or "|".join(
                    _text(offer.get(key))
                    for key in ("course_id", "start_datetime", "location_name", "instructor_display_name")
                )
                if not dedupe_key or dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                merged.setdefault(hub_key, []).append(dict(offer))
    for hub_slug, offers in list(merged.items()):
        merged[hub_slug] = sorted(offers, key=lambda item: _text(item.get("start_datetime")))
    return merged


def collect_public_dynamic_inventory(
    *,
    legacy_requestable_by_course: dict[str, list[dict[str, Any]]],
    universal_by_hub: dict[str, list[dict[str, Any]]],
    modeled_seed_by_hub: dict[str, list[dict[str, Any]]],
    public_sellable_seed_by_hub: dict[str, list[dict[str, Any]]],
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build the exact normalized dynamic collection consumed by public hubs."""
    universal_appointment_seed_by_hub = {
        hub: [row for row in rows if row.get("display_item_type") == "appointment_seed_offer"]
        for hub, rows in universal_by_hub.items()
    }
    appointment_seed_by_hub = merge_appointment_seed_offers(
        universal_appointment_seed_by_hub,
        modeled_seed_by_hub,
        public_sellable_seed_by_hub,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "legacy_requestable_by_course": legacy_requestable_by_course,
        "appointment_seed_by_hub": appointment_seed_by_hub,
        "universal_by_hub": universal_by_hub,
        "counts": {
            "legacy_requestable": sum(len(rows) for rows in legacy_requestable_by_course.values()),
            "appointment_seed": sum(len(rows) for rows in appointment_seed_by_hub.values()),
            "universal": sum(len(rows) for rows in universal_by_hub.values()),
        },
    }


def write_public_dynamic_inventory(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
