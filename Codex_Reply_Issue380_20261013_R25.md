# Issue 380 dispatch R25

Timestamp: 2026-10-13T21:44:37.2391381Z
Branch: codex/issue380-r25-20261013 (pushed to existing PR #381 head codex/issue380-manual-resolution-20261011).
Substantive commit: f4864ff258d5f5e7ffdfe7a6a9c5919454c780a8
State: PR_OPEN / IN_PROGRESS. Persistent evidence: BUILT only.

Execution acknowledged on originating issue before implementation. Required repository instructions read. Original dirty checkout, existing assignments, primary #371 and draft #372 preserved. No merge, deploy, production migration or installed runtime/state changes.

Root cause: direct service_role UPDATE bypassed publisher issue identity validation. Repaired existing intake trigger to reject issue_id changes. Real negative control also proves service_role can forge authoritative_observation without mutation audit and obtain reservation, always can_execute=false. This second finding remains a rollout blocker, not a fixed security boundary.

Changed files:
- data/audit/issue380_dispatch_transaction_draft.sql
- tests/reconciliation/board_intake_trust_boundary.py
- data/audit/issue380_intake_trust_review_20261013.md
- Codex_Reply_Issue380_20261013_R25.md

Validation: baseline two bypasses reproduced; final disposable PostgreSQL 27/27 tests, 11 observed Lock waits; Node backend/auth 83/83; Python AST and diff checks pass. Full commands/output and initial local port/tool setup error are retained in the report. Local test server stopped; fixtures outside repo retained. SQL remains outside migrations and unapplied. No public output changed.

Exact report for review: data/audit/issue380_intake_trust_review_20261013.md. Read full report and tests, particularly deliberately passing provenance forgery negative control. Trusted DELETE/reinsert, forged audit and shared credential authority remain unprotected. No production end-to-end proof, observer or observer-health proof. Expected outcome/cadence/recovery contract is in report; no healthy/installed duplicate suppression claim.

All six acceptance criteria remain open. Next engineering: restricted authenticated authoritative collector/write protocol with denial and atomic concurrency tests, installed canonical no-launch consumer and external side-effect fence/race proof, then private evidence and history/count UI/browser proof. No Brian account action required. Keep #381 draft/unmerged/undeployed.

Unrelated files excluded: Windows case-collision docs/Earl/index.html, docs/Jackson/index.html; test __pycache__ artifacts if present. Original unrelated dirty checkout untouched; no cleanup. Queue titles swept, no competing deep stream started. No ops/handoff/next_task.md used.

Push/receipt verification: this receipt is committed separately after the substantive commit; final pushed SHA and GitHub Contents verification are reported on issue #380 and in final response.
