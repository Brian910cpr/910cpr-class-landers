# Issue #380 — R18 commit boundary proof

Timestamp: 2026-10-13 (America/New_York, UTC-04:00).
Work-item state: IN_PROGRESS / PR_OPEN. Persistent evidence: BUILT overall, isolated transaction proof only.
Local branch: codex/issue380-r18-20261013.
Remote review branch: codex/issue380-manual-resolution-20261011.
Existing draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/381
Substantive commit: dbf2f7fda0babd6b1ef6d04c2fd31c0de46f9be9.

## Work and evidence

Execution acknowledged on originating issue before edits. Read full issue/comments and AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design/proof gates. Four real PostgreSQL regressions verify provisional RPC visibility/rollback/retry, multiple transitions per commit, rejection of missing intermediate audit despite original final state, and forced constraint validation. No SQL/application behavior changed and no new bypass found in these tested cases.

Exact intended files:
- tests/reconciliation/board_resolution_security.py
- data/audit/issue380_commit_boundary_proof_20261013.md
- Codex_Reply_Issue380_20261013_R18.md

Primary report above contains full normalized test output, exact commands, infrastructure paths, source references, limitations and next action. Draft reviewed: data/audit/issue380_resolution_transaction_draft.sql. PostgreSQL 16.4 / psycopg 3.2.10 / libpq 160009. Security/contention suite 17/17 passed in 2.578s; five actual Lock waits observed. Python AST syntax and git diff --check passed. No test failures. JS suites not repeated because JS/SQL unchanged; prior results are historical. Synthetic issue380_test_r18 retained; dedicated local server stopped after tests.

## Persistence and safety

Changed in repo and validated locally; push targets existing #381 branch. No production migration, runtime installation/state change, generator, merge or deployment. SQL remains outside migrations. Original dirty checkout preserved; Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded from commits. #371 primary and draft #372 untouched; existing assignments preserved. Queue and #266 dependency scanned; no unrelated assignment taken over.

## Unfinished gates and next action

All six acceptance criteria remain open. No credential/account blocker encountered. Authenticated atomic claim-or-skip/audit adapter, installed runtime pre-mutation fencing, private evidence, UI/history/counts and browser/upload proof remain unimplemented engineering work. This dispatch does not claim the initially contemplated adapter was delivered. Next: reviewed server-authenticated versioned/idempotent atomic claim/skip adapter with commit acknowledgement and isolated owner-resolution race proof, preserving #266 explicit worker-safe opt-in. Do not infer executable commands from issue prose. Keep PR #381 draft/unmerged/undeployed; separate rollout authorization required. No Brian/account action now.

Expected end-to-end success: owner resolution causes durable skip before worker side effects. Cadence: each claim and side effect. Last real end-to-end success: none. Failure/staleness: stale/resolved execution or success without durable audit. Observer and observer health not integrated; no MONITORED/HEALTHY claim. Recovery: hold rollout, retain evidence, complete authenticated atomic/runtime integration and proof. Trusted-role provenance and legacy activity retention limitations remain as documented in R17.
