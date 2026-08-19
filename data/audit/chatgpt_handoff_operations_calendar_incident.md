# Operations calendar incident handoff

## Root cause

Production `docs/admin/dashboard.html` bound `onclick` handlers to legacy `prevMonth` and `nextMonth` elements that no longer existed. Chrome raised:

`Uncaught TypeError: Cannot set properties of null (setting 'onclick')`

That synchronous exception occurred before `clearRecord(); load();`, so `/data/admin_schedule.json` was never fetched and the calendar never rendered. The failure became visible after the HOT_SYNC/admin changes because those changes shared the same startup script, but HOT_SYNC authentication was not the cause. Read-only schedule loading remains independent of the admin key; protected HOT_SYNC writes still require `X-Hot-Sync-Admin-Key`.

## Production evidence before repair

- `https://www.910cpr.com/data/admin_schedule.json` returned HTTP 200, JSON MIME type, and 23 sessions.
- The production JSON was semantically identical to repository `main`.
- The production dashboard HTML was identical to repository `main` after line-ending normalization.
- Headless Chrome rendered no `data-day` calendar elements and logged the uncaught line-112 `onclick` error.
- Authoritative August data contained 4 sessions on August 19 and 2 on August 20, including MedNorth.

## Changed files

- `docs/admin/dashboard.html`
- `docs/admin/schedule-model.js`
- `tests/dashboard_ops.test.cjs`
- `tests/dashboard_schedule.test.cjs`
- `tests/fixtures/admin_schedule_multiple_sessions.json`

## Repair behavior

- Removed the dead legacy month-button bindings; rendered month navigation retains its own scoped handlers.
- Added cache-busting to the administrative schedule read while retaining `cache: 'no-store'`.
- Added explicit loaded, normalized, current-month, rendered-session, and rendered-date reconciliation.
- Added a conspicuous `Schedule integrity error` alert for feed failures or count disagreement.
- Preserved distinct overlapping sessions, instructors, locations, registration counts, and URLs.
- Kept HOT_SYNC blocks merged into the same schedule dataset without requiring unlock for read-only visibility.
- Added a dark-mode treatment for the integrity alert.

## Validation

Command:

`node --test tests/dashboard_schedule.test.cjs tests/dashboard_ops.test.cjs`

Result: 17 tests passed, 0 failed.

Chrome smoke result against local tested files and current `docs/data/admin_schedule.json`:

- load status: `23 classes · 145 calendar events · 0 offered starts`
- August 19 calendar cell: `data-class-count="4"`
- August 19 detail: 4 scheduled classes and 4 distinct class cards
- MedNorth present
- integrity alert empty
- browser console errors: 0

## Open follow-up

The incident repair restores the existing month/day calendar. The larger tabbed instructor-lane scheduler should build on `ScheduleModel` as a separate follow-up after this production fix is live-verified, so it does not delay restoration or broaden the emergency deployment.
