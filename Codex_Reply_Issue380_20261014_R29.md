# Issue #380 — R29

Timestamp: 2026-10-14T03:50Z
State: PR_OPEN / BUILT only; all six acceptance criteria open.
Branch: codex/issue380-r29-20261014; push target existing draft PR #381 branch codex/issue380-manual-resolution-20261011.
Substantive commit: 0f7e8b2b623d24302bfffcd00b1ab62dd2e4bb91

Work: independent non-superuser login test proves six escalation/trigger bypass attempts and observation promotion denied; intended publication RPC remains usable with can_execute=false. Existing administrative-session role tests alone cannot establish inability to switch back to owner. No behavior SQL change.

Exact files: tests/reconciliation/board_intake_trust_boundary.py; data/audit/issue380_routine_login_privileges_20261014.md; this receipt. Primary report contains exact commands/output, findings, limitations and next gates.

Validated locally: PostgreSQL 29/29 tests, eleven observed Lock waits, AST PASS, final diff check PASS. Initial test constant typo corrected. Test login removed and local server stopped; synthetic fixtures retained. No additional API tests because no API changes. Existing Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded. Original E:/GitHub/910cpr-class-landers dirty files preserved. No unrelated failures encountered in final validation.

Deployment: pushed for draft review only; no merge/deploy/migration/production writes/installed runtime changes. #371 primary and #372 untouched. Existing assignments preserved. Queue titles scanned without starting competing deep work. No ops/handoff mailbox used.

Rollout blocker: no reviewed independently authenticated authoritative collector/restricted audited writes or production effective-privilege proof. Installed consumer/external atomic fence/race proof and private evidence/UI/history/counts/reopen unfinished. This test proves synthetic memberships only, not production permissions or arbitrary privileged-function reachability. Keep SQL outside migrations/unapplied and #381 draft.

Next ChatGPT action: review test/report and preserve denial regressions while advancing collector identity/write protocol; then installed consumer/fence and evidence/UI. No Brian/account action required for next backend work.

Persistent process: BUILT; no production end-to-end success. Expected outcome is authoritative skip before launch/mutation. Cadence remains unapproved (draft five-minute freshness/sixty-second reservation). Missing/stale evidence, escalation, version mismatch/uncertain acknowledgement fail closed. Installed observer and observer health unproven. Engineering owns recovery/monitoring implementation; Brian is not routine observer. Recover via durable request IDs/audit, escalate account-level needs only if actually encountered.
