# Issue #380 — R2 dispatch receipt

Timestamp: 2026-10-11T22:25:00Z (UTC)
Work-item state: PR_OPEN / IN_PROGRESS; acceptance incomplete.
Evidence state: BUILT advisory backend; CONNECTED read-only schema inspection only.
Local branch: codex/issue380-reconciliation-r2-20261011
Pushed PR branch: codex/issue380-manual-resolution-20261011
PR reused: https://github.com/Brian910cpr/910cpr-class-landers/pull/381
Substantive commit: e84d4b30b1649fc45e598b447cb9016e2f017c7b
Receipt commit: discover from branch tip; this receipt follows the substantive commit.

## Execution and preservation
Read full issue and owner comments, current repository AGENTS.md,
CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and
LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Execution acknowledgment preceded edits:
https://github.com/Brian910cpr/910cpr-class-landers/issues/380#issuecomment-6114531045
Used a separate named worktree at E:/GitHub/910cpr-issue380-r2-20261011 based on
PR #381's latest remote tip 86ef0ba8b378c1ce11a6e8b79bf9d188d5286731.
Original E:/GitHub/910cpr-class-landers dirty work remains untouched. Worktree's
Windows case-collision changes docs/Earl/index.html and docs/Jackson/index.html
are intentionally unstaged/uncommitted. No unrelated files staged. No generators,
cleanup, reset, merge, deploy, process interruption or launcher change. #371 remains
the primary deep assignment; draft #372 untouched. No arbitrary comment used as
owner authorization. No ops/handoff/next_task.md written.

## Findings and work
The earlier schema access blocker is cleared. Connected read-only Supabase tools
confirmed schema metadata and aggregate counts at 2026-10-11T22:21:35.13496Z:
100 cards, 42 Doing/Next; context_manifest and implementation_status exist; no
canonical resolution/version fields; no board triggers/policies; three private
buckets but no board-evidence bucket; storage.objects has no policies. Function
metadata still reports production-board v13. No private card data was fetched.

Updated the primary audit with current evidence, exact SQL, advisor baseline,
attribution to owner R1 review, and remaining gates. Historical R1 evidence is
retained and explicitly superseded where appropriate.

Added fail-closed handling for unknown/non-null canonical resolution states:
409 unknown_resolution_state; legacy missing/null and explicit unresolved still
require source review. Every outcome denies execution. Eleven additional tests
cover malformed/future states, legacy compatibility and actual handler response
privacy. This is preparatory backend work, not an integrated worker lease.

Exact changed files:
- supabase/functions/production-board/execution-check.mjs
- tests/production_execution_check.test.mjs
- data/audit/issue380_resolution_preflight_20261011.md
- Codex_Reply_Issue380_20261011_R2.md

## Validation
- node --experimental-strip-types --test tests/production_execution_check.test.mjs tests/owner_access.test.mjs
  Output: tests 28; pass 28; fail 0.
- node --check supabase/functions/production-board/execution-check.mjs: exit 0.
- git diff --check: exit 0.
- Live metadata SELECT and list_edge_functions succeeded; no production write.
- Security advisors read-only baseline: 107 INFO no-policy findings (including
  board tables), 2 ERROR security-definer views, 3 WARN search-path findings,
  1 WARN anon and 1 WARN authenticated function-execute findings. No DDL applied
  or unrelated remediation attempted; not a claim of security health.
- R1 recorded three obsolete Maxim auth assertion failures in Python board tests;
  not rerun or repaired in R2. Current targeted route/auth suite is green.

## Exact remaining gates and next action
Actual installed Windows dispatcher and its approved worker-safe card contract /
atomic pre-side-effect boundary are not established here. Issue #266 explicitly
requires an opt-in worker-safe flag for later Production Board integration.
Do not reinterpret arbitrary backlog prose as executable commands.
Production mutation, merge and deployment require separate review/authorization.

Backend migration, version/idempotency/audit transaction, private evidence proxy,
UI/history/count changes and SQL/concurrency/upload/browser tests remain unfinished,
not blocked by credentials. No psql/docker/supabase executable or PostgreSQL/Docker
installation was found via PATH/common Program Files checks. An isolated database
test target is needed before proving migrations; do not use production for tests.

Recommended next action: keep #381 draft; prepare and verify the additive migration
and transactional RPC against an isolated database, then owner evidence routes and
coordinated UI/counts. Establish dispatcher integration with #266's actual runtime
and explicit safe contract before enabling execution. No owner credential/export
is required. Account-level action is required only if an isolated database target
cannot be supplied locally, and for separately reviewed production rollout.
All six acceptance criteria are open; this dispatch does not close #380.

## Proof contract and deployment state
Persisted locally, committed; push and GitHub receipt verification performed after
this file was written. No merge/deploy. Mock route tests do not prove real owner
resolution/private upload/retrieve/worker skip. Last successful real cycle: none.
Expected evidence: each owner resolution has canonical history/private retrievable
proof and resolved cards disappear from active counts; every claim and side effect
reconciles current state. Failure: stale transition accepted, false attachment,
resolved card executed/counted, history lost. Observer and observer-health heartbeat
are not implemented/proven. Recovery: suspend execution, preserve evidence, reread
canonical state; never auto-reopen. Brian must not become the routine observer.

Queue sweep reviewed open [CODEX] titles; no additional issue was modified or
claimed. Existing assignments were preserved. Narrow independent backend safety
work was advanced while dispatcher/rollout gates remain unresolved.
