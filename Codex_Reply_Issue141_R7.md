# Codex Reply — Issue 141, Round 7

- Assignment: GitHub issue #141, attendance/scheduling backend validation continuation
- Timestamp: 2026-09-11T15:15:58-04:00 (America/New_York)
- Branch: `codex/issue-141-r7-db-validation`
- Base: Round 6 pushed tip `eadd652e97b2f3f01077bfd80ce8f889556b0160`
- Substantive commit: `b1cd7af8f97063971cb3e604db9ab324afbbf43d`
- Work-item state: `PR_OPEN`
- Persistent-system evidence state: `BUILT`; not `CONNECTED` or `PROVEN`

## Finding and work performed

Round 6's replay path treated any existing idempotency key as a successful replay without proving that the new payload matched the original operation. A reused key could therefore return an unrelated scheduling request or attendance assertion. Concurrent calls with the same new key could also race past the initial lookup and duplicate audit/state work or raise a uniqueness error instead of producing deterministic replay behavior.

The migration now:

- serializes each idempotency key with a transaction-scoped PostgreSQL advisory lock before lookup/write;
- accepts a scheduling replay only when requirement, required-by date, and normalized deadline source match;
- accepts an attendance replay only when roster membership, status, actor, assertion time, source type, source record, and document match;
- rejects a reused key with a different payload as `idempotency_key_payload_conflict`;
- continues to report `outboundEnabled=false` and contains no outbound message insert.

The rollback-only database test now covers payload-conflict rejection for both scheduling and attendance. It also uses one stable assertion timestamp so an exact replay is well-defined.

## Exact files changed

- `supabase/migrations/20260911190000_attendance_scheduling_state_gate.sql`
- `supabase/tests/issue_141_attendance_scheduling_state.sql`
- `tests/test_issue_141_attendance_scheduling_migration.py`
- `Codex_Reply_Issue141_R7.md`

## Tests and checks

- `python -m unittest tests.test_issue_141_attendance_scheduling_migration -v` — 5/5 passed.
- `python -m py_compile tests/test_issue_141_attendance_scheduling_migration.py` — passed.
- `git diff --check` and staged diff check — passed.
- PR #193 live state checked before work: open, mergeable/clean, with Cloudflare Pages preflight, source-integrity, and Cloudflare Pages checks passing.
- PR #194 remote checks after push: both preflight runs passed, both source-integrity/truncation-guard runs passed, and Cloudflare Pages passed.
- PostgreSQL runtime search: `psql`, Supabase CLI, Docker, Podman, and WSL are unavailable in this environment. Common Windows installation paths were also checked.

## Validation and deployment status

- Local static/contract validation: passed.
- Isolated PostgreSQL execution: not run; the required runtime is unavailable.
- Push: branch pushed.
- Merge: not attempted.
- Production migration/database write: not attempted.
- UI/generator/outbound participant or employer communication: not touched or enabled.

The last successful end-to-end historical backfill proof remains the production receipts already recorded on issue #141 (4,771 sessions, 10,726 registrations, 8,797 participants overall after bridge import, with duplicate/scope checks reported). This Round 7 state slice itself remains unexecuted against a database and must not be described as connected or proven.

## Preserved unrelated work

The primary checkout remains untouched. This fresh isolated worktree materialized `docs/Earl/index.html` as modified immediately after checkout; it was not staged or committed. A Python bytecode cache created by validation also remains untracked and is not committed.

## Remaining risk and exact next action

Run the migration and `supabase/tests/issue_141_attendance_scheduling_state.sql` in an isolated PostgreSQL/Supabase database containing the prerequisite canonical migrations. Confirm rollback, zero outbound-message delta, exact replay behavior, payload-conflict rejection, and concurrent same-key behavior. Only after that proof should PR #193 plus this hardening be merged or any production migration be considered. Keep issue #129 browser/UI work paused and outbound sends disabled.

No customer rows, participant PII, credentials, secrets, or tokens were read or committed. No user/account action is required if CI or an authorized database test runner can execute the isolated SQL test; otherwise an authorized operator must provide that runner.
