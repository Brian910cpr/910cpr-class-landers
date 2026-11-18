"""Synthetic freshness/identity regressions for the read-only Pages observer gate."""
import unittest

from scripts.wait_for_pages_publication import matching_pages_run

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

    def test_absent_run_fails_closed(self):
        self.assertIsNone(matching_pages_run([], SHA, REFRESH_DONE))


if __name__ == "__main__":
    unittest.main()
