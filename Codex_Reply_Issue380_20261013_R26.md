# Issue #380 — R26 dispatch receipt

Timestamp: 2026-10-14T00:15:26.8746635Z
Branch: codex/issue380-r26-20261013; pushed to existing PR head codex/issue380-manual-resolution-20261011.
Substantive commit: 86fb7d4cd33d4450748103c3d62e3ec2554a0553
State: PR_OPEN / IN_PROGRESS. Persistent-system evidence: BUILT only.
PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/381 (draft, unmerged, undeployed).

## Work and findings
Acknowledged actual execution on originating #380 before implementation. Read full issue/comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md and design/proof standards. Preserved primary #371, draft #372, existing assignments and original dirty checkout.

Real local negative control reproduced DELETE/reinsert bypass of R25 immutable issue-ID UPDATE protection. Removed routine service_role DELETE grant on intake; TRUNCATE remains denied. Tested transaction rollback preserving identity, version, activity, replay and ordinary publication. SQL remains an unapplied review draft outside migrations. No installed runtime, production/state change, merge or deployment.

Exact changed files:
- data/audit/issue380_dispatch_transaction_draft.sql
- tests/reconciliation/board_intake_trust_boundary.py
- data/audit/issue380_intake_delete_privilege_20261013.md (full report, commands, exact PostgreSQL output, limitations)
- Codex_Reply_Issue380_20261013_R26.md

Validation: baseline denial test failed as expected (Error not raised). Final isolated PostgreSQL 28/28, 11 observed Lock waits; backend/auth 83/83; Python AST and git diff --check pass. Local PostgreSQL stopped after proof. Existing broader Python obsolete auth assertions previously reported, not rerun. Worktree docs/Earl/index.html and docs/Jackson/index.html Windows case-collision dirt intentionally unstaged; no untracked runtime artifacts committed.

## Remaining gates and exact next action
All six acceptance criteria remain open. Provenance-forgery diagnostic still deliberately reproduces service_role authoritative-observation UPDATE without mutation audit, resulting only in non-executable reservation. This is a rollout blocker, not source verification. Effective role membership/default grants and restricted authoritative collector write protocol remain unfinished; no credential/account blocker claimed.

Review substantive commit/report and implement restricted collector mutation protocol with denial/atomic provenance tests, then installed no-launch consumer, external side-effect fence/race proof and private evidence/history/count UI/browser tests. Keep #381 draft and SQL unapplied. No Brian/account action now.

No production end-to-end proof or deployed observer/observer-health evidence. Expected outcome: skip handled/blocked work before launch and every side effect. Failure/staleness: stale/forged source, uncertain commit, card/version drift, absent runtime fence. Recovery: authenticated refresh/reconcile preserving request IDs; do not blindly retry. Source/reservation windows still require policy review. Brian is not assigned routine monitoring. This receipt push is durable handoff evidence only, not evidence that the operational system is healthy.
