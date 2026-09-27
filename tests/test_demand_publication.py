"""Isolated endpoint -> HTTP fetch -> runtime -> published selector proof.

The fixtures never write to production, real bookings, or repository public files.
"""
from __future__ import annotations

from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch

from scripts import apply_anchor_policy as anchor
from scripts import fetch_canonical_scheduling_demand as fetcher
from scripts.canonical_scheduling_demand import resolve_canonical_demand

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
            "location":occurrence["location_name"],"offerType":"dynamic_appointment",
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
        "registrations":[{"status":"registered"} for _ in range(count)] + [{"status":"canceled"}],
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
            if fetcher.run() != 0:
                raise AssertionError("Fixture fetch failed")
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
    def test_0_1_0_refresh_on_weekday_saturday_and_sunday(self):
        for day in ("2030-09-02","2030-09-07","2030-09-08"):
            with self.subTest(day=day), tempfile.TemporaryDirectory() as directory:
                _, empty, _ = publish_fixture(directory, day, 0)
                self.assertEqual(empty["anchors"],[])
                _, active, selector = publish_fixture(directory, day, 1)
                self.assertEqual(active["anchors"][0]["promotion_reason"],"canonical_active_registration")
                offers = [o for d in selector["dates"] for s in d["startTimes"] for o in s["courses"]]
                barnacles = [o for o in offers if o.get("schedule_role") == "barnacle"]
                self.assertEqual({o["startTime"] for o in barnacles},{"12:00","15:00"})
                self.assertEqual({o["attached_to_session_id"] for o in barnacles},{"fixture-occurrence"})
                self.assertEqual({o["barnacle_direction"] for o in barnacles},{"pre","post"})
                _, refreshed, again = publish_fixture(directory, day, 1)
                self.assertEqual(active["anchors"],refreshed["anchors"])
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


if __name__ == "__main__":
    unittest.main()
