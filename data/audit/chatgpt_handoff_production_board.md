# ChatGPT Review Handoff: LanderWare Production Board

## Scope and status

- Branch: `codex/landerware-production-board`
- Status: persisted locally, rendered locally, not deployed
- Production merge intentionally not performed pending Brian's visual review.
- Pre-existing generated/debug/cache changes remain unstaged and are unrelated to this branch's commit.

## Primary implementation audit

The implementation adds a compact four-lane production board at `docs/admin/production.html`, with Doing Now, Next Up, Needs Decision, and Parked lanes. Cards rank by `value_score / work_score` by default, retain an independent Brian override and manual rank, support drag/drop and explicit lane buttons, filters, search, alternate sorts, a detail drawer, timestamped thoughts, flags, and a context-copying `Work with ChatGPT` hook.

Persistence is Supabase/Postgres, not localStorage. The migration creates `production_board_cards`, `production_board_thoughts`, and `production_board_activity`; enables RLS; revokes anon/authenticated access; and seeds 24 requested items, including the August 10 BLS selector matrix review item. Browser requests go only through the `production-board` Edge Function using its server-side Supabase secret.

Authentication literally reuses the Maxim gate: the board sends the temporary code to the existing `maxim-portal/login` endpoint, retains its eight-hour `maximPortalSession` token in sessionStorage, and the board Edge Function validates that token against the existing `maxim_portal_sessions` table. No new code, credential, or login table was introduced.

LanderWare Operations now has Operations Overview, Schedule, Sync Health, and Production Board tab links. Its Production Board panel shows up to six active/high-priority cards when the shared Maxim session is unlocked, plus a link to the full board. A compact internal index is installed on the admin pages and includes all routes requested by Brian.

## Exact implementation files

- `docs/admin/production.html`
- `docs/admin/production.css`
- `docs/admin/production.js`
- `docs/admin/production-summary.js`
- `docs/admin/admin-nav.js`
- `docs/admin/admin-nav.css`
- `docs/admin/dashboard.html`
- `docs/admin/financial.html`
- `docs/admin/payments.html`
- `docs/admin/refresh-availability.html`
- `supabase/functions/production-board/index.ts`
- `supabase/migrations/20260812161043_production_board.sql`
- `tests/test_production_board.py`
- `data/audit/chatgpt_handoff_production_board.md`

## Validation evidence

`python -m scripts.audit_global_page_requirements --root docs/admin`

```text
GLOBAL PAGE REQUIREMENTS PASSED
Eligible pages scanned: 5
Documented exclusions: 1
Violations: 0
```

`python -m unittest tests.test_production_board tests.test_global_page_requirements -v`

```text
Ran 10 tests in 0.066s
OK
```

`node --check` passed for `production.js`, `production-summary.js`, and `admin-nav.js`.

`npx --yes deno check supabase/functions/production-board/index.ts`

```text
Check supabase/functions/production-board/index.ts
```

Rendered local browser checks confirmed the access gate, internal index, Production Board header/filter layout, and the Operations summary panel.

## Not validated / deployment blockers

`npx --yes supabase@latest migration list --local` could not connect because the local Supabase Postgres service is not running at `127.0.0.1:54322`. The migration therefore has not been executed against a database in this task. Per Brian's instruction, neither the migration nor Edge Function nor static site has been deployed. Until those two backend artifacts are deployed, the local UI can render and authenticate against Maxim, but board data cannot load from production.

## Review priorities

1. Confirm the initial 24 card scores and lane placement.
2. Review whether reusing the Maxim access code for every internal admin user is the desired interim policy.
3. Review the public-site origin CORS posture; data remains token-protected, but a narrower origin may be preferred later.
4. After approval: apply the migration, deploy `production-board`, push/merge the static files, then verify live HTML and API CRUD behavior.
