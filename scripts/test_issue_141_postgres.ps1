$ErrorActionPreference = "Stop"

if (-not $env:DATABASE_URL) { throw "DATABASE_URL is required" }

psql $env:DATABASE_URL -v ON_ERROR_STOP=1 -f supabase/tests/issue_141_bootstrap.sql
psql $env:DATABASE_URL -v ON_ERROR_STOP=1 -f supabase/migrations/20260810020058_maxim_durable_records.sql
psql $env:DATABASE_URL -v ON_ERROR_STOP=1 -f supabase/migrations/20260911190000_attendance_scheduling_state_gate.sql

$before = psql $env:DATABASE_URL -Atqc "select count(*) from public.landerware_organizations"
psql $env:DATABASE_URL -v ON_ERROR_STOP=1 -f supabase/tests/issue_141_attendance_scheduling_state.sql
$after = psql $env:DATABASE_URL -Atqc "select count(*) from public.landerware_organizations"
if ($before -ne $after) { throw "rollback proof failed: fixture rows persisted" }

python supabase/tests/issue_141_concurrency.py
python -m unittest tests.test_issue_141_attendance_scheduling_migration

Write-Output "Issue 141 PostgreSQL proof passed; rollback row count remained $after"
