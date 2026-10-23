# Issue 380 R21 — owner-authenticated typed intake publication

BUILT / validated locally. Existing PR #381 stays draft/unmerged/undeployed. All six original acceptance criteria remain open. SQL remains outside migrations and unapplied to production. Every response denies execution with can_execute=false.

## Result and authority
Acknowledged execution on #380 before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/380#issuecomment-6147333150 . Full issue/comments, current branch AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design/proof standards and prior R20 report read. The original checkout lacks the current handoff file; authoritative current PR checkout was used. Only Brian910cpr owner comments were used as owner direction. #371 remains primary; #372 remains untouched. Open queue scanned; no competing implementation stream opened.

Adds POST /production-board/<card>/dispatch-intake behind existing owner authorization. Typed declaration includes card/issue identity, expected string version, stable request UUID, explicit blocked/source-state/worker-safe values, source reference and canonical UTC observation timestamp. Actor is server-bound. This endpoint is an OWNER ASSERTION publisher, not an automated source verifier or arbitrary issue-comment interpreter. It does not reconcile GitHub priority, unblock an installed worker, reopen a card, grant execution, or claim source truth.

The draft database RPC locks publication request, then shared per-card advisory identity, then intake, then card. Dispatcher takes the same per-card advisory identity before intake/card. This serializes approved first publication despite no existing intake row. Existing-row direct DML retains intake-before-card ordering. Publication checks expected version, unresolved state, immutable existing issue identity, finite/fresh observation time; writes intake, bumped card version, immutable publication request record and activity atomically. Same-ID identical replay returns historical version without mutation; changed payload rejects. Resolved card cannot be reopened through this path. Updated intake invalidates reservations through existing version trigger.

The proxy returns committed=true only after the RPC transport acknowledgement; known version/resolution/identity/replay/time conflicts return clear 409, malformed requests 400, uncertain/malformed transport results 503 without private detail. Same request ID is retained for uncertain retries. Successful output is allowlisted and labels provenance owner_assertion_not_source_verification. No uploaded evidence is claimed.

## Design and security review
This continues mature optimistic concurrency, transactional audit and fixed lock-order practice already established in R14–R20, rather than inventing another catalog or workflow. Existing Production Board card owns truth; assertions/history survive changes. No Enrollware dependency is added; native queue integrity supports independence, but no training-business incumbent capability is replaced by this increment.

Used Supabase skill; fetched changelog index and current database-function docs (https://supabase.com/docs/guides/database/functions). Relevant recent changelog pages inspected: CBC TLS cipher deprecation and Postgres 15.19/17.11 changes. No SDK/transport configuration change made; isolated SQL executes on PostgreSQL 16.4. Functions use SECURITY INVOKER/empty search_path, public/anon/authenticated EXECUTE revoked; publication table RLS enabled and service_role only SELECT/INSERT. Proxy retains existing owner auth, server-only key and no-store. Local real-role tests reject anon/authenticated calls and service-role event deletion. No live project advisor/production mutation performed; advisors remain a rollout gate.

Known limits: service_role remains trusted and retains pre-existing direct intake DML/event INSERT privileges. This is not tamper-proof provenance or mandatory gateway enforcement against a compromised trusted role. Direct missing-row/bulk/card-first writers are outside approved lock protocol and require review before rollout. One-card-per-transaction RPC is tested; multi-card transactions may need sorted acquisition. Hash collision can conservatively serialize unrelated requests/cards. No distributed external side-effect fence exists. Five-minute freshness and sixty-second reservation policy windows remain draft policy. Owner authenticated declaration does not itself prove authoritative source access, worker-safe authorization policy or identity-specific owner attribution. Automated publisher/runtime consumer/priority reconciliation must not blindly turn third-party prose into these fields. Initial issue/card binding is an owner assertion; existing binding cannot change via this RPC.

## Exact changed files
- data/audit/issue380_dispatch_transaction_draft.sql
- data/audit/issue380_intake_publication_draft.sql
- supabase/functions/production-board/index.ts
- supabase/functions/production-board/publish-intake.mjs
- tests/reconciliation/board_intake_publication.py
- tests/production_intake_publication.test.mjs
- data/audit/issue380_intake_publication_20261013.md
- Codex_Reply_Issue380_20261013_R21.md (separate receipt commit)

## Local proof
Dedicated existing local cluster E:/GitHub/issue380-pg-portable/cluster-r16 started explicitly with -h 127.0.0.1 -p 55480. Fresh empty database issue380_test_r21; strict inherited empty/local target guard. Synthetic fixtures retained; server stopped after tests. No production DSN used. PostgreSQL 16.4, psycopg 3.2.10, libpq 160009.

Commands from E:/GitHub/910cpr-issue380-r21-20261013:
```powershell
$env:ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 user=issue380_local dbname=issue380_test_r21'
E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_intake_publication.py
node --test tests/production_intake_publication.test.mjs tests/production_dispatch_decision.test.mjs tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/live_dispatch_check.test.mjs tests/owner_access.test.mjs
node --check supabase/functions/production-board/publish-intake.mjs
python -c "import ast; ast.parse(open('tests/reconciliation/board_intake_publication.py').read())"
git diff --check
```
SQL actually parsed/executed in isolated database; edge index TypeScript stripped/parsed and actual routes executed with fake database transport, not deployed Supabase. 23/23 PostgreSQL tests passed, 11 observed Lock waits; 75/75 Node tests passed, no skips. AST, module syntax and diff checks pass. The final SQL comment-only clarification follows the database run; no executable SQL changed afterward. No known failure in these suites. Prior unrelated baseline Python board auth failures were not rerun. No generator/build chain run.

Full PostgreSQL output:
```text
PostgreSQL: PostgreSQL 16.4, compiled by Visual C++ build 1940, 64-bit
psycopg: 3.2.10 libpq: 160009
test_dispatch_audit_failure_rolls_back_reservation (__main__.IntakePublication.test_dispatch_audit_failure_rolls_back_reservation) ... ok
test_dispatch_canonical_gates (__main__.IntakePublication.test_dispatch_canonical_gates) ... ok
dispatch competing reservations: observed Lock wait
test_dispatch_competing_reservations_lock (__main__.IntakePublication.test_dispatch_competing_reservations_lock) ... ok
test_dispatch_intake_change_invalidates_reservation (__main__.IntakePublication.test_dispatch_intake_change_invalidates_reservation) ... ok
test_dispatch_intake_identity_cannot_move (__main__.IntakePublication.test_dispatch_intake_identity_cannot_move) ... ok
test_dispatch_intake_writer_first_no_deadlock: observed Lock wait
test_dispatch_intake_writer_first_no_deadlock (__main__.IntakePublication.test_dispatch_intake_writer_first_no_deadlock) ... ok
test_dispatch_reader_first_intake_writer_waits: observed Lock wait
test_dispatch_reader_first_intake_writer_waits (__main__.IntakePublication.test_dispatch_reader_first_intake_writer_waits) ... ok
test_dispatch_reservation_replay_and_conflict (__main__.IntakePublication.test_dispatch_reservation_replay_and_conflict) ... ok
test_dispatch_resolution_between_checks_skips (__main__.IntakePublication.test_dispatch_resolution_between_checks_skips) ... ok
test_dispatch_roles (__main__.IntakePublication.test_dispatch_roles) ... ok
test_dispatch_stale_source_and_expired_lease (__main__.IntakePublication.test_dispatch_stale_source_and_expired_lease) ... ok
test_dispatch_then_publication_invalidates_pre_side_effect: observed Lock wait
test_dispatch_then_publication_invalidates_pre_side_effect (__main__.IntakePublication.test_dispatch_then_publication_invalidates_pre_side_effect) ... ok
test_distinct_request_stale_writer_rejected: observed contender Lock wait
test_distinct_request_stale_writer_rejected (__main__.IntakePublication.test_distinct_request_stale_writer_rejected) ... ok
test_identical_request_replays_once: observed contender Lock wait
test_identical_request_replays_once (__main__.IntakePublication.test_identical_request_replays_once) ... ok
test_publication_audit_failure_atomic_rollback_and_retry (__main__.IntakePublication.test_publication_audit_failure_atomic_rollback_and_retry) ... ok
test_publication_competing_first_publishers: observed Lock wait
test_publication_competing_first_publishers (__main__.IntakePublication.test_publication_competing_first_publishers) ... ok
test_publication_create_update_replay_conflict (__main__.IntakePublication.test_publication_create_update_replay_conflict) ... ok
test_publication_rejects_stale_resolved_identity_and_time (__main__.IntakePublication.test_publication_rejects_stale_resolved_identity_and_time) ... ok
test_publication_roles (__main__.IntakePublication.test_publication_roles) ... ok
test_publication_then_dispatch_waits_and_rechecks: observed Lock wait
test_publication_then_dispatch_waits_and_rechecks (__main__.IntakePublication.test_publication_then_dispatch_waits_and_rechecks) ... ok
test_request_reuse_across_cards_conflicts: observed contender Lock wait
test_request_reuse_across_cards_conflicts (__main__.IntakePublication.test_request_reuse_across_cards_conflicts) ... ok
test_rollback_releases_request_without_phantom_receipt: observed contender Lock wait
test_rollback_releases_request_without_phantom_receipt (__main__.IntakePublication.test_rollback_releases_request_without_phantom_receipt) ... ok
test_same_request_changed_payload_conflicts: observed contender Lock wait
test_same_request_changed_payload_conflicts (__main__.IntakePublication.test_same_request_changed_payload_conflicts) ... ok

----------------------------------------------------------------------
Ran 23 tests in 4.191s

OK
```
Node summary: tests 75; suites 0; pass 75; fail/cancelled/skipped/todo 0.

## Operational proof contract and continuation
Expected outcome: canonical published owner state invalidates stale worker decisions before launch/mutation. Current evidence is isolated transaction/proxy tests, last locally observed 2026-10-13T14:04Z; no production end-to-end proof exists. Cadence: on explicit trusted reconciliation, fresh source observation within draft five-minute window and before each side effect. Failure/staleness: missing/stale version or source, missing commit acknowledgement, resolution, unsafe worker policy, absent external fence all deny execution. No deployed observer or observer-health evidence exists for this draft. Recovery: refresh canonical card/source; preserve request identity for uncertain retry; engineering investigates conflicts before any authorization. No Brian monitoring/account action assigned.

Next: security/policy review of publication RPC and owner assertion boundary; authenticated authoritative-source collector and installed selection/no-launch consumer with priority reconciliation, atomic external pre-mutation fence/race proof, then private evidence + resolution/history/count UI and upload/browser proof. Separate authorization/review required before production migration, merge or deployment. These are unfinished engineering/review gates, not a credential blocker. No production/runtime/state/task/process changes, merges or deployments performed (only disposable test server start/stop).

## Hygiene
Named isolated branch codex/issue380-r21-20261013 based on #381 tip 0922d14708616006f8265a75e48eab7662d006cc. Original E:/GitHub/910cpr-class-landers dirty state preserved. Fresh worktree Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html deliberately excluded. Stage explicit intended paths only. Reuse #381 by fast-forward push to its existing head branch; no new PR, force push or merge. No ops/handoff/next_task.md used. No Codex_Read file created/renamed.
