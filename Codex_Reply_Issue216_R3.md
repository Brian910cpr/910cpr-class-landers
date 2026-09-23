# Codex reply — Issue 216, round 3

- Timestamp: 2026-09-23 13:07 UTC
- Branch: `codex/now-dashboard-repair`
- Substantive commit: `1c8e12ec257c1cd37c12614915f715970045c7ff`
- Pull request: https://github.com/Brian910cpr/910cpr-class-landers/pull/277
- Work-item state: PR_OPEN
- Persistent-system evidence: BUILT; canonical database snapshot read separately, but authenticated owner browser and deployed endpoint round trip remain unproven.

## Findings

`now.html` carried a hidden required admin-key form and forced the access dialog invisible. `now.js` called `LanderWareAdminAuth.set(key)`, but the current owner-session helper rejects a legacy key and redirects signed-out visitors to the private access link. The page also promoted generic decision cards and blocked issue titles as Brian actions and gave an unconnected cash source prominent space.

## Work

Replaced the obsolete unlock flow with the current owner-session request. Rebuilt the screen around canonical counts and drill-downs, short current work and handoff file summaries, source freshness, and a collapsed unverified finance panel. The private endpoint now reads five known repository report files and returns only freshness metadata. Old green files remain stale. Only fully translated owner actions and verified finance prompts appear in Brian's action list.

Changed: `docs/admin/now.html`, `docs/admin/now.css`, `docs/admin/now.js`, `supabase/functions/owner-dashboard/core.mjs`, `supabase/functions/owner-dashboard/index.ts`, `ops/owner-dashboard/README.md`, `tests/owner-dashboard/core.test.mjs`.

## Checks and evidence

- `node --check docs/admin/now.js`: pass.
- `node --test tests/owner-dashboard/core.test.mjs`: 3/3 pass (human action gating, stale report behavior, incomplete finance gate).
- Static DOM ID and asset checks: pass. `git diff --check`: pass.
- Production `owner_dashboard_snapshot()` SQL at 2026-09-23 13:03 UTC: 8 upcoming permanent records, 1 class with missing linked eCard evidence, 1 person in the eProduct queue. This proves the source read, not the browser path.
- Signed-out live URL redirects to `/admin/access.html`; no owner-session access link was available in the cloud browser. Localhost preview was blocked by the cloud browser, so authenticated layout/drill-down proof remains outstanding.

## Next action

Review/merge PR #277, deploy `owner-dashboard` from merged source with `verify_jwt=false` (the function performs custom owner authorization), verify anonymous 401 and an authenticated owner read, then inspect the live NOW page and changed assets. Finance is still unconnected and should remain unverified until a trusted source supplies complete obligations. An independent observer is not configured; do not call the monitor HEALTHY.

No owner action is needed for the code change. The private access link is needed only for the final authenticated browser proof.
