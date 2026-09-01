import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from hx_builder import HxBuilder, adapt_enrollware_csv


SAMPLE = json.loads((ROOT / "tests/fixtures/hx_builder_sample.json").read_text(encoding="utf-8"))
REFERENCE = json.loads((ROOT / "tests/fixtures/hx_builder_reference.json").read_text(encoding="utf-8"))
MIGRATION = (
    ROOT / "supabase/migrations/20260901040152_hx_builder_evidence_inventory_contracts.sql"
).read_text(encoding="utf-8")


def build():
    return HxBuilder(SAMPLE, REFERENCE).process()


def test_dry_run_only_and_required_totals():
    report = build()
    assert report["worker"] == "Hx-Builder"
    assert report["mode"] == "dry_run"
    assert report["mutation_performed"] is False
    assert report["authority"] == "customers -> registrations -> class_sessions"
    assert report["summary"] == {
        "source_records_examined": 9,
        "people_matched": 1,
        "people_created": 1,
        "sessions_matched": 2,
        "sessions_created": 1,
        "registrations_matched": 2,
        "registrations_created": 1,
        "reschedules_reconstructed": 1,
        "completions_reconstructed": 1,
        "credentials_cards_reconstructed": 1,
        "unresolved_identities": 1,
        "ambiguous_conflicting_facts": 1,
        "duplicate_candidates": 1,
        "records_intentionally_excluded": 1,
    }
    assert report["reconciliation_totals_by_course_date_source"]


def test_identity_and_source_record_replay_are_idempotent():
    report = build()
    duplicate = report["duplicate_candidates"][0]
    assert duplicate["kind"] == "source_record_replay"
    enrollware = next(x for x in report["decisions"] if x["source_record_id"] == "ew-r1")
    assert enrollware["source_record_resolution"] == "matched"
    assert enrollware["person_resolution"] == "matched_alias"
    assert enrollware["session_resolution"] == "matched"
    assert enrollware["registration_resolution"] == "matched"


def test_conflicting_identity_is_review_only():
    report = build()
    conflict = next(x for x in report["unresolved_or_ambiguous"] if x["kind"] == "identity")
    assert conflict["candidate_customer_ids"] == ["customer-2", "customer-3"]
    assert not any(
        op.get("source_record_id") == "gmail-conflict-1"
        and op["command"] == "register_participant"
        for op in report["proposed_operations"]
    )


def test_reschedule_preserves_lineage_without_attendance_inference():
    report = build()
    move = next(op for op in report["proposed_operations"] if op["command"] == "move_registration")
    assert move["customer_id"] == "customer-1"
    assert move["source_session_id"] == "session-old"
    assert move["target_session_id"] == "session-new"
    assert move["reason"] == "customer rescheduled"
    assert move["occurred_at"] == "2024-01-15T12:00:00-05:00"
    assert not any(
        assertion["source_record_id"] == "doc-move-1"
        and assertion["fact_type"] == "attendance"
        for assertion in report["evidence_assertions"]
    )


def test_completion_credential_and_products_are_distinct_facts():
    report = build()
    types = {
        a["fact_type"] for a in report["evidence_assertions"]
        if a["source_record_id"] == "atlas-card-1"
    }
    assert types == {"attendance", "completion", "credential"}
    enrollware_types = {
        a["fact_type"] for a in report["evidence_assertions"]
        if a["source_record_id"] == "ew-r1"
    }
    assert "completion" not in enrollware_types


def test_every_assertion_retains_batch_source_confidence_and_original_value():
    for assertion in build()["evidence_assertions"]:
        assert assertion["import_batch_id"] == "hx-contract-fixture-v1"
        assert assertion["source"]
        assert assertion["source_record_id"]
        assert assertion["confidence_state"]
        assert assertion["original_source_value"]


def test_prepaid_inventory_is_generic_pool_event():
    report = build()
    event = next(
        op for op in report["proposed_operations"]
        if op["command"] == "propose_inventory_entitlement_event"
    )
    assert event["pool_key"] == "customer-prepaid-ecards-1"
    assert event["pool_id"] == "pool-1"
    assert event["quantity_delta"] == -1
    assert event["event_type"] == "consumed"
    assert "nhcso" not in json.dumps(event).lower()


def test_schema_contract_is_append_only_service_only_and_canonical():
    assert "public.lifecycle_evidence_assertions" in MIGRATION
    assert "public.inventory_entitlement_pools" in MIGRATION
    assert "public.inventory_entitlement_events" in MIGRATION
    assert "references public.customers" in MIGRATION
    assert "references public.registrations" in MIGRATION
    assert "references public.class_sessions" in MIGRATION
    assert "enable row level security" in MIGRATION
    assert "revoke all on table public.%I from anon, authenticated" in MIGRATION
    assert "before update or delete" in MIGRATION
    assert "supersedes_assertion_id" in MIGRATION
    assert "original_source_value jsonb not null" in MIGRATION
    assert "create table public.landerware_" not in MIGRATION


def test_enrollware_adapter_does_not_infer_completion_from_status():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        csv_path = base / "events.csv"
        seeds_path = base / "seeds.json"
        csv_path.write_text(
            "regId,courseId,courseSchedId,courseName,locationName,startTime,instructor,firstName,lastName,emailAddress,status,balanceDue\n"
            "r1,c1,s1,BLS,Office,2024-01-01 09:00:00,Instructor,Alex,Rivera,alex@example.test,Completed,0\n",
            encoding="utf-8",
        )
        seeds_path.write_text(json.dumps({"seeds": []}), encoding="utf-8")
        payload = adapt_enrollware_csv(csv_path, seeds_path)
    record = payload["records"][0]
    assert "completion" not in record["facts"]
    assert record["registration"]["status"] == "Completed"
    assert record["source_record_id"] == "r1"
