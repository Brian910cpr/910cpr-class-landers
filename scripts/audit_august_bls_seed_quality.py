from __future__ import annotations

import csv
import json
import urllib.parse
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
AUGUST_PREFIX = "2026-08"
PREFERRED_TIMES = ["09:15", "12:30", "18:15", "18:45"]
UNKNOWN = "UNKNOWN"

PUBLIC_SELLABLE_PATH = AUDIT_DIR / "public_sellable_offers_preview.json"
DYNAMIC_PATH = AUDIT_DIR / "dynamic_offers_preview.json"
SEEDS_PATH = AUDIT_DIR / "schedule_seeds_preview.json"
URLS_PATH = AUDIT_DIR / "seed_appointment_url_preview.json"
COURSE_CATALOG_PATH = ROOT / "data" / "config" / "course_catalog.json"
SEED_POLICY_PATH = ROOT / "data" / "config" / "seed_strategy_policy.json"
CONTAINERS_PATH = ROOT / "data" / "inventory" / "appointment_containers.json"
SCHEDULE_FUTURE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
PUBLIC_SCHEDULE_PATH = ROOT / "docs" / "public_schedule.json"
BLS_HTML_PATH = ROOT / "docs" / "bls.html"

QUALITY_MD = AUDIT_DIR / "august_bls_seed_quality_audit.md"
QUALITY_JSON = AUDIT_DIR / "august_bls_seed_quality_audit.json"
SELLABLE_CSV = AUDIT_DIR / "august_bls_public_sellable_24.csv"
RENDER_MD = AUDIT_DIR / "august_bls_rendered_seed_proof.md"
RENDER_JSON = AUDIT_DIR / "august_bls_rendered_seed_proof.json"
RECOMMENDATION_MD = AUDIT_DIR / "august_bls_seed_policy_recommendation.md"
FILE_POLICY_MD = AUDIT_DIR / "generated_preview_file_size_policy.md"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def is_august(row: dict[str, Any]) -> bool:
    return clean(row.get("date") or row.get("start") or row.get("start_at") or row.get("start_datetime")).startswith(AUGUST_PREFIX)


def is_bls_text(row: dict[str, Any]) -> bool:
    text = " ".join(clean(row.get(key)).lower() for key in ("course_id", "course_key", "course_family", "course_title", "title", "course_name", "official_course_name"))
    return "bls" in text


def catalog_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {clean(row.get("course_id")): row for row in payload.get("courses", []) if isinstance(row, dict)}


def by_offer_id(rows: list[dict[str, Any]], key: str = "offer_id") -> dict[str, dict[str, Any]]:
    return {clean(row.get(key)): row for row in rows if isinstance(row, dict) and clean(row.get(key))}


def hidden_reasons(payload: dict[str, Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for row in payload.get("hidden_offers", []):
        if isinstance(row, dict) and clean(row.get("source_offer_id")):
            out[clean(row.get("source_offer_id"))].append(clean(row.get("reason_code") or UNKNOWN))
    return dict(out)


def course_key(course_id: Any, catalog: dict[str, dict[str, Any]]) -> str:
    return clean(catalog.get(clean(course_id), {}).get("course_key") or UNKNOWN)


def page_card(course_id: str) -> str:
    if course_id == "209806":
        return "docs/bls.html#bls-provider"
    if course_id == "359474":
        return "docs/bls.html#bls-renewal"
    if course_id == "210549":
        return "docs/bls.html#bls-heartcode"
    if course_id == "445670":
        return "docs/hsi.html#hsi-bls-fa"
    return "unknown"


def am_pm(hhmm: str) -> str:
    parsed = datetime.strptime(hhmm, "%H:%M")
    return parsed.strftime("%-I:%M %p") if "%" not in "%-I" else parsed.strftime("%I:%M %p").lstrip("0")


def booking_url(offer: dict[str, Any]) -> str:
    start = datetime.strptime(clean(offer.get("start_time")), "%H:%M").strftime("%I:%M %p").lstrip("0")
    params = {
        "appointmentDayId": clean(offer.get("appointmentDayId")),
        "startTime": start,
        "courseId": clean(offer.get("course_id")),
    }
    return "https://coastalcprtraining.enrollware.com/enroll?" + urllib.parse.urlencode(params)


def appointment_day_expected(target_date: str, container: dict[str, Any]) -> int | None:
    try:
        first = date.fromisoformat(clean(container.get("first_valid_date")))
        target = date.fromisoformat(target_date)
        return int(container["first_valid_appointmentDayId"]) + (target - first).days
    except (KeyError, TypeError, ValueError):
        return None


def active_shipyard_container(containers: dict[str, Any]) -> dict[str, Any]:
    for row in containers.get("containers", []):
        if isinstance(row, dict) and row.get("status") == "active" and "shipyard" in clean(row.get("container_id")).lower():
            return row
    return {}


def selection_rank(offer: dict[str, Any], policy: dict[str, Any]) -> tuple[int, int, str, str]:
    preferred = policy.get("preferred_start_times_by_family", {}).get(clean(offer.get("course_family")), [])
    try:
        preferred_rank = preferred.index(clean(offer.get("start_time")))
    except ValueError:
        preferred_rank = 999
    terms = policy.get("course_title_priority_terms", [])
    title = clean(offer.get("course_title"))
    title_rank = 999
    for index, term in enumerate(terms):
        if clean(term).lower() in title.lower():
            title_rank = index
            break
    return preferred_rank, title_rank, clean(offer.get("start_time")), clean(offer.get("offer_id"))


def run() -> dict[str, Any]:
    public_sellable = read_json(PUBLIC_SELLABLE_PATH)
    dynamic = read_json(DYNAMIC_PATH)
    seeds = read_json(SEEDS_PATH)
    urls = read_json(URLS_PATH)
    catalog = catalog_by_id(read_json(COURSE_CATALOG_PATH))
    seed_policy = read_json(SEED_POLICY_PATH)
    containers = read_json(CONTAINERS_PATH)
    schedule_future = read_json(SCHEDULE_FUTURE_PATH)
    public_schedule = read_json(PUBLIC_SCHEDULE_PATH)
    bls_html = BLS_HTML_PATH.read_text(encoding="utf-8", errors="ignore")
    container = active_shipyard_container(containers)

    sellable_bls = [
        row for row in public_sellable.get("offers", [])
        if isinstance(row, dict) and is_august(row) and is_bls_text(row)
    ]
    dynamic_common_time_bls = [
        row for row in dynamic.get("offers", [])
        if isinstance(row, dict) and is_august(row) and is_bls_text(row) and clean(row.get("start_time")) in PREFERRED_TIMES
    ]
    hidden_common_time_bls = [
        row for row in public_sellable.get("hidden_offers", [])
        if isinstance(row, dict)
        and isinstance(row.get("offer"), dict)
        and is_august(row["offer"])
        and is_bls_text(row["offer"])
        and clean(row["offer"].get("start_time")) in PREFERRED_TIMES
    ]
    sellable_lookup = by_offer_id(sellable_bls)
    selected_by_offer = by_offer_id(seeds.get("seeds", []), "source_offer_id")
    url_by_offer = by_offer_id(urls.get("previews", []), "source_offer_id")
    rejected = hidden_reasons(seeds)

    quality_rows = []
    sorted_offers = sorted(sellable_bls, key=lambda row: (row.get("date", ""), selection_rank(row, seed_policy)))
    for index, offer in enumerate(sorted_offers, start=1):
        offer_id = clean(offer.get("offer_id"))
        selected = offer_id in selected_by_offer
        seed = selected_by_offer.get(offer_id, {})
        url = url_by_offer.get(offer_id, {})
        expected_day = appointment_day_expected(clean(offer.get("date")), container)
        row = {
            "date": offer.get("date"),
            "start_time": offer.get("start_time"),
            "end_time": offer.get("end_time"),
            "courseId": offer.get("course_id"),
            "course_name": offer.get("course_title"),
            "course_key": course_key(offer.get("course_id"), catalog),
            "course_family": offer.get("course_family"),
            "instructor": offer.get("instructor_display_name"),
            "resource": offer.get("resource"),
            "location": offer.get("location"),
            "appointmentDayId": offer.get("appointmentDayId"),
            "booking_url": (url.get("appointment_url_preview") if selected else booking_url(offer)),
            "selection_rank": index,
            "preferred_start_rank": selection_rank(offer, seed_policy)[0],
            "title_rank": selection_rank(offer, seed_policy)[1],
            "selected": "yes" if selected else "no",
            "reason_selected_or_rejected": ";".join(seed.get("reasons", [])) if selected else ";".join(rejected.get(offer_id, ["not_selected_or_hidden_after_seed_strategy"])),
            "source_availability_window": offer.get("source_availability_window"),
            "expected_appointmentDayId": expected_day,
            "appointmentDayId_matches_date": str(expected_day == offer.get("appointmentDayId")),
        }
        quality_rows.append(row)

    selected_rows = [row for row in quality_rows if row["selected"] == "yes"]
    common_time_presence = {
        target: {
            "dynamic_candidate_count": sum(1 for row in dynamic_common_time_bls if row.get("start_time") == target),
            "public_sellable_count": sum(1 for row in quality_rows if row["start_time"] == target),
            "dynamic_public_sellable_available": any(row["start_time"] == target for row in quality_rows),
            "selected_count": sum(1 for row in selected_rows if row["start_time"] == target),
            "public_filter_hidden_reasons": dict(Counter(
                reason
                for item in hidden_common_time_bls
                if item["offer"].get("start_time") == target
                for reason in item.get("reason_codes", [])
            ).most_common()),
        }
        for target in PREFERRED_TIMES
    }
    public_bls_august_rows = [
        row for row in public_schedule.get("sessions", [])
        if isinstance(row, dict) and is_august(row) and is_bls_text(row)
    ]
    future_bls_august_rows = [
        row for row in schedule_future.get("sessions", [])
        if isinstance(row, dict) and is_august(row) and is_bls_text(row)
    ]
    render_rows = []
    for row in selected_rows:
        rendered_url_present = clean(row["booking_url"]) in bls_html
        rendered_seed_future = any(clean(item.get("seed_id")) and clean(item.get("source_offer_id")) == clean(sellable_lookup.get(clean(row.get("source_offer_id")), {}).get("offer_id")) for item in schedule_future.get("sessions", []))
        render_rows.append({
            "page_card_destination": page_card(clean(row["courseId"])),
            "visible_date": row["date"] if rendered_url_present else "",
            "visible_time": row["start_time"] if rendered_url_present else "",
            "visible_course_label": row["course_name"] if rendered_url_present else "",
            "visible_button_text": "Check this date/time" if rendered_url_present else "",
            "url_type": "appointment_seed",
            "booking_url": row["booking_url"],
            "renders_on_current_bls_html": rendered_url_present,
            "rendered_seed_row_in_schedule_future": rendered_seed_future,
            "appears_alongside_real_enrollware_rows": rendered_url_present and bool(public_bls_august_rows),
            "proof_note": "No current rendered seed row found; this branch generated URL proof only." if not rendered_url_present else "Rendered in docs/bls.html.",
        })

    url_sanity = []
    for row in selected_rows:
        parsed = urllib.parse.urlparse(clean(row["booking_url"]))
        params = urllib.parse.parse_qs(parsed.query)
        url_sanity.append({
            "date": row["date"],
            "start_time": row["start_time"],
            "courseId": row["courseId"],
            "course_key": row["course_key"],
            "appointmentDayId": row["appointmentDayId"],
            "expected_appointmentDayId": row["expected_appointmentDayId"],
            "appointmentDayId_matches_date": row["appointmentDayId_matches_date"],
            "startTime_param": params.get("startTime", [""])[0],
            "courseId_param": params.get("courseId", [""])[0],
            "courseId_matches_row": str(params.get("courseId", [""])[0] == clean(row["courseId"])),
            "initial_renewal_mapping_ok": str(
                ("provider_renewal" in row["course_key"] and row["courseId"] == "359474")
                or ("aha_bls_provider" == row["course_key"] and row["courseId"] == "209806")
                or ("heartcode" in row["course_key"] and row["courseId"] == "210549")
            ),
        })

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "read_only": True,
        "deployed": False,
        "august_bls_public_sellable_offers": len(quality_rows),
        "selected_august_bls_seeds": len(selected_rows),
        "selected_by_date": dict(Counter(row["date"] for row in selected_rows)),
        "selected_by_course": dict(Counter(f"{row['courseId']} {row['course_name']}" for row in selected_rows)),
        "selected_by_start_time": dict(Counter(row["start_time"] for row in selected_rows)),
        "public_sellable_by_start_time": dict(Counter(row["start_time"] for row in quality_rows)),
        "common_public_time_presence": common_time_presence,
        "common_public_time_dynamic_candidates_total": len(dynamic_common_time_bls),
        "common_public_time_hidden_reasons_total": dict(Counter(reason for item in hidden_common_time_bls for reason in item.get("reason_codes", [])).most_common()),
        "preferred_bls_start_times_policy": seed_policy.get("preferred_start_times_by_family", {}).get("BLS", []),
        "morning_friendly_families": seed_policy.get("morning_friendly_families", []),
        "real_august_bls_rows_schedule_future": len(future_bls_august_rows),
        "real_august_bls_rows_public_schedule": len(public_bls_august_rows),
        "selected_seed_rows_rendered_on_bls_html": sum(1 for row in render_rows if row["renders_on_current_bls_html"]),
        "recommendation": "B",
        "recommendation_text": "Adjust selector to prefer known public-friendly time bands through config, but do not hardcode new times in code. The current 08:00/08:30 choices are policy-driven and safe. The common public times exist dynamically, but current public-sellable caps/policy hide them before seed selection.",
        "large_public_sellable_preview_size_mb": round(PUBLIC_SELLABLE_PATH.stat().st_size / (1024 * 1024), 2),
    }

    report = {
        "summary": summary,
        "quality_rows": quality_rows,
        "render_rows": render_rows,
        "url_sanity": url_sanity,
    }

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    write_quality_csv(SELLABLE_CSV, quality_rows)
    QUALITY_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    QUALITY_MD.write_text(render_quality_md(report), encoding="utf-8")
    RENDER_JSON.write_text(json.dumps({"summary": summary, "render_rows": render_rows, "url_sanity": url_sanity}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    RENDER_MD.write_text(render_render_md(summary, render_rows), encoding="utf-8")
    RECOMMENDATION_MD.write_text(render_recommendation_md(summary), encoding="utf-8")
    FILE_POLICY_MD.write_text(render_file_policy_md(summary), encoding="utf-8")
    return report


def write_quality_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "date", "start_time", "end_time", "courseId", "course_name", "course_key", "course_family",
        "instructor", "resource", "location", "appointmentDayId", "booking_url", "selection_rank",
        "preferred_start_rank", "title_rank", "selected", "reason_selected_or_rejected",
        "source_availability_window", "expected_appointmentDayId", "appointmentDayId_matches_date",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def render_quality_md(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        "# August BLS Seed Quality Audit",
        "",
        "Status: read-only audit. No deploy was performed.",
        "",
        "## Plain Answer",
        "",
        "The selected BLS seeds are safe URL-backed candidates, but the current times are early because the seed strategy policy prefers BLS `08:30` then `09:00`, and the August public-sellable BLS set only contains `08:00`, `08:15`, and `08:30` starts.",
        "",
        f"- August BLS-text public sellable offers: {s['august_bls_public_sellable_offers']}",
        f"- Selected August BLS seeds: {s['selected_august_bls_seeds']}",
        f"- Selected by date: {s['selected_by_date']}",
        f"- Selected by course: {s['selected_by_course']}",
        f"- Public sellable by start time: {s['public_sellable_by_start_time']}",
        "",
        "## Common Public Time Bands",
        "",
    ]
    for time_value, item in s["common_public_time_presence"].items():
        lines.append(f"- `{time_value}`: dynamic candidates {item['dynamic_candidate_count']}, public-sellable candidates {item['public_sellable_count']}, selected {item['selected_count']}, hidden reasons {item['public_filter_hidden_reasons']}")
    lines.extend([
        "",
        "## Selected Seeds",
        "",
        "| Date | Time | Course | courseId | appointmentDayId | Reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for row in report["quality_rows"]:
        if row["selected"] == "yes":
            lines.append(f"| {row['date']} | {row['start_time']} | {row['course_name']} | {row['courseId']} | {row['appointmentDayId']} | {row['reason_selected_or_rejected']} |")
    lines.extend(["", "See `august_bls_public_sellable_24.csv` for all 24 public-sellable BLS-text offers and rejection reasons.", ""])
    return "\n".join(lines)


def render_render_md(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# August BLS Rendered Seed Proof",
        "",
        "Status: read-only proof. No public page was regenerated or deployed.",
        "",
        f"- Selected seed rows rendered on current `docs/bls.html`: {summary['selected_seed_rows_rendered_on_bls_html']}",
        f"- Real August BLS rows in `docs/data/schedule_future.json`: {summary['real_august_bls_rows_schedule_future']}",
        f"- Real August BLS rows in `docs/public_schedule.json`: {summary['real_august_bls_rows_public_schedule']}",
        "",
        "| Page/Card | Visible Date | Visible Time | Label | Button | URL Type | Rendered? | Proof |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['page_card_destination']} | {row['visible_date']} | {row['visible_time']} | {row['visible_course_label']} | {row['visible_button_text']} | {row['url_type']} | {row['renders_on_current_bls_html']} | {row['proof_note']} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_recommendation_md(summary: dict[str, Any]) -> str:
    return "\n".join([
        "# August BLS Seed Policy Recommendation",
        "",
        "Recommendation: **B. Adjust selector to prefer known public-friendly time bands**, but only through existing config-driven policy.",
        "",
        "Smallest safe rule change: update `data/config/seed_strategy_policy.json` `preferred_start_times_by_family.BLS` after Brian approves the desired BLS public time order. Do not hardcode times in selector code.",
        "",
        "Current facts:",
        "",
        f"- Current BLS preferred starts: {summary['preferred_bls_start_times_policy']}",
        f"- Common requested bands checked: {summary['common_public_time_presence']}",
        f"- `09:15`, `12:30`, `18:15`, and `18:45` exist as dynamic candidates ({summary['common_public_time_dynamic_candidates_total']} total), but they are not present in the current August BLS public-sellable set. Hidden reasons: {summary['common_public_time_hidden_reasons_total']}.",
        "- The selector is not purely choosing earliest time; it is choosing the first available preferred BLS time, then title priority, then start time.",
        "- Four BLS seeds across August 3, 4, 10, and 11 are reasonable but shallow; deeper August spread would require either a longer public sellable candidate window or a seed strategy that intentionally samples later weeks.",
        "",
    ])


def render_file_policy_md(summary: dict[str, Any]) -> str:
    return "\n".join([
        "# Generated Preview File Size Policy",
        "",
        "Status: report only. No generated preview files were moved, deleted, truncated, or compressed.",
        "",
        f"- `data/audit/public_sellable_offers_preview.json`: {summary['large_public_sellable_preview_size_mb']} MB",
        "- It remains tracked on this review branch because downstream audits currently read the full preview.",
        "- A summarized audit output can replace it long-term for Git history, provided local regeneration remains deterministic.",
        "- Recommended repo policy: keep compact summaries and CSVs in git; move full generated previews to ignored runtime/debug output or CI artifacts after review approval.",
        "",
    ])


def main() -> int:
    report = run()
    summary = report["summary"]
    print("August BLS seed quality audit complete (READ ONLY).")
    print(f"August BLS public sellable offers: {summary['august_bls_public_sellable_offers']}")
    print(f"Selected August BLS seeds: {summary['selected_august_bls_seeds']}")
    print(f"Rendered on current BLS HTML: {summary['selected_seed_rows_rendered_on_bls_html']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
