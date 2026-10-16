# Issue #380 — R19 dispatch transaction checkpoint

Timestamp: 2026-10-13T08:38:14.095308+00:00
Branch: codex/issue380-r19-20261013; pushed to existing PR #381 head codex/issue380-manual-resolution-20261011.
Substantive commit: f51b5c77e1db0b64011486e55bb26bd7a7fd86ea
State: PR_OPEN / IN_PROGRESS. Persistent-system level: BUILT, local isolated transaction proof only. All six acceptance criteria remain open.

## Work performed and evidence
Added service-role transactional dispatch decision/reservation draft and existing-owner-authenticated POST proxy. Canonical card version/resolution plus typed intake checked under locks. Single current-version reservation, idempotent replay/conflict, skip/review audit and rollback covered. Owner resolution after selection produces a recorded skip before the next check. All responses can_execute=false; reservation is not external mutation permission. Successful PostgREST response acknowledges commit; transport uncertainty requires SAME request ID retry.

Primary report with full PostgreSQL output, exact commands, limitations and next gates: data/audit/issue380_dispatch_transaction_20261013.md.
Exact changed source/config/test files:
- data/audit/issue380_dispatch_transaction_draft.sql
- supabase/functions/production-board/dispatch-decision.mjs
- supabase/functions/production-board/index.ts
- tests/production_dispatch_decision.test.mjs
- tests/reconciliation/board_dispatch_transaction.py
- data/audit/issue380_dispatch_transaction_20261013.md
- Codex_Reply_Issue380_20261013_R19.md

14/14 real local PostgreSQL tests pass: 9 dispatch cases and 5 inherited resolution contention cases; competing reservations observed real Lock wait. PostgreSQL 16.4, psycopg 3.2.10/libpq 160009. 68/68 Node backend/auth tests pass; Node syntax, Python AST, evaluated TypeScript route, staged diff check pass. No failures in selected suites. Previously reported legacy Python auth assertions not rerun; no claim of full-repo green.

## Safety, blockers and remaining engineering
No account/credential blocker. SQL remains OUTSIDE migrations, unapplied to production. No merge/deploy, public generator, installed runtime/state/task/process change. Dedicated synthetic PostgreSQL server stopped; test fixtures retained outside repo. Preserved original dirty checkout, #371 primary stream, draft #372 and all assignments. Existing PR reused: https://github.com/Brian910cpr/910cpr-class-landers/pull/381.

Engineering gates: authenticated canonical intake publisher/version binding, review draft lock order (intake/card order can deadlock and safely abort), trusted service-role provenance, policy windows (5-minute source observation, 60-second reservation are unapproved draft choices), runtime selection consumer and atomic pre-side-effect external fence. No operational end-to-end proof/observer-health evidence exists. Missing/stale state, expired reservation or uncertain commit deny execution. Recovery is fresh authoritative reconciliation and same-ID retry; security/rollout review before operational wiring. Private evidence/UI/history/counts remain unfinished. Do not enable execution on the strength of this receipt.

Recommended next ChatGPT action: review primary report and SQL/API/tests, then continue authenticated intake lock-order protocol and installed no-launch/pre-mutation fencing proof in #381. Keep draft/unmerged/undeployed. No Brian/account action required now.

Persistence: intended files committed locally and pushed with this receipt; final pushed SHA and Contents API verification recorded on originating issue. Only unrelated Windows case-collision docs/Earl/index.html and docs/Jackson/index.html modifications plus Python __pycache__ remain excluded/uncommitted in isolated worktree. Original checkout untouched. No ops/handoff/next_task.md used.
