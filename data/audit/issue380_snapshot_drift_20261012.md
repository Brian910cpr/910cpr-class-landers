# Issue 380 R11 — snapshot drift during decision persistence

2026-10-12 America/New_York. Existing draft PR #381. BUILT, validated locally only.

Finding: checkLiveDispatch evaluated the canonical reader's object before awaiting recordDecision, then returned the old candidate even if the shared object changed during persistence. A regression test reproduced candidate instead of review before the fix (7 pass / 1 fail).

Change: capture the seven reconciliation inputs and compare them after durable acknowledgement. Drift in issue identity, authority, version, resolution, blocker, source state or worker opt-in returns review/canonical_snapshot_changed_during_persistence, always can_execute=false. Tests cover all seven mutations at both selection and pre_side_effect. The audit event remains a record of the earlier evaluated decision; it must not be interpreted as a claim. No extra audit is fabricated for the post-await drift result.

Files: supabase/functions/production-board/live-dispatch-check.mjs; tests/live_dispatch_check.test.mjs; this report; unique root receipt Codex_Reply_Issue380_20261012_R11.md.

Validation: node --test tests/live_dispatch_check.test.mjs tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/owner_access.test.mjs => 51 tests, 51 pass, 0 fail. node --check on source and test; git diff --check pass. No generator. Original dirty checkout preserved; isolated worktree case-collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded from commits. Open CODEX queue scanned; no other assignment claimed or changed, #371 remains primary and #372 untouched.

Limitations: this detects local shared-object drift only. Remote state can change without mutating this object; transient changes can escape detection. It supplies no authentication, atomic claim, idempotent persistence, lease, installed runtime fence, or permission to execute. All six issue acceptance criteria remain open. No production write, runtime/state/task/process change, install, merge or deploy. This is a targeted backend guard, not completion of the requested Handled Manually feature. No Enrollware dependency/training workflow changed.

Next engineering step: authenticated canonical reader and transactional versioned/idempotent claim-or-skip/audit adapter against isolated database, followed by approved runtime integration and actual no-launch/pre-mutation proof. Resolution/private evidence/UI/history/counts and concurrency/upload/browser proof remain unfinished. Keep #381 draft. No owner credential blocker or Brian action required for this review; rollout requires separate authorization.

Proof contract: expected outcome blocked/resolved/stale items never launch or mutate, with durable canonical decision. Cadence every selection and mutation. Last real end-to-end proof: none. Failure condition: stale/resolved launch/mutation or missing durable decision. Observer and observer-health proof for that outcome remain unintegrated. Recovery: preserve state/evidence, use approved hold and finish atomic adapter before rollout. Engineering handles integration; Brian must not become routine monitoring layer.
