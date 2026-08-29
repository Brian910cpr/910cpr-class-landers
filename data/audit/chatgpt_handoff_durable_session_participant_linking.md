# LanderWare Durable Session / Participant Linking Handoff

## Goal

Make ES.910CPR and LanderWare Operations use one durable Session Workspace and one canonical participant count derived from durable registrations, while preserving the distinction between a real empty Enrollware roster and unavailable roster information.

## Primary audit findings

1. `scripts/publish_admin_schedule.py` coerced every missing participant count to `0` in both `normalize_session` and `normalize_hot_sync`.
2. `docs/admin/dashboard.html` independently counted embedded participant arrays and then fell back to schedule aggregate fields with `0` as the default.
3. `docs/admin/schedule-reader.html` (the source served at `https://es.910cpr.com`) displayed `registered_count` but linked only to registration, not to participant operations.
4. The live `docs/data/admin_schedule.json` contract was schema `1.1`, contained 44 Enrollware iCal sessions, and every row displayed zero. The feed did not include evidence proving those were empty rosters.
5. The canonical durable relationships already exist in Supabase: `landerware_sessions`, `landerware_registrations`, `landerware_rosters`, `landerware_roster_memberships`, people, requirements, credentials, documents, and activity events.
6. Production durable-registration inspection is blocked: the Supabase CLI has no `SUPABASE_ACCESS_TOKEN`, the dashboard browser session is signed out, and the new Edge Function is therefore not deployed. It is not yet possible to state which native `Participants (0)` sessions already have registrations in production.

## Implemented source changes

- `scripts/publish_admin_schedule.py`
  - Preserves unavailable count as `null`.
  - Adds `participant_count_available`, `participant_count_source`, and `roster_available`.
  - Emits zero only when schedule/student-report evidence establishes a true zero.
- `docs/assets/session-workspace.js`
  - Owns canonical workspace URL generation and participant display semantics.
  - Counts durable registrations while excluding canceled, removed, superseded, replacing, and deleted states.
  - Hydrates ES and Dashboard from the durable summary API; no ES/Dashboard counter is maintained.
- `docs/admin/schedule-reader.html`
  - Renders `Participants (N)` or `Participants (—)` as a Session Workspace link.
- `docs/admin/dashboard.html`
  - Uses the same helper and same absolute Session Workspace route in lanes, timelines, and class context.
- `docs/admin/session-workspace.html`
  - Canonical noindex workspace route with metadata, roster/count, attendance/registration, cards, requirements, paperwork, and history surfaces.
  - PII/card detail is shown only when the existing `maximPortalSession` validates.
- `supabase/functions/session-workspace/index.ts`
  - Public sanitized summaries contain no participant PII.
  - Authorized detail uses the existing portal session table.
  - Canonical counts derive from `landerware_registrations`, excluding non-participant lifecycle states.

## Validation

- `node --check docs/assets/session-workspace.js` — passed.
- `deno check supabase/functions/session-workspace/index.ts` — passed.
- `node --test tests/session_workspace.test.cjs tests/dashboard_schedule.test.cjs tests/dashboard_ops.test.cjs` — 28 tests passed.
- `python -m unittest tests.test_publish_admin_schedule tests.test_import_enrollware_student_report` — 4 tests passed.
- Required regression cases covered: native nonzero, native zero, Enrollware aggregate/no roster, imported unknown, canceled, walk-in, and Past/Future links.

## Deployment status and exact blocker

- Persisted locally: yes.
- Changed in review worktree: yes.
- Validated locally: yes.
- Supabase Edge Function deployed: **no**. `npx supabase projects list` returned `LegacyPlatformAuthRequiredError: Access token not provided` and the browser reached the Supabase sign-in page.
- Static GitHub Pages deployed: **no**. Static deployment was intentionally withheld because the required canonical endpoint currently returns HTTP 404.
- Live real-participant confirmation: **blocked** until the Edge Function is deployed and production durable registrations can be queried.

## Next concrete steps

1. Authenticate Supabase (`npx supabase login`) for project `wktwgcnwdvbebcobgyey`.
2. Deploy `session-workspace`: `npx supabase functions deploy session-workspace --project-ref wktwgcnwdvbebcobgyey`.
3. Call `/functions/v1/session-workspace/summaries` with known native session locators and audit all native rows currently rendered as zero.
4. Commit/push/merge the static/source changes and wait for GitHub Pages.
5. Verify one known nonzero native session on both `https://es.910cpr.com` and `https://www.910cpr.com/admin/dashboard.html`; assert identical label text and identical absolute Workspace href, then open the Workspace and confirm authorized roster details.

## Open questions / assumptions

- Existing registration states observed in migrations include `active`, `completed`, `replacing`, and `superseded`; only the latter two are excluded. `canceled/cancelled`, `removed`, and `deleted` are also excluded. Walk-ins remain included unless explicitly moved into an excluded state.
- Enrollware aggregate counts remain displayable without exposing roster PII. They are explicitly marked `roster_available: false`.
- No manual participant count was written anywhere.
