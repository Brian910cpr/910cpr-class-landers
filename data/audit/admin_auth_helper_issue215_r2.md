# Issue 215 R2: shared credential helper ready for coordinated adoption

State: **IN_PROGRESS**; helper BUILT and locally tested. No page migrated or production authentication changed in this checkpoint.

This narrow prerequisite continues the R1 inventory during blocked ShiftCommander #214. Base is `c2ffef4a608007a54fd135d2f6efb1d7bc2dc2f8`, including #216's deployed `now.html` monitor and updated Production Board. R1's exact inventory is historical at `8808884a23e4da2ce055b4da6a9002a6ea17c39c`; it must be refreshed for the coordinated migration. In particular, current `docs/admin/production.js` has optional canonical headers alongside corporate credentials, and `docs/admin/now.js` adds another page-local implementation. Do not apply the original inventory blindly.

## Implementation contract

`docs/admin/admin-auth.js` installs one frozen `window.LanderAdminAuth` object. It has no automatic network requests, page mutation, login prompt, timer, credential constant or localStorage use. It exclusively reads/writes `sessionStorage.hotSyncAdminKey` and creates `X-Hot-Sync-Admin-Key`. Existing private values, corporate sessions, draft storage and UI preferences are outside this helper.

- `getKey()`, `setKey(value)`, `clearKey()` own credential storage. Set trims surrounding input as existing owner gates do and rejects empty/non-string/header-breaking values. Set means a key is present, not that a server accepted it. Server authorization remains mandatory.
- `subscribe(callback)` immediately supplies `{hasKey, revision, reason}` and returns unsubscribe. Events never contain the credential. On **every** event, subscribers must discard private data/DOM/dialogs and cancel page-local state before deciding whether to reload. Keep existing page wording. A failed/reentrant hook cannot stop other invalidation or deliver an obsolete unlock event after a newer lock.
- `createClient({endpoints: [...]})` requires explicit trusted API origin/path prefixes. A whole origin is refused. Path boundary checks reject adjacent paths, encoded path separators, URL credentials and fragments. HTTPS is required except same-origin HTTP for controlled local development. Use only verified owner endpoints; declaring a route here does not make its server authorization correct.
- `client.json(url, options)` sends the canonical header and preserves application method/body/content-type. It forces no-store, omitted ambient cookies, no-referrer and redirect error. Caller-supplied corporate session/bearer headers are refused. Both GET/POST 401 and 403 clear the current shared key; network errors/503 retain it. An older denial cannot clear a replacement key, including identical text re-entered after lock.
- `json` returns `{data, isCurrent, commit(render)}`. Use `result.commit(data => render(data))` **synchronously** for private UI updates, especially after another await. Do not retain and later render `data` without checking the current revision. This guard suppresses responses after lock, replacement, storage change, or back/forward restoration. It cannot retract a mutation that the server already accepted; a lock is not transaction cancellation or secret rotation.
- `client.prepare(url, headers)` exposes a guarded ticket for transitional low-level callers: `url`, canonical `Headers`, `signal`, `isCurrent`, `assertCurrent`, `handleStatus`, `finish`. Always finish it in a finally block. This only prepares the initial request; it cannot control another transport's redirects or response handling. Prefer `client.json`/fetch migration for existing XHR uploads, since browser XHR does not expose fetch's redirect-error control. The tests exercise tickets, not actual XHR/browser redirect behavior.
- Storage failures lock this document without inventing an in-memory credential fallback. A failed remove explicitly throws `STORAGE_UNAVAILABLE` because persisted logout across navigation cannot be promised. A successful explicit set can recover once storage is available. Back/forward restoration invalidates prior results even if the same credential text was restored.

Example for an already canonical, reviewed endpoint (illustrative adoption only):

```javascript
const auth = window.LanderAdminAuth;
const client = auth.createClient({endpoints: ['https://schedule.910cpr.com/admin']});
auth.subscribe(state => {
  clearPrivateView();
  showExistingGate(!state.hasKey);
  if (state.hasKey) load().catch(showExistingError);
});
async function load() {
  const result = await client.json('https://schedule.910cpr.com/admin/hot-sync');
  result.commit(bundle => renderExistingView(bundle));
}
```

The helper is not a security boundary against arbitrary script execution on the same origin; all sessionStorage-based admin pages already share that trust. Static shells/feed exposure and endpoint authorization must be evaluated separately. Do not describe the presence of this script as private-page protection.

## Validation

```powershell
node --check docs/admin/admin-auth.js
node --check tests/admin_auth.test.mjs
node --test tests/admin_auth.test.mjs
git diff --check
```

Final result: **26 tests passed**, zero failures/cancellations/skips. The first 23-case suite passed; review then added three cases and strengthened encoded-path rejection, reentrant notifications and delayed storage-event invalidation. Both JavaScript syntax checks passed. All credentials and responses in fixtures are synthetic. No network/provider/account/production data access occurs in tests.

Evidence covers shared storage across two simulated page contexts; preservation of corporate/draft values; nonsecret lock hooks; invalid input; locked request rejection; canonical header and no-redirect/no-cache/cookie rules; origin/path containment; no mixed authentication; GET/POST 401/403; late denial and late success races; lock during JSON decoding; guarded render after lock; back/forward restoration; low-level ticket invalidation; external storage events; network/503 retention; cancellation; read/write/remove/getter storage failures; duplicate script loads; and reentrant lock hooks.

These are Node VM/Fetch API tests, not real browser navigation, backend authorization, GitHub CI, staging or production proof. No unrelated application suite was rerun because existing application/backend files are unchanged. No generator or dependency installation was needed. Only this report, the helper and its test are substantive changes; a unique root receipt follows in a separate commit.

## Remaining implementation and precise gates

1. Refresh the R1 inventory against current main, include `now.html`/owner-dashboard, and coordinate all live admin clients and backend scopes. Preserve #216 dashboard functionality and explicitly excluded corporate/NHCSO surfaces.
2. Migrate every true owner page to the helper, including fetch/inline/detail/summary/upload paths and lock clearing of private UI. Version every added/changed script URL. Avoid partial production cutover while corporate-only backend routes still reject the canonical contract.
3. Complete canonical endpoint authorization/CORS and remove owner-route corporate fallbacks while preserving intentional corporate/public/redacted consumers. Reuse the protected HOT_SYNC authority; never substitute another secret or treat a client gate as backend auth.
4. Prove real same-tab unlock/navigation/lock/back-forward behavior and server denials, rendering and business flows with controlled fixtures, then approved live credentials privately. Account parity in #140 is still unresolved: its 2026-09-13T17:25:22Z owner-update verification records two rerun attempts failing protected HTTP 401. No service secret, permission or deployed configuration was changed here, and no unchanged failing request was retried.
5. Merge/deploy only the coordinated candidate after required review/validation; verify live HTML and each changed asset. Keep #215 open until full acceptance, not just this prerequisite, is proven.

There is no new owner decision blocking local coordinated implementation. Production account parity and access are external verification gates. This checkpoint was intentionally limited to an independent reusable prerequisite while #214 remains blocked; it does not claim that all admin pages now share authentication.

Persistent-system proof: helper BUILT. Real successful admin unlock -> cross-page reads -> shared lock -> denied requests -> preserved corporate sessions has no new end-to-end timestamp. Expected checks run on migration/change and after deployment. Late private rendering, repeated prompts, stale accepted credentials or cross-surface authorization are failure conditions. No independent observer/heartbeat or healthy-service claim is established by this module.
