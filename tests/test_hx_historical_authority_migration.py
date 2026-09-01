import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT / "supabase/migrations/20260901054718_historical_location_authority_and_session_unknowns.sql"
).read_text(encoding="utf-8")
REPORT = json.loads(
    (ROOT / "data/audit/hx_historical_authority_migration_review_redacted.json")
    .read_text(encoding="utf-8")
)


def test_location_authority_fails_safe_and_is_audited():
    assert "alter column scheduling_status set default 'inactive'" in MIGRATION
    assert "historical_only" in MIGRATION
    assert "locations_public_requires_active_check" in MIGRATION
    assert "location_scheduling_status_events" in MIGRATION
    assert "a location referenced by an operational session cannot become" in MIGRATION
    assert "revoke all on table public.location_scheduling_status_events from anon, authenticated" in MIGRATION


def test_unknown_fields_are_historical_only_not_sentinels():
    assert "alter column lead_instructor_id drop not null" in MIGRATION
    assert "alter column end_at drop not null" in MIGRATION
    assert "class_sessions_operational_fields_check" in MIGRATION
    assert "class_sessions_historical_contract_check" in MIGRATION
    assert "drop function if exists public.class_sessions_historical_required_defaults" in MIGRATION
    assert "historical_unknown_instructor" not in MIGRATION
    assert "new.record_scope = 'operational'" in MIGRATION


def test_full_dry_run_gate_is_deterministic_and_review_preserving():
    assert REPORT["source_records_examined"] == 8199
    assert REPORT["historical_location_candidates"] == 126
    assert REPORT["historical_location_rows_resolvable"] == 3837
    assert REPORT["fully_canonicalized_sessions_before"] == 2063
    assert REPORT["fully_canonicalized_sessions_after_locations"] == 3439
    assert REPORT["sessions_accepted_with_unknown_instructor"] == 105
    assert REPORT["sessions_accepted_with_unknown_duration"] == 27
    assert REPORT["remaining_unresolved_locations"] == 421
    assert REPORT["remaining_course_ambiguity"] == 17
    assert REPORT["independent_run_equality"] is True
    assert REPORT["replay_additional_operations"] == 0
    assert REPORT["replay_additional_assertions"] == 0
    assert REPORT["unexplained_mismatches"] == 0
