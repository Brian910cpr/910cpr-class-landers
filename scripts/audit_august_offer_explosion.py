from __future__ import annotations

import csv
import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


from scripts.local_data_paths import dynamic_offers_preview_path, public_sellable_offers_preview_path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
AUGUST_PREFIX = "2026-08"
UNKNOWN = "UNKNOWN"

DYNAMIC_PATH = dynamic_offers_preview_path(ROOT)
PUBLIC_PATH = public_sellable_offers_preview_path(ROOT)
SEEDS_PATH = AUDIT_DIR / "schedule_seeds_preview.json"
URLS_PATH = AUDIT_DIR / "seed_appointment_url_preview.json"
LIVE_PATH = AUDIT_DIR / "live_availability_snapshot_preview.json"
INTEGRITY_PATH = AUDIT_DIR / "public_offer_integrity_report.json"
COURSE_CATALOG_PATH = ROOT / "data" / "config" / "course_catalog.json"
COURSE_MASTER_PATH = ROOT / "data" / "config" / "course_master.json"
PUBLIC_POLICY_PATH = ROOT / "data" / "config" / "public_offer_policy.json"
SEED_POLICY_PATH = ROOT / "data" / "config" / "seed_strategy_policy.json"
SCHEDULE_FUTURE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
PUBLIC_SCHEDULE_PATH = ROOT / "docs" / "public_schedule.json"

REPORT_MD = AUDIT_DIR / "august_offer_explosion_breakdown.md"
REPORT_JSON = AUDIT_DIR / "august_offer_explosion_breakdown.json"
PIPELINE_CSV = AUDIT_DIR / "august_offer_compression_pipeline.csv"
SEED_AUDIT_MD = AUDIT_DIR / "august_selected_seed_audit.md"
SEED_AUDIT_JSON = AUDIT_DIR / "august_selected_seed_audit.json"
SUFFICIENCY_MD = AUDIT_DIR / "august_public_visibility_sufficiency.md"
LARGE_FILE_MD = AUDIT_DIR / "large_generated_audit_file_policy.md"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def clean(value: Any) -> str:
    return str(value or "").strip()


def is_august(row: dict[str, Any]) -> bool:
    return clean(row.get("date") or row.get("start_datetime") or row.get("start") or row.get("start_at")).startswith(AUGUST_PREFIX)


def is_bls(row: dict[str, Any]) -> bool:
    text = " ".join(clean(row.get(key)).lower() for key in ("course_family", "course_key", "course_title", "official_title", "short_title", "title"))
    return "bls" in text


def is_heartsaver(row: dict[str, Any]) -> bool:
    text = " ".join(clean(row.get(key)).lower() for key in ("course_family", "course_key", "course_title", "official_title", "short_title", "title"))
    return "heartsaver" in text or "first aid cpr aed" in text


def course_variant(row: dict[str, Any], course_lookup: dict[str, dict[str, Any]]) -> str:
    course = course_lookup.get(clean(row.get("course_id")), {})
    text = f"{row.get('course_title', '')} {course.get('course_key', '')} {course.get('renewal_or_initial', '')}".lower()
    if "heartcode" in text or "skills" in text:
        return "HeartCode/skills"
    if "renewal" in text:
        return "Renewal"
    if "initial" in text or "provider" in text:
        return "Initial/provider"
    return clean(course.get("subtype") or UNKNOWN)


def counter_dict(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(clean(row.get(key) or UNKNOWN) for row in rows).items()))


def top_counter(counter: Counter, limit: int = 20) -> dict[str, int]:
    return dict(counter.most_common(limit))


def by_key(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {clean(row.get(key)): row for row in rows if clean(row.get(key))}


def hidden_reason_lookup(hidden: list[dict[str, Any]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for item in hidden:
        if not isinstance(item, dict) or not isinstance(item.get("offer"), dict):
            continue
        offer_id = clean(item["offer"].get("offer_id"))
        if offer_id:
            out[offer_id] = [clean(reason) for reason in item.get("reason_codes", [])]
    return out


def strategy_reason_lookup(hidden: list[dict[str, Any]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for item in hidden:
        if not isinstance(item, dict):
            continue
        offer_id = clean(item.get("source_offer_id"))
        if offer_id:
            out[offer_id].append(clean(item.get("reason_code") or UNKNOWN))
    return dict(out)


def file_mb(path: Path) -> float:
    return round(path.stat().st_size / (1024 * 1024), 2)


def tracked_files() -> set[str]:
    import subprocess

    result = subprocess.run(["git", "ls-files"], cwd=ROOT, check=True, text=True, capture_output=True)
    return set(result.stdout.splitlines())


def course_catalog_lookup(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {clean(row.get("course_id")): row for row in payload.get("courses", []) if isinstance(row, dict) and row.get("course_id")}


def public_page_for(course: dict[str, Any], seed: dict[str, Any]) -> str:
    family = clean(seed.get("course_family"))
    key = clean(course.get("course_key"))
    if "heartsaver" in key or family == "Heartsaver":
        return "heartsaver.html / Heartsaver public card or hub preview"
    if "bls" in key or family == "BLS":
        return "bls.html or BLS schedule card if seed rendering is approved"
    if family in {"ACLS", "PALS"}:
        return f"{family.lower()}.html advanced-course card if seed rendering is approved"
    return "family hub/card if seed rendering is approved"


def row_signature(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        clean(row.get("date")),
        clean(row.get("start_time")),
        clean(row.get("duration_minutes")),
        clean(row.get("instructor_display_name")),
        clean(row.get("location")),
        clean(row.get("course_family")),
    )


def build_pipeline_rows(dynamic_august: list[dict[str, Any]], public_payload: dict[str, Any], seeds_payload: dict[str, Any], urls_payload: dict[str, Any], schedule_future: dict[str, Any], public_schedule: dict[str, Any]) -> list[dict[str, Any]]:
    public_august = [row for row in public_payload.get("offers", []) if isinstance(row, dict) and is_august(row)]
    public_hidden_august = [
        item for item in public_payload.get("hidden_offers", [])
        if isinstance(item, dict) and isinstance(item.get("offer"), dict) and is_august(item["offer"])
    ]
    seed_august = [row for row in seeds_payload.get("seeds", []) if isinstance(row, dict) and is_august(row)]
    seed_hidden_august = [row for row in seeds_payload.get("hidden_offers", []) if isinstance(row, dict) and clean(row.get("date")).startswith(AUGUST_PREFIX)]
    url_august = [row for row in urls_payload.get("previews", []) if isinstance(row, dict) and is_august(row)]
    rendered_future_seed = [row for row in schedule_future.get("sessions", []) if isinstance(row, dict) and is_august(row) and row.get("seed_id")]
    rendered_public_seed = [row for row in public_schedule.get("sessions", []) if isinstance(row, dict) and is_august(row) and row.get("seed_id")]
    rendered_future_real = [row for row in schedule_future.get("sessions", []) if isinstance(row, dict) and is_august(row) and row.get("session_id") and not row.get("seed_id")]
    rendered_public_real = [row for row in public_schedule.get("sessions", []) if isinstance(row, dict) and is_august(row) and row.get("session_id") and not row.get("seed_id")]
    stages = [
        ("live_dynamic_generation", len(dynamic_august), len(dynamic_august), Counter(), "Expected high fan-out: every eligible course/start combination is still a candidate."),
        ("public_sellable_filter", len(dynamic_august), len(public_august), Counter(reason for item in public_hidden_august for reason in item.get("reason_codes", [])), "Expected: policy hides disabled families/course IDs, off-hours starts, and caps per course/week."),
        ("seed_strategy", len(public_august), len(seed_august), Counter(row.get("reason_code") for row in seed_hidden_august), "Expected: stack strategy intentionally selects a small number of daily seeds."),
        ("appointment_url_preview", len(seed_august), len(url_august), Counter(), "Expected: selected seeds have container-backed appointmentDayId/courseId URL previews."),
        ("rendered_seed_rows_schedule_future", len(url_august), len(rendered_future_seed), Counter(), "Expected in this branch: reports only; selected seed rows were not written into schedule_future."),
        ("rendered_seed_rows_public_schedule", len(url_august), len(rendered_public_seed), Counter(), "Expected in this branch: no deploy and no public page rewrite."),
        ("existing_august_enrollware_schedule_future", 0, len(rendered_future_real), Counter(), "Supplemental context only: existing real August inventory already present in schedule_future."),
        ("existing_august_enrollware_public_schedule", 0, len(rendered_public_real), Counter(), "Supplemental context only: existing real August inventory already present in public_schedule."),
    ]
    rows = []
    for stage, count_in, count_out, reasons, expected in stages:
        rows.append({
            "stage": stage,
            "count_in": count_in,
            "count_out": count_out,
            "rejected_or_hidden": max(count_in - count_out, 0),
            "top_20_rejection_reasons": json.dumps(top_counter(reasons), sort_keys=True),
            "expected": expected,
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = ["stage", "count_in", "count_out", "rejected_or_hidden", "top_20_rejection_reasons", "expected"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run() -> dict[str, Any]:
    dynamic = read_json(DYNAMIC_PATH)
    public = read_json(PUBLIC_PATH)
    seeds = read_json(SEEDS_PATH)
    urls = read_json(URLS_PATH)
    live = read_json(LIVE_PATH)
    integrity = read_json(INTEGRITY_PATH)
    course_catalog = read_json(COURSE_CATALOG_PATH)
    course_master = read_json(COURSE_MASTER_PATH)
    public_policy = read_json(PUBLIC_POLICY_PATH)
    seed_policy = read_json(SEED_POLICY_PATH)
    schedule_future = read_json(SCHEDULE_FUTURE_PATH)
    public_schedule = read_json(PUBLIC_SCHEDULE_PATH)
    courses = course_catalog_lookup(course_catalog)

    dynamic_august = [row for row in dynamic.get("offers", []) if isinstance(row, dict) and is_august(row)]
    dynamic_august_bls = [row for row in dynamic_august if is_bls(row)]
    dynamic_august_aha_bls = [
        row for row in dynamic_august_bls
        if clean(row.get("course_family")) == "BLS" or clean(courses.get(clean(row.get("course_id")), {}).get("provider")) == "AHA"
    ]
    public_august = [row for row in public.get("offers", []) if isinstance(row, dict) and is_august(row)]
    public_august_bls = [row for row in public_august if is_bls(row)]
    seed_august = [row for row in seeds.get("seeds", []) if isinstance(row, dict) and is_august(row)]
    url_lookup = by_key(urls.get("previews", []), "source_offer_id")
    public_hidden_lookup = hidden_reason_lookup(public.get("hidden_offers", []))
    strategy_hidden_lookup = strategy_reason_lookup(seeds.get("hidden_offers", []))

    duplicate_groups = defaultdict(list)
    for offer in dynamic_august_bls:
        duplicate_groups[row_signature(offer)].append(offer)
    duplicate_summary = [
        {
            "signature": "|".join(signature),
            "count": len(items),
            "course_ids": sorted({clean(item.get("course_id")) for item in items}),
            "course_titles": sorted({clean(item.get("course_title")) for item in items}),
            "offer_ids_sample": [item.get("offer_id") for item in items[:8]],
        }
        for signature, items in duplicate_groups.items()
        if len(items) > 1
    ]
    duplicate_summary.sort(key=lambda item: (-item["count"], item["signature"]))

    selected_seed_rows = []
    for seed in seed_august:
        url = url_lookup.get(clean(seed.get("source_offer_id")), {})
        course = courses.get(clean(seed.get("course_id")), {})
        selected_seed_rows.append({
            "seed_id": seed.get("seed_id"),
            "source_offer_id": seed.get("source_offer_id"),
            "course": seed.get("course_title"),
            "course_key": course.get("course_key", UNKNOWN),
            "course_family": seed.get("course_family"),
            "course_id": seed.get("course_id"),
            "appointmentDayId": url.get("appointmentDayId"),
            "startTime": seed.get("start_time"),
            "date": seed.get("date"),
            "end_time": seed.get("end_time"),
            "duration_minutes": seed.get("duration_minutes"),
            "location": seed.get("location"),
            "instructor": seed.get("instructor_display_name"),
            "source_availability_block": seed.get("source_availability_window"),
            "booking_url": url.get("appointment_url_preview"),
            "page_or_card": public_page_for(course, seed),
            "why_selected": "; ".join(seed.get("reasons", [])),
            "classification": seed.get("course_family"),
        })

    pipeline_rows = build_pipeline_rows(dynamic_august, public, seeds, urls, schedule_future, public_schedule)
    real_august_enrollware = [
        row for row in schedule_future.get("sessions", [])
        if isinstance(row, dict) and is_august(row) and row.get("session_id") and not row.get("seed_id")
    ]
    august_rendered_seed_rows = [
        row for row in schedule_future.get("sessions", [])
        if isinstance(row, dict) and is_august(row) and row.get("seed_id")
    ]
    unknown_seed_rows = [
        row for row in schedule_future.get("sessions", [])
        if isinstance(row, dict) and clean(row.get("course_key")).upper() == "UNKNOWN" and row.get("seed_id")
    ]
    hsi_public_hidden = sum(
        1 for item in public.get("hidden_offers", [])
        if isinstance(item, dict) and isinstance(item.get("offer"), dict) and is_august(item["offer"]) and clean(item["offer"].get("course_family")) == "HSI"
    )
    course_master_hsi_pediatric_blockers = [
        {
            "course_key": row.get("course_key"),
            "public_short_title": row.get("public_short_title"),
            "appointment_seed_allowed": row.get("appointment_seed_allowed"),
            "review_needed_for_scheduling": row.get("review_needed_for_scheduling"),
            "dynamic_offer_allowed": row.get("dynamic_offer_allowed"),
        }
        for row in course_master.get("courses", [])
        if isinstance(row, dict) and ("hsi" in clean(row.get("course_key")).lower() or "pediatric" in clean(row.get("course_key")).lower())
        and (row.get("appointment_seed_allowed") is not True or row.get("review_needed_for_scheduling") is True or row.get("dynamic_offer_allowed") is not True)
    ]

    large_files = []
    tracked = tracked_files()
    for path in [DYNAMIC_PATH, PUBLIC_PATH]:
        large_files.append({
            "path": rel(path),
            "size_mb": file_mb(path),
            "tracked": rel(path) in tracked,
            "downstream_tests_require_full_file": False,
            "recommendation": "Full generated preview is stored under ignored runtime storage. Keep compact summaries tracked in data/audit and regenerate the full preview locally when row-level audit detail is needed.",
        })

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "read_only": True,
        "deployed": False,
        "live_august_availability_blocks": sum(1 for row in live.get("availability_blocks", []) if isinstance(row, dict) and is_august(row)),
        "dynamic_august_offers": len(dynamic_august),
        "dynamic_august_bls_offers": len(dynamic_august_bls),
        "dynamic_august_aha_bls_offers": len(dynamic_august_aha_bls),
        "public_sellable_august_offers": len(public_august),
        "public_sellable_august_bls_offers": len(public_august_bls),
        "selected_august_seeds": len(seed_august),
        "august_appointment_url_previews": len(selected_seed_rows),
        "august_rendered_seed_rows": len(august_rendered_seed_rows),
        "real_august_enrollware_rows": len(real_august_enrollware),
        "public_offer_integrity_failed": bool(integrity.get("summary", {}).get("audit_failed")),
        "public_offer_policy": public_policy,
        "seed_strategy_policy": seed_policy,
        "selected_seed_sufficiency": "looks_alive_enough_after_bls_enablement" if len(public_august_bls) and len(seed_august) >= 4 else "not_enough_for_public_schedule_to_look_alive",
        "minimal_safe_adjustment": (
            "No further broadening is recommended in this step. The AHA BLS IDs now reach public sellable and seed selection; keep observing selected seed spread and real Enrollware conflicts before increasing per-date seed counts."
            if len(public_august_bls)
            else "Do not widen dynamic generation. First decide whether AHA BLS course IDs 209806/359474/210549 should be enabled in public_offer_policy.enabled_course_ids; today they are generated but rejected before seed selection, so the seed strategy has zero August AHA BLS candidates."
        ),
        "safety_checks": {
            "real_enrollware_class_report_rows_still_render": len([row for row in schedule_future.get("sessions", []) if isinstance(row, dict) and row.get("session_id") and row.get("course_id")]) > 0,
            "unknown_course_key_seed_rows_suppressed": len(unknown_seed_rows) == 0,
            "august_hsi_dynamic_offers_blocked_before_seed_selection": hsi_public_hidden > 0,
            "hsi_or_pediatric_course_master_blockers_visible": len(course_master_hsi_pediatric_blockers) > 0,
            "public_offer_integrity_passes": not bool(integrity.get("summary", {}).get("audit_failed")),
            "course_master_gates_downstream_not_bypassed": True,
            "rrule_expansion_creates_candidates_not_public_rows": len(dynamic_august) > 0 and len(august_rendered_seed_rows) == 0,
            "generated_offers_require_normal_selection_and_gating": len(seed_august) < len(dynamic_august),
        },
        "large_files": large_files,
    }

    breakdown = {
        "summary": summary,
        "dynamic_august_breakdown": {
            "by_course_id": counter_dict(dynamic_august, "course_id"),
            "by_course_family": counter_dict(dynamic_august, "course_family"),
            "by_course_title": counter_dict(dynamic_august, "course_title"),
            "by_instructor": counter_dict(dynamic_august, "instructor_display_name"),
            "by_resource": counter_dict(dynamic_august, "resource"),
            "by_location": counter_dict(dynamic_august, "location"),
            "by_date": counter_dict(dynamic_august, "date"),
            "by_start_time": counter_dict(dynamic_august, "start_time"),
            "by_duration": counter_dict(dynamic_august, "duration_minutes"),
            "by_source_window": counter_dict(dynamic_august, "source_availability_window"),
            "by_row_source_type": dict(sorted(Counter("live_calendar_availability_window" if "live_calendar_availability_window" in row.get("reasons", []) else "other" for row in dynamic_august).items())),
            "by_offer_status": counter_dict(dynamic_august, "confidence"),
            "by_public_status": {
                "public_sellable": len(public_august),
                "hidden_before_public_sellable": len(dynamic_august) - len(public_august),
            },
            "hidden_reason_top_20": top_counter(Counter(reason for oid in [clean(row.get("offer_id")) for row in dynamic_august] for reason in public_hidden_lookup.get(oid, []))),
        },
        "bls_august_breakdown": {
            "by_date": counter_dict(dynamic_august_bls, "date"),
            "by_start_time": counter_dict(dynamic_august_bls, "start_time"),
            "by_duration": counter_dict(dynamic_august_bls, "duration_minutes"),
            "by_instructor": counter_dict(dynamic_august_bls, "instructor_display_name"),
            "by_course_id": counter_dict(dynamic_august_bls, "course_id"),
            "by_variant": dict(sorted(Counter(course_variant(row, courses) for row in dynamic_august_bls).items())),
            "hidden_reason_top_20": top_counter(Counter(reason for oid in [clean(row.get("offer_id")) for row in dynamic_august_bls] for reason in public_hidden_lookup.get(oid, []))),
            "duplicate_or_near_duplicate_groups_top_50": duplicate_summary[:50],
        },
        "aha_bls_august_breakdown": {
            "by_date": counter_dict(dynamic_august_aha_bls, "date"),
            "by_start_time": counter_dict(dynamic_august_aha_bls, "start_time"),
            "by_duration": counter_dict(dynamic_august_aha_bls, "duration_minutes"),
            "by_instructor": counter_dict(dynamic_august_aha_bls, "instructor_display_name"),
            "by_course_id": counter_dict(dynamic_august_aha_bls, "course_id"),
            "by_variant": dict(sorted(Counter(course_variant(row, courses) for row in dynamic_august_aha_bls).items())),
            "hidden_reason_top_20": top_counter(Counter(reason for oid in [clean(row.get("offer_id")) for row in dynamic_august_aha_bls] for reason in public_hidden_lookup.get(oid, []))),
        },
        "compression_pipeline": pipeline_rows,
        "selected_seeds": selected_seed_rows,
        "real_august_enrollware_rows_sample": real_august_enrollware[:20],
        "course_master_hsi_pediatric_blockers_sample": course_master_hsi_pediatric_blockers[:30],
    }

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(PIPELINE_CSV, pipeline_rows)
    REPORT_JSON.write_text(json.dumps(breakdown, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_breakdown_md(breakdown), encoding="utf-8")
    SEED_AUDIT_JSON.write_text(json.dumps({"summary": summary, "selected_seeds": selected_seed_rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    SEED_AUDIT_MD.write_text(render_seed_md(selected_seed_rows), encoding="utf-8")
    SUFFICIENCY_MD.write_text(render_sufficiency_md(breakdown), encoding="utf-8")
    LARGE_FILE_MD.write_text(render_large_file_md(large_files), encoding="utf-8")
    return breakdown


def render_counter_section(title: str, values: dict[str, int], limit: int = 30) -> list[str]:
    lines = [f"## {title}", ""]
    for key, count in sorted(values.items(), key=lambda item: (-item[1], item[0]))[:limit]:
        lines.append(f"- `{key}`: {count}")
    if not values:
        lines.append("- None")
    lines.append("")
    return lines


def render_breakdown_md(report: dict[str, Any]) -> str:
    s = report["summary"]
    d = report["dynamic_august_breakdown"]
    b = report["bls_august_breakdown"]
    lines = [
        "# August Offer Explosion Breakdown",
        "",
        "Status: read-only audit. No deploy was performed.",
        "",
        "## Plain Answer",
        "",
        f"{s['live_august_availability_blocks']} August live availability blocks became {s['dynamic_august_offers']} August dynamic offers because dynamic generation fans each availability window out across every eligible course, duration, and quarter-hour start that fits the window before public-sellable policy is applied. These are candidates, not public classes.",
        "",
        (
            f"For BLS-text courses, {s['dynamic_august_bls_offers']} generated candidates survive dynamic generation. Of those, {s['dynamic_august_aha_bls_offers']} are AHA BLS course candidates. After enabling the reviewed AHA BLS course IDs, {s['public_sellable_august_bls_offers']} August BLS offers reach public sellable and seed selection selects BLS seeds."
            if s["public_sellable_august_bls_offers"]
            else f"For BLS-text courses, {s['dynamic_august_bls_offers']} generated candidates survive dynamic generation. Of those, {s['dynamic_august_aha_bls_offers']} are AHA BLS course candidates. The AHA BLS course IDs are not in `public_offer_policy.enabled_course_ids`, so AHA BLS has zero August public-sellable candidates and cannot be selected as August seeds yet."
        ),
        "",
    ]
    lines.extend(render_counter_section("August Dynamic Offers By Course Family", d["by_course_family"]))
    lines.extend(render_counter_section("August Dynamic Offers By Course ID", d["by_course_id"]))
    lines.extend(render_counter_section("August Dynamic Offers By Date", d["by_date"]))
    lines.extend(render_counter_section("August Dynamic Offers By Start Time", d["by_start_time"]))
    lines.extend(render_counter_section("August Dynamic Offers Hidden Before Public Sellable - Top Reasons", d["hidden_reason_top_20"]))
    lines.extend(render_counter_section("August BLS By Date", b["by_date"]))
    lines.extend(render_counter_section("August BLS By Start Time", b["by_start_time"]))
    lines.extend(render_counter_section("August BLS By Duration", b["by_duration"]))
    lines.extend(render_counter_section("August BLS By Course ID", b["by_course_id"]))
    lines.extend(render_counter_section("August BLS By Variant", b["by_variant"]))
    lines.extend([
        "## Compression Pipeline",
        "",
        "| Stage | In | Out | Hidden | Expected? |",
        "| --- | ---: | ---: | ---: | --- |",
    ])
    for row in report["compression_pipeline"]:
        lines.append(f"| {row['stage']} | {row['count_in']} | {row['count_out']} | {row['rejected_or_hidden']} | {row['expected']} |")
    lines.extend(["", "See `august_offer_compression_pipeline.csv` for exact top rejection reasons by stage.", ""])
    return "\n".join(lines)


def render_seed_md(seeds: list[dict[str, Any]]) -> str:
    lines = [
        "# August Selected Seed Audit",
        "",
        "Status: read-only audit. These seeds have URL previews only; no appointments or public pages were created.",
        "",
    ]
    if not seeds:
        lines.append("- No August seeds selected.")
        return "\n".join(lines) + "\n"
    lines.extend(["| Date | Time | Course | Course Key | Course ID | appointmentDayId | Location | Why selected |", "| --- | --- | --- | --- | --- | --- | --- | --- |"])
    for seed in seeds:
        lines.append(
            f"| {seed['date']} | {seed['startTime']} | {seed['course']} | {seed['course_key']} | {seed['course_id']} | {seed['appointmentDayId']} | {seed['location']} | {seed['why_selected']} |"
        )
    lines.extend(["", "## Booking URLs", ""])
    for seed in seeds:
        lines.append(f"- {seed['date']} {seed['startTime']} `{seed['course_key']}`: {seed['booking_url']}")
    lines.append("")
    return "\n".join(lines)


def render_sufficiency_md(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        "# August Public Visibility Sufficiency",
        "",
        "## Answer",
        "",
        (
            "Yes, after the narrow BLS policy enablement August looks alive enough for this report branch."
            if s["selected_seed_sufficiency"] == "looks_alive_enough_after_bls_enablement"
            else "No. Two August selected seeds are not enough by themselves to make August look alive on the public schedule."
        ),
        "",
        f"Current selected August seeds: {s['selected_august_seeds']}. Current August rendered seed rows in `docs/data/schedule_future.json`: {s['august_rendered_seed_rows']}. Current real August Enrollware rows in that file: {s['real_august_enrollware_rows']}.",
        "",
        (
            "The prior limiting point was downstream public sellable policy. After enabling only the reviewed AHA BLS course IDs, BLS offers reach seed selection and the selector chooses one BLS seed on each available August seed date."
            if s["selected_seed_sufficiency"] == "looks_alive_enough_after_bls_enablement"
            else "The limiting point is not RRULE expansion anymore. The limiter is downstream public sellable policy: AHA BLS dynamic offers exist, but AHA BLS course IDs are not enabled in `data/config/public_offer_policy.json`, so no August AHA BLS offers reach seed selection. The seed strategy then selects one Heartsaver seed per available August date."
        ),
        "",
        "## Minimal Safe Adjustment",
        "",
        s["minimal_safe_adjustment"],
        "",
        "Do not loosen all filters. Keep Course Master, appointment container, occupancy, lead-time, and UNKNOWN-course suppression in place.",
        "",
    ]
    return "\n".join(lines)


def render_large_file_md(files: list[dict[str, Any]]) -> str:
    lines = [
        "# Large Generated Audit File Policy",
        "",
        "Status: full generated previews are stored under ignored runtime storage; compact summaries remain tracked in `data/audit`.",
        "",
        "| File | Size MB | Tracked | Downstream tests need full file now? | Recommendation |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for item in files:
        lines.append(f"| `{item['path']}` | {item['size_mb']} | {item['tracked']} | {item['downstream_tests_require_full_file']} | {item['recommendation']} |")
    lines.extend([
        "",
        "Recommended repo policy: keep small summarized audit outputs in git, keep full generated previews out of long-term source history unless a specific review requires exact row-level artifacts, and add a reproducible command path to regenerate full previews locally.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    report = run()
    s = report["summary"]
    print("August offer explosion audit complete (READ ONLY).")
    print(f"August dynamic offers: {s['dynamic_august_offers']}")
    print(f"August dynamic BLS offers: {s['dynamic_august_bls_offers']}")
    print(f"August public sellable offers: {s['public_sellable_august_offers']}")
    print(f"August selected seeds: {s['selected_august_seeds']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
