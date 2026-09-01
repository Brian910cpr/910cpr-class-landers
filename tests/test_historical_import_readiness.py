import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from historical_import_readiness import REPORT_KEYS, reconcile


FIXTURE = json.loads(
    (ROOT / "tests/fixtures/historical_import_readiness.json").read_text(encoding="utf-8")
)


def test_harness_is_read_only_and_explains_every_required_count():
    report = reconcile(FIXTURE["sample"], FIXTURE["reference"])
    assert report["mode"] == "dry_run"
    assert report["mutation_performed"] is False
    assert set(report["counts"]) == set(REPORT_KEYS)


def test_external_replay_and_alias_are_idempotent():
    report = reconcile(FIXTURE["sample"], FIXTURE["reference"])
    assert report["counts"]["customers_matched_through_aliases"] == 1
    assert report["counts"]["duplicates_suppressed"] == 1
    first = report["decisions"][0]
    assert first["registration_action"] == "suppress_duplicate"
    assert first["rule"] == "do_not_overwrite"
    assert report["counts"]["records_changing_existing_facts"] == 1


def test_conflicting_exact_identity_requires_review():
    report = reconcile(FIXTURE["sample"], FIXTURE["reference"])
    assert report["counts"]["ambiguous_identities"] == 1
    second = report["decisions"][1]
    assert second["action"] == "review"
    assert len(second["candidates"]) == 2


def test_missing_facts_are_unknown_not_false():
    report = reconcile(FIXTURE["sample"], FIXTURE["reference"])
    new_record = report["decisions"][2]
    assert set(new_record["unknown_facts"]) == {
        "completion", "credential", "materials", "payment"
    }
    assert report["counts"]["customers_newly_proposed"] == 1
