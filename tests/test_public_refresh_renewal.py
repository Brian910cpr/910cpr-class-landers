"""Check all rendered dynamic leases and the workflow's read-only renewal wiring."""
import datetime
import json
import re
import tempfile
import unittest
from pathlib import Path
from scripts.audit_family_publication_coverage import FAMILIES
from scripts.publication_renewal import publication_needs_renewal

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/refresh-public-site.yml"
NOW = datetime.datetime(2026, 10, 2, 10, 43, tzinfo=datetime.timezone.utc)

class PublicationRenewalTests(unittest.TestCase):
    def evaluate(self, minutes=90, bad=None, missing=None, root=None, change=None):
        def run(folder):
            folder.mkdir(parents=True, exist_ok=True)
            lease = (NOW + datetime.timedelta(minutes=minutes)).isoformat()
            for key in FAMILIES:
                path = folder / (key + ".json")
                if key == missing:
                    path.unlink(missing_ok=True)
                    continue
                payload = {"validUntil": bad if key == "bls" and bad is not None else lease,
                           "dates": [{"startTimes": [{"courses": [
                               {"offerType": "seated_class"},
                               {"offerType": "dynamic_appointment", "validUntil": lease}
                           ]}]}]}
                if change:
                    change(key, payload)
                path.write_text(json.dumps(payload))
            before = {p.name: p.read_bytes() for p in folder.glob("*.json")}
            result = publication_needs_renewal(folder, NOW)
            self.assertEqual(before, {p.name: p.read_bytes() for p in folder.glob("*.json")})
            return result
        if root is not None:
            return run(root)
        with tempfile.TemporaryDirectory() as d:
            return run(Path(d))

    def test_due_before_next_cycle_and_processing(self):
        self.assertTrue(self.evaluate(minutes=37))
    def test_exact_margin_boundary(self):
        self.assertTrue(self.evaluate(minutes=45))
    def test_just_outside_margin_unchanged(self):
        self.assertFalse(self.evaluate(minutes=45.1))
    def test_already_expired(self):
        self.assertTrue(self.evaluate(minutes=-1))
    def test_no_change_and_not_due(self):
        self.assertFalse(self.evaluate())
    def test_missing_or_invalid_lease_renews(self):
        self.assertTrue(self.evaluate(missing="pals"))
        self.assertTrue(self.evaluate(bad="not-a-date"))
        self.assertTrue(self.evaluate(bad="2026-10-03T12:00:00"))
    def test_each_family_and_earliest_individual_offer(self):
        self.assertEqual(set(FAMILIES), {"bls", "heartsaver", "acls", "pals", "arc", "hsi", "uscg_first_aid_cpr_aed", "family_cpr"})
        for family in FAMILIES:
            with self.subTest(family=family):
                self.assertTrue(self.evaluate(missing=family))
                def change(key, payload):
                    if key == family:
                        payload["dates"][0]["startTimes"][0]["courses"].append(
                            {"offerType": "dynamic_appointment", "validUntil": NOW.isoformat()})
                self.assertTrue(self.evaluate(change=change))
    def test_invalid_or_missing_dynamic_lease_renews(self):
        for value in (None, "bad", "2026-10-03T12:00:00"):
            def change(key, payload):
                if key == "arc":
                    offer = payload["dates"][0]["startTimes"][0]["courses"][1]
                    if value is None:
                        del offer["validUntil"]
                    else:
                        offer["validUntil"] = value
            self.assertTrue(self.evaluate(change=change))
    def test_seated_class_does_not_require_individual_lease(self):
        def change(key, payload):
            payload["dates"][0]["startTimes"][0]["courses"] = [{"offerType": "seated_class"}]
        self.assertFalse(self.evaluate(change=change))
    def test_empty_dates_valid_but_missing_dates_fail_closed(self):
        self.assertFalse(self.evaluate(change=lambda key, payload: payload.update(dates=[])))
        self.assertTrue(self.evaluate(change=lambda key, payload: payload.pop("dates")))
    def test_queued_contender_rechecks_new_publication(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.assertTrue(self.evaluate(minutes=20, root=root))
            self.assertFalse(self.evaluate(minutes=90, root=root))
    def test_workflow_uses_renewal_and_source_change(self):
        source = WORKFLOW.read_text()
        self.assertIn("python -m scripts.publication_renewal --margin-minutes 45", source)
        self.assertIn("$rebuildRequired = ($currentHash -ne $previousHash) -or $renewPublication", source)
        self.assertIn("Publication renewal check failed; preserving published inventory.", source)
        self.assertIn("if ($LASTEXITCODE -ne 0 -or $renewResult -notin", source)
    def test_concurrent_publication_guards_preserved(self):
        source = WORKFLOW.read_text()
        self.assertRegex(source, r"concurrency:\s*\n\s*group: schedule-publish-main\s*\n\s*cancel-in-progress: false")
        self.assertIn("ref: main", source)
        self.assertIn("if ($remoteMain -ne $baseCommit)", source)
        self.assertIn("Refusing to replay generated output onto a different source tree", source)
    def test_cadence_and_budget_cover_observed_run(self):
        source = WORKFLOW.read_text()
        self.assertIn('cron: "13,43 * * * *"', source)
        margin = int(re.search(r"--margin-minutes (\d+)", source).group(1))
        self.assertGreaterEqual(margin, 30+7+8)

if __name__ == "__main__":
    unittest.main()
