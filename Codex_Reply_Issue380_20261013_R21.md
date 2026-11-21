# Issue #380 — R21 typed intake publisher

Timestamp: 2026-10-13T14:08:45.8169627Z
State: PR_OPEN / IN_PROGRESS; overall evidence BUILT, validated locally.
Branch: codex/issue380-r21-20261013
Existing PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/381
PR head push destination: codex/issue380-manual-resolution-20261011
Substantive commit: 32bc022521bf7be0b504a3cc04c476317834fea4

## Work and findings
Acknowledged execution on the originating issue before implementation. Added owner-authenticated typed intake publication, version/idempotency checks, atomic publication/activity audit, shared per-card lock for first-publication concurrency, and conflict/uncertain-commit handling. Publication is labeled owner assertion, not source verification. Every result can_execute=false. SQL stays outside migrations/unapplied. Existing unresolved-card identity owns intake; publication never reopens resolved cards. Keeps one implementation stream and all existing assignments; #371 primary, #372 untouched/draft. No third-party comment used as authorization.

## Exact files and review record
- data/audit/issue380_dispatch_transaction_draft.sql
- data/audit/issue380_intake_publication_draft.sql
- supabase/functions/production-board/index.ts
- supabase/functions/production-board/publish-intake.mjs
- tests/reconciliation/board_intake_publication.py
- tests/production_intake_publication.test.mjs
- data/audit/issue380_intake_publication_20261013.md — primary report, complete PostgreSQL output, commands, policy/security limits and operational proof contract
- Codex_Reply_Issue380_20261013_R21.md — this required unique root receipt

## Validation and deployment
Real disposable PostgreSQL 16.4 / psycopg 3.2.10 / libpq 160009: 23/23 tests passed with 11 observed Lock waits, including first-publisher competition, writer/dispatcher ordering, reservation invalidation, audit rollback/retry, stale/resolved/identity/freshness rejection and role boundaries. Existing dispatch/resolution contention tests inherited. Backend/auth route suites: 75/75 passed; no skips. Python AST, module syntax and diff checks passed. Edge route executed locally with fake transport; no deployed edge proof. Test DB issue380_test_r21 retains synthetic fixtures on dedicated loopback cluster; server stopped. No known failures in executed suites. Historical unrelated Python board auth failures not rerun.

Persisted locally and committed in repo; this receipt is pushed to the existing draft PR head. No production database writes/migration, runtime install/state/task changes, merge or deployment. Disposable test server start/stop only. Original dirty checkout preserved. Worktree docs/Earl/index.html and docs/Jackson/index.html case-collision dirt intentionally unstaged. No generated public pages/caches/binaries staged; no generators run; no ops/handoff/next_task.md or Codex_Read file written.

## Remaining gates and exact next action
All six acceptance criteria remain open. No credential/account blocker and no Brian action required. Implementation/review gates: trusted-role authenticity/direct-DML bypass, owner assertion versus authoritative verification policy, freshness/lease policy review, installed canonical selection/priority consumer, atomic external pre-side-effect fence and runtime race proof, private evidence and resolution/history/count UI with upload/browser tests. This increment does not implement those or claim live duplicate suppression.

ChatGPT: review the SQL/proxy and complete report at data/audit/issue380_intake_publication_20261013.md, especially missing-row lock protocol, owner assertion boundary, replay and explicit commit acknowledgement. Keep #381 draft/unmerged/undeployed; continue authenticated authoritative collector and installed no-launch/pre-mutation proof after security/policy review. Do not apply SQL to production or enable execution from these responses.

Expected operational outcome: published canonical owner state stops stale worker decisions before launch/mutation. Last proof is local isolated tests on 2026-10-13, not production end-to-end. Draft freshness window five minutes; observer/observer-health/cadence not deployed or proven. Missing/stale state, resolution, unknown commit or missing external fence deny execution. Recovery: fresh canonical reconciliation; same-ID retry after uncertain outcome. Engineering owns remaining integration/monitoring; Brian is not routine observer. Full contract is in the primary report.
