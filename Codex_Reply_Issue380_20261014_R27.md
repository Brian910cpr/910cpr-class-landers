# Issue 380 dispatch R27

Timestamp: 2026-10-14T01:29Z (UTC).
Branch: codex/issue380-r27-20261014; pushed to existing PR #381 head codex/issue380-manual-resolution-20261011.
Substantive commit: 0661145b95512d28c0a6d61f1fc83b10e1ca2062.
State: PR_OPEN; diagnostic increment validated locally; persistent evidence BUILT only.

Execution acknowledged on originating issue before implementation. Full issue/comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design/proof gates read. #371 primary, #372 draft and all assignments preserved.

Findings: routine service_role can forge authoritative observation by initial INSERT without publication/audit; it can also revive stale prior observation by refreshing timestamp/reference without assigning provenance or creating mutation audit. Both yield only non-executable reservations. These are deliberate diagnostic negative controls, not a security fix. Existing grants plus SECURITY INVOKER publication require a reviewed restricted collector/write protocol; simply revoking grants breaks publication and protecting provenance column alone misses refresh. Exact rollout blocker is unauthenticated writable source attestation. No credential blocker or Brian/account action required for the review.

Files changed:
- tests/reconciliation/board_intake_trust_boundary.py
- data/audit/issue380_provenance_attack_paths_20261014.md (primary report, exact commands/output and next repair boundary)
- Codex_Reply_Issue380_20261014_R27.md

Checks: real disposable local PostgreSQL 30/30 tests, 11 observed Lock waits, AST PASS, git diff --check PASS. No SQL/backend behavior changed; Node suite not rerun. Test cluster stopped and status confirmed. No new unrelated failures. Windows case-collision docs/Earl/index.html and docs/Jackson/index.html intentionally uncommitted; original checkout's unrelated dirty work untouched.

Pushed review work only. No migration, production DB writes, installed runtime/state changes, generator, merge, deployment or ops/handoff/next_task.md usage. All six acceptance criteria remain open. SQL outside migrations/unapplied; PR #381 remains draft.

No production end-to-end proof, active observer or observer-health evidence for draft. Expected outcome: skip handled/blocked work before selection and every side effect. Failure: forged/stale source provenance, uncertain commit/version or absent external fence. Recovery: retain request ID, investigate authenticated source state, fail closed; monitoring integration remains unfinished and is not assigned to Brian.

Next reviewer action: inspect report and two new negative controls, implement independently authenticated restricted collector/write protocol covering INSERT and all observation fields, convert all forgery controls to denial/downgrade proofs, then installed consumer/external fence and private evidence/UI. Keep #381 draft/unmerged/undeployed. This dispatch is diagnostic progress, not issue completion. Unrelated queue titles swept; no competing deep stream or unrelated implementation begun.
