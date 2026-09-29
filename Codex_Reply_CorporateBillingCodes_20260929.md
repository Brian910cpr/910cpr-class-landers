# Corporate Billing Code calendar picker

- **Assignment:** Add a compact corporate Billing Code picker to the reusable course-family calendar.
- **Timestamp:** 2026-09-29, America/New_York.
- **Branch:** `codex/corporate-billing-code-autocomplete-20260929`.
- **Implementation commit:** `3cbe9aef809de880944862f06000d0e472719249`.
- **State:** VERIFIED locally; not pushed, merged, deployed, or live-verified.
- **Evidence state:** BUILT and locally verified. This is a static browser feature, not a monitored persistent process.

## Finding and scope decision

The supplied workbook distinguishes named corporate accounts from general, promotional, expired, invoice-only, and other broadly distributed codes. Only the named corporate accounts are included in the browser-loaded suggestion directory: AssistedCare, Breakthrough Autism, Maxim Homecare, Maxim Behavioral Health, and Maxim Direct Support Professionals. General-purpose codes are intentionally absent.

The calendar hands registration to Enrollware. Its public registration material supports entering a promo/billing code during enrollment, but no documented safe query parameter was found for pre-filling it. The picker therefore confirms the selected company code and tells the registrant to enter it on the Enrollware registration page; it does not append an invented parameter or alter billing.

## Work performed

- Added an accessible compact `Billing Code` combobox to `docs/assets/calendar-time-filters.js`.
- Suggestions begin only after three characters, match company names, codes, and approved aliases, and only list named corporate accounts.
- Added restrained responsive styling in `docs/assets/calendar-time-filters.css`.
- Bumped shared calendar asset versions to `20260929.2` on all selector pages and in the authoritative renderer so browsers receive the matching assets.
- Added unit and real-calendar browser coverage for the threshold, Maxim suggestions, generic-code exclusion, BLS, ACLS, and compact mobile layout.

## Changed files

- `docs/assets/calendar-time-filters.js`
- `docs/assets/calendar-time-filters.css`
- `scripts/build_bls_block_schedule_pilot.py`
- Selector HTML assets: `docs/ACLS.html`, `docs/BLS.html`, `docs/HEARTSAVER.html`, `docs/PALS.html`, `docs/acls.html`, `docs/arc.html`, `docs/bls.html`, `docs/courses/uscg-first-aid-cpr-aed.html`, `docs/family-cpr.html`, `docs/heartsaver.html`, `docs/hsi.html`, `docs/pals.html`, and `docs/uscg-elementary-first-aid-cpr.html`.
- `tests/resolved_selector_availability.test.mjs`
- `tests/test_calendar_time_filters_browser.py`
- `tests/test_selector_mobile_progression.py`

## Validation

- `node --test tests/resolved_selector_availability.test.mjs` — passed, 25 tests.
- `python -B -m unittest tests.test_calendar_time_filters_browser` — passed, 3 tests. This served BLS and ACLS with real repository availability and exercised the billing picker plus mobile widths.
- `python -B -m unittest tests.test_selector_mobile_progression.SelectorMobileProgressionTests.test_timing_filters_share_one_path_and_preserve_course_context tests.test_selector_mobile_progression.SelectorMobileProgressionTests.test_authoritative_builder_inherits_timing_controls_without_page_specific_setup` — passed, 2 tests.
- `python -m py_compile scripts/build_bls_block_schedule_pilot.py` and `git diff --check` — passed.

## Known unrelated failures and preserved work

- `tests.test_block_start_time_selector` cannot complete in this worktree because the tracked fixture dependency `data/sessions_current.json` is absent. It reports 18 errors and 16 failures rooted in that missing required input; no billing-picker code is executed before the failure.
- The broader `tests.test_selector_mobile_progression` has pre-existing progression assertions absent from current generated pages; its two timing-control assertions pass.
- Unstaged `docs/Earl/index.html` and `docs/Jackson/index.html` changes pre-existed in the worktree and were not staged or modified by this assignment.

## Recommended next action

Push this branch, open a focused PR, merge it, and verify the deployed BLS and ACLS pages load `calendar-time-filters.js?v=20260929.2` and show only company-account suggestions after three characters. No user or account action is needed for local validation; a deployment review is still required.
