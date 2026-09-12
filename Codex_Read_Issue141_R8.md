# Codex Reply — Issue 141, Round 8

- Assignment: GitHub issue #141, attendance/scheduling backend stabilization continuation
- Timestamp: 2026-09-11T15:35:18-04:00 (America/New_York)
- Branch: `codex/issue-141-r8-request-idempotency`
- Substantive commit: `423ce261b592fbe625fffee4ae40a85752163921`
- Work-item state: `PR_OPEN`
- Persistent-system evidence state: `BUILT`; not `CONNECTED` or `PROVEN`

## Finding and root cause

Round 7 correctly rejected mismatched reuse of the current scheduling idempotency key, but the key was stored only on the mutable `landerware_requirement_scheduling_state` row. A later valid scheduling request replaced that key. Replaying the earlier key after that replacement was therefore treated as new work, could restore older deadline state, and could emit a duplicate `scheduling_requested` audit event.

## Work performed

- Added immutable `landerware_scheduling_request_receipts` rows keyed by idempotency key.
- Changed `landerware_request_scheduling` to validate replays against immutable receipts before touching current state.
- Preserved transactional behavior: current-state projection, immutable receipt, and audit event succeed or roll back together.
- Enabled RLS and removed `anon`/`authenticated` access to the new backend-only table.
- Added rollback-only SQL assertions proving that two distinct requests can occur and an older-key replay creates neither a third receipt nor a third audit event.
- Kept all participant/employer outbound sends absent and `outboundEnabled=false`.

## Exact files changed

- `supabase/migrations/20260911190000_attendance_scheduling_state_gate.sql`
- `supabase/tests/issue_141_attendance_scheduling_state.sql`
- `tests/test_issue_141_attendance_scheduling_migration.py`
- `Codex_Reply_Issue141_R8.md`

The fresh worktree's unrelated generated `docs/Earl/index.html` modification was preserved and not staged.

## Validation

- `python -m unittest tests.test_issue_141_attendance_scheduling_migration -v` — 5/5 passed.
- `python -m py_compile tests/test_issue_141_attendance_scheduling_migration.py` — passed.
- `git diff --check` and staged diff check — passed (Git emitted only Windows line-ending notices).
- SQL database test remains rollback-only and ends in `rollback;`.
- No generator ran.
- No production migration, database write, UI/browser change, or outbound communication was attempted.

## Known limitation / exact blocker

The SQL migration and rollback test were not executed against PostgreSQL. This environment has no `psql`, Supabase CLI, Docker, or Podman runtime; `wsl.exe` is present only as the Windows stub and reports that WSL is not installed. Therefore concurrent and historical-key replay behavior is contract-tested but not database-proven.

## Deployment status

- Local validation: passed at contract-test level.
- Push: branch and receipt pushed.
- Merge: not attempted.
- Migration/deployment: not attempted.
- Production database: unchanged.
- Last successful end-to-end proof: none for this new attendance/scheduling gate.
- Failure/staleness detection and observer: not applicable until the migration is connected; outbound processing remains disabled.

## Remaining risks and next action

Run PR #193 + #194 + this Round 8 migration and `supabase/tests/issue_141_attendance_scheduling_state.sql` in an isolated, prerequisite-complete PostgreSQL database. Include concurrent same-key calls and the new historical-key replay sequence. If that passes, review and merge the stacked backend PRs in order. Do not migrate production or enable outbound sends until isolated DB proof succeeds.

No Brian/user-level action is required if the supervisor can provide the isolated database runner. Account-level production access is not required for this next proof.
