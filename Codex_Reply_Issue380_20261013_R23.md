# Issue 380 R23 receipt

Timestamp: 2026-10-13T14:12:00-04:00
Work-item state: PR_OPEN / IN_PROGRESS. Evidence: BUILT, validated locally only.
Local branch: codex/issue380-r23-20261013.
Push target: codex/issue380-manual-resolution-20261011 (existing draft PR #381).
Substantive commit: 62db8c97452953cfad7c407eeb0ca5a3debb2bb1.
Pushed tip: receipt commit, discoverable as this file's GitHub commit; final issue comment records full SHA after push.

Repaired impossible bigint acknowledgement acceptance; negative control reproduced committed=true before fix. 78/78 backend/auth tests and syntax/diff checks pass. All six issue acceptance criteria remain open. No production or installed runtime/state changes, migration, merge or deployment; #372 untouched. No account blocker/Brian action. Next: review and continue canonical collector/consumer and external fence gates, then evidence/UI.

Exact changed paths and full primary report follow. This receipt is also the complete local review handoff; no summary-only evidence dependency.

Known unrelated infrastructure failure: commit succeeded, but automatic git gc/repack reported bad object refs/remotes/origin/codex/group-training-experience. No ref cleanup, reset or unrelated work modification attempted. Push and remote receipt verification are checked separately. Original dirty work and isolated case-collision HTML remain uncommitted.
# Issue 380 R23 — intake acknowledgement version boundary

State: PR_OPEN; persistent-system evidence BUILT only. Timestamp: 2026-10-13T14:11:00-04:00.
Branch: codex/issue380-r23-20261013, based on a67a06d55fa8f90a5706641ace26c2a5f0ad4a27; reuses draft PR https://github.com/Brian910cpr/910cpr-class-landers/pull/381.
Execution acknowledged before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/380#issuecomment-6152051461.

## Finding and repair
Typed owner-intake publication accepted an unbounded positive decimal acknowledgement version, unlike dispatchDecision. A malformed RPC response could receive committed=true even with a version impossible for PostgreSQL bigint. Limit successful acknowledgement versions to canonical positive decimal strings of at most 19 digits and maximum 9223372036854775807. Validate length before BigInt conversion. Invalid acknowledgement yields existing private 503, committed=false, can_execute=false; that means commit is unconfirmed, not rollback proven. Retry the same request ID after refreshing state. Existing request-version limits are unchanged.

This is a narrow backend contract repair, not verified-source evidence, installed duplicate suppression or execution authority. No new workflow, schema, integration or Enrollware dependency was added. Owner assertions remain assertions. Trusted-role/direct-DML authenticity, policy review, authoritative collector, installed canonical consumer, external side-effect fencing and evidence/UI remain unfinished. All six acceptance criteria remain open.

## Exact negative control
Executed HEAD version of publish-intake.mjs in a data-URL module, with synthetic request and version 9223372036854775808. Output:
```json
{"status":200,"body":{"request_id":"00000000-0000-4000-8000-000000000001","version":"9223372036854775808","replayed":false,"committed":true,"can_execute":false,"provenance":"owner_assertion_not_source_verification"}}
```
The unchanged baseline reproduced the defect. No production query or write occurred.

## Validation
Commands:
```
node --test tests/production_intake_publication.test.mjs tests/production_dispatch_decision.test.mjs tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/live_dispatch_check.test.mjs tests/owner_access.test.mjs
node --check supabase/functions/production-board/publish-intake.mjs
git diff --check
```
Exact summary:
```
# tests 78
# suites 0
# pass 78
# fail 0
# cancelled 0
# skipped 0
# todo 0
```
Syntax/diff exit 0. New regression covers zero, leading zero, negative, fractional, exponent, whitespace/newline, bigint overflow, 10,000-digit response, numeric/null version and valid minimum/maximum. Existing actual-route fake-transport auth/no-store tests pass. SQL unchanged; prior isolated PostgreSQL proof reused, no DB suite rerun. Known obsolete Python board auth failures not rerun.

Supabase skill read; current changelog and Edge Function auth documentation retrieved by local Invoke-WebRequest after web tool rejected markdown content type. Reviewed linked TLS cipher deprecation notice (HTTP 200); no TLS/auth/SDK configuration change. Sources: https://supabase.com/changelog.md , https://supabase.com/docs/guides/functions/auth.md , https://supabase.com/changelog/cbc-tls-ciphers-deprecated . No schema/advisor action needed for this JavaScript-only response validation.

## Files and hygiene
Intended files:
- supabase/functions/production-board/publish-intake.mjs
- tests/production_intake_publication.test.mjs
- data/audit/issue380_intake_ack_version_20261013.md
- Codex_Reply_Issue380_20261013_R23.md (separate receipt commit)

Original dirty E:/GitHub/910cpr-class-landers preserved. Isolated worktree E:/GitHub/910cpr-issue380-r23 has Windows case-collision dirt in docs/Earl/index.html and docs/Jackson/index.html; both excluded from explicit staging. No generated output, migration, runtime/state/task changes, merge or deployment. #371 remains primary, #372 untouched. Queue titles scanned; no competing stream or independent item modified. No ops/handoff/next_task.md used; no Codex_Read file created/renamed.

## Proof and next action
Expected operational outcome remains suppressing resolved/blocked/stale work at each selection and side effect. No installed end-to-end proof, production cadence observation, observer or observer-health evidence exists for this increment. Local success evidence: 78 tests on 2026-10-13. Failure condition: malformed/uncertain acknowledgement denies confirmation and execution. Recovery: preserve request identity, refresh canonical state, investigate transport/conflict. Production integration remains gated by engineering and separate review/authorization, not owner credentials. Brian is not assigned routine monitoring; missing installed consumer/observer remains an explicit operational gap.

Next: review this response-boundary repair and continue policy/trusted-role review, authoritative collector and installed no-launch consumer, external side-effect fence/race proof, then private evidence/history/count UI and upload/browser proof. Keep PR #381 draft/unmerged/undeployed. No Brian/account action required.

