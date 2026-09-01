from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT / "supabase/migrations/20260901113658_secure_ingestion_compliance_surfaces.sql"
).read_text(encoding="utf-8").lower()
TRIGGER_MIGRATION = (
    ROOT / "supabase/migrations/20260901114054_secure_compliance_trigger_helpers.sql"
).read_text(encoding="utf-8").lower()

TABLES = (
    "ingest_jobs",
    "ingest_facts",
    "ingest_review_queue",
    "compliance_requirement_sources",
    "compliance_requirements",
    "session_compliance_requirements",
    "historical_registration_import_rows",
)


def test_all_internal_tables_are_rls_enabled_and_browser_grants_revoked():
    for table in TABLES:
        assert f"alter table public.{table} enable row level security" in MIGRATION
        assert (
            f"revoke all privileges on table public.{table} "
            "from anon, authenticated"
        ) in MIGRATION


def test_internal_views_do_not_reexpose_protected_relations():
    assert (
        "revoke all privileges on table public.ingest_operational_dashboard "
        "from anon, authenticated"
    ) in MIGRATION
    assert (
        "revoke all privileges on table public.session_compliance_summary "
        "from anon, authenticated"
    ) in MIGRATION


def test_privileged_mutation_functions_are_service_only_and_hardened():
    for signature in (
        "import_historical_registration_batch(jsonb)",
        "populate_session_compliance_requirements(uuid)",
    ):
        assert (
            f"revoke all privileges on function public.{signature}\n"
            "  from public, anon, authenticated"
        ) in MIGRATION
        assert f"grant execute on function public.{signature}\n  to service_role" in MIGRATION
        assert f"alter function public.{signature}\n  set search_path = pg_catalog" in MIGRATION


def test_no_browser_policy_is_added_to_silence_rls_findings():
    assert "create policy" not in MIGRATION


def test_trigger_only_compliance_helpers_are_not_browser_rpcs():
    for signature in (
        "trg_seed_session_compliance()",
        "release_archive_when_compliant()",
    ):
        assert (
            f"revoke all privileges on function public.{signature}\n"
            "  from public, anon, authenticated"
        ) in TRIGGER_MIGRATION
        assert f"alter function public.{signature}\n  set search_path = pg_catalog" in TRIGGER_MIGRATION
