# Issue 380 R8 — candidate ranking reconciliation

2026-10-12 America/New_York. PR #381 remains draft. BUILT, validated locally only.

Finding: rankDispatchCandidates trusted caller-supplied check.decision, so a cached candidate could outrank #371 even when its supplied snapshot now recorded resolution, blocking or a changed version. No production caller currently imports this contract; this is a latent integration defect, not proof of a deployed exploit.

Changed supabase/functions/production-board/dispatch-reconciliation.mjs to recompute selection eligibility from state and expectedVersion, reject duplicate/invalid numeric issue identities and unknown priorities, and preserve P0/owner priority/stable tie ordering. Existing consumers must supply state and expectedVersion; cached check alone now fails closed. All results remain advisory and grant no execution permission. Authenticated identity-to-snapshot binding, live fetching and atomic claims remain adapter responsibilities.

Tests: node --test tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/owner_access.test.mjs => 41 tests, 41 pass, zero fail. node --check supabase/functions/production-board/dispatch-reconciliation.mjs and git diff --check pass. Four new regressions cover stale/forged checks, missing snapshots/version, duplicate/malformed identities/priorities, stable ordering and input immutability. rg confirms only test callers of rankDispatchCandidates; no runtime integration changed.

No generator, installed runtime/state/process/task changes, production mutation, merge or deployment. #371 primary and #372 preserved; original dirty checkout untouched. Worktree inherited docs/Earl/index.html and docs/Jackson/index.html dirt excluded. Queue titles scanned; no other assignment changed or claimed.

Remaining: all six issue acceptance criteria open. Authenticated canonical intake and transactional versioned claim/skip/audit with actual pre-mutation wiring remain unfinished engineering, not an owner credential blocker. Resolution/private evidence/UI/history also unfinished. Reuse #381 for next adapter increment; no Brian action required.

Proof contract: expected outcome blocked/resolved skipped at each selection and mutation with durable audit. No real end-to-end proof. Failure: stale or resolved work launches/mutates. Observer and observer health for this outcome remain unintegrated. Recovery: preserve evidence and state, use approved hold, reconcile canonical state before rollout. This increment adds no Enrollware dependency and changes no training workflow.
