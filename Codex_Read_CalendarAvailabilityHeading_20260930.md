# Calendar availability heading

- **Assignment:** Add a primary heading above the shared timing and corporate-code pills.
- **Timestamp:** 2026-09-30, America/New_York.
- **Branch:** `codex/calendar-availability-heading-20260930`.
- **Implementation commit:** `98925de1ed3fed701febb3da68b104cfe2c05f5b`.
- **State:** VERIFIED locally; not pushed, merged, deployed, or live-verified.
- **Evidence state:** BUILT and locally verified.

## Work performed

Added the semantic level-two heading **“When are YOU available?”** above the two calendar search-control pills. Its type size and spacing match the selector’s other primary decision headings, including “Choose your class” and “Calendar.” The reusable component carries this heading to all course-family selector pages.

The heading change does not alter timing filters, Smart Filter parsing, Billing Code suggestions, course-family prefiltering, availability, or registration links.

## Changed files

- `docs/assets/calendar-time-filters.js`
- `docs/assets/calendar-time-filters.css`
- `scripts/build_bls_block_schedule_pilot.py`
- Selector pages: `docs/ACLS.html`, `docs/BLS.html`, `docs/HEARTSAVER.html`, `docs/PALS.html`, `docs/acls.html`, `docs/arc.html`, `docs/bls.html`, `docs/courses/uscg-first-aid-cpr-aed.html`, `docs/family-cpr.html`, `docs/heartsaver.html`, `docs/hsi.html`, `docs/pals.html`, and `docs/uscg-elementary-first-aid-cpr.html`.
- `tests/test_calendar_time_filters_browser.py`
- `tests/test_selector_mobile_progression.py`

## Validation

- `python -B -m unittest tests.test_calendar_time_filters_browser` — passed, 3 tests across BLS and ACLS; now asserts the exact heading.
- `node --test tests/resolved_selector_availability.test.mjs` — passed, 25 tests.
- Targeted selector-progression checks — passed, 2 tests.
- `git diff --check` — passed.

## Preserved unrelated work

Unstaged `docs/Earl/index.html` and `docs/Jackson/index.html` changes pre-existed and were not staged or modified.

## Recommended next action

Push, merge, and verify the production BLS and ACLS pages load asset version `20260930.1` with the new heading. No user or account action is required for this change.
