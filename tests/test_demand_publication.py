"""Isolated endpoint -> HTTP fetch -> runtime -> published selector proof.

The fixtures never write to production, real bookings, or repository public files.
"""
from __future__ import annotations

from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import shutil
from pathlib import Path
import subprocess
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch

from scripts import apply_anchor_policy as anchor
from scripts import fetch_canonical_scheduling_demand as fetcher
from scripts.canonical_scheduling_demand import resolve_canonical_demand
from scripts.canonical_scheduling_demand import exclude_non_session_sources
from scripts import build_schedule_future as future
from scripts.publish_admin_schedule import build_admin_schedule
from scripts.publish_landerware_ical import build_ical
from scripts.validate_public_refresh_output import validate_non_session_publication

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads((ROOT / "data/config/anchor_schedule_policy.json").read_text(encoding="utf-8"))


def fixture(day):
    occurrence = {
        "session_id": "fixture-occurrence", "course_id": "359474",
        "start_at": f"{day}T13:00:00-04:00", "end_at": f"{day}T15:00:00-04:00",
        "location_name": ":: Wilmington; Shipyard Blvd - B", "public_direct_booking": True,
        "registration_url": "https://example.test/committed-fixture",
    }
    slots = []
    for clock, cid, duration in [("08:00","210549",60),("12:00","210549",60),("13:00","359474",120),("15:00","210549",60),("18:30","210549",60)]:
        offer = {
            "courseId":cid,"courseName":"BLS Renewal" if cid == "359474" else "HeartCode BLS Skills",
            "courseFamily":"BLS","deliveryMode":"in-person" if cid == "359474" else "skills-session",
            "date":day,"startTime":clock,"displayStartTime":clock,"durationMinutes":duration,
            "location":occurrence["location_name"],"offerType":"seated_class" if cid == "359474" else "dynamic_appointment",
            "appointmentUrl":occurrence["registration_url"] if cid == "359474" else f"https://example.test/fixture/{clock}",
        }
        slots.append({"startTime":clock,"displayStartTime":clock,"courses":[offer]})
    return occurrence, {
        "schemaVersion":"selector-resolved-availability.v1", "pageKey":"bls",
        "generatedAt":datetime.now(timezone.utc).isoformat(),
        "dates":[{"date":day,"displayDate":day,"startTimes":slots}],"counts":{},
    }


def endpoint_payload(occurrence, count):
    row = {
        "id":"fixture-canonical","external_class_id":occurrence["session_id"],
        "external_course_id":occurrence["course_id"], "start_at":occurrence["start_at"], "end_at":occurrence["end_at"],
        "source":"fixture","status":"scheduled","registration_backend":"landerware",
        "external_reconciliation": {"complete":True, "source_observed_at":datetime.now(timezone.utc).isoformat(),
            "active_registration_count":count,"active_external_registration_ids":[f"fixture-{i}" for i in range(count)]},
        "landerware_sessions":[{"id":"fixture-workspace","starts_at":occurrence["start_at"],"ends_at":occurrence["end_at"]}],
        "registrations":[{"status":"registered","external_registration_id":f"fixture-{i}","registration_source":"enrollware"} for i in range(count)] + [{"status":"canceled"}],
    }
    completed = subprocess.run(
        ["node", str(ROOT / "tests/helpers/canonical_demand_endpoint.cjs")],
        input=json.dumps([row]),capture_output=True,text=True,check=True,
    )
    return json.loads(completed.stdout)


def publish_fixture(directory, day, count, *, commitment=None):
    """Exercise actual code with only file locations and external DB/auth isolated."""
    directory = Path(directory)
    occurrence, legal = fixture(day)
    schedule = directory / "schedule.json"
    if not schedule.exists():
        if commitment:
            occurrence["anchor_basis"] = commitment
        schedule.write_text(json.dumps({"sessions":[occurrence]}))
    selector_dir = directory / "selectors"
    selector_dir.mkdir(exist_ok=True)
    selector = selector_dir / "bls.json"
    # Each production refresh reconstructs hard-legal input before compaction.
    selector.write_text(json.dumps(legal))
    payload = endpoint_payload(occurrence, count)
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.headers.get("X-Hot-Sync-Admin-Key") != "fixture-only":
                self.send_error(401)
                return
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1",0),Handler)
    thread = Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        with ExitStack() as stack:
            for module, key, path in [
                (fetcher,"OUTPUT",directory / "runtime.json"),
                (fetcher,"STATUS_OUTPUT",directory / "fetch-status.json"),
                (anchor,"CANONICAL_DEMAND_PATH",directory / "runtime.json"),
                (anchor,"SCHEDULE_PATH",schedule),(anchor,"ADMIN_SCHEDULE_PATH",directory / "no-admin.json"),
                (anchor,"SELECTOR_DIR",selector_dir),(anchor,"ANCHOR_FEED_PATH",directory / "anchors.json"),
                (anchor,"DEMAND_MATCH_AUDIT_PATH",directory / "matches.json"),
            ]:
                stack.enter_context(patch.object(module,key,path))
            stack.enter_context(patch.dict(fetcher.os.environ,{
                "HOT_SYNC_ADMIN_KEY":"fixture-only",
                "CANONICAL_SCHEDULING_DEMAND_URL":f"http://127.0.0.1:{server.server_port}/demand",
            }))
            # Inject fixture transport only; production endpoint restrictions stay intact.
            stack.enter_context(patch.object(fetcher, "request_url",
                return_value=f"http://127.0.0.1:{server.server_port}/demand"))
            if fetcher.run() != 0:
                raise AssertionError("Fixture fetch failed")
            finalized = anchor.finalize_selector_payload(legal, json.loads(schedule.read_text())["sessions"], payload,
                                                        anchor.production_anchor_policy())
            selector.write_text(json.dumps(finalized))
            stats = anchor.run()
            first = json.loads(selector.read_text(encoding="utf-8"))
            anchor.run()  # the final public-build reapply must be idempotent
            assert first["dates"] == json.loads(selector.read_text(encoding="utf-8"))["dates"]
            return stats, json.loads((directory / "anchors.json").read_text(encoding="utf-8")), first
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


class DemandPublicationTests(unittest.TestCase):
    def test_reviewed_deadline_flows_from_endpoint_to_public_schedule_calendar_and_anchor(self):
        occurrence, _ = fixture("2030-09-08")
        deadline = {**occurrence, "session_id":"11341058", "start_at":"2030-09-08T00:00:00-04:00",
                    "end_at":"2030-09-08T02:00:00-04:00", "course_name":"BLS Renewal", "mapping_status":"mapped"}
        health = {"external_class_id":"11341058", "start_at":deadline["start_at"],
                  "status":"classified_non_session", "non_session_classification":"renewal_deadline",
                  "reason":"owner_confirmed_renewal_deadline", "source_observed_at":datetime.now(timezone.utc).isoformat(),
                  "registrations":[{"email":"must-not-publish@example.test"}]}
        payload = endpoint_payload(occurrence, 1)
        output = subprocess.run(["node",str(ROOT/"tests/helpers/canonical_demand_endpoint.cjs")],
                                input=json.dumps({"sessions":[], "health":{"sessions":[health]}}),
                                capture_output=True,text=True,check=True)
        payload["non_session_sources"] = json.loads(output.stdout)["non_session_sources"]
        self.assertNotIn("email",json.dumps(payload))
        payload = fetcher.validate_payload(payload)
        public, _ = anchor.apply_demand_projection([deadline,occurrence],payload)
        self.assertEqual([r["session_id"] for r in public],[occurrence["session_id"]])
        self.assertEqual(anchor.promote_seated_sessions(public)[0]["promotion_reason"],"canonical_active_registration")
        admin = build_admin_schedule({"sessions":[deadline,occurrence]},canonical_demand=payload)
        self.assertEqual(admin["counts"]["excluded_canonical_non_sessions"],1)
        self.assertNotIn("11341058",build_ical(admin))
        self.assertIn(occurrence["session_id"],build_ical(admin))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/"data/config").mkdir(parents=True)
            for path in ("data/config/course_map.json", "data/config/location_resource_map.json", "data/course_aliases.json"):
                shutil.copyfile(ROOT/path,root/path)
            (root/"data/runtime").mkdir()
            (root/"data/runtime/canonical_scheduling_demand.json").write_text(json.dumps(payload))
            raw = {"build":{"source_mode":"enrollware_ical_authoritative"},"sessions":[deadline,{**occurrence,"mapping_status":"mapped"}]}
            (root/"data/sessions_current.json").write_text(json.dumps(raw))
            page = root/"docs/classes/11341058.html"
            page.parent.mkdir(parents=True)
            page.write_text("stale booking page")
            for _ in range(2):
                with patch("sys.argv",["build_schedule_future","--repo-root",str(root)]), patch.object(future,"BuildStatusReporter"), patch.object(future,"write_status_snapshot"):
                    self.assertEqual(future.main(),0)
                published = json.loads((root/"docs/data/schedule_future.json").read_text())
                self.assertEqual([r["session_id"] for r in published["sessions"]],[occurrence["session_id"]])
                self.assertEqual(published["build"]["counts"]["skipped_canonical_non_sessions"],1)
                self.assertFalse(page.exists())
            self.assertEqual(json.loads((root/"data/sessions_current.json").read_text()),raw)
            (root/"docs/data/admin_schedule.json").write_text(json.dumps(admin))
            (root/"docs/data/landerware.ics").write_text(build_ical(admin))
            validate_non_session_publication(root,payload)
            page.write_text("regressed booking page")
            with self.assertRaisesRegex(ValueError,"non-session page remains"):
                validate_non_session_publication(root,payload)

        for invalid in ({**deadline,"start_at":"2030-09-09T00:00:00-04:00"}, {**deadline,"start_at":None}):
            with self.assertRaisesRegex(ValueError,"identity changed"):
                exclude_non_session_sources([invalid],payload)
        for classification in ("unknown","inactive_location"):
            wrong = deepcopy(payload)
            wrong["non_session_sources"][0]["classification"] = classification
            with self.assertRaisesRegex(ValueError,"Unproven"):
                fetcher.validate_payload(wrong)
        # An unclassified zero-demand/unknown row is never silently discarded.
        self.assertEqual(exclude_non_session_sources([deadline],{"non_session_sources":[]})[0],[deadline])

    def test_0_1_0_refresh_on_weekday_saturday_and_sunday(self):
        for day in ("2030-09-02","2030-09-07","2030-09-08"):
            with self.subTest(day=day), tempfile.TemporaryDirectory() as directory:
                _, empty, _ = publish_fixture(directory, day, 0)
                self.assertEqual(empty["anchors"],[])
                _, active, selector = publish_fixture(directory, day, 1)
                self.assertEqual(active["anchors"][0]["promotion_reason"],"canonical_active_registration")
                offers = [o for d in selector["dates"] for s in d["startTimes"] for o in s["courses"]]
                barnacles = [o for o in offers if o.get("schedule_role") == "barnacle"]
                self.assertEqual(barnacles,[])  # Full BLS and HeartCode are not an approved compatibility pair.
                self.assertEqual({o["startTime"] for o in offers},{"13:00"})
                _, refreshed, again = publish_fixture(directory, day, 1)
                self.assertEqual(active["anchors"],refreshed["anchors"])
                for result in (selector, again):
                    for day_row in result["dates"]:
                        for slot in day_row["startTimes"]:
                            for offer in slot["courses"]:
                                offer.pop("validUntil", None)
                self.assertEqual(selector["dates"],again["dates"])
                _, cancelled, _ = publish_fixture(directory, day, 0)
                self.assertEqual(cancelled["anchors"],[])
                session = json.loads((Path(directory)/"schedule.json").read_text(encoding="utf-8"))["sessions"][0]
                self.assertNotIn("schedule_role",session)
                self.assertEqual(session["active_registration_count"],0)
                _, final, _ = publish_fixture(directory, day, 0)
                self.assertEqual(final["anchors"],[])

    def test_separate_commitment_and_manual_override_survive_zero(self):
        for basis in ("committed_public_session","manual_override"):
            with tempfile.TemporaryDirectory() as directory:
                publish_fixture(directory,"2030-09-08",1,commitment=basis)
                _, feed, _ = publish_fixture(directory,"2030-09-08",0)
                self.assertEqual(feed["anchors"][0]["promotion_reason"],basis)

    def test_legacy_explicit_commitment_survives_a_demand_refresh(self):
        for basis in ("committed_public_session", "manual_override"):
            with tempfile.TemporaryDirectory() as directory:
                occurrence, _ = fixture("2030-09-08")
                occurrence["promotion_reason"] = basis
                (Path(directory)/"schedule.json").write_text(json.dumps({"sessions":[occurrence]}),encoding="utf-8")
                publish_fixture(directory,"2030-09-08",1)
                _, feed, _ = publish_fixture(directory,"2030-09-08",0)
                self.assertEqual(feed["anchors"][0]["promotion_reason"],basis)

    def test_missing_and_ambiguous_demand_clear_previous_projection(self):
        row, _ = fixture("2030-09-08")
        demand = endpoint_payload(row,1)["sessions"][0]
        previous, _ = resolve_canonical_demand([row],[demand])
        for rows in ([],[demand,{**demand,"canonical_session_id":"conflicting-session"}]):
            resolved, audit = resolve_canonical_demand(previous,rows)
            self.assertIsNone(resolved[0]["active_registration_count"])
            self.assertFalse(resolved[0]["count_available"])
            self.assertEqual(anchor.promote_seated_sessions(resolved),[])
            self.assertFalse(any(a["result"] == "matched" for a in audit))

    def test_missing_snapshot_blocks_publication(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(anchor,"CANONICAL_DEMAND_PATH",Path(directory)/"absent.json"):
            with self.assertRaisesRegex(ValueError,"Fresh canonical"):
                anchor.sessions_with_canonical_demand([])

    def test_each_publisher_fetches_before_applying_and_registration_only_change_runs_anchor_step(self):
        for name in ("refresh-admin-availability.yml","refresh-public-site.yml"):
            source = (ROOT/".github/workflows"/name).read_text(encoding="utf-8")
            self.assertLess(source.index("python -m scripts.fetch_canonical_scheduling_demand"), source.index("python -m scripts.apply_anchor_policy"))
        source = (ROOT/".github/workflows/refresh-public-site.yml").read_text(encoding="utf-8")
        condition = source.split("- name: Reapply canonical Anchor metadata after public rebuild",1)[1].split("shell:",1)[0]
        self.assertIn("steps.canonical.outputs.changed == 'true'",condition)
        admin = (ROOT/".github/workflows/refresh-admin-availability.yml").read_text(encoding="utf-8")
        self.assertLess(admin.index("python -m scripts.fetch_canonical_scheduling_demand"),admin.index("python -m scripts.build_schedule_future"))


if __name__ == "__main__":
    unittest.main()
