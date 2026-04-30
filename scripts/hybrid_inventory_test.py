from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from scripts.hybrid_inventory import APPOINTMENT_ENDPOINT, TZ, session_enrolled_count


ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
DEBUG_DIR = ROOT / "debug"
HUBS = ["bls", "acls", "pals", "heartsaver"]


@dataclass
class AppointmentProbe:
    payload: dict[str, str]
    status: int
    access_control_allow_origin: str | None
    urls: list[str]
    raw_response_preview: str


def probe_appointment_endpoint(payload: dict[str, str]) -> AppointmentProbe:
    request = Request(
        APPOINTMENT_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8", errors="replace")
        payload = json.loads(body)
        html_blob = html.unescape(str(payload.get("d") or ""))
        urls = re.findall(
            r"href=['\"](https://coastalcprtraining\.enrollware\.com/enroll\?appointmentDayId[^'\"]+)['\"]",
            html_blob,
        )
        return AppointmentProbe(
            payload=payload,
            status=response.status,
            access_control_allow_origin=response.headers.get("Access-Control-Allow-Origin"),
            urls=urls,
            raw_response_preview=body[:800],
        )


def main() -> int:
    schedule = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
    sessions = schedule.get("sessions", [])
    popular_sessions = [s for s in sessions if session_enrolled_count(s) >= 1]
    real_inventory_sessions = [s for s in sessions if "enroll?id=" in str(s.get("registration_url") or "")]

    hub_checks = {}
    for slug in HUBS:
        html_path = ROOT / "docs" / f"{slug}.html"
        html = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
        hub_checks[slug] = {
            "exists": html_path.exists(),
            "has_popular_section": "Popular Upcoming Classes" in html,
            "has_scheduled_section": "Next Scheduled Classes" in html,
            "has_flexible_section": "Flexible Available Times" in html,
        }

    may_probe = probe_appointment_endpoint({"date": "053126", "locationId": "101560", "courseId": "463119"})
    jan_probe = probe_appointment_endpoint({"date": "010127", "locationId": "101560", "courseId": "463119"})

    payload = {
        "generated_at": __import__("datetime").datetime.now(TZ).isoformat(),
        "schedule_counts": {
            "sessions_total": len(sessions),
            "sessions_with_enrolled_count": len(popular_sessions),
            "sessions_with_real_enroll_url": len(real_inventory_sessions),
        },
        "hub_checks": hub_checks,
        "appointment_tests": {
            "may_31_2026": may_probe.__dict__,
            "jan_1_2027": jan_probe.__dict__,
        },
        "notes": {
            "browser_cors_direct_fetch_supported": bool(
                may_probe.access_control_allow_origin or jan_probe.access_control_allow_origin
            ),
            "caveat": "Enrollware did not advertise Access-Control-Allow-Origin in the tested response headers, so the on-page flexible inventory widget must fail gracefully and offer the live open-seat page when the browser blocks cross-origin POSTs.",
        },
    }

    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    json_path = DEBUG_DIR / "hybrid_inventory_test.json"
    md_path = DEBUG_DIR / "hybrid_inventory_test.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Hybrid Inventory Test",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Scheduled Inventory",
        "",
        f"- Total future scheduled sessions: {len(sessions)}",
        f"- Sessions with enrolled_count >= 1: {len(popular_sessions)}",
        f"- Sessions with direct `enroll?id=` registration URLs: {len(real_inventory_sessions)}",
        "",
        "## Hub Checks",
        "",
    ]
    for slug, check in hub_checks.items():
        lines.append(
            f"- `{slug}.html`: popular={check['has_popular_section']}, scheduled={check['has_scheduled_section']}, flexible={check['has_flexible_section']}"
        )

    lines.extend(
        [
            "",
            "## Appointment Endpoint",
            "",
            f"- May 31, 2026 returned {len(may_probe.urls)} enrollment URLs (HTTP {may_probe.status})",
            f"- January 1, 2027 returned {len(jan_probe.urls)} enrollment URLs (HTTP {jan_probe.status})",
            f"- Access-Control-Allow-Origin header present: {payload['notes']['browser_cors_direct_fetch_supported']}",
            "",
            "### Sample URLs",
            "",
        ]
    )
    for url in (may_probe.urls[:3] + jan_probe.urls[:3]):
        lines.append(f"- {url}")

    lines.extend(
        [
            "",
            "## Constraint",
            "",
            payload["notes"]["caveat"],
            "",
        ]
    )

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
