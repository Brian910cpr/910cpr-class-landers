# Issue 215 — remembered-owner Worker boundary implementation, R2

Timestamp: 2026-10-12T14:03:00-04:00
Branch: codex/issue215-worker-session-20261012
Substantive commit: fe19a34598c43ade4a3967fb43056e760cbff36d
State: IN_PROGRESS; production continuation BLOCKED at Finance Worker account discovery/access.
Evidence: BUILT and validated locally. Not deployed, not a complete authentication migration.

## Authority and preservation
Read full #215 body and comments, repository AGENTS.md and CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md before implementation. Execution acknowledgement: https://github.com/Brian910cpr/910cpr-class-landers/issues/215#issuecomment-6129709119 . The owner's private remembered-session directive governs; the withdrawn public-access directive was not revived. Third-party review comments are context, not authorization.

Original E:\GitHub\910cpr-class-landers and E:\GitHub\910cpr-issue215-20261012 dirty work preserved. Isolated worktree: E:\GitHub\910cpr-issue215-worker-session-20261012. Windows case collisions produce unrelated docs/Earl/index.html and docs/Jackson/index.html differences here; neither staged. No cleanup, reset, rebase, merge, generator, schedule/data edits, secrets or payment operations. One implementation stream, no additional workers. Queue scanned; existing fleet, scheduling, payments, Studio, dashboard and documents assignments retained, without competing implementations. PR #372 remains draft, unmodified, unmerged and undeployed. No ops/handoff/next_task.md used.

## Implementation and exact files
- worker/owner-session-auth.js: shared authorization for both Workers. Browser credential X-LanderWare-Owner-Session must match lw_s_ followed by 64 lowercase hex characters. Each request validates against the existing pinned https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/owner-access/session authority. GET, no-store, redirects rejected, five-second abort. Exactly HTTP 200 authorizes; 401/403 denies; all other status/network/timeout failures become 503. Response profile body is cancelled and never returned or logged. No validation caching, so revocation is rechecked per request. A presented owner session cannot fall back to an automation key, even if that key is correct. With no session header, HOT_SYNC_ADMIN_KEY / X-Hot-Sync-Admin-Key retains hashed constant-time comparison. Corporate credentials do not authorize.
- worker/admin-api.js: all existing protected /admin/* dispatches use the shared validator before data access: Hot Sync, class student routes, Session Bundles and inbox including downloads, uploads, metadata changes and deletion. Restricted first-party CORS now allows the owner-session header; origin checks remain before validation. Route business behavior and existing no-store responses preserved.
- worker/finance-worker.js: same shared validator before all /admin/finance/* dispatches; CORS adds only the owner-session header. Stripe/payment implementation untouched.
- tests/worker_owner_session.test.mjs: eight new tests cover pinned destination, minimal forwarded credentials, automation separation, malformed/corporate denial, revoked/expired authority rejection, no fallback, redirects/unexpected statuses/network outages, real five-second timeout, and Finance/Hot Sync/inbox/Session Bundle protected dispatch/CORS ordering. Authority calls are local mocks; no network or financial writes.
- tests/admin_api.test.mjs: existing data-URL entrypoint harness resolves new shared module.
- tests/finance_auth_boundary.test.mjs: updates the prior key-only boundary assertions for the coordinated backend implementation while retaining anonymous/corporate/malformed denial, independent automation and origin coverage.

No admin pages migrated in this checkpoint. docs/admin/admin-auth.js remains unchanged: schedule.910cpr.com still uses its legacy key lane, preserving remembered sessions on legacy service failure. Browser activation must follow verified backend deployment. This change reuses the existing remembered owner authority rather than introducing another identity store. It preserves revocation lifecycle and reduces native operations' credential fragmentation without adding Enrollware dependencies; no training-business workflow was replaced.

## Validation
Local command:
node --test tests/worker_owner_session.test.mjs tests/finance_auth_boundary.test.mjs tests/admin_auth.test.mjs tests/owner_access.test.mjs tests/owner_access_ui.test.mjs tests/admin_api.test.mjs
Exact summary: tests 48; suites 0; pass 48; fail 0; cancelled 0; skipped 0; todo 0.
Node syntax checks passed for worker/owner-session-auth.js, worker/admin-api.js, worker/finance-worker.js and tests/worker_owner_session.test.mjs. All test modules parsed/executed through the test run. git diff --cached --check passed.
python scripts/check_source_integrity.py: Source integrity OK: no tool-truncation markers detected.
python scripts/check_case_insensitive_paths.py: Validated 6 approved collision groups; no new collisions found.

GitHub CI for substantive commit fe19a34598c43ade4a3967fb43056e760cbff36d:
- Source integrity run 38288046853: completed / success.
- Cloudflare Pages preflight run 38288046811: completed / success.
These CI jobs are source/preflight checks, not the 48 local auth tests. No Worker-runtime packaging dry run, accepted-session browser proof, live protected read, or deployment claimed.

Current main bdb5e5b67bdb1a11ea9ba4311c99545fafc17510 was fetched; relevant Worker/helper/owner-access handler sources match the checkpoint base before edits. The branch inherits the previous #215 test/receipt checkpoint and is behind main's operational data updates. Main-to-branch tree differences include unrelated historical/generated data; DO NOT publish this branch tree wholesale or overwrite current operational data. For integration use the six-file substantive commit fe19a34598c43ade4a3967fb43056e760cbff36d on the current coordinated branch after review. No new PR created: #218 remains the historical unused-helper prerequisite, not safely repurposed for this backend continuation; #372 is explicitly excluded. Existing PRs were inspected and left intact rather than retargeted or force-pushed.

## Exact deployment blocker and next step
Wrangler 4.60.0 is installed at C:\Users\ten77\AppData\Roaming\npm\wrangler.ps1. One read-only wrangler whoami attempt failed:
A request to the Cloudflare API (/accounts) failed.
Cannot use the access token from location: 2600:1702:6bf0:940:790d:a634:1f7b:5f6 [code: 9109]
No auth retry, token output or rotation.

Available Cloudflare connector authenticates as the owner. GET /accounts succeeded (200), exposing one account. Explicit settings reads in that account:
- free-time-offer-worker: status 200, success true.
- landerware-financial-worker: Error: Cloudflare API error: 10007: This Worker does not exist on your account.
An earlier generic bindings lookup failed without details; explicit account reads above supersede that ambiguity. This is NOT a claim all Cloudflare access is missing. Finance target/account/route ownership must be located before deploying its replacement. Repository wrangler.finance.toml names landerware-financial-worker and schedule.910cpr.com/admin/finance/*, but that name is absent in the connected account. Do not create a second Worker or overwrite bindings to bypass this discrepancy.

Next action: locate the production Finance route's actual Worker/account using authorized account/zone administration; reconcile remote settings and preserve secrets/bindings, review/integrate the six-file commit, package and validate both Workers, deploy backend first and verify anonymous/corporate denials plus revocable accepted-owner reads. Only then switch the shared browser helper to send remembered sessions to those exact /admin routes, version affected references, and prove same-browser navigation, lock and back/forward clearing. No Brian secret copying is requested. Additional account access is required only if discovery confirms the route lives outside the currently connected account. Historical #140 is closed; its old parity failure is not reused as this blocker.

Other unfinished #215 scope: static private-feed/public-repository exposure, instructor identities/roles and current production monitoring. Source backend tests do not establish comprehensive privacy.

## Operational proof limits
Expected outcome: remembered private owner access across the real admin surfaces, with automation/corporate separation and immediate revocation/lock denial. Current successful proof is deterministic local boundary regression only. Historical September 14 API proof is in #215; no new production end-to-end timestamp established. Required failure condition: revoked/expired session denied; authority outage yields 503 without data access; stale browser responses cannot restore private state. Validator timeout implemented; production success cadence, observer, observer health, alerting and recovery automation remain unproven. Recovery: reconcile target account, deploy coordinated validated backend and prove browser workflow. Brian must not be routine monitoring. No MONITORED/HEALTHY claim.

Publication: six intended code/test files committed and pushed; this unique receipt committed separately and pushed. No merge or production deployment. Final receipt commit SHA and GitHub receipt-content verification reported on #215 and in chat.
