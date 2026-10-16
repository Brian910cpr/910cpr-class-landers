# Issue 380 R12 — bounded adapter waits

2026-10-12 America/New_York. Existing draft PR #381. BUILT, validated locally only.

Finding: both injected canonical reads and decision persistence were awaited without a deadline. A never-settling adapter could occupy the advisory boundary indefinitely. This is an independent backend safety gate; it does not implement the canonical transaction.

Change: each adapter invocation has a default 5000ms deadline (configurable integer 1..30000ms). Adapters receive a second argument containing an AbortSignal. Timeout signals cancellation and returns the existing fail-closed read/persistence failure. A late acknowledgement cannot revive the returned decision. Timers are cleared after settlement. Every result remains can_execute=false. Existing one-argument adapters remain compatible.

Important limit: AbortSignal is cooperative; an adapter that ignores it can continue remote work after this caller returns. Timed-out persistence may still have committed. Never retry non-idempotent writes or interpret timeout as proof of rollback. Maximum normal wait is two per-adapter deadlines, since a failed read still attempts to record its review. This provides no remote atomic fence, lease, authentication, idempotency or installed runtime permission. Concrete canonical mapping for blocker/source-check/worker opt-in plus versioned transactional claim/skip persistence remains absent. No schema baseline credential request is needed; the previously reviewed live facts still apply.

Changed files: supabase/functions/production-board/live-dispatch-check.mjs; tests/live_dispatch_check.test.mjs; this report; Codex_Reply_Issue380_20261012_R12.md.

Validation commands and output:
- node --test tests/live_dispatch_check.test.mjs tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/owner_access.test.mjs: tests 56, pass 56, fail 0, cancelled 0, skipped 0.
- node --check supabase/functions/production-board/live-dispatch-check.mjs: exit 0.
- node --check tests/live_dispatch_check.test.mjs: exit 0.
- git diff --check: exit 0.
Five added tests cover hung reads and late persistence acknowledgements at both phases, and invalid deadlines before any adapter side effects. These are fake-adapter tests, not real dispatcher proof. No known failures in this focused suite; broader baseline tests not rerun.

Safety: original E:/GitHub/910cpr-class-landers dirty checkout untouched. Isolated codex/issue380-r12-20261012 worktree's Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded. Open CODEX queue scanned; no other assignment claimed or changed. #371 remains primary, #372 untouched. No generator, production schema/write, installed runtime/state/task/process change, merge or deployment. Supabase skill and current changelog reviewed while assessing transaction work; no Supabase API or SQL implementation was added. No Enrollware/training workflow or dependency changed.

All six acceptance criteria remain open. Next: reuse draft #381; implement authenticated canonical intake and versioned/idempotent transactional claim-or-skip/audit against an isolated database, then approved runtime wiring and real no-launch/pre-mutation proof. Resolution/private evidence/UI/history/counts and concurrency/upload/browser proof remain unfinished. Keep #381 draft/unmerged/undeployed. No Brian/account action needed for this review.

Proof contract: desired outcome is blocked/resolved/stale jobs skipped with durable audit before every selection and mutation. Last real end-to-end proof: none. Failure is stale/resolved launch/mutation or missing canonical audit. Observer and observer-health proof remain unintegrated; automated monitoring is unfinished and Brian must not be the routine monitor. Recovery: preserve evidence/state, use approved hold and finish atomic adapter before rollout. Engineering/review handles current work; separate rollout authorization remains required.
