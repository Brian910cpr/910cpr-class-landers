from __future__ import annotations

import csv
import html
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data" / "audit"
RAW_CLASSES = ROOT / "data" / "raw" / "classes_raw_live.csv"
PAGES = [
    "docs/bls.html",
    "docs/acls.html",
    "docs/pals.html",
    "docs/courses/heartsaver-first-aid-cpr-aed.html",
    "docs/courses/heartsaver-cpr-aed.html",
    "docs/courses/heartsaver-pediatric-first-aid-cpr-aed.html",
    "docs/heartsaver.html",
    "docs/hsi.html",
    "docs/arc.html",
]
PIPELINE_FILES = {
    "dynamic_offers": "data/audit/dynamic_offers_preview.json",
    "public_sellable": "data/audit/public_sellable_offers_preview.json",
    "schedule_seeds": "data/audit/schedule_seeds_preview.json",
    "seed_url_preview": "data/audit/seed_appointment_url_preview.json",
    "internal_dynamic_seed_preview": "data/audit/internal_dynamic_seed_preview.json",
    "presentation_policy": "data/audit/dynamic_offer_presentation_policy_report.json",
    "rendered_proof": "data/audit/rendered_dynamic_offer_proof.json",
    "schedule_future": "docs/data/schedule_future.json",
    "sessions_current": "data/sessions_current.json",
    "slug_hubs": "data/config/slug_hubs.json",
    "course_catalog": "data/config/course_catalog.json",
    "course_map": "data/config/course_map.json",
}


def clean(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", clean(value).lower()).strip("_")


def read_json(path: str) -> Any:
    p = ROOT / path
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def parse_attrs(text: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for key, quote, value in re.findall(r"([\w:-]+)\s*=\s*(['\"])(.*?)\2", text, flags=re.S):
        attrs[key] = html.unescape(value)
    return attrs


def parse_dt(value: Any) -> datetime | None:
    text = clean(value)
    if not text:
        return None
    for fmt in ("%m/%d/%Y %I:%M %p", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def date_key(value: Any) -> str:
    dt = parse_dt(value)
    return dt.date().isoformat() if dt else clean(value)[:10]


def time_key(value: Any) -> str:
    dt = parse_dt(value)
    return dt.strftime("%H:%M") if dt else clean(value)


def load_class_report() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    with RAW_CLASSES.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            cid = clean(row.get("Internal ID"))
            start = parse_dt(row.get("Class Times Start Time"))
            normalized = {
                "class_id": cid,
                "course_name": clean(row.get("Course Name")),
                "course_id": clean(row.get("Course Id")),
                "registration_link": clean(row.get("Registration Link")),
                "location_name": clean(row.get("Location Name")),
                "price": clean(row.get("Price")),
                "start_datetime": start.isoformat() if start else clean(row.get("Class Times Start Time")),
                "date": start.date().isoformat() if start else date_key(row.get("Class Times Start Time")),
                "time": start.strftime("%H:%M") if start else time_key(row.get("Class Times Start Time")),
                "lead_instructor": clean(row.get("Lead Instructor Name")),
            }
            rows.append(normalized)
            if cid and cid not in by_id:
                by_id[cid] = normalized
    schedule_future = read_json("docs/data/schedule_future.json")
    for session in json_rows(schedule_future):
        sid = clean(session.get("session_id"))
        start = parse_dt(session.get("start_at"))
        normalized = {
            "class_id": sid,
            "course_name": clean(session.get("course_name") or session.get("official_course_name")),
            "course_id": clean(session.get("course_id")),
            "registration_link": clean(session.get("registration_url")),
            "location_name": clean(session.get("location_name") or session.get("location_display")),
            "price": clean(session.get("price")),
            "start_datetime": start.isoformat() if start else clean(session.get("start_at")),
            "date": start.date().isoformat() if start else date_key(session.get("start_at")),
            "time": start.strftime("%H:%M") if start else time_key(session.get("start_at")),
            "lead_instructor": clean(session.get("lead_instructor_name")),
            "class_report_source": "docs/data/schedule_future.json",
        }
        rows.append(normalized)
        if sid:
            by_id[sid] = normalized
    return rows, by_id


def visible_url(page: str) -> str:
    short = page.removeprefix("docs/").replace("\\", "/")
    return "/" + short


def page_course_key(page: str, subtitle: str) -> str:
    p = page.lower()
    if "bls" in p and "heartcode" not in p:
        return "aha_bls"
    if "acls" in p:
        return "aha_acls"
    if "pals" in p:
        return "aha_pals"
    if "heartsaver-first-aid-cpr-aed" in p:
        return "aha_heartsaver_first_aid_cpr_aed"
    if "heartsaver-cpr-aed" in p:
        return "aha_heartsaver_cpr_aed"
    if "pediatric" in p:
        return "aha_heartsaver_pediatric_first_aid_cpr_aed"
    if "hsi" in p:
        return "hsi"
    if "arc" in p:
        return "arc"
    return norm(subtitle) or "unknown"


def extract_articles(page: str) -> list[dict[str, Any]]:
    path = ROOT / page
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    rows: list[dict[str, Any]] = []
    for match in re.finditer(r"<article\b(?P<attrs>[^>]*)>(?P<body>.*?)</article>", text, flags=re.S | re.I):
        attrs = parse_attrs(match.group("attrs"))
        body = match.group("body")
        if "slug-pill" not in attrs.get("class", ""):
            continue
        links = re.findall(r"<a\b([^>]*)>(.*?)</a>", body, flags=re.S | re.I)
        link_attrs = parse_attrs(links[-1][0]) if links else {}
        link_text = clean(links[-1][1]) if links else ""
        href = html.unescape(link_attrs.get("data-original-href") or link_attrs.get("href") or "")
        parsed = urlparse(href)
        q = parse_qs(parsed.query)
        subtitle = clean(re.search(r'class="slug-pill-subtitle"[^>]*>(.*?)</div>', body, flags=re.S).group(1)) if re.search(r'class="slug-pill-subtitle"[^>]*>(.*?)</div>', body, flags=re.S) else ""
        chips = [clean(item) for item in re.findall(r'class="slug-pill-chip[^"]*"[^>]*>(.*?)</span>', body, flags=re.S)]
        location = next((chip for chip in chips if "NC -" in chip or "@" in chip), "")
        time_text = chips[0] if chips else ""
        row = {
            "visible_page_url": visible_url(page),
            "page_path": page,
            "course_display_name": subtitle,
            "normalized_course_key": page_course_key(page, subtitle),
            "date": date_key(attrs.get("data-start") or attrs.get("data-session-start")),
            "time": time_text,
            "location_town": location,
            "visible_button_text": link_text,
            "visible_booking_check_url": href,
            "session_id": attrs.get("data-session-id") or clean((q.get("id") or [""])[0]),
            "appointmentDayId": clean((q.get("appointmentDayId") or [""])[0]),
            "courseId": clean((q.get("courseId") or [""])[0]),
            "source_offer_id": attrs.get("data-source-offer-id", ""),
            "render_source": attrs.get("data-render-source", ""),
            "presentation_mode": attrs.get("data-presentation-mode", ""),
            "row_source": "unknown",
            "confidence": "low",
            "notes": "",
        }
        rows.append(row)
    return rows


def classify_visible_rows(rows: list[dict[str, Any]], class_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    for row in rows:
        sid = row.get("session_id")
        if sid and sid in class_by_id:
            row["row_source"] = "existing_enrollware_class"
            row["confidence"] = "high"
            row["matching_class_report_row"] = sid
            row["enrollware_class_session_id"] = sid
            row["class_report_source"] = class_by_id[sid].get("class_report_source", "data/raw/classes_raw_live.csv")
            row["notes"] = "Visible row session ID matches latest Class Report."
        elif row.get("appointmentDayId"):
            row["row_source"] = "appointment_seed"
            row["confidence"] = "high" if row.get("source_offer_id") else "medium"
            row["matching_class_report_row"] = ""
            row["enrollware_class_session_id"] = ""
            row["seed_source_file"] = "data/audit/dynamic_offer_presentation_policy_report.json"
            row["dynamic_offer_source_file"] = "data/audit/public_sellable_offers_preview.json"
            row["notes"] = "AppointmentDayId URL, not an enroll?id class URL."
        elif "request" in row.get("visible_button_text", "").lower():
            row["row_source"] = "request_only"
            row["confidence"] = "medium"
            row["matching_class_report_row"] = ""
            row["notes"] = "Request-style CTA without final Enrollware class ID."
        else:
            row["row_source"] = "unknown"
            row["matching_class_report_row"] = ""
            row["notes"] = "No Class Report ID or appointmentDayId detected."
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, Any]], fields: list[str], limit: int | None = None) -> str:
    selected = rows[:limit] if limit else rows
    lines = ["| " + " | ".join(fields) + " |", "|" + "|".join(["---"] * len(fields)) + "|"]
    for row in selected:
        lines.append("| " + " | ".join(clean(row.get(field)).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(lines)


def course_counts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["normalized_course_key"]].append(row)
    out = []
    for key, items in sorted(grouped.items()):
        out.append({
            "course_key": key,
            "total_visible_rows": len(items),
            "visible_rows_matching_class_report": sum(1 for r in items if r.get("row_source") == "existing_enrollware_class"),
            "visible_rows_not_found_in_class_report": sum(1 for r in items if r.get("row_source") != "existing_enrollware_class"),
            "visible_rows_with_enroll_id_links": sum(1 for r in items if "enroll?id=" in r.get("visible_booking_check_url", "")),
            "visible_rows_with_appointmentDayId_links": sum(1 for r in items if "appointmentDayId=" in r.get("visible_booking_check_url", "")),
            "visible_rows_with_check_request_cta": sum(1 for r in items if re.search(r"check|request", r.get("visible_button_text", ""), re.I)),
            "unknown_rows": sum(1 for r in items if r.get("row_source") == "unknown"),
        })
    return out


def json_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("offers", "render_offers", "sessions", "approved_seed_offers", "selected_seeds"):
            if isinstance(payload.get(key), list):
                return [row for row in payload[key] if isinstance(row, dict)]
    return []


def count_august(rows: list[dict[str, Any]], course_match: str) -> dict[str, Any]:
    relevant = []
    for row in rows:
        text = json.dumps(row, default=str).lower()
        date_text = clean(row.get("date") or row.get("start_datetime") or row.get("start_at") or row.get("Class Times Start Time") or row.get("public_display_start"))
        if "2026-08" in date_text and course_match.lower() in text:
            relevant.append(row)
    return {"total": len(rows), "august_matching_rows": len(relevant)}


def build_pipeline_counts(class_rows: list[dict[str, Any]], visible_rows: list[dict[str, Any]], course_label: str) -> list[dict[str, Any]]:
    rows = []
    class_aug = [r for r in class_rows if r["date"].startswith("2026-08") and course_label.lower() in (r["course_name"] + " " + r["course_id"]).lower()]
    visible_aug = [r for r in visible_rows if r["date"].startswith("2026-08") and course_label.lower().split()[0] in r["course_display_name"].lower()]
    rows.append({"stage": "raw_class_report", "input_files": "data/raw/classes_raw_live.csv", "output_files": "", "total_count": len(class_rows), "august_count": len(class_aug), "notes": "Existing Enrollware class safety-net rows."})
    rows.append({"stage": "visible_rendered_pages", "input_files": "; ".join(PAGES), "output_files": "docs/*.html", "total_count": len(visible_rows), "august_count": len(visible_aug), "notes": "Rows parsed from customer-facing stacked pages."})
    for stage, rel in PIPELINE_FILES.items():
        payload = read_json(rel)
        stage_rows = json_rows(payload)
        counts = count_august(stage_rows, course_label)
        rows.append({"stage": stage, "input_files": rel, "output_files": rel, "total_count": counts["total"], "august_count": counts["august_matching_rows"], "notes": "File missing or non-row output." if payload is None else ""})
    return rows


def find_copy_issues() -> list[dict[str, Any]]:
    patterns = ["appointment-backed", "request-based scheduling", "real scheduled options show first", "dynamic offer", "seeded", "public sellable", "internal dynamic", "Check this date/time"]
    findings = []
    for path in list((ROOT / "docs").rglob("*.html")) + list((ROOT / "data").rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for pattern in patterns:
            if pattern.lower() in text.lower():
                findings.append({
                    "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "term": pattern,
                    "proposed_replacement": "Need another date? We may be able to schedule a private, workplace, or small-group class." if pattern != "Check this date/time" else "Use consistently only for traceable appointment-backed rows; otherwise use Request a class time.",
                })
    return findings


def seo_snapshot() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sitemap = ROOT / "docs" / "sitemap.xml"
    urls = re.findall(r"<loc>(.*?)</loc>", sitemap.read_text(encoding="utf-8", errors="ignore")) if sitemap.exists() else []
    pages = []
    for url in urls:
        rel = url.replace("https://www.910cpr.com/", "docs/")
        p = ROOT / rel
        text = p.read_text(encoding="utf-8", errors="ignore") if p.exists() and p.is_file() else ""
        noindex = bool(re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', text, re.I))
        pages.append({"url": url, "path": rel, "exists": p.exists(), "noindex": noindex, "preserve_recommendation": "preserve_or_redirect" if any(k in url for k in ["bls", "acls", "pals", "heartsaver", "cpr", "first-aid", "index"]) else "review"})
    gsc_files = [str(p.relative_to(ROOT)).replace("\\", "/") for p in ROOT.rglob("*") if re.search(r"(gsc|search.console|queries|pages).*\\.(csv|xlsx|json)$", p.name, re.I)]
    return pages, [{"gsc_export_file": item} for item in gsc_files]


def main() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    class_rows, class_by_id = load_class_report()
    visible_rows = []
    for page in PAGES:
        visible_rows.extend(extract_articles(page))
    visible_rows = classify_visible_rows(visible_rows, class_by_id)

    visible_fields = ["visible_page_url", "course_display_name", "normalized_course_key", "date", "time", "location_town", "visible_button_text", "visible_booking_check_url", "row_source", "matching_class_report_row", "enrollware_class_session_id", "appointmentDayId", "courseId", "seed_source_file", "dynamic_offer_source_file", "confidence", "notes"]
    write_csv(AUDIT / "visible_row_source_audit.csv", visible_rows, visible_fields)
    (AUDIT / "visible_row_source_audit.json").write_text(json.dumps({"rows": visible_rows, "counts": Counter(r["row_source"] for r in visible_rows)}, indent=2), encoding="utf-8")
    (AUDIT / "visible_row_source_audit.md").write_text("# Visible Row Source Audit\n\n" + markdown_table(visible_rows, visible_fields, 200) + "\n", encoding="utf-8")

    counts = course_counts(visible_rows)
    write_csv(AUDIT / "class_report_visibility_comparison.csv", counts)
    lines = ["# Class Report Visibility Comparison", "", "## Counts By Course", "", markdown_table(counts, list(counts[0].keys()) if counts else [])]
    key_checks = []
    for label, times in [("BLS", ["09:15", "12:30", "18:15", "18:45"]), ("Heartsaver First Aid CPR AED", ["09:15", "18:15"]), ("ACLS/PALS", ["14:00"])]:
        found = [r for r in visible_rows if any(t in r["time"] for t in times) and (label.split("/")[0].lower() in (r["course_display_name"] + r["normalized_course_key"]).lower() or label == "ACLS/PALS")]
        key_checks.append({"check": label, "times": ", ".join(times), "visible_rows": len(found), "class_report_matches": sum(1 for r in found if r["row_source"] == "existing_enrollware_class"), "appointment_rows": sum(1 for r in found if r["row_source"] == "appointment_seed")})
    lines.extend(["", "## Requested Time Checks", "", markdown_table(key_checks, ["check", "times", "visible_rows", "class_report_matches", "appointment_rows"])])
    (AUDIT / "class_report_visibility_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    check_rows = [r for r in visible_rows if "Check this date/time" in r.get("visible_button_text", "") or (r["date"] == "2026-07-04" and r["appointmentDayId"])]
    trace = {"rows": check_rows, "verdict": "July 4 check rows are appointment_seed rows emitted by dynamic_offer_presentation_policy/build_slug_hubs, not Class Report enroll?id rows.", "recommendation": "Keep only if appointment seed pipeline remains traceable and proof passes; otherwise hide/disable seeded rows until valid."}
    (AUDIT / "heartsaver_check_row_trace.json").write_text(json.dumps(trace, indent=2), encoding="utf-8")
    (AUDIT / "heartsaver_check_row_trace.md").write_text("# Heartsaver July 4 Check Row Trace\n\n" + markdown_table(check_rows, visible_fields, 100) + "\n\n" + trace["verdict"] + "\n", encoding="utf-8")

    bls_counts = build_pipeline_counts(class_rows, visible_rows, "BLS")
    hs_counts = build_pipeline_counts(class_rows, visible_rows, "Heartsaver")
    write_csv(AUDIT / "bls_august_pipeline_counts.csv", bls_counts)
    write_csv(AUDIT / "heartsaver_august_pipeline_counts.csv", hs_counts)
    august = {"bls": bls_counts, "heartsaver": hs_counts, "filtering_causes_to_review": ["date window too short", "seed output not consumed by pages", "missing appointmentDayId", "course_key mismatch", "stale generated output", "inside_minimum_lead_time"]}
    (AUDIT / "august_seed_visibility_trace.json").write_text(json.dumps(august, indent=2), encoding="utf-8")
    (AUDIT / "august_seed_visibility_trace.md").write_text("# August Seed Visibility Trace\n\n## BLS Pipeline\n\n" + markdown_table(bls_counts, list(bls_counts[0].keys())) + "\n\n## Heartsaver Pipeline\n\n" + markdown_table(hs_counts, list(hs_counts[0].keys())) + "\n", encoding="utf-8")

    model = {
        "recommended_output": "data/public/course_location_inventory.json",
        "status": "proposal",
        "row_sources": ["existing_enrollware_class", "appointment_seed", "dynamic_offer", "anchor_class", "request_only"],
        "fields": ["course_key", "course_display_name", "course_family", "town", "location_name", "start_datetime_local", "end_datetime_local", "display_date", "display_time", "row_source", "booking_url", "button_text", "price", "public_status", "reason_if_hidden", "sort_order", "source_file", "source_id", "confidence"],
    }
    (AUDIT / "unified_inventory_model_recommendation.json").write_text(json.dumps(model, indent=2), encoding="utf-8")
    (AUDIT / "unified_inventory_model_recommendation.md").write_text("# Unified Inventory Model Recommendation\n\nUse a single `course_location_inventory` artifact that merges Class Report rows first, then traceable appointment/dynamic/request rows. Public pages render stacked rows from this one model while preserving internal `row_source` metadata.\n\n```json\n" + json.dumps(model, indent=2) + "\n```\n", encoding="utf-8")

    heartsaver_expl = """# Heartsaver vs BLS/ACLS/PALS Pipeline Explanation

Heartsaver grouping is primarily defined in `data/config/slug_hubs.json`, `scripts/build_slug_hubs.py`, `data/config/course_catalog.json`, and `data/config/course_map.json`.

BLS/ACLS/PALS grouping is also defined in `data/config/slug_hubs.json` and rendered through `scripts/build_slug_hubs.py`, but those families are simpler tab structures around provider/renewal/HeartCode paths.

Heartsaver has more buyer variants: CPR AED only, First Aid CPR AED, pediatric options, online+skills, classroom, group/workplace, and adjacent HSI/ARC alternatives. That explains the extra guidance, but it should still render from the same stacked inventory model: course/date/time/location/button.

Current Heartsaver check/request behavior is real appointment-seed output when it has `appointmentDayId` links and `data-source-offer-id`, but it is not broad August coverage. It should be treated as a growth layer, not the August safety net.
"""
    (AUDIT / "heartsaver_vs_bls_pipeline_explanation.md").write_text(heartsaver_expl, encoding="utf-8")

    copy_findings = find_copy_issues()
    (AUDIT / "customer_copy_cleanup_report.md").write_text("# Customer Copy Cleanup Report\n\n" + markdown_table(copy_findings, ["path", "term", "proposed_replacement"], 300) + "\n", encoding="utf-8")

    arch = {
        "homepage_blocks": ["AHA BLS", "AHA ACLS", "AHA PALS", "AHA First Aid / CPR / AED", "HSI / Red Cross", "Group / Onsite Training"],
        "principles": ["Preserve existing SEO URLs", "Use course/location pages for primary buyer path", "Real Enrollware rows first", "Seeded/requestable rows only when traceable"],
    }
    (AUDIT / "simplified_course_location_architecture.json").write_text(json.dumps(arch, indent=2), encoding="utf-8")
    (AUDIT / "simplified_course_location_architecture.md").write_text("# Simplified Course/Location Architecture\n\nThe public path should be course/location pages with stacked rows. Preserve current ranking URLs and introduce new city-specific URLs only with redirect/internal-link planning.\n", encoding="utf-8")
    url_rows = [
        {"current_url": "/bls.html", "proposed_role": "preserve family hub", "future_url": "/aha-bls-wilmington-nc/", "redirect": "no immediate redirect"},
        {"current_url": "/acls.html", "proposed_role": "preserve family hub", "future_url": "/aha-acls-wilmington-nc/", "redirect": "no immediate redirect"},
        {"current_url": "/pals.html", "proposed_role": "preserve family hub", "future_url": "/aha-pals-wilmington-nc/", "redirect": "no immediate redirect"},
        {"current_url": "/courses/heartsaver-first-aid-cpr-aed.html", "proposed_role": "preserve course page", "future_url": "/aha-first-aid-cpr-aed-wilmington-nc/", "redirect": "only if replaced"},
    ]
    write_csv(AUDIT / "proposed_url_map.csv", url_rows)
    (AUDIT / "implementation_phases.md").write_text("# Implementation Phases\n\n1. Keep current pages and audit source labels.\n2. Build unified inventory artifact.\n3. Render stacked rows from unified inventory.\n4. Add city-specific links while preserving current URLs.\n5. Only then consider redirects.\n", encoding="utf-8")

    pages, gsc = seo_snapshot()
    (AUDIT / "seo_authority_snapshot.md").write_text("# SEO Authority Snapshot\n\nGSC exports found: " + (", ".join(g["gsc_export_file"] for g in gsc) or "none found in repo") + "\n\n" + markdown_table(pages, ["url", "path", "exists", "noindex", "preserve_recommendation"], 300) + "\n", encoding="utf-8")
    write_csv(AUDIT / "migration_protection_map.csv", pages, ["url", "path", "exists", "noindex", "preserve_recommendation"])
    redirect_rows = [{"url": row["url"], "priority": "high" if row["preserve_recommendation"] == "preserve_or_redirect" else "review", "redirect_target": "preserve current URL unless replacement is explicitly approved"} for row in pages]
    write_csv(AUDIT / "redirect_priority_report.csv", redirect_rows)
    (AUDIT / "redirect_priority_report.md").write_text("# Redirect Priority Report\n\n" + markdown_table(redirect_rows, ["url", "priority", "redirect_target"], 300) + "\n", encoding="utf-8")

    safe_plan = """# Minimum Safe Fix Plan

1. Keep real Enrollware class rows as the public schedule safety net.
2. Do not rely on seeded/requestable rows for August until the pipeline shows August rows with source metadata and proof.
3. If August Class Report rows are sparse, manually create enough August Enrollware classes for BLS and Heartsaver Wilmington.
4. Hide seeded/requestable rows that lack traceable `appointmentDayId`, `courseId`, source offer ID, and rendered proof.
5. Replace customer-facing internal copy with: "Need another date? We may be able to schedule a private, workplace, or small-group class."
6. Build a unified `course_location_inventory` artifact and make stacked pages consume it.
7. Preserve current SEO URLs; add city-specific pages as linked supplements before any redirects.
"""
    (AUDIT / "minimum_safe_fix_plan.md").write_text(safe_plan, encoding="utf-8")
    print("Wrote stacked inventory/August audit reports")


if __name__ == "__main__":
    main()
