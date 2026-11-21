# Issue #380 R10 dispatch reply

Timestamp: 2026-10-12T18:20:51.891923+00:00
Branch: codex/issue380-r10-20261012; pushed to existing PR branch codex/issue380-manual-resolution-20261011.
Substantive commit: 073e4484d95320c57b1281a292bc2d3f21cc2912.
Work-item state: PR_OPEN / IN_PROGRESS. Evidence level: BUILT only.
PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/381 (draft).

Actual execution acknowledged on originating issue before implementation:
https://github.com/Brian910cpr/910cpr-class-landers/issues/380#issuecomment-6130055413

Exact changed files: supabase/functions/production-board/dispatch-reconciliation.mjs; tests/dispatch_reconciliation.test.mjs; data/audit/issue380_ranking_identity_20261012.md; Codex_Reply_Issue380_20261012_R10.md.

Locally persisted and validated. Intended files committed; receipt pushed with branch, not merged or deployed. No production or installed runtime changes. All acceptance criteria remain open. No owner/account action required; next engineering work and limitations follow in the full report. Final pushed receipt SHA is reported in chat/issue after commit, avoiding a self-referential hash.

## Full primary report

# Issue 380 R10 — ranking canonical identity binding

2026-10-12 America/New_York. Existing draft PR #381. BUILT / validated locally only.

Finding: rankDispatchCandidates validated outer IDs and snapshot state/version separately, but did not require state.issue_id to equal outer id. A P0 candidate could therefore rank using another issue's eligible snapshot. Added strict numeric identity equality before priority ranking. Missing, string, malformed and swapped snapshot IDs fail closed. Fixtures now carry explicit canonical identity; matching candidates retain their object identity and ordering.

Files: supabase/functions/production-board/dispatch-reconciliation.mjs; tests/dispatch_reconciliation.test.mjs; this report. No new schema, API, authentication mechanism, dependency or Enrollware workflow. This repairs the existing native operational contract and adds no incumbent dependency.

Validation commands:
- node --test tests/live_dispatch_check.test.mjs tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/owner_access.test.mjs
- node --check supabase/functions/production-board/dispatch-reconciliation.mjs
- node --check tests/dispatch_reconciliation.test.mjs
- git diff --check

Results: 49 tests, 49 pass, 0 fail. Syntax/diff checks pass. Negative control temporarily removed only the new identity predicate: focused regression exited 1, actual [900,371] versus expected [371]. Predicate restored. No known failure in targeted suite. Earlier baseline Python obsolete auth assertions not rerun or changed.

Remaining gates are engineering work, not an owner credential blocker: authenticated canonical intake, transactional versioned/idempotent claim-or-skip audit, approved installed runtime wiring and atomic pre-mutation fencing. Read-then-act still has a race; this ranking check does not solve it. Resolution/version/evidence migration, private uploads, owner UI/history/counts and concurrency/browser proof remain unfinished. All six acceptance criteria remain open. No result grants execution permission.

Proof contract: expected outcome is blocked/resolved/stale jobs skipped before launch and mutation with durable canonical audit, at every selection/side effect. Last real end-to-end proof: none. Failure is launch/mutation of ineligible work or missing durable decision. Observer and observer-health wiring for that outcome remain absent; BUILT only. Recovery: preserve state/evidence, use approved hold, finish and prove canonical atomic adapter before rollout. Escalation: engineering/review now, separate rollout authorization later; Brian is not assigned routine monitoring.

Original dirty checkout preserved, including corrupt object found on fetch (bad object 6e61cabca5981d1389e52c60d95424d9893bb50f). Healthy existing clone used for isolated codex/issue380-r10-20261012 worktree. Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded. No generator, production writes, installed script/state/process/task changes, merge or deployment. #371 remains primary; #372 untouched/draft. Queue scanned without claiming or modifying other assignments.

Next review: inspect the exact source/test paths above and this report on #381. Continue concrete authenticated atomic adapter and isolated transaction/pre-mutation proof; keep draft and undeployed. No user/account action needed for this review.
