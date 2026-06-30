from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
DYNAMIC_PATH = AUDIT_DIR / "dynamic_offers_preview.json"
SELLABLE_PATH = AUDIT_DIR / "public_sellable_offers_preview.json"
SEEDS_PATH = AUDIT_DIR / "schedule_seeds_preview.json"
SEED_POLICY_PATH = ROOT / "data" / "config" / "seed_strategy_policy.json"
REPORT_MD = AUDIT_DIR / "bls_preferred_time_cap_blocker_report.md"
REPORT_JSON = AUDIT_DIR / "bls_preferred_time_cap_blocker_report.json"
REJECTIONS_CSV = AUDIT_DIR / "bls_preferred_time_candidate_rejections.csv"
TRACE_MD = AUDIT_DIR / "bls_cap_ordering_trace.md"
RECOMMENDATION_MD = AUDIT_DIR / "bls_cap_ordering_recommendation.md"

PREFERRED_TIMES = ["09:15", "12:30", "18:15", "18:45"]
AHA_BLS_IDS = {"209806", "359474", "210549"}
CAP_REASONS = {
    "max_total_offers_per_day_exceeded",
    "max_offers_per_course_per_day_exceeded",
    "max_offers_per_course_per_week_exceeded",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value: Any) -> str:
    return str(value or "").strip()


def is_august(row: dict[str, Any]) -> bool:
    return norm(row.get("date") or row.get("start_at") or row.get("start_datetime")).startswith("2026-08")


def is_bls_like(row: dict[str, Any]) -> bool:
    text = " ".join(norm(row.get(key)).lower() for key in ("course_id", "course_key", "course_family", "course_title", "title", "course_name", "official_course_name"))
    return "bls" in text


def is_preferred_candidate(row: dict[str, Any]) -> bool:
    return is_august(row) and is_bls_like(row) and norm(row.get("start_time")) in PREFERRED_TIMES


def stage_for_reasons(reasons: list[str]) -> str:
    if any(reason in CAP_REASONS for reason in reasons):
        return "public_sellable_cap_limit"
    if any(reason in {"course_id_not_enabled", "course_family_disabled", "course_family_not_enabled", "course_id_disabled"} for reason in reasons):
        return "public_sellable_course_policy"
    if any("container" in reason or "location" in reason for reason in reasons):
        return "appointment_container_location_gate"
    if any("lead" in reason or "days_out" in reason or "hours" in reason for reason in reasons):
        return "date_window_lead_time_gate"
    if any("occupancy" in reason or "overlap" in reason for reason in reasons):
        return "occupancy_overlap_gate"
    return "public_sellable_base_gate"


def reason_bucket(reasons: list[str]) -> str:
    if any(reason == "max_offers_per_course_per_week_exceeded" for reason in reasons):
        return "weekly_cap"
    if any(reason == "max_total_offers_per_day_exceeded" for reason in reasons):
        return "day_cap"
    if any(reason == "max_offers_per_course_per_day_exceeded" for reason in reasons):
        return "course_day_cap"
    if any(reason in {"course_id_not_enabled", "course_family_disabled", "course_family_not_enabled", "course_id_disabled"} for reason in reasons):
        return "course_or_family_disabled"
    if any("container" in reason or "location" in reason for reason in reasons):
        return "location_or_container"
    if any("lead" in reason or "days_out" in reason for reason in reasons):
        return "date_window_or_lead_time"
    if any("occupancy" in reason or "overlap" in reason for reason in reasons):
        return "occupancy_or_overlap"
    return "other"


def main() -> None:
    dynamic = read_json(DYNAMIC_PATH)
    sellable = read_json(SELLABLE_PATH)
    seeds = read_json(SEEDS_PATH)
    seed_policy = read_json(SEED_POLICY_PATH)
    dynamic_rows = [row for row in dynamic.get("offers", []) if isinstance(row, dict)]
    sellable_rows = [row for row in sellable.get("offers", []) if isinstance(row, dict)]
    hidden_rows = [row for row in sellable.get("hidden_offers", []) if isinstance(row, dict)]
    seed_rows = [row for row in seeds.get("seeds", []) if isinstance(row, dict)]
    sellable_ids = {norm(row.get("offer_id")) for row in sellable_rows}
    hidden_by_id: dict[str, list[str]] = {}
    for hidden in hidden_rows:
        offer = hidden.get("offer") if isinstance(hidden.get("offer"), dict) else {}
        offer_id = norm(offer.get("offer_id"))
        if offer_id:
            hidden_by_id[offer_id] = [norm(reason) for reason in hidden.get("reason_codes", [])]

    candidate_rows = []
    summary: dict[str, dict[str, Any]] = {}
    for start_time in PREFERRED_TIMES:
        generated = [row for row in dynamic_rows if is_preferred_candidate(row) and norm(row.get("start_time")) == start_time]
        sellable_at = [row for row in sellable_rows if is_preferred_candidate(row) and norm(row.get("start_time")) == start_time]
        aha_generated = [row for row in generated if norm(row.get("course_id")) in AHA_BLS_IDS]
        non_aha_generated = [row for row in generated if norm(row.get("course_id")) not in AHA_BLS_IDS]
        reasons = Counter()
        stages = Counter()
        buckets = Counter()
        for row in generated:
            offer_id = norm(row.get("offer_id"))
            row_reasons = hidden_by_id.get(offer_id, [])
            if offer_id in sellable_ids:
                first_stage = "public_sellable"
                bucket = "kept"
            else:
                first_stage = stage_for_reasons(row_reasons)
                bucket = reason_bucket(row_reasons)
            reasons.update(row_reasons or (["public_sellable"] if offer_id in sellable_ids else ["unknown_rejection"]))
            stages[first_stage] += 1
            buckets[bucket] += 1
            candidate_rows.append({
                "offer_id": offer_id,
                "date": norm(row.get("date")),
                "start_time": start_time,
                "course_id": norm(row.get("course_id")),
                "course_title": norm(row.get("course_title")),
                "is_aha_bls": norm(row.get("course_id")) in AHA_BLS_IDS,
                "public_sellable": offer_id in sellable_ids,
                "first_rejection_stage": first_stage,
                "rejection_bucket": bucket,
                "rejection_reasons": ";".join(row_reasons),
            })
        summary[start_time] = {
            "generated_candidate_count": len(generated),
            "aha_bls_course_id_count": len(aha_generated),
            "non_aha_bls_like_disabled_course_id_count": len(non_aha_generated),
            "public_sellable_count": len(sellable_at),
            "rejection_reasons": dict(reasons.most_common()),
            "first_rejection_stage_counts": dict(stages.most_common()),
            "rejection_bucket_counts": dict(buckets.most_common()),
        }

    selected_august_bls = [
        {
            "date": norm(row.get("date")),
            "start_time": norm(row.get("start_time")),
            "course_id": norm(row.get("course_id")),
            "course_title": norm(row.get("course_title")),
            "source_offer_id": norm(row.get("source_offer_id")),
        }
        for row in seed_rows
        if is_august(row) and norm(row.get("course_id")) in AHA_BLS_IDS
    ]
    report = {
        "generated_at": datetime.now().isoformat(),
        "preferred_times": PREFERRED_TIMES,
        "aha_bls_course_ids": sorted(AHA_BLS_IDS),
        "summary_by_time": summary,
        "selected_august_aha_bls_after_cap_order_fix": selected_august_bls,
        "cap_ordering": {
            "script": "scripts/filter_public_sellable_offers.py",
            "function": "apply_offer_limits",
            "previous_sort_order": "(date, start_time, course_id)",
            "new_sort_order_for_aha_bls": "(month, seed_strategy_policy BLS preferred time rank, date, start_time, course_id)",
            "caps_applied_after_base_safety_gates": True,
            "cap_counts_changed": False,
            "course_ids_enabled_changed": False,
            "source_preference_policy": "data/config/seed_strategy_policy.json",
            "bls_preferred_order": seed_policy.get("preferred_start_times_by_family", {}).get("BLS", []),
        },
        "plain_answer": "Yes. Before this fix, earlier 08:00/08:30 rows could consume public-sellable caps before 09:15/12:30/evening rows. The cap limiter lived in scripts/filter_public_sellable_offers.py::apply_offer_limits and sorted by date, start_time, course_id before applying weekly/day/course caps.",
        "recommendation": "C. Keep the AHA-BLS-only cap preference layer. It preserves all safety gates and cap counts, moves AHA BLS public-sellable/selected seeds toward preferred 09:15 starts, and does not enable any additional course IDs. A separate seed-selector variant balance rule would be needed if Brian wants Initial/Renewal balance after the cap-order fix.",
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with REJECTIONS_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(candidate_rows[0].keys()))
        writer.writeheader()
        writer.writerows(candidate_rows)

    lines = [
        "# BLS preferred time cap blocker report",
        "",
        "## Plain answer",
        report["plain_answer"],
        "",
        "## Preferred-time summary",
        "| Start | Generated | AHA BLS | Non-AHA/BLS-like | Public sellable | Top rejection buckets |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for start_time, item in summary.items():
        buckets = "; ".join(f"{key}:{value}" for key, value in item["rejection_bucket_counts"].items())
        lines.append(
            f"| {start_time} | {item['generated_candidate_count']} | {item['aha_bls_course_id_count']} | "
            f"{item['non_aha_bls_like_disabled_course_id_count']} | {item['public_sellable_count']} | {buckets} |"
        )
    lines.extend([
        "",
        "## Selected August AHA BLS after cap ordering",
        "| Date | Time | CourseId | Course |",
        "| --- | --- | --- | --- |",
    ])
    for row in selected_august_bls:
        lines.append(f"| {row['date']} | {row['start_time']} | {row['course_id']} | {row['course_title']} |")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    TRACE_MD.write_text(
        "\n".join([
            "# BLS cap ordering trace",
            "",
            "- Script: `scripts/filter_public_sellable_offers.py`",
            "- Function: `apply_offer_limits`",
            "- Previous cap sort: `(date, start_time, course_id)`",
            "- Result of previous sort: earlier starts could consume `max_offers_per_course_per_week`, `max_offers_per_course_per_day`, and `max_total_offers_per_day` before BLS preferred times were evaluated.",
            "- New AHA BLS cap sort: `(month, seed_strategy_policy BLS preferred time rank, date, start_time, course_id)`",
            "- Scope: course IDs `209806`, `359474`, `210549` only.",
            "- Safety gates: unchanged and still run before cap ordering.",
            "- Cap counts: unchanged.",
            "- Course ID enablement: unchanged.",
        ]) + "\n",
        encoding="utf-8",
    )
    RECOMMENDATION_MD.write_text(
        "\n".join([
            "# BLS cap ordering recommendation",
            "",
            "Recommendation: C. Add a BLS-specific cap preference layer.",
            "",
            "This has been implemented only for reviewed AHA BLS course IDs `209806`, `359474`, and `210549`. It sorts cap candidates by the BLS preferred time order from `data/config/seed_strategy_policy.json` before weekly/day/course caps are consumed.",
            "",
            "Why not increase caps: the current issue is ordering, not proven lack of capacity. Increasing caps would expose more generated rows without first choosing better rows inside existing limits.",
            "",
            "Residual issue: after preferred-time rows survive public-sellable caps, seed selection still chooses the first BLS family/course-priority row per date. That currently favors AHA BLS Provider Initial over Renewal. Fixing Initial/Renewal balance should be a separate seed-selector policy change, not a public-sellable cap change.",
        ]) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {REPORT_MD}")
    print(f"Selected August AHA BLS seeds: {len(selected_august_bls)}")


if __name__ == "__main__":
    main()
