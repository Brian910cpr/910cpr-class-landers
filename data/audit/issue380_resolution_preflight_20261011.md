## R2 current evidence — 2026-10-11T22:22Z

This section supersedes R1's access blocker below; R1 is retained as historical evidence.
The connected Supabase tools are available in this dispatch. No owner credential or
metadata export is needed. Owner follow-up/read acknowledgment at
`Codex_Read_Issue380_20261011T2029Z_R1.md` was read before editing.

Read-only `execute_sql` observation at `2026-10-11 22:21:35.13496+00`:
- `production_board_cards` has `context_manifest` (jsonb), `implementation_status`
  (text), `card_type`, `parent_card_id`, and original/incremental/separate/bundled
  work-score fields plus bundle_advantage. The tracked original migration lacks
  these additions; this is schema-history drift, not absent live columns.
- No `resolution_state`, canonical version or evidence reference field is present
  on cards. Existing timestamp is `updated_at`.
- Noninternal triggers on public production_board_* tables: 0. Board RLS policies: 0.
- Storage buckets: class-session-docs, nhcso-class-docs,
  landerware-requirement-documents; all public=false. Storage objects policies: 0.
  None is a dedicated Production Board evidence bucket.
- Total cards: 100; Doing/Next: 42. These counts are a point-in-time observation,
  not proof of freshness or unresolved business state. Owner's earlier 99/42
  observation is historical, not a contradiction.
- `list_edge_functions`: production-board ACTIVE, version 13. No function was
  deployed or mutated. Route absence was confirmed by the owner's R1 read receipt;
  this dispatch independently checked version metadata, not deployed source.

SQL used (metadata and aggregate counts only; no private card/evidence contents):
```sql
select now() as observed_at,
 (select jsonb_agg(jsonb_build_object('name',column_name,'type',data_type)
  order by ordinal_position) from information_schema.columns
  where table_schema='public' and table_name='production_board_cards') as card_columns,
 (select count(*) from pg_trigger t join pg_class c on c.oid=t.tgrelid
  join pg_namespace n on n.oid=c.relnamespace where n.nspname='public'
  and c.relname like 'production_board_%' and not t.tgisinternal) as board_triggers,
 (select count(*) from pg_policies where schemaname='public'
  and tablename like 'production_board_%') as board_policies,
 (select jsonb_agg(jsonb_build_object('id',id,'public',public))
  from storage.buckets) as buckets,
 (select count(*) from pg_policies where schemaname='storage'
  and tablename='objects') as storage_policies,
 (select count(*) from public.production_board_cards) as card_count,
 (select count(*) from public.production_board_cards
  where lane in ('doing','next')) as doing_next_count;
```

Security advisors at 2026-10-11T22:22:21.462Z: 107 INFO RLS-enabled/no-policy
findings, including board cards/activity/thoughts/dependencies. These fit the
current service-role-only model; do not add broad authenticated access to silence
an advisor. Other baseline findings: 2 ERROR security-definer views, 3 WARN mutable
function search paths, 1 WARN anon and 1 WARN authenticated security-definer
function execution. No DDL was applied; this dispatch did not remediate unrelated
findings or claim a clean security baseline.
[Advisor guidance](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy).

### Backend increment and local validation

`execution-check.mjs` now returns HTTP 409 / `unknown_resolution_state` when a
non-null canonical state is neither unresolved nor either supported resolved
state. This prevents a future/invalid state from falling through as unresolved.
Missing/null states retain legacy source-review behavior. All outcomes still
have can_execute=false. Unknown values and private card text are not echoed.

`node --experimental-strip-types --test tests/production_execution_check.test.mjs tests/owner_access.test.mjs`:
tests 28, pass 28, fail 0 (11 additional cases). Includes actual handler route
execution via Node VM, not only the helper. Mocked DB/auth; not Deno or live
end-to-end proof. `node --check supabase/functions/production-board/execution-check.mjs`
and `git diff --check`: exit 0.

### Remaining gates versus unfinished implementation

Issue #266 explicitly scopes v1 to queued/recurring allowlisted worker jobs and
puts later Production Board integration behind an explicit worker-safe flag.
The actual installed Windows dispatcher, approved worker-safe card contract and
atomic side-effect boundary are not established by this checkout. Repository
search of scripts/ops/tests found no dispatcher implementation to safely wire.
Do not change launcher/runtime or infer executable jobs from card prose.

No schema/storage access blocker remains. Transactional resolution/version/
idempotency/audit migration, owner-proxied evidence, UI/history/count changes,
and isolated SQL/concurrency/upload/browser tests are still **unfinished work**,
not claimed blocked by missing credentials. Local SQL tooling discovery found
no psql/docker/supabase command and no PostgreSQL/Docker installation at the
common Program Files paths checked; no installation or production SQL test was
attempted. Obtain an isolated database test target before proving migrations.
Review/authorization is still required before production mutation/merge/deploy.
All six acceptance criteria remain open. BUILT for advisory backend only;
production schema metadata CONNECTED read-only does not prove the feature.
The proof contract below remains unmet. #371 stays the primary deep stream,
#372 stays draft/unmerged/undeployed, and subsequent increments reuse #381.

---

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

## R3 dispatcher contract and installed-selector discovery â€” 2026-10-12T03:42Z

Correcting the earlier search conclusion: `ops/scripts/Invoke-CodexWake.ps1`
contains a Codex queue selector. The installed copy exists at
`C:/Users/ten77/AppData/Local/910CPR/CodexWake/Invoke-CodexWake.ps1`.
Read-only SHA256 observations:
- Installed: DB81F14C5894B614FBD34FC6C9E2DDA4E24C9D3F8B5A17D70DFFE1918F7AB168
- Tracked: 9B5DC9D634FD65143952D9634203C1E0BFCB77DB2221CFC0837E70EAF8A96B0F

Installed selection lines 78-87 use owner-authored issue/title plus updatedAt
watermarks, not canonical resolution/blocker/source state. Owner filtering prevents
third-party issue dispatch, but subsequent comments still change updatedAt. Receipt
verification and post-run watermarking exist in the installed copy; neither proves
that a blocker has cleared. Preferred task selection precedes priority ordering,
so a preferred non-P0 can outrank a new P0. These are code findings consistent with
the issue's #297 reproducer, not an observed new launcher cycle.

No runtime/state/task changes were made. Do not overwrite the installed copy from
the older tracked installer: that would lose receipt verification, manual holds,
retry handling and explicit dispatch support. Actual integration now needs a
reviewed reconciliation of that drift plus an authenticated structured intake
adapter and atomic side-effect boundary. Identification of the selector is no
longer the blocker; authoritative runtime input/claim wiring remains unimplemented.

Independent backend increment: `dispatch-reconciliation.mjs` provides pure typed
selection/pre-side-effect checks and stable candidate ranking. Canonically resolved
cards skip; any blocked item skips until explicit authoritative reconciliation,
even if source signature changes; stale/missing/ambiguous state requires review.
Already-corrected sources propose verification. Worker-safe opt-in is required.
P0 candidates outrank authenticated owner priority; blocked candidates cannot enter
ranking. All outcomes retain can_execute=false. No HTTP route/dispatcher imports
this module yet. This is executable contract coverage, not a lease or integration.

Mature queue lesson: distinguish source-event updates from lifecycle transitions;
retain explicit blockers and versioned claims instead of treating comments as work.
Canonical card owns resolution; immutable transition history and separate evidence
remain necessary. This increment introduces no Enrollware dependency and improves
native operating discipline; no training workflow is replaced.

Validation: node --experimental-strip-types --test tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/owner_access.test.mjs
Result: 37 tests, 37 pass, 0 fail. New contract cases: 9. Mocked/pure local tests only.
node --check supabase/functions/production-board/dispatch-reconciliation.mjs and
git diff --check passed. No generator, SQL, upload/browser proof, merge or deploy.

All six issue acceptance criteria remain open. Canonical transaction/evidence/UI
work remains unfinished, not access-blocked. Keep #381 draft and #371 primary;
#372 untouched. Next: reconcile installed selector into a reviewed source baseline,
add authenticated typed intake/versioned claim adapter with durable skip audit,
then prove #297 suppression before launch and owner-resolution stop before mutation
in an isolated runtime. Never infer worker permission from issue prose.

Evidence level BUILT only. Last end-to-end reconciliation proof: none. Expected
window: each selection and side effect. Failure: blocked/resolved work launches,
stale claim executes, priority bypasses P0. Observer/observer health: not integrated
or proven; current regression is reported on #380. Recovery: preserve runtime
and audit state, suspend affected dispatch via approved controls, reconcile live
canonical state. No Brian action required for this code review increment.
