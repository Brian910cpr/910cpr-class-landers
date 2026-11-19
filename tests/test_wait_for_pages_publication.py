"""Synthetic freshness/identity regressions for the read-only Pages observer gate."""
import io
import json
import os
import tempfile
import unittest
from http.client import IncompleteRead
from unittest.mock import patch

from scripts.wait_for_pages_publication import main, matching_pages_run, read_runs

REFRESH_DONE = "2026-11-18T17:04:48Z"
SHA = "164f3e23f5bf037e7a69002e5a59719701e3dcf0"


def run(created, sha=SHA, status="completed", conclusion="success", name="pages build and deployment"):
    return dict(created_at=created, head_sha=sha, status=status,
                conclusion=conclusion, name=name)


class PagesPublicationWaitTests(unittest.TestCase):
    def test_matching_new_pages_deployment(self):
        item = run("2026-11-18T17:04:47Z")
        self.assertEqual(matching_pages_run([item], SHA, REFRESH_DONE), item)

    def test_old_release_cannot_satisfy_fresh_commit(self):
        self.assertIsNone(matching_pages_run(
            [run("2026-11-18T17:04:47Z", sha="another-commit")], SHA, REFRESH_DONE))
        self.assertIsNone(matching_pages_run(
            [run("2026-11-18T16:52:00Z")], SHA, REFRESH_DONE))

    def test_wrong_workflow_cannot_count_as_deployment(self):
        self.assertIsNone(matching_pages_run(
            [run("2026-11-18T17:04:47Z", name="Refresh admin availability")],
            SHA, REFRESH_DONE))

    def test_latest_matching_run_is_not_hidden_by_older_success(self):
        early = run("2026-11-18T17:04:47Z")
        latest = run("2026-11-18T17:05:47Z", status="in_progress", conclusion=None)
        self.assertEqual(matching_pages_run([early, latest], SHA, REFRESH_DONE), latest)

    def test_sha_scoped_api_query_and_complete_bounded_pagination(self):
        first = [run("2026-11-18T17:04:47Z")] * 30
        second = [run("2026-11-18T17:05:47Z")]
        requests = []

        def response(request, timeout):
            requests.append((request.full_url, timeout))
            rows = first if len(requests) == 1 else second
            return io.BytesIO(json.dumps({"workflow_runs": rows}).encode())

        with patch("scripts.wait_for_pages_publication.urlopen", side_effect=response):
            items = read_runs("example/repo", "test-token", SHA)
        self.assertEqual(len(items), 31)
        self.assertEqual(len(requests), 2)
        self.assertTrue(all(f"head_sha={SHA}" in url for url, _ in requests))
        self.assertTrue(all("per_page=30" in url for url, _ in requests))
        self.assertIn("page=2", requests[-1][0])

    def test_incomplete_github_response_retries_then_verifies_actual_sha(self):
        event = {"workflow_run": {"name": "Refresh admin availability",
                "conclusion": "success", "updated_at": REFRESH_DONE}}
        with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as handle:
            json.dump(event, handle)
            handle.flush()
            with patch.dict(os.environ, {"GITHUB_EVENT_PATH": handle.name,
                    "GITHUB_REPOSITORY": "example/repo", "GITHUB_SHA": SHA,
                    "GITHUB_TOKEN": "test-token"}):
                with patch("scripts.wait_for_pages_publication.read_runs",
                           side_effect=[IncompleteRead(b"partial", 200),
                                        [run("2026-11-18T17:05:47Z")]]) as api:
                    with patch("scripts.wait_for_pages_publication.time.sleep"):
                        self.assertEqual(main(), 0)
            self.assertEqual(api.call_count, 2)

    def test_bounded_pages_exhaustion_fails_closed(self):
        full = [run("2026-11-18T17:04:47Z")] * 30
        def response(_request, timeout):
            # Each HTTP request gets its own stream, just like urlopen.
            return io.BytesIO(json.dumps({"workflow_runs": full}).encode())
        with patch("scripts.wait_for_pages_publication.urlopen", side_effect=response):
            with self.assertRaisesRegex(ValueError, "bounded pagination"):
                read_runs("example/repo", "test-token", SHA)

    def test_absent_run_fails_closed(self):
        self.assertIsNone(matching_pages_run([], SHA, REFRESH_DONE))


if __name__ == "__main__":
    unittest.main()
