# Issue 380: Production Board resolution preflight

State: BLOCKED for resolution writes/private uploads; read-only backend increment BUILT and locally validated.

## Scope and authority

Owner request: https://github.com/Brian910cpr/910cpr-class-landers/issues/380
Execution acknowledged before implementation in issue comment 6113224651; compact plan posted in comment 6113243739.
Base: 8b6ec23014b6abc3662f40dfcad67561df9341dd.
Branch: codex/issue380-manual-resolution-20261011.
Separate checkout: E:/GitHub/910cpr-issue380-20261011.
PR #372 is the existing independent primary #371 stream and remains untouched, draft, unmerged and undeployed. No existing PR for #380 was found among open PRs; use this issue's review branch rather than adding unrelated changes to CRM.

Read AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Read the Supabase skill and current changelog/storage access-control documentation. No new service or dependency.

## Facts found in authoritative repository sources

- `supabase/migrations/20260812161043_production_board.sql`: cards own identity; lane is constrained to doing/next/decision/parked. No resolution/version/evidence relation. Cards, thoughts and activity have RLS and no anon/authenticated grants. Service role can mutate/delete audit rows: the current activity table is not immutable.
- `supabase/functions/production-board/index.ts`: owner authorization is shared; list returns cards and associated thoughts/activity; PATCH reads, updates, then inserts audit in separate HTTP requests. No transaction, idempotency receipt, version predicate or resolved-card guard. Thought insertion changes updated_at. Do not use timestamps as a transactional lease.
- `supabase/functions/_shared/owner-auth.ts` and `owner-session.ts`: owner session or legacy automation key, first-party origin check; corporate sessions are not owner authorization. No auth/origin changes in this increment.
- `docs/admin/production.js`: four lanes, active count uses doing, drag/drop PATCH, no resolution dialog/history/evidence UI. Existing submit closes drawer even after save failure; preserve this finding for the resolution UI work.
- `docs/admin/production-summary.js`: active cards selected by doing/next only.
- `supabase/migrations/20260913164411_brian_monitor_dashboard.sql`: owner snapshot selects implementation_status/context_manifest but tracked board migrations do not define those fields. This is concrete schema-history inconsistency, not proof of a live defect.
- `supabase/functions/owner-dashboard/core.mjs`: boardPrompts uses free-text implementation_status matching done/verified/closed/completed. Resolution rollout must replace that heuristic with canonical resolution state.
- Searches of repository scripts/ops found no Production Board dispatcher mutation implementation. The external launcher must be identified before claiming workers enforce reconciliation.
- Production endpoint unauthenticated GET returned HTTP 401. No authenticated live schema/card/storage inspection was performed. No Supabase credentials were present in environment variable names checked; no Supabase MCP tool is available in this session. Checked PATH and common C:/Tools, Scoop, WinGet and .deno locations without finding Supabase/Deno/Postgres executables there. This does not prove none exists elsewhere.

## Safe backend increment

Added owner-gated read-only route:

`GET /production-board/<uuid>/execution-check?expected_updated_at=<exact previously read updated_at>`

Implementation: `supabase/functions/production-board/execution-check.mjs`, invoked from `index.ts` after existing owner auth.

- Every response has `can_execute: false`; this advisory route cannot authorize a side effect or grant a claim/lease.
- Invalid card ID: 400; no database query.
- Missing card: 404 / skip.
- Recorded canonical handled_manually or verified_resolved: 200 / skip, even if claimed timestamp is old.
- Missing expected timestamp: 428 / review. Changed/unavailable version: 409 / review.
- Database failure or wrong-card result: 503 / review, with no underlying private error/details returned.
- Legacy/unresolved matching card: 200 / review / authoritative_source_check_required. Doing/Next is not proof the problem persists. Parked/Needs Decision is not resolution.
- Reads exactly one card; returns only ID/version/decision, never card text, attachments or credentials. Response is no-store.
- `resolution_state` and its two resolved values are a **proposed contract**, not a claim that live storage already supports them. Legacy cards remain review-required. No write API or schema migration is introduced here.

No dispatcher has been wired to this route, and no skip audit is persisted yet. This is preparation for acceptance 2/6, not their completion. Source inspection still needs source-specific verified adapters. Rechecking a GET cannot eliminate the race between check and an external side effect; transactional claims and execution-time checks remain required.

## Design and next migration gates

Use the established card object, not a second task catalog. Mature issue trackers separate resolution from lane, preserve reopen history, and record evidence separately from workflow labels; the existing GitHub issue/PR lifecycle provides the local reference pattern. This is native operational evidence/provenance, independent of Enrollware; no additional Enrollware dependency.

Before resolution-write implementation/rollout:

1. Read live metadata for card columns/constraints/grants, activity permissions/triggers, owner snapshot and storage buckets/policies. Reconcile implementation_status/context_manifest schema-history gap. Read live active card state without changing it.
2. Prepare additive canonical state/version fields and append-only resolution/evidence events with server-derived actor, source, prior/new states, completion time, justification, original explanation and affected record references. Keep lane separate. No silent deletion or automatic reopen from old alerts.
3. Use one transactional RPC for compare-and-swap version, idempotency payload binding, card transition and audit insertion. Concurrent/replayed submissions must not create duplicate transitions. Block legacy PATCH from reopening/changing resolved work; it cannot remain an escape hatch.
4. Use existing private Storage if verified suitable. Owner-authenticated upload/download proxy, opaque card-bound object keys, size/type checks, checksum/verified upload result, retention/deletion audit. Never put evidence in this repository, public buckets, public URLs or arbitrary client-selected object paths. Upload failures must not attach evidence; manual resolution with evidence pending remains allowed.
5. Add resolution dialog, editable completion date, source/context, pasted text/URL/reference inputs and multiple labeled attachments/drop/paste. Provide upload error/pending/verified states and justified reopen. Change board/summary/owner snapshot together to hide resolved cards from active counts and offer searchable history. Version changed public asset URLs.
6. Identify the real dispatcher and add canonical live reconciliation before claim and before each side effect, with durable skip/review reason. Read authoritative class/payment/eCard/deployment state only through safe supported access, proposing verified resolution when already fixed. Unknown state blocks execution rather than inferring failure.
7. Isolated SQL and owner-session/browser integration tests, synthetic evidence upload/retrieve/failure and conflict tests; rollback plan preserving resolution history. Post exact rollout for separate review/authorization. No production mutation, merge or deploy authorized by this report.

## Validation (local)

`node --experimental-strip-types --test tests/production_execution_check.test.mjs tests/owner_access.test.mjs`

Result: tests 17, pass 17, fail 0. Twelve new behavioral tests plus five existing owner access tests. Actual index.ts handler executed in VM after Node TypeScript syntax stripping, with imports supplied and database/auth mocked. No real DB query or Deno runtime/type-check proof.

`node --check supabase/functions/production-board/execution-check.mjs`: exit 0.

`git diff --check`: exit 0.

Baseline `python -m unittest discover -s tests -p test_production_board.py`: Ran 4, FAILED (failures=3), before changes. Failures assert former maximPortalSession, maxim-portal/login, maxim_portal_sessions behavior removed by prior owner-auth migration. Do not restore corporate authorization to satisfy obsolete assertions. These failures remain unrelated/unfixed.

## Preservation and blockers

Original E:/GitHub/910cpr-class-landers dirty work preserved. Fetch failed with bad object 6e61cabca5981d1389e52c60d95424d9893bb50f and bad refs/remotes/origin/codex/group-training-experience; no reset, cleanup, repair or repack was attempted by this work. Fetch itself triggered Git's automatic maintenance, which also failed; no repeated fetch retry.

Fresh clone has known Windows case collisions producing dirty docs/Earl/index.html and docs/Jackson/index.html. Explicit staging excludes both. No generator ran. Existing Codex processes were observed; none interrupted, no worker/assignment/launcher modifications, installs or reboot.

Exact remaining blocker: no authenticated live schema/storage/card-state access in this execution session to verify the required production baseline, plus unresolved tracked schema-history discrepancy. Need an authorized read-only Supabase session or sanitized metadata export (never post secrets) and identification of actual dispatcher integration point. Production rollout separately requires explicit review/authorization. The read-only increment can be reviewed without bypassing either gate.

## Proof contract

Evidence level: BUILT for advisory check only; not CONNECTED/PROVEN/MONITORED/HEALTHY. Last real owner-card resolution + private-evidence + worker-skip cycle: none observed. Expected outcome: owner records manual completion with private retrievable evidence, all active views exclude it, next worker skips, justified reopen retains history. Expected window: each submitted resolution and every worker claim/side effect. Failure: stale version accepted, unavailable state treated as executable, false attachment success, resolved card counted/executed or history lost. Future observer: real dispatcher reconciliation receipts plus owner-board health outcome; observer heartbeat/recovery not yet implemented/proven. Recovery: suspend affected execution, preserve audit/evidence, re-read canonical state; do not auto-reopen. Escalate only unavailable account access, retention decisions or rollout approval. Present process is not monitored and must not be represented as healthy; routine owner checking is not an acceptable final monitor.

All six issue acceptance criteria remain open. Continue #371 as primary; use this branch/PR for subsequent #380 increments rather than creating a competing deep stream.
