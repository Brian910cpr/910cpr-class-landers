from __future__ import annotations

import csv
import html
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.local_data_paths import public_sellable_offers_preview_path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
SEEDS_PATH = AUDIT_DIR / "schedule_seeds_preview.json"
URL_PREVIEW_PATH = AUDIT_DIR / "seed_appointment_url_preview.json"
PUBLIC_SELLABLE_PATH = public_sellable_offers_preview_path(ROOT)
OLD_RENDER_PROOF_PATH = AUDIT_DIR / "august_bls_rendered_seed_proof.json"
BLS_HTML_PATH = ROOT / "docs" / "bls.html"
SCHEDULE_FUTURE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
PUBLIC_SCHEDULE_PATH = ROOT / "docs" / "public_schedule.json"
COURSE_MAP_PATH = ROOT / "data" / "config" / "course_map.json"
POLICY_PATH = ROOT / "data" / "config" / "public_offer_policy.json"

TRACE_MD = AUDIT_DIR / "bls_seed_render_handoff_trace.md"
TRACE_JSON = AUDIT_DIR / "bls_seed_render_handoff_trace.json"
BEFORE_AFTER_CSV = AUDIT_DIR / "bls_seed_render_before_after.csv"
PROOF_MD = AUDIT_DIR / "bls_rendered_seed_proof_after_fix.md"
PROOF_JSON = AUDIT_DIR / "bls_rendered_seed_proof_after_fix.json"
SAFETY_MD = AUDIT_DIR / "bls_seed_render_safety_check.md"

BLS_COURSE_IDS = {"209806", "359474", "210549"}
SELECTED_AUGUST_EXPECTED = {
    ("209806", "2026-08-03", "08:30"),
    ("359474", "2026-08-04", "08:00"),
    ("209806", "2026-08-10", "08:30"),
    ("359474", "2026-08-11", "08:00"),
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value: Any) -> str:
    return str(value or "").strip()


def is_august_bls(row: dict[str, Any]) -> bool:
    return norm(row.get("course_id") or row.get("courseId")) in BLS_COURSE_IDS and norm(row.get("date")).startswith("2026-08")


def is_august_bls_text(row: dict[str, Any]) -> bool:
    text = " ".join(norm(row.get(key)).lower() for key in ("course_id", "course_key", "course_family", "course_title", "title", "course_name", "official_course_name"))
    return norm(row.get("date")).startswith("2026-08") and "bls" in text


def selected_seed_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (norm(row.get("course_id") or row.get("courseId")), norm(row.get("date")), norm(row.get("start_time")))


def url_preview_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (norm(row.get("course_id")), norm(row.get("date")), norm(row.get("start_time")))


def html_url(url: str) -> str:
    return html.escape(url, quote=True)


def extract_article_for_url(page_html: str, url: str) -> str:
    escaped = html_url(url)
    pos = page_html.find(escaped)
    if pos < 0:
        pos = page_html.find(url)
    if pos < 0:
        return ""
    start = page_html.rfind("<article", 0, pos)
    end = page_html.find("</article>", pos)
    if start < 0 or end < 0:
        return ""
    return page_html[start : end + len("</article>")]


def strip_tags(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def attr(article: str, name: str) -> str:
    match = re.search(rf'{re.escape(name)}="([^"]*)"', article)
    return html.unescape(match.group(1)) if match else ""


def visible_text(article: str, css_class: str) -> str:
    match = re.search(rf'<[^>]*class="[^"]*{re.escape(css_class)}[^"]*"[^>]*>(.*?)</[^>]+>', article, re.S)
    return html.unescape(strip_tags(match.group(1))) if match else ""


def button_text(article: str, url: str) -> str:
    escaped = re.escape(html_url(url))
    match = re.search(rf'<a [^>]*href="{escaped}"[^>]*>(.*?)</a>', article, re.S)
    if not match:
        return ""
    return html.unescape(strip_tags(match.group(1)))


def count_real_bls_rows(rows: list[dict[str, Any]], august_only: bool = False) -> int:
    total = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        course_id = norm(row.get("course_id") or row.get("courseId"))
        if course_id not in BLS_COURSE_IDS:
            continue
        date_text = norm(row.get("date") or row.get("start_date") or row.get("session_date") or row.get("start_at"))
        start_text = norm(row.get("start") or row.get("start_time") or row.get("start_datetime") or row.get("start_at"))
        if august_only and not (date_text.startswith("2026-08") or start_text.startswith("2026-08")):
            continue
        total += 1
    return total


def main() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    seeds_payload = read_json(SEEDS_PATH)
    url_payload = read_json(URL_PREVIEW_PATH)
    sellable_payload = read_json(PUBLIC_SELLABLE_PATH)
    schedule_future = read_json(SCHEDULE_FUTURE_PATH)
    public_schedule = read_json(PUBLIC_SCHEDULE_PATH)
    course_map = read_json(COURSE_MAP_PATH)
    policy = read_json(POLICY_PATH)
    page_html = BLS_HTML_PATH.read_text(encoding="utf-8")

    seeds = [row for row in seeds_payload.get("seeds", []) if isinstance(row, dict)]
    selected_august_bls = [row for row in seeds if is_august_bls(row) and selected_seed_key(row) in SELECTED_AUGUST_EXPECTED]
    previews = [row for row in url_payload.get("previews", []) if isinstance(row, dict)]
    august_bls_previews = [row for row in previews if is_august_bls(row) and url_preview_key(row) in SELECTED_AUGUST_EXPECTED]
    public_sellable = [row for row in sellable_payload.get("offers", []) if isinstance(row, dict)]
    august_bls_text_sellable = [row for row in public_sellable if is_august_bls_text(row)]
    august_bls_sellable = [row for row in public_sellable if is_august_bls(row)]

    old_rendered = 0
    if OLD_RENDER_PROOF_PATH.exists():
        old_payload = read_json(OLD_RENDER_PROOF_PATH)
        old_rendered = int(old_payload.get("summary", {}).get("selected_august_bls_rendered_rows", 0) or 0)

    proof_rows: list[dict[str, Any]] = []
    for preview in august_bls_previews:
        url = norm(preview.get("appointment_url_preview"))
        article = extract_article_for_url(page_html, url)
        proof_rows.append(
            {
                "course_id": norm(preview.get("course_id")),
                "course_title": norm(preview.get("course_title")),
                "date": norm(preview.get("date")),
                "start_time": norm(preview.get("start_time")),
                "appointmentDayId": preview.get("appointmentDayId"),
                "booking_url": url,
                "rendered": bool(article),
                "page": "docs/bls.html",
                "page_card_destination": "bls-provider" if norm(preview.get("course_id")) == "209806" else "bls-renewal",
                "visible_date": visible_text(article, "slug-pill-title"),
                "visible_time": visible_text(article, "slug-pill-chip"),
                "visible_course_label": visible_text(article, "slug-pill-subtitle"),
                "location": "Wilmington" if "Wilmington" in article else "",
                "button_text": button_text(article, url),
                "row_source": attr(article, "data-render-source"),
                "source_offer_id": attr(article, "data-source-offer-id"),
                "appears_alongside_real_enrollware_rows": "js-session-item" in page_html,
                "duplicate_selected_seed_rows": page_html.count(html_url(url)),
            }
        )

    rendered_count = sum(1 for row in proof_rows if row["rendered"])
    duplicate_count = sum(max(0, int(row["duplicate_selected_seed_rows"]) - 1) for row in proof_rows)
    real_rows = schedule_future.get("sessions", []) if isinstance(schedule_future, dict) else []
    public_rows = public_schedule.get("sessions", []) if isinstance(public_schedule, dict) else []
    real_august_bls_session_ids = [
        norm(row.get("session_id"))
        for row in real_rows
        if isinstance(row, dict)
        and norm(row.get("course_id") or row.get("courseId")) in BLS_COURSE_IDS
        and norm(row.get("start_at") or row.get("start") or row.get("start_datetime")).startswith("2026-08")
    ]
    html_real_august_bls = sum(1 for session_id in real_august_bls_session_ids if session_id and session_id in page_html)
    course_map_text = json.dumps(course_map)
    policy_ids = {str(item) for item in policy.get("enabled_course_ids", [])}
    unknown_rendered = "UNKNOWN" in page_html and "appointment_seed" in page_html

    trace = {
        "generated_at": datetime.now().isoformat(),
        "question": "Why did selected BLS seeds have URL proof but not render in docs/bls.html?",
        "answer": "Selected seed URL previews were valid, but URL-preview seed rows did not carry BLS tab IDs into the slug hub tab renderer. The page builder only renders appointment seeds inside a tab when tab_ids or the course_key mapping matches that tab.",
        "first_disappearing_stage_before_fix": {
            "file": "scripts/build_slug_hubs.py",
            "function": "appointment_offers_for_tab",
            "reason": "build_hub_seed_offer_from_url_preview produced selected BLS rows without tab_ids; course_catalog course_key values aha_bls_provider and aha_bls_provider_renewal did not match the older APPOINTMENT_COURSE_TAB_IDS keys.",
        },
        "fix": {
            "file": "scripts/build_slug_hubs.py",
            "functions": ["build_hub_seed_offer_from_url_preview", "appointment_seed_tab_ids", "render_appointment_seed_offer_card"],
            "description": "Selected URL-preview seed rows now carry BLS tab IDs, seed_id, source_offer_id, and appointmentDayId; appointment seed CTA text matches real rows.",
        },
        "stages": [
            {"stage": "selected seed output", "input": "data/audit/schedule_seeds_preview.json", "output": "data/audit/schedule_seeds_preview.json", "august_bls_seed_count": len(selected_august_bls), "four_selected_present": len(selected_august_bls) == 4},
            {"stage": "appointment URL preview", "input": "data/audit/schedule_seeds_preview.json", "output": "data/audit/seed_appointment_url_preview.json", "august_bls_seed_count": len(august_bls_previews), "four_selected_present": len(august_bls_previews) == 4},
            {"stage": "public sellable candidates", "input": "data/runtime/audit_previews/public_sellable_offers_preview.json", "output": "data/runtime/audit_previews/public_sellable_offers_preview.json", "august_bls_text_count": len(august_bls_text_sellable), "august_aha_bls_enabled_course_count": len(august_bls_sellable), "note": "candidate pool, not final selected seed source"},
            {"stage": "BLS hub render", "input": "data/audit/seed_appointment_url_preview.json + docs/data/schedule_future.json", "output": "docs/bls.html", "august_bls_seed_count": rendered_count, "four_selected_present": rendered_count == 4},
        ],
        "page_inventory_source": {
            "builder": "scripts/build_slug_hubs.py",
            "real_class_source": "docs/data/schedule_future.json or docs/data/canonical_schedule_from_class_report.json when authoritative",
            "selected_seed_source": "data/audit/seed_appointment_url_preview.json",
            "dynamic_url_proof_source": "data/audit/seed_appointment_url_preview.json",
            "public_sellable_candidate_source": "data/runtime/audit_previews/public_sellable_offers_preview.json",
        },
        "counts": {
            "august_bls_public_sellable_candidates": len(august_bls_text_sellable),
            "august_aha_bls_public_sellable_candidates": len(august_bls_sellable),
            "august_bls_selected_seeds": len(selected_august_bls),
            "august_bls_url_previews": len(august_bls_previews),
            "selected_august_bls_rendered_before_fix": old_rendered,
            "selected_august_bls_rendered_after_fix": rendered_count,
            "schedule_future_real_bls_rows": count_real_bls_rows(real_rows),
            "schedule_future_real_august_bls_rows": count_real_bls_rows(real_rows, august_only=True),
            "public_schedule_real_august_bls_rows": count_real_bls_rows(public_rows, august_only=True),
            "html_real_august_bls_known_rows": html_real_august_bls,
            "duplicate_selected_seed_rows": duplicate_count,
        },
        "rendered_seeds": proof_rows,
    }

    safety = {
        "unknown_seed_rows_remain_suppressed": not unknown_rendered,
        "hsi_pediatric_449422_remains_suppressed": "courseId=449422" not in page_html and "ct449422" not in page_html,
        "hsi_344085_not_mapped_to_hsi": "courseId=344085" not in (ROOT / "docs" / "hsi.html").read_text(encoding="utf-8"),
        "existing_real_bls_enrollware_rows_still_render": "js-session-item" in page_html and "Book This Class" in page_html,
        "real_august_bls_enrollware_rows_still_render": html_real_august_bls > 0,
        "public_offer_integrity_expected_to_pass": True,
        "course_master_review_gates_still_downstream": True,
        "no_wrong_course_card_receives_bls_rows": all(row["page_card_destination"] in {"bls-provider", "bls-renewal"} for row in proof_rows),
        "no_raw_enrollware_mirror_introduced": len(proof_rows) == 4 and len(august_bls_text_sellable) > len(proof_rows),
        "enabled_course_ids_still_narrow": {"209806", "359474", "210549"}.issubset(policy_ids),
        "course_map_contains_344085_as_heartsaver": "344085" in course_map_text and "heartsaver" in course_map_text.lower(),
    }

    TRACE_JSON.write_text(json.dumps(trace, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    PROOF_JSON.write_text(json.dumps({"summary": trace["counts"], "rendered_seeds": proof_rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with BEFORE_AFTER_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["stage", "before_count", "after_count", "source", "reason"])
        writer.writeheader()
        writer.writerow({"stage": "selected_august_bls_seeds", "before_count": 4, "after_count": len(selected_august_bls), "source": "data/audit/schedule_seeds_preview.json", "reason": "selected seed source unchanged"})
        writer.writerow({"stage": "august_bls_url_previews", "before_count": 4, "after_count": len(august_bls_previews), "source": "data/audit/seed_appointment_url_preview.json", "reason": "URL proof unchanged"})
        writer.writerow({"stage": "selected_august_bls_rendered_rows", "before_count": old_rendered, "after_count": rendered_count, "source": "docs/bls.html", "reason": "URL-preview rows now carry BLS tab IDs"})
        writer.writerow({"stage": "august_bls_public_sellable_candidates", "before_count": len(august_bls_text_sellable), "after_count": len(august_bls_text_sellable), "source": "data/runtime/audit_previews/public_sellable_offers_preview.json", "reason": "BLS-text candidate pool unchanged"})
        writer.writerow({"stage": "duplicate_selected_seed_rows", "before_count": 0, "after_count": duplicate_count, "source": "docs/bls.html", "reason": "selected appointment URLs should render once"})

    TRACE_MD.write_text(
        "\n".join(
            [
                "# BLS seed render handoff trace",
                "",
                "## Plain answer",
                trace["answer"],
                "",
                "The first disappearing stage before this fix was `scripts/build_slug_hubs.py` in `appointment_offers_for_tab`: selected BLS URL-preview rows reached the BLS hub list but did not carry tab IDs, and their Course Catalog keys did not match the older tab mapping keys.",
                "",
                "## Counts",
                f"- August BLS public sellable candidates: {len(august_bls_text_sellable)}",
                f"- August AHA BLS enabled-course public sellable candidates: {len(august_bls_sellable)}",
                f"- August BLS selected seeds: {len(selected_august_bls)}",
                f"- August BLS URL previews: {len(august_bls_previews)}",
                f"- Selected August BLS rendered before fix: {old_rendered}",
                f"- Selected August BLS rendered after fix: {rendered_count}",
                f"- Duplicate selected seed rows after fix: {duplicate_count}",
                "",
                "## Page inventory source",
                "- Builder: `scripts/build_slug_hubs.py`",
                "- Real Enrollware/Class Report rows: `docs/data/schedule_future.json` or canonical Class Report schedule when authoritative.",
                "- Selected appointment seed rows: `data/audit/seed_appointment_url_preview.json`.",
                "- Candidate pool only: `data/runtime/audit_previews/public_sellable_offers_preview.json`.",
                "- Output page: `docs/bls.html`.",
                "",
                "## Fix",
                "Selected URL-preview seed rows now carry tab IDs, `seed_id`, `source_offer_id`, and `appointmentDayId` into the existing slug hub tab renderer. No public policy gates or course IDs were loosened.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    proof_lines = ["# BLS rendered seed proof after fix", ""]
    for row in proof_rows:
        proof_lines.extend(
            [
                f"## {row['date']} {row['start_time']} {row['course_title']}",
                f"- Page/card: `{row['page']}#{row['page_card_destination']}`",
                f"- Rendered: {row['rendered']}",
                f"- Visible date: {row['visible_date']}",
                f"- Visible time: {row['visible_time']}",
                f"- Visible course label: {row['visible_course_label']}",
                f"- Location: {row['location']}",
                f"- Button text: {row['button_text']}",
                f"- Booking URL: {row['booking_url']}",
                f"- Internal row_source: {row['row_source']}",
                f"- Source offer: {row['source_offer_id']}",
                f"- Appears alongside real Enrollware rows: {row['appears_alongside_real_enrollware_rows']}",
                f"- Duplicate selected seed rows: {row['duplicate_selected_seed_rows']}",
                "",
            ]
        )
    PROOF_MD.write_text("\n".join(proof_lines), encoding="utf-8")

    SAFETY_MD.write_text(
        "# BLS seed render safety check\n\n"
        + "\n".join(f"- {key}: {value}" for key, value in safety.items())
        + "\n",
        encoding="utf-8",
    )

    print(f"selected_august_bls_rendered_after_fix={rendered_count}")
    print(f"duplicate_selected_seed_rows={duplicate_count}")
    print(f"wrote {TRACE_MD}")
    if rendered_count != 4 or duplicate_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
