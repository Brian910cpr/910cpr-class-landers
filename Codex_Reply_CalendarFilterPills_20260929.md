# Calendar search-control pills

- **Assignment:** Group the reusable calendar controls into a prominent timing/search pill and a separate corporate-code pill; assess the next multi-student checkout step.
- **Timestamp:** 2026-09-29, America/New_York.
- **Branch:** `codex/calendar-filter-pills-20260929`.
- **Implementation commit:** `ba2ca244bca71575aa7c43ac3a1c6539235155c0`.
- **State:** VERIFIED locally; not pushed, merged, deployed, or live-verified.
- **Evidence state:** BUILT and locally verified. This static UI component is not a monitored persistent process.

## Work performed

- Wrapped Time of Day and Smart Filter in one lightly emphasized, rounded scheduling-preferences pill.
- Wrapped Billing Code in a separate rounded corporate-code pill.
- Kept the controls side by side on desktop and stacked them on narrow screens.
- Preserved the original shared filter and code-picker behavior; no scheduling data, family prefilter, or checkout behavior changed.
- Bumped the shared calendar asset version to `20260929.3` across every selector page and the authoritative renderer.

## Checkout recommendation

The next checkout feature should be **one session, multiple students, one order**. The existing native registration page already models that flow and supports per-student add-ons. A single submission containing several different dates or sessions needs a later multi-session cart with independent capacity holds, prices, cancellation rules, and fulfillment records. It should not be coupled to this UI change.

## Changed files

- `docs/assets/calendar-time-filters.js`
- `docs/assets/calendar-time-filters.css`
- `scripts/build_bls_block_schedule_pilot.py`
- Selector pages: `docs/ACLS.html`, `docs/BLS.html`, `docs/HEARTSAVER.html`, `docs/PALS.html`, `docs/acls.html`, `docs/arc.html`, `docs/bls.html`, `docs/courses/uscg-first-aid-cpr-aed.html`, `docs/family-cpr.html`, `docs/heartsaver.html`, `docs/hsi.html`, `docs/pals.html`, and `docs/uscg-elementary-first-aid-cpr.html`.
- `tests/test_calendar_time_filters_browser.py`
- `tests/test_selector_mobile_progression.py`

## Validation

- `python -B -m unittest tests.test_calendar_time_filters_browser` — passed, 3 tests. This checks BLS and ACLS, all filters, Billing Code behavior, desktop side-by-side pills, and mobile stacking.
- `node --test tests/resolved_selector_availability.test.mjs` — passed, 25 tests.
- Targeted selector-progression checks — passed, 2 tests.
- `python -m py_compile scripts/build_bls_block_schedule_pilot.py` and `git diff --check` — passed.

## Preserved unrelated work

Unstaged `docs/Earl/index.html` and `docs/Jackson/index.html` changes pre-existed in the worktree and were not staged or modified by this assignment.

## Recommended next action

Push and merge this visual-only branch, verify the BLS and ACLS pages load version `20260929.3`, then begin a separate BLS native-registration cutover for multiple students attending the same selected session. No user or account action is required for this local validation.
