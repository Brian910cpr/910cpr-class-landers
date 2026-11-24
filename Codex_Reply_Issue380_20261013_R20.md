# Issue #380 — R20

Timestamp: 2026-10-13T10:38:00Z
State: PR_OPEN / IN_PROGRESS. Persistent system: BUILT only.
Local branch: codex/issue380-r20-20261013
Pushed destination: codex/issue380-manual-resolution-20261011 (existing draft PR #381)
Substantive commit: 1fc8976ad8df7991fb1bc36f3de94bd44e6fd137
PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/381

## Findings and work
Acknowledged actual execution on originating issue before implementation. Reproduced R19 intake/card deadlock with two real PostgreSQL sessions. Draft dispatch SQL now locks intake before card, matching intake DML trigger ordering. Added writer-first and reader-first contention tests that observe actual Lock waits and confirm stale-version rejection after intake changes. No response permits execution.

Exact changed files:
- data/audit/issue380_dispatch_transaction_draft.sql
- tests/reconciliation/board_dispatch_transaction.py
- data/audit/issue380_intake_lock_order_20261013.md
- Codex_Reply_Issue380_20261013_R20.md

Primary review report: data/audit/issue380_intake_lock_order_20261013.md. It includes commands, negative control, final test output, assumptions and remaining gates. Prior context: data/audit/issue380_dispatch_transaction_20261013.md; its lock inversion limitation is repaired for existing-row intake DML by this increment.

## Validation
Negative control: unchanged R19 SQL, 1 regression fails with real DeadlockDetected after observed Lock wait.
Final: real PostgreSQL 16.4 / psycopg 3.2.10 suite 16/16 passes (8 observed Lock waits), backend/auth Node suite 68/68 passes. Python AST and git diff --check pass. Disposable local issue380_test_r20_* databases only; retained synthetic fixtures. Dedicated test server stopped.
Initial local setup timeout (0 tests) corrected by explicit port override; missing portable createdb utility replaced by local psycopg database creation. No unrelated application test failures encountered in executed suites.

## Persistence, rollout and hygiene
Changed in repo, validated locally, committed and pushed for review. SQL stays outside migrations, unapplied to production. No generator, runtime installation/state/task change, merge or deployment. #372 untouched; #371 stays primary; #381 stays draft. Original dirty checkout and corrupt object left untouched. Separate healthy worktree used. Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html intentionally uncommitted; local Python caches ignored. No ops/handoff/next_task.md used.

## Remaining gates / next action
All six issue acceptance criteria remain open. Authenticated typed intake publication/version/idempotency/audit and policy/provenance review remain unfinished; installed consumer/external side-effect fence, private evidence and resolution/history/count UI remain unfinished. No new credential blocker or Brian/account action. Missing-intake insert races conservatively review; multi-card/bulk ordering and trusted-role card-first writes are not proven safe by this narrow repair.

Review substantive SQL diff and two concurrency regressions, then implement authenticated typed-intake publisher with the same intake-before-card protocol and expected-version/idempotency/audit tests. Keep draft unmerged/undeployed until separately authorized. Queue scanned without opening a competing deep stream.

Expected operational success remains skip resolved/blocked work before launch and recheck before mutation. Last local proof 2026-10-13T10:36Z; no production end-to-end success/cadence/observer-health proof yet. Missing/stale canonical state, uncertain commit or absent external fence denies execution. Recovery is fresh canonical reconciliation plus same-ID retry for uncertain outcome; engineering owns remaining integration, Brian is not assigned routine monitoring.
