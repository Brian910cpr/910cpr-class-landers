# Issue #380 — R17 security review and audit invariant

- Timestamp: 2026-10-13T05:15Z (UTC).
- State: PR_OPEN / IN_PROGRESS. Overall evidence BUILT, validated locally only. All six issue acceptance criteria remain open.
- Existing PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/381 (keep draft).
- Local branch: codex/issue380-r17-20261013. Push destination: codex/issue380-manual-resolution-20261011 (existing #381).
- Initial review/reproducer commit: 339490ee25f22327779135732e7d358ddc5bb466.
- Substantive repair commit: 5b0ff1efb1e70e0027e12fc7d7522d8c53205ebf. Receipt commit is the next pushed tip, externally verifiable without a self-referential SHA.

## Execution and findings

Read full #380 body/comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design/proof standards and #266 dependency. Acknowledged actual execution on #380 before implementation. Reused existing draft #381 in a separate worktree, preserving primary #371, draft #372 and all assignments. Queue scanned; no competing deep stream started.

Security review reproduced service_role direct resolution UPDATE without event/activity on the previous draft. Version trigger alone did not enforce provenance. Repaired the unapplied SQL using an initially deferred audit constraint: new cards start unresolved; resolution changes require matching event/activity at transaction end. Direct resolve/reopen and resolved insertion fail and roll back. Missing activity at COMMIT rolls back card/event. Normal edits and justified RPC reopen remain compatible. No SECURITY DEFINER or browser grant added.

The role remains a trusted backend: it can manufacture matching provenance and retains legacy activity privileges. This enforces completeness at transition, not independent actor authenticity or lifetime immutable activity. Proxy actor must be server-bound. Callers must await COMMIT before external effects. No worker lease/fencing or execution permission is provided.

## Exact intended changed files

1. data/audit/issue380_resolution_transaction_draft.sql — deferred invariant, outside migrations.
2. tests/reconciliation/board_resolution_security.py — real role/commit tests, inherits five contention scenarios.
3. data/audit/issue380_transaction_security_review_20261013.md — primary report, final result first with retained historical reproducer/output and exact next gates.
4. Codex_Reply_Issue380_20261013_R17.md — this unique root receipt.

Review source/test/report together; the report's historical OPEN bypass section is explicitly superseded by the final repair section. No new JSON contract.

## Validation

- Actual local PostgreSQL 16.4, psycopg 3.2.10/libpq 160009: final 13/13 pass in 2.156s. Each of five contention scenarios observed Lock wait. Anonymous/authenticated access denied; service event modification denied; RLS misgrant defense checked; all three functions invoker/empty search_path; direct transition rollback and missing-activity commit rollback verified.
- Initial 11-test review reproduced the insecure outcome; first repair 11/11, final expanded suite 13/13. Green historical reproducer was not security approval.
- node --test tests/reconciliation/board-resolution.test.mjs tests/reconciliation/reconcile.test.mjs: 2/2 PGlite suites pass, no skips/failures.
- Python AST syntax and git diff --check passed. No JS behavior changed; older 60 route tests not rerun.
- No known test failure in this run. No remote advisors run; local role proof is not deployment advisor approval.
- Dedicated loopback cluster reused; new empty issue380_test_r17, issue380_test_r17_guard and issue380_test_r17_final databases retain synthetic before/after evidence. Server stopped. Binaries/venv/data/logs outside repo, uncommitted. No operational database touched.

## Persistence, deployment and remaining work

Persisted in actual isolated repository, committed and pushed to existing #381 branch. Original dirty E:/GitHub/910cpr-class-landers untouched. Worktree's Windows case-collision changes docs/Earl/index.html and docs/Jackson/index.html excluded. Ignored test dependency/cache artifacts excluded. No generator, production migration/write, runtime install/state change, merge or deploy. #372 untouched.

Review the constraint's trusted-role assumptions, target grants/defaults and commit semantics before any migration promotion. Then implement authenticated canonical versioned/idempotent claim-or-skip/audit adapter and isolated pre-side-effect race proof. Owner resolution UI/history/counts, private evidence upload/access, browser proof and all original acceptance remain unfinished. No new credential/account blocker. Brian action: none for this increment; separate rollout authorization still required.

Success boundary remains actual owner resolution/evidence producing durable worker skip before side effects. Last real end-to-end proof: none. Observer, observer health and automatic recovery not integrated; no MONITORED/HEALTHY claim. Failure/staleness: worker proceeds after canonical stop or without durable audit. Recovery: retain evidence, hold rollout, finish reviewed atomic adapter and prove owner-resolution/worker race. Do not substitute more selector-only hardening or depend on Brian to monitor manually.
