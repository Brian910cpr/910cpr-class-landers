# Codex reply — Issue 380 R13

Timestamp: 2026-10-12T21:45:02.230462+00:00
Branch: codex/issue380-r13-20261012, pushed to existing PR branch codex/issue380-manual-resolution-20261011.
Commit SHA (substantive): 556451f548c3af061035582236381161c5936502. Receipt commit is the commit containing this file; full pushed tip recorded on originating issue and final response.
State: PR_OPEN / IN_PROGRESS; BUILT only. https://github.com/Brian910cpr/910cpr-class-landers/pull/381

Exact intended files: supabase/functions/production-board/live-dispatch-check.mjs; tests/live_dispatch_check.test.mjs; data/audit/issue380_accessor_failures_20261012.md; Codex_Reply_Issue380_20261012_R13.md.
Original dirty checkout preserved; isolated case-collision dirt excluded. No intentional untracked files. Locally validated and pushed for review only; no merge/deployment/runtime change. All acceptance criteria remain open. No owner/account action required.

Full primary report follows:

# Issue 380 R13 — canonical accessor failure containment

State: PR_OPEN; BUILT advisory backend only, validated locally. All six issue acceptance criteria remain open. Existing draft PR #381 remains unmerged and undeployed.

Root cause: adapter-provided canonical objects were reread outside protected boundaries while constructing observed_version and checking drift after audit persistence. Throwing getters rejected checkLiveDispatch rather than returning its closed decision contract. A scalar allowlisted projection now supplies reconciliation and audit construction; unreadable post-persistence state returns canonical_snapshot_changed_during_persistence. Read failures clear the projection and record canonical_read_failed with observed_version=null. No exception text or private evidence is recorded. Every result remains can_execute=false.

Changed source: supabase/functions/production-board/live-dispatch-check.mjs.
Changed tests: tests/live_dispatch_check.test.mjs.
Substantive commit: 556451f548c3af061035582236381161c5936502.

Negative control before repair: node --test tests/live_dispatch_check.test.mjs yielded tests 18, pass 14, fail 4. Both phases reproduced escaped private getter/drift exceptions.
After repair: node --test tests/live_dispatch_check.test.mjs tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/owner_access.test.mjs yielded tests 60, pass 60, fail 0, cancelled 0, skipped 0. Node syntax checks for changed source/test and git diff --check exited 0. An earlier run with production_board_auth.test.mjs yielded 55 passes; the final explicitly named owner_access suite is the authoritative 60-test result. No broader tests rerun; no known failures in focused suite.

Safety: isolated codex/issue380-r13-20261012 based on current #381 head 5b5db49893b370f71852378e8a6f7bc3a7b3f35b. Original dirty checkout untouched. Worktree case-collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded from staging. No generators, installed runtime/state/task/process changes, SQL/API writes, merge, deploy, or launcher changes. #371 remains primary; #372 untouched. Open CODEX queue scanned without claiming or modifying other assignments. Supabase skill/changelog inspected; this changes ordinary JavaScript only, no Supabase feature signatures/schema/auth/storage. No training-business workflow or Enrollware dependency changes.

Remaining engineering gates, not credential blockers: concrete authenticated canonical reader and mapping for blocker/source-state/worker-safe; transactional versioned/idempotent claim-or-skip with audit; installed runtime and real atomic pre-mutation proof. Full manual-resolution/private-evidence/UI/history/count workflow and concurrency/upload/browser proof remain unfinished. This local projection does not provide remote atomic fencing, rollback, leases or execution authorization. No production integration claimed.

Proof contract: desired outcome is durable audited suppression of blocked/resolved/stale tasks before selection/mutation. Last real end-to-end proof: none. Success cadence: every selection and side effect. Failure: stale/resolved launch or missing canonical audit. Observer/observer-health proof not integrated; monitoring remains unfinished and must not depend on Brian routinely checking. Recovery: preserve state/evidence, use approved hold, finish atomic adapter before rollout. Escalation: engineering/review now; separately authorize rollout. No owner/account action needed for this increment.

Next action: review this narrow diff and retain #381 draft; continue canonical transaction and isolated concurrency proof on the same backend stream. Do not substitute further advisory hardening for those acceptance gates.

