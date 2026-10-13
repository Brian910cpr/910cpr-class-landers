# Issue #380 — R22 dispatch receipt

Timestamp: 2026-10-13T15:00:00Z (dispatch date; exact commit timestamp is in Git).
Branch: codex/issue380-r22-20261013; pushed to existing PR #381 head codex/issue380-manual-resolution-20261011.
Substantive commit: abd8079a667c7247d56007fdbac2e51625d9a07b.
State: PR_OPEN / IN_PROGRESS. Persistent evidence: BUILT only.

Found dispatch proxy forwarding arbitrary RPC response fields and accepting arbitrary reason/version strings. Replaced with explicit field/reason allowlists and PostgreSQL bigint validation. Every response still can_execute=false. Full report: data/audit/issue380_dispatch_ack_privacy_20261013.md.

Files changed: supabase/functions/production-board/dispatch-decision.mjs; tests/production_dispatch_decision.test.mjs; data/audit/issue380_dispatch_ack_privacy_20261013.md; this receipt.

Validation: 77/77 targeted backend/auth tests pass, 0 failures/skips; node syntax and git diff checks pass. Actual edge routes tested locally with fake transport. No SQL change; prior isolated database evidence reused. Unrelated baseline Python board auth failures not rerun. Windows case-collision HTML dirt in isolated checkout excluded; original dirty checkout preserved.

Deployment: locally persisted, committed, pushed for draft review only. No merge, migration, deploy, installed runtime/state/task change or generator. #371 remains primary; #372 untouched/draft. All six acceptance criteria remain open.

Operational proof: no production end-to-end proof or deployed observer health exists. Last narrow success is local 77-test run on dispatch date. Expected checks: each selection/pre-side-effect; unresolved source/version/commit/fence denies execution. Recovery: refresh canonical state, retain request ID for uncertain outcomes; do not infer rollback from unconfirmed acknowledgement. No Brian monitoring/account action required.

Next action for ChatGPT: review substantive commit and full report; keep #381 draft. Continue authoritative collector/installed no-launch consumer and external side-effect fence/race proof, policy/trusted-role review, then evidence/private storage/UI/history/counts. Those are unfinished engineering/review gates, not credential blockers. This receipt does not claim installed suppression or acceptance completion. No ops/handoff/next_task.md used; no Codex_Read manufactured.
