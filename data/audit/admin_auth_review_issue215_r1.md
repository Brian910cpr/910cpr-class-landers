# Issue 215: admin authentication inventory and migration boundaries

Source: `8808884a23e4da2ce055b4da6a9002a6ea17c39c` in Brian910cpr/910cpr-class-landers.
Assessment: September 13, 2026, America/New_York (UTC-04:00).
State: **IN_PROGRESS**. This independent audit checkpoint advances #215 while #214 is release-blocked. Shared auth implementation, migration, browser verification and deployment remain outstanding; this report does not satisfy the full issue acceptance criteria.

## Scope and reproducibility

Inventoried all **34 files / 19 HTML pages** under `docs/admin/`, **5 directly referenced asset paths** (4 present and 1 missing), and **7 relevant backend boundary files**. Every CSS/JS/model file under admin is included even when it contains no authentication token. The machine-readable record is `data/audit/admin_auth_inventory_issue215_r1.json`.

```powershell
python -B scripts/audit_admin_auth_contract.py --ref 8808884a23e4da2ce055b4da6a9002a6ea17c39c --output data/audit/admin_auth_inventory_issue215_r1.json
python -B -m unittest discover -s tests -p test_audit_admin_auth_contract.py -v
```

The inventory reads committed Git objects; it is independent of dirty files or sparse-checkout contents. Its only generated output is the explicitly named JSON. It does not execute application JS, fetch APIs, inspect browser storage, access secret values, publish files or read operational data snapshots. Literal matches, source-line numbers and constant candidates are evidence for manual review, not proof of runtime behavior. Dynamic imports, computed property storage access and externally loaded code need review during implementation. Asset reference counts conservatively match basenames across committed docs files.

Useful exact JSON fields:

- `source_commit`, `counts`, `contract` and `limitations` establish the snapshot and scope.
- `files[]` is keyed by `path`; `scope` distinguishes admin file, referenced asset and endpoint boundary.
- `files[].storage[]` records store, operation, key identifier, resolution and line, never the stored value.
- `files[].token_lines`, `markers`, `direct_assets` and `exists_in_source_commit` record evidence locations and missing references.
- `files[].reference_matches.outside_admin` helps distinguish exclusively admin assets from the general theme. It is not a runtime reachability proof.

## Verified findings

1. **Canonical contract is duplicated, not absent.** Admin Port, All Classes, dashboard admin operations and Financial already read `sessionStorage.hotSyncAdminKey` and send `X-Hot-Sync-Admin-Key`; Class Registry prefers it. No shared admin-auth helper exists in this snapshot. These pages each manage gates, storage and errors independently.
2. **Owner routes use corporate credentials.** `docs/admin/production.js:1,2,13,15` logs in through the Maxim portal, stores `maximPortalSession` and sends `x-maxim-session`. `docs/admin/production-summary.js:1` does the same for dashboard cards. `docs/assets/instructor-workbench.js:6,8,14` requires the corporate session and has no canonical admin unlock flow. `docs/admin/dashboard.html:109` separately uses a corporate session for participant detail. A single helper must cover these less-visible paths as well as the principal unlock button.
3. **Class Registry has fallback in both layers.** `docs/assets/class-registry.js:16` falls back to `maximPortalSession`. `supabase/functions/class-registry/index.ts:10` can accept a corporate session after a supplied admin key is rejected. Owner-admin callers must not regain authorization through that fallback. Preserve any intentionally separate corporate surface via explicit endpoint scope, not an implicit fallback on an admin route.
4. **Backend migration is required for some clients.** Production Board and Instructor Workbench authenticate corporate-session records and do not currently accept the canonical admin header. Their CORS allowlists also omit it. Renaming the client header alone would lock those admin pages out. The dashboard detail endpoint has a separate public/redacted versus authorized-data contract; preserve its non-admin consumers while adding an explicitly protected admin path.
5. **401/403 clearing differs by call path.** Admin Port (`admin-port.js:41`), All Classes load (`all-classes.js:60`) and Class Registry load (`class-registry.js:19`) explicitly clear on 401 only. All Classes save does not centrally clear on either denial. Financial load handles both statuses (`financial.html:36`), but its payment-write catch only shows an error (`financial.html:38`). Dashboard operations contain multiple handlers and an XHR upload path. An inventory status mention does not prove every branch handles expiry.
6. **Other storage is business/UI state, not alternate credentials.** Keep `hotSyncDrafts`, `lw-instructor-intake-prototype-v1`, `lw-nhcso-workspace-prototype-v2`, `lw-nhcso-v4-prototype` and `910cpr-color-theme` separate. Do not replace them or use `sessionStorage.clear()`/`localStorage.clear()` for admin logout. NHCSO/corporate sessions and prototype data are explicitly outside the auth conversion.
7. **Public/static shells need an explicit classification.** Some admin paths have no protected request at all; a client-side gate cannot make publicly served JSON or embedded content private. This audit did not read their data files or verify public exposure. Do not report access control solely because the shared script is loaded.

## Every admin HTML page

All paths below are relative to `docs/admin/`. No page was migrated in this checkpoint.

| Page | Current source behavior | Next disposition |
|---|---|---|
| `admin-port.html` | Canonical key via `admin-port.js`; local unlock/lock; 401 clear | Migrate through helper and preserve date-scoped workspace behavior. |
| `all-classes.html` | Canonical key via `all-classes.js`; local unlock/lock; separate read/write flows | Migrate both requests and clear rendered private state on lock/denial. |
| `class-registry.html` | `assets/class-registry.js` uses canonical key with corporate fallback | Remove owner-route fallback in client and server. |
| `dashboard.html` | Canonical inline/admin-ops requests; corporate production summary and participant detail | Cover inline, fetch, XHR and summary/detail paths together; coordinate #216 changes. |
| `financial.html` | Inline canonical key and browser prompt; separate payment write | Preserve UI/payment behavior while centralizing unlock and all denial handling. |
| `production.html` | Corporate login/session via `production.js` | Coordinate canonical admin backend contract and CORS before client cutover. |
| `instructor-workbench.html` | Corporate-only `assets/instructor-workbench.js` | Add canonical admin route/contract; preserve separately scoped corporate access. |
| `payments.html` | Fetches `/data/admin_payables.json` without an auth header | Classify published feed/privacy boundary and integrate owner-shell behavior; helper alone cannot protect static data. |
| `refresh-availability.html` | Reads published availability and links to GitHub Actions | Owner-shell helper; GitHub retains separate account authorization. |
| `schedule-reader.html` | Public schedule read; no credential plumbing | Owner-shell helper without inventing a second secret or blocking public schedule API consumers. |
| `scheduling-landscape.html` | Published diagnostic feed and `scheduling-landscape-lanes.js`; no credential plumbing | Owner-shell helper; preserve feed semantics and public/private classification. |
| `toolbox.html` | Navigation/copy-command UI; no credential plumbing | Owner-shell helper; its command-copy prompt is not an auth prompt. |
| `instructor-session.html` | Static session prototype; no storage or fetch auth found | Explicit prototype/owner-shell disposition; no production save claims. |
| `instructor-class-intake-prototype.html` | Browser-local prototype draft storage | Keep draft storage unchanged; owner-shell disposition separately. |
| `nhcso-training-history-v5.html` | NHCSO historical prototype | Excluded from credential conversion under issue's explicit NHCSO exclusion. |
| `nhcso-training-workspace-prototype.html` | NHCSO browser-local prototype | Excluded; preserve its data storage. |
| `nhcso-training-workspace-v3-prototype.html` | Redirect to NHCSO v6 | Excluded; preserve redirect and target auth lane. |
| `nhcso-training-workspace-v4-prototype.html` | NHCSO browser-local prototype | Excluded; preserve its data storage. |
| `nhcso-training-workspace-v6.html` | NHCSO workspace prototype | Excluded; do not infer owner-admin identity from its directory alone. |

The 15 other admin files (5 CSS and 10 JS) are individually present in JSON, including models and navigation with no credential behavior. `docs/assets/class-registry.js` and `docs/assets/instructor-workbench.js` have only admin HTML reference matches in this snapshot. `site-theme.js` and `site-theme.css` each have 979 outside-admin reference matches; keep them general-purpose. No `/corp/*`, Maxim or NHCSO application file was changed or converted.

## Backend expectations and coordinated changes

| File / route | Existing expectation | Required migration boundary |
|---|---|---|
| `worker/admin-api.js:7-14,41-52` / `/admin/*` | `HOT_SYNC_ADMIN_KEY`; canonical header; missing config 503; invalid key 401; origin rejection 403 | Reuse current secret authority and fail-closed behavior. |
| `worker/finance-worker.js:8-23` / finance service | Same canonical secret/header | Preserve payment semantics and endpoint authorization. |
| `supabase/functions/canonical-session-workspace/index.ts:31-38` | Validates canonical header through the HOT_SYNC authority | Preserve contract; do not introduce alternate credential. |
| `supabase/functions/class-registry/index.ts:6,10` | Canonical validation plus corporate fallback | Explicit owner-only boundary; failed admin validation must not fall through. |
| `supabase/functions/production-board/index.ts:3,8,14` | `x-maxim-session` or bearer token referencing corporate session table | Canonical admin auth plus matching CORS/client update; inventory remaining consumers before retiring any corporate route. |
| `supabase/functions/instructor-workbench/index.ts:4,8,16` | Corporate session header/table | Explicit admin contract for owner UI, preserve corporate use separately. |
| `supabase/functions/session-workspace/index.ts:4,10` | Corporate-authorized details with a broader resolve/summary contract | Admin detail adapter/route must preserve public/redacted and corporate semantics. |

The local implementation is eligible; no new owner decision is needed to use the contract explicitly approved by #215. However, production credential parity remains a separate gate in [#140's latest instruction](https://github.com/Brian910cpr/910cpr-class-landers/issues/140#issuecomment-5645954782). That instruction says the GitHub secret differs from the deployed canonical value and requires private owner restoration before publisher verification. This is existing issue evidence, not a new secret check or failed-auth retry. Do not weaken validation or rotate production services to make an admin migration appear successful.

## Concrete next implementation and verification

1. Create one admin-only helper owning key get/set/clear, canonical headers, unlock/lock hooks and denial handling. Keep page-specific messages. Clear only the canonical key and page's private state; preserve corporate and draft/theme storage. Ensure stale in-flight responses cannot repopulate a locked page or clear a newly entered replacement key.
2. Inventory other consumers of the three corporate-backed services and establish explicitly scoped admin endpoint behavior/CORS. Preserve corporate authentication on corporate surfaces and redacted/public summary semantics. Follow the existing HOT_SYNC authority rather than inventing another secret.
3. Migrate every true owner page, including dashboard inline/detail/XHR and production-summary requests. Exclude the five NHCSO pages above plus `/corp/*`/Maxim. Update changed JS URLs with a version and coordinate dashboard #216 edits before merge; no sitewide generator is needed.
4. Test helper get/set/clear and denial behavior, no credential leakage to unapproved origins, missing configuration fail-closed, and corporate-only tokens rejected on owner routes. Include abort/late response after lock, unlock one page then navigate same tab, lock and back/forward cache restoration, 401 and 403 on both reads and writes, and preservation of corporate/draft storage. Existing data/business tests must remain green.
5. Prove actual rendered admin-page navigation and repeated authentication behavior with synthetic fixtures first, then the approved live canonical credential privately. No secret may enter screenshots/logs/receipts. Merge/deploy only the coordinated verified candidate through existing host processes, then verify live HTML and each changed JS asset. Until then report local evidence only.

## Validation and limits of this checkpoint

- **6 audit regression tests passed**, zero failures/errors/skips. They cover value/prompt redaction, constant and unresolved keys, conflicting constant assignments, asset URL sanitization, corporate-versus-admin property storage, and complete admin inventory with missing assets.
- Initial five tests passed, then the first inventory run stopped at missing `docs/assets/css/global.css`. The scanner was corrected to retain explicit missing-reference evidence; one additional regression was added and all six passed. No application fix was made for that unrelated asset.
- The missing CSS is referenced by `docs/admin/production.html:12` and `docs/admin/scheduling-landscape.html:8`. Existing CSS fallback/layout behavior was not tested; keep this as a known unrelated finding for a separately scoped repair.
- Final expected inventory: 34 admin files, 19 HTML pages, 5 referenced asset paths, 1 missing referenced asset, 7 endpoint files; 46 total records; no unresolved storage expressions in this snapshot.
- Both Python files passed AST/in-memory syntax validation; JSON count/coverage and deterministic readback checks passed for all 34 admin files and all 19 report pages. No application auth scenario, browser cross-page navigation, provider configuration, real payment, CI or deployment test has been performed in this audit tranche.
- Persistent evidence for consolidated admin auth: not yet BUILT. Existing source behavior is inventoried only; no new end-to-end proof/observer/healthy claim. Expected proof is one private admin unlock serving all owner pages, consistent lock/expiry, failed unauthorized requests and unchanged corporate sessions. Last successful proof is unknown.

Exact intended checkpoint files: `scripts/audit_admin_auth_contract.py`, `tests/test_audit_admin_auth_contract.py`, `data/audit/admin_auth_inventory_issue215_r1.json`, this report, then repository-root `Codex_Reply_AdminAuthUnification_R1.md` in a separate receipt commit referencing the audit commit. No live application or configuration file changes. Original dirty work, caches and operational data remain outside this branch.
