# Codex Reply — Issue 141, Round 9

- Assignment: isolated PostgreSQL proof for the Issue #141 attendance/scheduling-state gate
- Timestamp: 2026-09-11T16:17:38-04:00 (America/New_York)
- Branch: `codex/issue-141-r9-postgres-proof`
- Substantive commit: `13e8824825ec2b2af52dab92f13e8e6a56065c4d`
- PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/196
- Work-item state: `PR_OPEN`
- Persistent evidence: `PROVEN` for the isolated database safety gate; the production feature remains `BUILT`, not production-`CONNECTED` or production-`PROVEN`

## Findings

The complete R6/R7/R8 stack executes successfully in disposable PostgreSQL. The smallest missing prerequisite was a vanilla-PostgreSQL bootstrap defining the three Supabase roles and the two pre-existing Maxim tables required by `20260810020058_maxim_durable_records.sql`. No production migration was weakened or changed.

Real concurrent calls with the same idempotency key serialize deterministically for both scheduling and attendance: one call reports a first effect and the other an idempotent replay. Each path leaves exactly one immutable record and one audit event.

## Work performed

- Added a GitHub Actions PostgreSQL 16.4 service test.
- Applied the checked-in durable-record prerequisite migration and the complete proposed R6–R8 gate migration unchanged.
- Executed the rollback-only database test with `ON_ERROR_STOP=1`.
- Verified its fixture row count was zero before and after rollback.
- Executed two genuinely concurrent database connections for each idempotency path.
- Retained the existing static contract suite as an additional guard.

## Exact files changed

- `.github/workflows/issue-141-postgres-proof.yml`
- `scripts/test_issue_141_postgres.ps1`
- `supabase/tests/issue_141_bootstrap.sql`
- `supabase/tests/issue_141_concurrency.py`
- `tests/test_issue_141_attendance_scheduling_migration.py`
- `Codex_Reply_Issue141_R9.md`

No UI, generator, production migration, or outbound communication file was changed. The fresh worktree presented an unrelated modified generated file, `docs/Earl/index.html`, immediately after checkout; it was preserved and excluded. Local Python bytecode was also left untracked and excluded.

## Exact tests and results

- Local: `python -m unittest tests.test_issue_141_attendance_scheduling_migration` — 6/6 passed.
- Local: `python -m py_compile supabase/tests/issue_141_concurrency.py tests/test_issue_141_attendance_scheduling_migration.py` — passed.
- Local: `git diff --check` — passed.
- GitHub Actions workflow run: `34643326908`; job `103408067758` — passed in 35 seconds.
- Database: PostgreSQL `16.4 (Debian 16.4-1.pgdg120+2)`, 64-bit.
- Commands executed by the green runner:
  - `psql $DATABASE_URL -v ON_ERROR_STOP=1 -f supabase/tests/issue_141_bootstrap.sql`
  - `psql $DATABASE_URL -v ON_ERROR_STOP=1 -f supabase/migrations/20260810020058_maxim_durable_records.sql`
  - `psql $DATABASE_URL -v ON_ERROR_STOP=1 -f supabase/migrations/20260911190000_attendance_scheduling_state_gate.sql`
  - `psql $DATABASE_URL -v ON_ERROR_STOP=1 -f supabase/tests/issue_141_attendance_scheduling_state.sql`
  - `python supabase/tests/issue_141_concurrency.py`
- Rollback proof: organization fixture count remained `0`; the SQL script emitted `BEGIN`, `DO`, `ROLLBACK` without error.
- Concurrency proof: scheduling produced one request receipt and one scheduling audit event; attendance produced one assertion and one attendance audit event. Each concurrent pair returned exactly `[first effect, idempotent replay]`.
- Historical replay proof: request A, request B, exact replay A retained two receipts/two audit events and did not restore A; mismatched replay A failed closed.
- Safety proof: unknown passed-session attendance produced internal closeout state and zero outbound messages; affirmative absence without matching provenance was rejected.
- All PR checks passed: PostgreSQL proof, both preflight checks, both truncation guards, and Cloudflare Pages.

## Deployment and migration status

- Local validation: passed.
- Isolated database execution: passed.
- Push: substantive branch and PR pushed.
- Merge: not attempted.
- Production migration: not attempted; production database unchanged.
- Outbound participant/employer sends: disabled and absent.

## Remaining risks and next action

PR #196 is intentionally stacked on PR #195 so R7/R8 hardening cannot be lost. Review and merge/consolidate PRs #193 → #194 → #195 → #196 in dependency order, or retarget the consolidated final branch after its predecessors merge. Only after that review should an explicitly authorized production migration round be considered. Keep #129 browser/UI work paused.

No Brian account-level action is required for this proof. Production migration authorization remains a separate future decision.
