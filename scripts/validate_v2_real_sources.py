"""Read-only exact-head V2 comparison; raw inputs stay in runner-local storage.

Run only in the approved CI environment with HOT_SYNC_ADMIN_KEY injected.
The only shareable files are sanitized/summary.json and sanitized/report.md.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import types
import traceback
from collections import Counter
from datetime import datetime, timezone
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("bls", "heartsaver", "acls", "pals")


class PublicProbeFailure(RuntimeError):
    def __init__(self, code, public_probe):
        super().__init__(code)
        self.public_probe = public_probe


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str), encoding="utf-8")


def fresh_sources(out):
    from scripts import build_sessions_current as sessions
    from scripts import export_calendar_snapshots as calendars
    from scripts import build_live_availability_snapshot as availability
    from scripts import fetch_canonical_scheduling_demand as demand

    key = os.environ.get("HOT_SYNC_ADMIN_KEY")
    if not key:
        raise RuntimeError("approved_reader_credential_unavailable")
    # No private credential stores or newly configured credentials are consulted.
    with contextlib.redirect_stdout(io.StringIO()):
        sessions.build_sessions_from_enrollware_ical(
            repo_root=ROOT, ical_url=sessions.DEFAULT_ENROLLWARE_ICAL_URL,
            output_path=out / "sessions_current.json", audit_dir=out / "sessions_audit",
            course_map=sessions.load_course_map(ROOT, "data/config/course_map.json"))
    calendar_dir = out / "calendar_snapshots"
    read_json = calendars.read_json
    with patch.multiple(calendars, RUNTIME_SNAPSHOT_DIR=calendar_dir,
                        AUDIT_DIR=out / "calendar_audit",
                        SUMMARY_PATH=out / "calendar_audit/summary.json",
                        REPORT_PATH=out / "calendar_audit/report.md"), \
         patch.object(calendars, "read_json", side_effect=lambda p: ({}, "not_consulted")
                      if p == calendars.PRIVATE_CALENDAR_SECRETS_PATH else read_json(p)):
        exported = calendars.export_calendar_snapshots()
    if any(s["export_status"] != "ok" for s in exported["sources"]):
        raise RuntimeError("configured_calendar_export_incomplete")
    with patch.multiple(availability, RUNTIME_CALENDAR_SNAPSHOT_DIR=calendar_dir,
                        AUDIT_DIR=out / "availability_audit", LOCAL_SNAPSHOT_CANDIDATES=[],
                        SNAPSHOT_PATH=out / "live_availability_snapshot.json",
                        REPORT_PATH=out / "availability_audit/report.md"):
        availability.run()
    # The supported reader performs an authenticated GET only. Neither key nor
    # headers are serialized, printed, or included in artifacts.
    canonical = demand.validate_payload(demand.fetch(url=demand.DEFAULT_URL, key=key))
    demand._atomic_write_json(out / "canonical_scheduling_demand.json", canonical)
    live = json.loads((out / "live_availability_snapshot.json").read_text())
    now = datetime.now(timezone.utc)
    if not live.get("layered_commitment_coverage"):
        raise RuntimeError("complete_calendar_coverage_unavailable")
    for proof in live["layered_commitment_coverage"]:
        if not datetime.fromisoformat(proof["observed_at"]) <= now < datetime.fromisoformat(proof["valid_until"]):
            raise RuntimeError("calendar_coverage_expired")
    raw = json.loads((out / "sessions_current.json").read_text())
    if raw["build"]["source_mode"] != "enrollware_ical_authoritative":
        raise RuntimeError("unexpected_timing_source")
    age = (now - datetime.fromisoformat(raw['build']['generated_at'])).total_seconds()
    if not -300 <= age <= 900:
        raise RuntimeError("timing_source_stale")
    return raw, canonical, live


def future_projection(raw, canonical, now):
    """Use the existing pure future-schedule functions; never invoke page writes."""
    from scripts import build_schedule_future as future
    from scripts.canonical_scheduling_demand import exclude_non_session_sources, resolve_canonical_demand
    aliases = future.load_aliases(ROOT / "data/course_aliases.json")
    reference = json.loads((ROOT / "data/config/course_map.json").read_text())
    locations = future.load_public_location_aliases(ROOT / future.LOCATION_RESOURCE_MAP_PATH)
    rows, _ = exclude_non_session_sources(copy.deepcopy(raw["sessions"]), canonical)
    flattened = []
    for row in rows:
        start = future.parse_iso_dt(future.session_start_candidate(row))
        if not start or start < now or future.has_tbd_location(row):
            continue
        location = future.public_location_for_session(row, locations)
        if not location:
            continue
        identity = future.resolve_course_identity(row, aliases, reference)
        if row.get("mapping_status") != "mapped" and not future.identity_can_include_session(identity):
            continue
        future.apply_public_location(row, location)
        flattened.append(future.build_public_future_session(row, identity))
    resolved, _ = resolve_canonical_demand(flattened, canonical["sessions"])
    return {"sessions": resolved}


@contextlib.contextmanager
def baseline_modules(ref):
    import scripts
    names = ("layered_scheduling_engine", "layered_selector_adapter", "layered_publication_adapter",
             "layered_day_cache", "block_start_time_selector", "build_bls_block_schedule_pilot")
    saved = {}
    try:
        for name in names:
            full = "scripts." + name
            saved[full] = sys.modules.get(full)
            module = types.ModuleType(full)
            module.__file__ = str(ROOT / "scripts" / (name + ".py"))
            sys.modules[full] = module
            setattr(scripts, name, module)
            source = subprocess.check_output(["git", "show", f"{ref}:scripts/{name}.py"],
                                             cwd=ROOT, text=True, encoding="utf-8")
            exec(compile(source, module.__file__, "exec"), module.__dict__)
        yield
    finally:
        for full, module in saved.items():
            if module is not None:
                sys.modules[full] = module
                setattr(scripts, full.split(".")[-1], module)
            else:
                sys.modules.pop(full, None)


def calculate_pages(out, label, canonical, now):
    from scripts import block_start_time_selector as selector
    from scripts import layered_day_cache as cache
    from scripts.canonical_scheduling_demand import resolve_canonical_demand
    from scripts.fetch_canonical_scheduling_demand import validate_payload
    original_cache = cache.cached_calculate

    def isolated_cache(*args, **kwargs):
        kwargs["cache_dir"] = out / label / "calculation_cache"
        return original_cache(*args, **kwargs)

    patches = dict(SESSIONS_CURRENT_PATH=out / "sessions_current.json",
                   SCHEDULE_FUTURE_PATH=out / "schedule_future.json",
                   LIVE_AVAILABILITY_PATH=out / "live_availability_snapshot.json",
                   load_publication_demand=lambda root: validate_payload(copy.deepcopy(canonical)),
                   sessions_with_canonical_demand=lambda rows: resolve_canonical_demand(rows, canonical["sessions"]),
                   selector_reference_datetime=lambda: now)
    with contextlib.ExitStack() as stack:
        for name, value in patches.items():
            stack.enter_context(patch.object(selector, name, value))
        if hasattr(selector, "LAYERED_HISTORY_PATH"):
            stack.enter_context(patch.object(selector, "LAYERED_HISTORY_PATH", out / label / "private_history.json"))
        stack.enter_context(patch.object(cache, "cached_calculate", side_effect=isolated_cache))
        configs = selector.load_block_schedule_page_configs()
        return {page: selector.build_block_schedule_page(configs[page]) for page in PAGES}


def public_reasons(reasons):
    aggregated = Counter()
    for reason, count in reasons.items():
        aggregated[reason.split(":", 1)[0]] += count
    return dict(aggregated)


def offer_key(offer):
    return (offer["date"], offer["startTime"], str(offer["courseId"]), offer.get("offerType", ""))


def same_public_booking_url(expected, actual):
    """Attribution may decorate/re-encode a link, but booking identity must match."""
    from urllib.parse import urlparse, urljoin, parse_qs
    def identity(url):
        parsed = urlparse(urljoin('https://validation.invalid/', url or ''))
        params = {key: values for key, values in parse_qs(parsed.query).items()
                  if not key.lower().startswith('utm_')}
        return parsed.scheme, parsed.hostname, parsed.path, params
    return identity(expected) == identity(actual)



def removed_direct_proofs(before, after):
    current = {offer_key(o) for o in after['offers']}
    rejected = {offer_key(o): o for o in after['rejectedCourseStartTimes'] if o.get('offerType') == 'seated_class'}
    results = []
    trusted = {'verified_positive_demand','retained_verified_commitment','explicit_class_commitment',
               'explicit_calendar_or_manual_commitment','explicit_hold'}
    for offer in before['offers']:
        key = offer_key(offer)
        if offer.get('offerType') != 'seated_class' or key in current:
            continue
        row = rejected.get(key, {})
        proofs = row.get('directConstraintProofs', [])
        lifecycle = row.get('directLifecycleProven') is True
        verified = lifecycle or any(p['basis'] in trusted and p['bounded_interval_conflict'] and (p['room_constraint'] or p['instructor_constraint']) for p in proofs)
        results.append({'public_choice':key,'reasons':sorted(set(row.get('reasons',[]))),
                        'constraint_bases':sorted({p['basis'] for p in proofs}),
                        'room_conflict_checked':any(p['room_constraint'] for p in proofs),
                        'instructor_conflict_checked':any(p['instructor_constraint'] for p in proofs),
                        'verified_or_explicit_constraint_proven':verified,
                        'readiness':'proven_constraint' if verified else 'unresolved_source_uncertainty'})
    return results

def physical_occupancy_preserved(before, after):
    """Count safety violations without exposing private source identities."""
    from scripts.layered_selector_adapter import aware
    sources = after["layeredDiagnostics"]["projected_sources"]
    retired = {str(x.get("source_event_id")) for x in sources
               if x.get("commitment_state") in {"inactive", "inventory"}}
    actual = [busy for r in after["layeredDiagnostics"]["reports"] for busy in r["normalized_occupancy"]]
    def person(value):
        return str(value or "").strip().casefold().replace(" ennis", "")
    violations = 0
    checked = set()
    for report in before["layeredDiagnostics"]["reports"]:
        for busy in report["normalized_occupancy"]:
            key = (busy["id"], str(busy["start"]), str(busy["end"]))
            if key in checked or str(busy["id"]) in retired:
                continue
            checked.add(key)
            if not any(person(other["instructor"]) == person(busy["instructor"])
                       and other["location"] == busy["location"]
                       and aware(other["start"]) <= aware(busy["start"])
                       and aware(busy["end"]) <= aware(other["end"]) for other in actual):
                violations += 1
    return violations


def rendered_probe(payload, now):
    """Offline Chrome consumes the actual real-source calculated public feed."""
    from playwright.sync_api import sync_playwright
    from scripts.build_bls_block_schedule_pilot import render_html, public_selector_availability_payload
    from urllib.parse import urlparse, parse_qs
    choices = [o for o in payload["offers"] if o.get("offerType") == "dynamic_appointment"]
    if not choices:
        choices = [o for o in payload["offers"] if o.get("offerType") == "seated_class"]
    if not choices:
        return {"status": "unrun_no_public_choices"}
    probe_choices = choices[:1] if choices[0].get("offerType") == "dynamic_appointment" else choices
    html, feed = render_html(payload), public_selector_availability_payload(payload)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        try:
            for chosen in probe_choices:
                for width in (1440, 390):
                    page = browser.new_page(viewport={"width": width, "height": 1000}, timezone_id="America/New_York")
                    page.add_init_script("const D=Date;const t=" + str(int(now.timestamp()*1000)) +
                                         ";window.Date=class extends D{constructor(...a){super(...(a.length?a:[t]));}static now(){return t;}};")
                    errors = []
                    page.on("pageerror", lambda e: errors.append(type(e).__name__))
                    def route(request):
                        path = urlparse(request.request.url).path
                        if path == "/validation.html":
                            request.fulfill(status=200, content_type="text/html", body=html)
                        elif path.startswith("/data/block-selector-availability/"):
                            request.fulfill(status=200, content_type="application/json", body=json.dumps(feed))
                        elif path.startswith("/assets/") and (ROOT / "docs" / path.lstrip("/")).is_file():
                            request.fulfill(status=200, path=str(ROOT / "docs" / path.lstrip("/")))
                        else:
                            request.fulfill(status=204, body="")
                    page.route("**/*", route)
                    page.goto("https://validation.invalid/validation.html", wait_until="domcontentloaded")
                    page.wait_for_function("typeof availabilityReady==='function' && availabilityReady()")
                    button = page.locator(f'[data-course-id="{chosen["courseId"]}"]')
                    toggle = page.locator("#show-all-toggle")
                    if not button.is_visible() and toggle.is_visible(): toggle.check()
                    if button.is_visible(): button.click()
                    page.evaluate("o=>{selectedCourseId=o.courseId;selectedDate=o.date;selectedStart=o.startTime;renderAll();}", chosen)
                    visible = page.evaluate("filteredDates().flatMap(d=>d.startTimes.map(t=>[d.date,t.startTime]))")
                    if [chosen["date"], chosen["startTime"]] not in visible or errors:
                        raise RuntimeError("rendered_real_window_not_selectable")
                    hrefs = page.locator("#course-list a").evaluate_all("els=>els.map(e=>e.getAttribute('href'))")
                    if not any(same_public_booking_url((chosen.get("appointmentUrl") or chosen.get("registrationUrl") or chosen.get("url")), href) for href in hrefs):
                        def public_parameters(url):
                            params = parse_qs(urlparse(url or '').query)
                            return {k: params[k] for k in ('courseId', 'appointmentDayId', 'startTime', 'date') if k in params}
                        raise PublicProbeFailure("rendered_real_booking_link_mismatch", {
                            'expected_window': offer_key(chosen),
                            'selection': page.evaluate('({courseId:selectedCourseId,date:selectedDate,startTime:selectedStart})'),
                            'expected_parameters': public_parameters(chosen['appointmentUrl']),
                            'expected_query_keys': sorted(parse_qs(urlparse(chosen['appointmentUrl']).query)),
                            'rendered_query_keys': [sorted(parse_qs(urlparse(href or '').query)) for href in hrefs],
                            'rendered_parameters': [public_parameters(href) for href in hrefs],
                        })
                    page.close()
        finally:
            browser.close()
    return {"status": "passed", "viewports": [1440, 390], "public_choices_checked": [offer_key(o) for o in probe_choices]}


def run(out, baseline):
    # Import all current modules before baseline substitution.
    from scripts import block_start_time_selector, layered_day_cache, build_bls_block_schedule_pilot
    raw, canonical, live = fresh_sources(out)
    now = datetime.now(timezone.utc)
    write(out / "schedule_future.json", future_projection(raw, canonical, now))
    after = calculate_pages(out, "after", canonical, now)
    with baseline_modules(baseline):
        before = calculate_pages(out, "before", canonical, now)
    summary = {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
               "baseline": baseline, "source_validation": "authenticated_fresh_read_only",
               "canonical_schema_validated": True, "calendar_coverage_validated": True,
               "private_inputs_uploaded": False, "production_mutations": False, "pages": {}}
    for name in PAGES:
        previous = {offer_key(o) for o in before[name]["offers"]}
        current = {offer_key(o) for o in after[name]["offers"]}
        violations = physical_occupancy_preserved(before[name], after[name])
        summary["pages"][name] = {"before_offers": len(previous), "after_offers": len(current),
            "added_public_windows": sorted(current-previous), "removed_public_windows": sorted(previous-current),
            "occupancy_preservation_violations": violations,
            "before_rejection_reasons": public_reasons(before[name]["rejectionReasonCounts"]),
            "after_rejection_reasons": public_reasons(after[name]["rejectionReasonCounts"]),
            "removed_direct_choice_proofs": removed_direct_proofs(before[name], after[name])}
        if violations:
            raise RuntimeError("real_occupied_interval_not_preserved")
    summary['status'] = 'calculated'
    write(out / 'sanitized/summary.json', summary)
    for name in PAGES:
        summary['pages'][name]['rendered_probe'] = rendered_probe(after[name], now)
        write(out / 'sanitized/summary.json', summary)
    clinical_unproven = [p for name in ('acls','pals') for p in summary['pages'][name]['removed_direct_choice_proofs'] if not p['verified_or_explicit_constraint_proven']]
    if clinical_unproven:
        summary['release_readiness'] = 'blocked_unproven_clinical_direct_suppression'
        write(out / 'sanitized/summary.json', summary)
        raise RuntimeError('unproven_clinical_direct_suppression')
    summary['release_readiness'] = 'clinical_removals_proven_by_verified_or_explicit_constraints'
    summary["status"] = "passed"
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    safe = out / "sanitized"
    write(safe / 'summary.json', {'status':'started', 'baseline':args.baseline})
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            result = run(out, args.baseline)
    except Exception as error:
        # No exception bodies, headers, source rows, URLs or credentials in logs.
        result = json.loads((safe / 'summary.json').read_text())
        result.update({"status": "failed", "failure_type": type(error).__name__,
                  "failure_code": str(error) if str(error) in {
                      "approved_reader_credential_unavailable", "configured_calendar_export_incomplete",
                      "complete_calendar_coverage_unavailable", "calendar_coverage_expired", "unexpected_timing_source", "timing_source_stale",
                      "rendered_real_window_not_selectable", "rendered_real_booking_link_mismatch",
                      "real_occupied_interval_not_preserved", "unproven_clinical_direct_suppression"} else "source_or_validation_check_failed",
                  "http_status": getattr(error, "code", None),
                  "code_locations": [{"file": Path(frame.filename).name, "function": frame.name, "line": frame.lineno}
                                     for frame in traceback.extract_tb(error.__traceback__)][-5:],
                  "private_inputs_uploaded": False, "production_mutations": False})
        if isinstance(error, PublicProbeFailure):
            result['public_probe'] = error.public_probe
    write(safe / "summary.json", result)
    report = "V2 validation-only result: " + result["status"] + "\n\n"
    if result["status"] == "passed":
        report += f"Head: {result['head']}\nBaseline: {result['baseline']}\n"
        for page, data in result["pages"].items():
            report += f"{page}: {data['before_offers']} -> {data['after_offers']} public choices; occupancy violations {data['occupancy_preservation_violations']}; browser {data['rendered_probe']['status']}\n"
    else:
        report += "Failure: " + result["failure_type"] + "/" + result["failure_code"] + "\n"
    (safe / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
