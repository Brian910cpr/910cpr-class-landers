from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT / "supabase/migrations/20260901014900_canonical_participant_lifecycle.sql"
).read_text(encoding="utf-8")
BASELINE = (
    ROOT / "supabase/migrations/20260901014857_capture_nhcso_deployed_baseline.sql"
).read_text(encoding="utf-8")


def test_pr109_baseline_defines_but_does_not_invoke_promotion():
    assert "create or replace function public.promote_nhcso_class" in BASELINE
    assert "grant execute on function public.promote_nhcso_class(text) to service_role" in BASELINE
    assert "select public.promote_nhcso_class" not in BASELINE
    assert "perform public.promote_nhcso_class" not in BASELINE


def test_canonical_tables_reference_existing_authority():
    for table in (
        "customer_identity_aliases",
        "registration_supersessions",
        "registration_requirements",
        "participant_lifecycle_events",
        "participant_completions",
        "participant_credentials",
        "lifecycle_import_batches",
        "lifecycle_import_records",
    ):
        assert f"public.{table}" in MIGRATION
    assert "references public.customers" in MIGRATION
    assert "references public.registrations" in MIGRATION
    assert "references public.class_sessions" in MIGRATION
    assert "create table public.landerware_" not in MIGRATION


def test_lifecycle_tables_are_server_only_and_rls_protected():
    assert "enable row level security" in MIGRATION
    assert "revoke all on table public.%I from anon, authenticated" in MIGRATION
    assert "grant all on table public.%I to service_role" in MIGRATION
    assert "revoke all on function public.register_participant" in MIGRATION
    assert "revoke all on function public.move_registration" in MIGRATION


def test_registration_and_move_are_idempotent_and_append_events():
    assert "pg_advisory_xact_lock" in MIGRATION
    assert "'register:'||p_idempotency_key" in MIGRATION
    assert "on conflict(customer_id,class_session_id)" in MIGRATION
    assert "registration_supersessions where idempotency_key=p_idempotency_key" in MIGRATION
    assert "participant_lifecycle_events" in MIGRATION


def test_completed_history_and_paid_material_links_are_preserved():
    assert "participant_completions where registration_id=v_source.id" in MIGRATION
    assert "if not v_has_completion then" in MIGRATION
    assert "update public.registration_orders set registration_id=v_target_id" in MIGRATION
    assert "source_item_key" in MIGRATION


def test_ambiguous_identity_requires_review():
    assert "'ambiguous'" in MIGRATION
    assert "'review_required'" in MIGRATION
    assert "candidate_customer_ids" in MIGRATION
