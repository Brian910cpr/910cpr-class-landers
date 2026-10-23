# Issue #380 — R31 collector publication checkpoint

Timestamp: 2026-10-14T07:06Z (UTC).
State: PR_OPEN / BUILT only; all six acceptance criteria remain open.
Local branch: codex/issue380-r31-20261014.
Pushed destination: codex/issue380-manual-resolution-20261011, existing draft PR https://github.com/Brian910cpr/910cpr-class-landers/pull/381 .
Substantive commit: 761bf5248127e316b886aa4eb30af34025c28022. Receipt is committed separately; final pushed SHA is reported on the issue and in chat.

## Findings and work

R30's raw collector capability lacked a typed expected-version/idempotency/first-publication lock protocol. Added an isolated SQL publisher using authenticated session actor, request/card advisory locks then intake/card locks, stale/resolved/identity/freshness rejection, actor-scoped replay receipts and atomic automatic observation audit. SQL returns can_execute=false and no committed claim. Test helper acknowledges only after COMMIT. Historical replay never grants current eligibility.

Exact changed files:

- data/audit/issue380_collector_publication_draft.sql
- tests/reconciliation/board_collector_publication.py
- data/audit/issue380_collector_publication_20261014.md
- Codex_Reply_Issue380_20261014_R31.md

Primary audit includes full test output, commands, limitations and reference documentation. Review the SQL and six new tests together with inherited tests/reconciliation/board_collector_capability.py and data/audit/issue380_collector_capability_draft.sql.

## Validation and persistence

Validated locally: 39/39 real PostgreSQL tests; seventeen observed Lock waits (six new). Covers first publication replay/stale contention/rollback, owner/dispatch contention, invalid/stale/resolved/identity rejection, permissions, provisional response isolation and receipt-failure atomic rollback. SQL executed successfully; Python AST syntax and git diff --check pass. PostgreSQL 16.4, psycopg 3.2.10, libpq 160009; explicit disposable issue380_test_r31 on 127.0.0.1:55480. Test log fully preserved in primary audit. Local server stopped; temporary authenticated test logins removed. No unrelated test failures observed; Node/browser tests not rerun because no API/UI/public artifacts changed.

Persisted locally in isolated worktree and committed for push to existing PR. No generator, production write, migration, installed runtime/state change, merge or deployment. SQL stays outside migrations/unapplied. Original E:/GitHub/910cpr-class-landers dirty files and existing assignments untouched. Worktree's unrelated Windows case-collision docs/Earl/index.html and docs/Jackson/index.html left unstaged. #371 remains primary and #372 remains draft/untouched. No new PR or ops/handoff/next_task.md.

## Remaining gates and exact next action

This is not a production-ready exclusive gateway: raw R30 capability DML and receipt INSERT remain possible; a compromised collector can fabricate source assertions/receipts. Authentication/audit does not prove authoritative source truth. No credential/account blocker is asserted. Engineering still needs narrow authoritative reader identity binding, restricted audited write gateway, production effective privilege/PUBLIC grant proof, additional cross-actor/cross-card and dispatcher-first/resolution races, installed no-launch consumer/external atomic side-effect fence, and private evidence/UI/history/count/reopen/browser acceptance. Keep #381 draft and SQL unapplied. ChatGPT should review substantive commit and primary audit, then continue reader/restricted-gateway implementation on #381 while preserving all denial regressions. No Brian/account action required.

Persistent-system state: BUILT only. Expected useful outcome: skip handled/blocked/already-corrected tasks before launch/mutation. Last production end-to-end proof: none. Missing/stale evidence, version mismatch, uncertain commit and unauthorized writes must fail closed. Installed cadence/observer/observer-health/recovery/escalation remain unproven engineering gates; retain durable request/audit evidence for recovery. Brian is not assigned routine monitoring. No HEALTHY/completion claim.
