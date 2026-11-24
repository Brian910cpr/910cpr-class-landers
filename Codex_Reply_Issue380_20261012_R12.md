# Issue #380 — R12 dispatch receipt

Timestamp: 2026-10-12 America/New_York.
State: PR_OPEN / IN_PROGRESS. Persistent evidence: BUILT only.
Local branch: codex/issue380-r12-20261012.
Push target / existing draft PR #381: codex/issue380-manual-resolution-20261011.
Substantive commit: acd069378dc70f9f7eb10ec9187a4b78a84c9624.

Read full issue/comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design/proof standards. Acknowledged execution on #380 before implementation. Preserved #371 primary, #372 draft and all other assignments. No arbitrary third-party authorization used.

Implemented bounded waits for injected canonical reader and durable-decision adapter, with cooperative cancellation and fail-closed results. Default 5 seconds per invocation; configurable 1..30000ms integer. Late acknowledgement cannot restore a timed-out candidate. Abort does not guarantee remote cancellation/rollback; non-idempotent retries remain unsafe. This is advisory backend progress, not completion of Handled Manually.

Exact changed files:
- supabase/functions/production-board/live-dispatch-check.mjs
- tests/live_dispatch_check.test.mjs
- data/audit/issue380_adapter_deadlines_20261012.md
- Codex_Reply_Issue380_20261012_R12.md

Primary review report: data/audit/issue380_adapter_deadlines_20261012.md. It includes commands, output counts, limits and proof contract. Focused node suite: 56 tests, 56 pass, 0 fail; source/test syntax and git diff --check pass. Five added tests exercise hung read and late persistence at both phases plus invalid deadlines. No broader baseline retest or live browser/database proof claimed. No known failure in targeted suite.

Locally persisted and committed; receipt and implementation pushed to existing PR branch by send procedure. No merge, deploy, generator, production writes/schema changes, installed runtime/state/task/process changes. Original dirty checkout unchanged; isolated worktree docs/Earl/index.html and docs/Jackson/index.html case-collision dirt intentionally uncommitted. No temporary/debug files intentionally tracked. Queue scanned; other assignments not claimed or changed.

Exact unfinished gates: authenticated canonical intake and mappings for blocker/source-check/worker opt-in, transactional versioned/idempotent claim-or-skip/audit, installed runtime pre-mutation fencing. Existing schema baseline is not credential-blocked. Resolution/version/evidence persistence, private upload path, coordinated owner UI/history/counts, concurrency/upload/browser proof remain unfinished. All six acceptance criteria remain open. No execution permission granted.

Expected outcome: blocked/resolved/stale items never launch or mutate, with durable canonical audit at every selection/side effect. Last real end-to-end proof: none. Failure/staleness: stale/resolved execution or absent canonical audit. Observer and observer-health proof: not integrated. Recovery: preserve evidence/state, use approved hold and implement/prove atomic adapter before rollout. Escalation: engineering/review now, separate rollout authorization later. Brian is not an acceptable routine monitor; automated monitoring remains unfinished.

Next for ChatGPT: review substantive commit and exact report/source/tests, keep #381 draft/unmerged/undeployed; continue canonical transactional adapter against isolated DB and approved no-launch/pre-mutation boundary. No Brian/account action required for this review.
