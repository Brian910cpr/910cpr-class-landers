from pathlib import Path


SQL = (Path(__file__).resolve().parents[1] / "data/audit/hx_session_alias_migration_review.sql").read_text(encoding="utf-8")


def test_alias_migration_is_fail_closed_and_service_only():
    assert SQL.count("revoke all privileges on table public.historical_") == 3
    assert "default 'unreviewed'" in SQL
    assert "default false" in SQL
    assert SQL.count("primary key (source_system, source_label)") == 3
    assert "historical alias identity, target, and provenance are immutable" in SQL
    assert "not active or (review_status in ('reviewed','approved_legacy')" in SQL
    assert "reviewed_by is not null" in SQL
    assert "Plain INSERT plus the scoped primary key deliberately fails closed" in SQL
    assert "on conflict" not in SQL.lower()


def test_only_reviewed_alias_counts_are_present():
    assert SQL.count("insert into public.historical_location_aliases") == 2
    assert SQL.count("insert into public.historical_instructor_aliases") == 55
    assert SQL.count("insert into public.historical_course_aliases") == 15
    assert SQL.count("'migration_review:8e3d48d2ae8'") == 72
