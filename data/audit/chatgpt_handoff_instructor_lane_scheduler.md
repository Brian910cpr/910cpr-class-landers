# Instructor lane scheduler handoff

## Scope

This follow-up builds on the repaired authoritative schedule pipeline. It does not create separate calendars or alter schedule generation.

## Changed files

- `docs/admin/dashboard.html`
- `docs/admin/schedule-model.js`
- `tests/dashboard_schedule.test.cjs`

## Behavior

- Adds an `All schedules` catch-all tab plus dynamic instructor tabs from the shared normalized session array.
- Current production data produces Brian, Amy, Nicholas, and Unassigned views; additional instructors appear automatically.
- The catch-all day board groups cards into instructor lanes.
- Same-time sessions remain separate cards.
- Overlaps and same-location conflicts are annotated instead of merged or hidden.
- Location, registered count, and HOT_SYNC provenance remain visible on cards.
- The original complete day timeline remains below the lanes as a second truthful representation.
- Dark-mode lane and conflict states use dark surfaces and readable text.

## Validation

`node --test tests/dashboard_schedule.test.cjs tests/dashboard_ops.test.cjs`

Result: 19 passed, 0 failed.

Chrome smoke using current `docs/data/admin_schedule.json`:

- 6 tabs in markup/script result, including All schedules, Brian, Amy, Nicholas, and Unassigned
- August 19 retained four original timeline class cards
- Brian lane reported four August 19 classes
- Amy and Nicholas tabs present
- integrity alert empty
- console errors: 0

## Data rule

All tabs and lanes are filters/groupings over the same normalized `admin_schedule.json` plus committed HOT_SYNC block array. No instructor or location has an independently maintained calendar.
