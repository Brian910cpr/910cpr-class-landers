# Schedule Integrity / Stop-the-Bleeding Handoff

## Goal

Prevent a durable LanderWare session from disappearing from `admin_schedule.json`, make durable registrations authoritative for participant counts, preserve unknown rather than coercing it to zero, and link ES/Dashboard to one Session Workspace.

## Root cause

`scripts/publish_admin_schedule.py` built the operational schedule only from `data/sessions_current.json` (Enrollware iCal) plus committed HOT_SYNC records. It never queried `landerware_sessions`. Missing participant counts were coerced to zero in the generator and again in Dashboard JavaScript. This explains both observed failures: Little Leaps could exist durably without appearing on September 19, and sessions with durable registrations could render `0`.

## Implemented changes

- `supabase/functions/session-workspace/index.ts`: sanitized `GET /projection` returns every upcoming non-cancelled durable session plus a count derived from active durable registrations. It exposes no participant PII.
- `scripts/fetch_durable_session_snapshot.py`: fetches that projection into private workflow runtime state.
- `scripts/publish_admin_schedule.py`: durable sessions are normalized first and are authoritative; Enrollware/HOT_SYNC can enrich or add unmatched evidence but cannot remove a durable record. Durable counts cannot be overwritten by the Enrollware student snapshot.
- `scripts/publish_admin_schedule.py`: command-line publishing now refuses to overwrite `admin_schedule.json` when the durable source is unavailable or when expected/projected durable counts disagree.
- `.github/workflows/refresh-admin-availability.yml`: fetches the durable projection before publishing.
- Existing shared Session Workspace source changes from commit `e73c19749` preserve unknown-vs-zero semantics and make ES/Dashboard use one participant resolver and one workspace route.

## Regression evidence

- Little Leaps fixture: 2026-09-19 11:00–14:00 is projected from a durable session with canonical count 5.
- Duplicate fixture: the same class from durable + Enrollware projects once, retains durable count, and is enriched with the external registration URL.
- Unknown Enrollware counts remain `null`; confirmed empty snapshots remain `0`.
- Canceled registrations are excluded; active/walk-in registrations are counted.

## Validation

- `python -m py_compile scripts/publish_admin_schedule.py scripts/fetch_durable_session_snapshot.py` — passed.
- `python -m unittest tests.test_publish_admin_schedule tests.test_import_enrollware_student_report tests.test_canonical_schedule_hot_sync` — 9 passed.
- `node --test tests/session_workspace.test.cjs tests/schedule_reader.test.cjs tests/dashboard_schedule.test.cjs tests/dashboard_ops.test.cjs` — relevant suites passed after restoring the sparse-checkout JSON fixture; 31 total tests across the two runs, all passed.
- `node --check docs/assets/session-workspace.js` — passed.
- `npx --yes deno check supabase/functions/session-workspace/index.ts` — passed.
- Live `GET /functions/v1/session-workspace/projection` — HTTP 404 because the function is not deployed.

## Deployment blocker

Local `SUPABASE_ACCESS_TOKEN` is absent. The GitHub repository Actions secrets list does not contain a Supabase deployment token. Therefore the required Edge Function cannot be deployed autonomously from this environment. Static deployment is intentionally withheld because the schedule workflow would correctly fail closed until the endpoint exists.

## Next concrete step

Authenticate Supabase for project `wktwgcnwdvbebcobgyey`, deploy `session-workspace`, verify `/projection` contains Little Leaps and the named registered sessions, then merge this branch. The scheduled workflow will publish `admin_schedule.json`; verify live ES and Dashboard counts and September 19 rendered output before declaring production complete.
