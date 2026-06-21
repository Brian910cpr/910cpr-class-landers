from __future__ import annotations

import html
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"

SEEDS_PATH = AUDIT_DIR / "schedule_seeds_preview.json"
URL_PREVIEW_PATH = AUDIT_DIR / "seed_appointment_url_preview.json"
PUBLIC_OFFER_POLICY_PATH = ROOT / "data" / "config" / "public_offer_policy.json"
SEED_STRATEGY_POLICY_PATH = ROOT / "data" / "config" / "seed_strategy_policy.json"

HTML_PATH = AUDIT_DIR / "internal_dynamic_seed_preview.html"
JSON_PATH = AUDIT_DIR / "internal_dynamic_seed_preview.json"
REPORT_PATH = AUDIT_DIR / "internal_dynamic_seed_preview_report.md"
UNKNOWN = "UNKNOWN"


def read_json(path: Path) -> tuple[Any | None, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"invalid_json: {exc}"
    except OSError as exc:
        return None, f"read_error: {exc}"


def clean_text(value: Any) -> str:
    text = str(value or "").strip()
    return " ".join(text.split()) or UNKNOWN


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def seed_records(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    rows = payload.get("seeds")
    if rows is None:
        rows = payload.get("selected_seeds")
    return [row for row in as_list(rows) if isinstance(row, dict)]


def url_preview_lookup(payload: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for preview in as_list(payload.get("previews")):
        if not isinstance(preview, dict):
            continue
        seed_id = str(preview.get("seed_id") or "").strip()
        source_offer_id = str(preview.get("source_offer_id") or "").strip()
        if seed_id:
            out[seed_id] = preview
        if source_offer_id:
            out[source_offer_id] = preview
    return out


def match_preview(seed: dict[str, Any], lookup: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    seed_id = str(seed.get("seed_id") or "").strip()
    source_offer_id = str(seed.get("source_offer_id") or "").strip()
    return lookup.get(seed_id) or lookup.get(source_offer_id)


def build_rows(seeds_payload: Any, url_payload: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lookup = url_preview_lookup(url_payload)
    rows: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for seed in seed_records(seeds_payload):
        preview = match_preview(seed, lookup)
        seed_id = clean_text(seed.get("seed_id"))
        source_offer_id = clean_text(seed.get("source_offer_id"))
        if not preview:
            missing.append({
                "seed_id": seed_id,
                "source_offer_id": source_offer_id,
                "course_title": clean_text(seed.get("course_title")),
                "date": clean_text(seed.get("date")),
                "start_time": clean_text(seed.get("start_time")),
            })
        rows.append({
            "seed_id": seed_id,
            "source_offer_id": source_offer_id,
            "course_id": clean_text(seed.get("course_id")),
            "course_title": clean_text(seed.get("course_title")),
            "course_family": clean_text(seed.get("course_family")),
            "date": clean_text(seed.get("date")),
            "start_time": clean_text(seed.get("start_time")),
            "end_time": clean_text(seed.get("end_time") or preview.get("end_time") if preview else seed.get("end_time")),
            "appointment_display_start": clean_text(seed.get("appointment_display_start") or (preview or {}).get("appointment_display_start") or seed.get("start_time")),
            "appointment_display_end": clean_text(seed.get("appointment_display_end") or (preview or {}).get("appointment_display_end")),
            "scheduler_consumption_start": clean_text(seed.get("scheduler_consumption_start") or (preview or {}).get("scheduler_consumption_start")),
            "scheduler_consumption_end": clean_text(seed.get("scheduler_consumption_end") or (preview or {}).get("scheduler_consumption_end")),
            "scheduler_consumption_minutes": clean_text(seed.get("scheduler_consumption_minutes") or (preview or {}).get("scheduler_consumption_minutes")),
            "instructor_lock_start": clean_text(seed.get("instructor_lock_start") or (preview or {}).get("instructor_lock_start")),
            "instructor_lock_end": clean_text(seed.get("instructor_lock_end") or (preview or {}).get("instructor_lock_end")),
            "resource_lock_start": clean_text(seed.get("resource_lock_start") or (preview or {}).get("resource_lock_start")),
            "resource_lock_end": clean_text(seed.get("resource_lock_end") or (preview or {}).get("resource_lock_end")),
            "instructor_display_name": clean_text(seed.get("instructor_display_name")),
            "public_offer_location": clean_text(seed.get("offer_location") or seed.get("location") or (preview or {}).get("location")),
            "source_availability_location": clean_text(seed.get("source_location")),
            "matched_container_id": clean_text((preview or {}).get("matched_container_id") or seed.get("matched_container_id")),
            "appointmentDayId": (preview or {}).get("appointmentDayId") or seed.get("appointmentDayId") or UNKNOWN,
            "appointment_url_preview": clean_text((preview or {}).get("appointment_url_preview")),
            "confidence": clean_text((preview or {}).get("confidence") or seed.get("confidence")),
            "blocking_reason": (preview or {}).get("blocking_reason"),
            "review_status_options": ["approve", "hide", "adjust", "needs recheck"],
            "review_only": True,
        })
    return rows, missing


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else UNKNOWN), quote=True)


def render_html(rows: list[dict[str, Any]], stats: dict[str, Any]) -> str:
    cards = []
    for row in rows:
        url = row.get("appointment_url_preview")
        link = "<span class=\"missing\">No URL preview matched</span>"
        if url and url != UNKNOWN and not row.get("blocking_reason"):
            link = f"<a class=\"button\" href=\"{esc(url)}\">REVIEW ONLY — would redirect to Enrollware</a>"
        cards.append(f"""
      <article class="seed-card">
        <div class="card-head">
          <div>
            <p class="eyebrow">{esc(row['course_family'])}</p>
            <h2>{esc(row['course_title'])}</h2>
          </div>
          <strong class="confidence">{esc(row['confidence'])}</strong>
        </div>
        <dl>
          <div><dt>Date/time</dt><dd>{esc(row['date'])} {esc(row['start_time'])}-{esc(row['end_time'])}</dd></div>
          <div><dt>Customer appointment time</dt><dd>{esc(row['appointment_display_start'])} to {esc(row['appointment_display_end'])}</dd></div>
          <div><dt>Lander scheduler lock window</dt><dd>{esc(row['scheduler_consumption_start'])} to {esc(row['scheduler_consumption_end'])} ({esc(row['scheduler_consumption_minutes'])} min)</dd></div>
          <div><dt>Instructor lock</dt><dd>{esc(row['instructor_lock_start'])} to {esc(row['instructor_lock_end'])}</dd></div>
          <div><dt>Resource lock</dt><dd>{esc(row['resource_lock_start'])} to {esc(row['resource_lock_end'])}</dd></div>
          <div><dt>Instructor</dt><dd>{esc(row['instructor_display_name'])}</dd></div>
          <div><dt>Public offer location</dt><dd>{esc(row['public_offer_location'])}</dd></div>
          <div><dt>Source availability location</dt><dd>{esc(row['source_availability_location'])}</dd></div>
          <div><dt>Matched container</dt><dd>{esc(row['matched_container_id'])}</dd></div>
          <div><dt>appointmentDayId</dt><dd>{esc(row['appointmentDayId'])}</dd></div>
          <div><dt>Seed ID</dt><dd><code>{esc(row['seed_id'])}</code></dd></div>
        </dl>
        <div class="actions">{link}</div>
        <p class="review-controls">Review status placeholders: approve / hide / adjust / needs recheck</p>
      </article>""")
    body = "\n".join(cards) if cards else "<p class=\"empty\">No selected seeds were available to preview.</p>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Internal Dynamic Seed Preview</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; color: #172033; background: #f5f7fb; }}
    header {{ background: #111827; color: white; padding: 24px; }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
    .warning {{ background: #fff3cd; border: 1px solid #e7c45f; border-radius: 12px; padding: 16px; margin-bottom: 20px; }}
    .summary {{ display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 20px; }}
    .summary div {{ background: white; border: 1px solid #d8dee9; border-radius: 12px; padding: 12px 16px; min-width: 140px; }}
    .seed-card {{ background: white; border: 1px solid #d8dee9; border-radius: 16px; padding: 18px; margin-bottom: 16px; box-shadow: 0 2px 10px rgba(15, 23, 42, 0.05); }}
    .card-head {{ display: flex; justify-content: space-between; gap: 16px; align-items: start; }}
    .eyebrow {{ color: #475569; font-size: 12px; letter-spacing: .08em; margin: 0 0 4px; text-transform: uppercase; }}
    h1, h2 {{ margin: 0; }}
    h2 {{ font-size: 20px; }}
    dl {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; margin: 16px 0; }}
    dt {{ font-size: 12px; color: #64748b; text-transform: uppercase; }}
    dd {{ margin: 4px 0 0; }}
    code {{ font-size: 12px; overflow-wrap: anywhere; }}
    .button {{ display: inline-block; background: #1d4ed8; color: white; text-decoration: none; padding: 10px 14px; border-radius: 10px; font-weight: 700; }}
    .confidence {{ background: #e0f2fe; color: #075985; padding: 6px 10px; border-radius: 999px; }}
    .review-controls, .missing, .empty {{ color: #7c2d12; }}
  </style>
</head>
<body>
  <header>
    <h1>Internal Dynamic Seed Preview</h1>
    <p>Review-only preview for selected dynamic schedule seeds.</p>
  </header>
  <main>
    <section class="warning">
      <strong>This is not public. This has not rechecked live availability at click-time.</strong>
      <p>Links are preview-only and were not fetched. Do not publish this file as a customer page.</p>
    </section>
    <section class="summary">
      <div><strong>{esc(stats['seeds_read'])}</strong><br>Seeds read</div>
      <div><strong>{esc(stats['urls_matched'])}</strong><br>URLs matched</div>
      <div><strong>{esc(stats['preview_rows_rendered'])}</strong><br>Rows rendered</div>
      <div><strong>{esc(stats['missing_urls'])}</strong><br>Missing URLs</div>
    </section>
    {body}
  </main>
</body>
</html>
"""


def render_report(stats: dict[str, Any], missing: dict[str, str], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Internal Dynamic Seed Preview Report",
        "",
        "Read-only internal/admin preview. No public pages, Enrollware calls, appointment creation, appointment URL changes, Worker routes, deploys, or commits were performed.",
        "",
        "## Summary",
        "",
        f"- Seeds read: {stats['seeds_read']}",
        f"- URLs matched: {stats['urls_matched']}",
        f"- Preview rows rendered: {stats['preview_rows_rendered']}",
        f"- Missing URLs: {stats['missing_urls']}",
        f"- Next chain link ready: {stats['next_chain_link_ready']}",
        "",
        "## Files Missing Or Unreadable",
        "",
    ]
    if missing:
        lines.extend(f"- `{name}`: {reason}" for name, reason in sorted(missing.items()))
    else:
        lines.append("- None")
    lines.extend(["", "## Preview Rows", ""])
    if rows:
        lines.extend(["| Date | Time | Course | Instructor | Location | URL? |", "| --- | --- | --- | --- | --- | --- |"])
        for row in rows:
            has_url = "yes" if row.get("appointment_url_preview") not in (None, "", UNKNOWN) else "no"
            lines.append(f"| {row['date']} | {row['start_time']}-{row['end_time']} | {row['course_title']} | {row['instructor_display_name']} | {row['public_offer_location']} | {has_url} |")
    else:
        lines.append("- No rows rendered.")
    lines.extend([
        "",
        "## Next Safest Step",
        "",
        "- Manually review the internal HTML preview. The next chain link is a controlled manual click/registration proof, not public publishing.",
        "",
    ])
    return "\n".join(lines)


def run() -> dict[str, Any]:
    seeds_payload, seeds_error = read_json(SEEDS_PATH)
    url_payload, url_error = read_json(URL_PREVIEW_PATH)
    public_policy, public_policy_error = read_json(PUBLIC_OFFER_POLICY_PATH)
    seed_policy, seed_policy_error = read_json(SEED_STRATEGY_POLICY_PATH)
    missing: dict[str, str] = {}
    if seeds_error:
        missing["schedule_seeds_preview"] = seeds_error
    if url_error:
        missing["seed_appointment_url_preview"] = url_error
    if public_policy_error:
        missing["public_offer_policy"] = public_policy_error
    if seed_policy_error:
        missing["seed_strategy_policy"] = seed_policy_error

    rows, missing_urls = build_rows(seeds_payload or {}, url_payload or {})
    stats = {
        "seeds_read": len(seed_records(seeds_payload or {})),
        "urls_matched": len(rows) - len(missing_urls),
        "preview_rows_rendered": len(rows),
        "missing_urls": len(missing_urls),
        "rows_by_course_family": dict(sorted(Counter(row["course_family"] for row in rows).items())),
        "next_chain_link_ready": bool(rows) and not missing_urls,
    }
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only": True,
        "public_site_affected": False,
        "enrollware_called": False,
        "appointments_created": False,
        "appointment_urls_changed": False,
        "worker_routes_enabled": False,
        "source_schedule_seeds": str(SEEDS_PATH),
        "source_seed_appointment_url_preview": str(URL_PREVIEW_PATH),
        "source_public_offer_policy": str(PUBLIC_OFFER_POLICY_PATH),
        "source_seed_strategy_policy": str(SEED_STRATEGY_POLICY_PATH),
        "stats": stats,
        "policies_loaded": {
            "public_offer_policy": isinstance(public_policy, dict),
            "seed_strategy_policy": isinstance(seed_policy, dict),
        },
        "rows": rows,
        "missing_url_matches": missing_urls,
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    HTML_PATH.write_text(render_html(rows, stats), encoding="utf-8")
    REPORT_PATH.write_text(render_report(stats, missing, rows), encoding="utf-8")
    return {
        "stats": stats,
        "missing": missing,
        "output_paths": [HTML_PATH, JSON_PATH, REPORT_PATH],
    }


def main() -> int:
    result = run()
    print("Internal dynamic seed preview complete (READ ONLY).")
    print("No public pages, Enrollware calls, appointments, appointment URL changes, Worker routes, deploys, or commits were performed.")
    print("")
    print(f"Seeds read: {result['stats']['seeds_read']}")
    print(f"URLs matched: {result['stats']['urls_matched']}")
    print(f"Preview rows rendered: {result['stats']['preview_rows_rendered']}")
    print(f"Missing URLs: {result['stats']['missing_urls']}")
    print(f"Next chain link ready: {result['stats']['next_chain_link_ready']}")
    print("")
    print("Output files:")
    for path in result["output_paths"]:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
