# Calendar time filters — review handoff

- Assignment: shared 910CPR calendar time preferences and Smart Filter.
- Timestamp: 2026-09-29, America/New_York.
- Branch: `codex/calendar-time-smart-filters-20260929`.
- Implementation commit: `3bbae84d7ad` (resolve full SHA with `git rev-parse 3bbae84d7ad`).
- Verified base main: `e0bb74e8225f29055412c2e9635b857b3821340a`.
- Origin: `https://github.com/Brian910cpr/910cpr-class-landers.git`.
- Work-item state at this receipt: `IN_PROGRESS` — implemented and validated locally; production release follows this receipt.
- Evidence level: `BUILT`, with local end-to-end browser proof; production is not claimed by this receipt.

## Work performed and evidence

Added the compact five-bucket checkbox row, local scheduling-language parser, interpretation/error message, and timing reset. Both paths use one constraint object after existing course/family filtering. No source schedules or availability are created or changed. No-results stay empty. Existing comparison, course deep links, and registration targets were tested.

Read the complete primary report at `data/audit/calendar_time_filters_20260929.md`. Structured counts and baseline-failure comparisons are at `data/audit/calendar_time_filters_20260929.json` (`counts`, `baselineTests`). These retain the exact boundaries, semantics, limitations, file list, source inventory counts, rejected-result counts, and test commands.

Most important source/test paths:

- `docs/assets/calendar-time-filters.js`
- `docs/assets/calendar-time-filters.css`
- `scripts/build_bls_block_schedule_pilot.py`
- `tests/resolved_selector_availability.test.mjs`
- `tests/test_selector_mobile_progression.py`
- `tests/test_calendar_time_filters_browser.py`

Changed rendered paths:

- `docs/bls.html`, `docs/acls.html`, `docs/pals.html`, `docs/heartsaver.html`
- `docs/arc.html`, `docs/hsi.html`, `docs/family-cpr.html`
- `docs/uscg-elementary-first-aid-cpr.html`, `docs/courses/uscg-first-aid-cpr-aed.html`
- Existing aliases `docs/BLS.html`, `docs/ACLS.html`, `docs/PALS.html`, `docs/HEARTSAVER.html`

Local verification: 24 JavaScript tests pass; 5 focused Python integration/clock tests pass; 3 browser tests pass, covering both BLS and ACLS, all required filters, reset, empty states, comparison, deep links, and 1280/390/320-pixel layouts. JavaScript/Python syntax and targeted diff checks pass. Browser tests use real resolved inventory and submit no registrations.

Known unrelated failures: nine legacy mobile string assertions fail identically on untouched main. They expect removed motion implementation strings. Exact cases are retained in the JSON evidence; the new integration tests pass.

Unrelated checkout differences in `docs/Earl/index.html` and `docs/Jackson/index.html` remain uncommitted. No intentional untracked files remain in the repository. Scratch scripts and screenshots stay outside it. Four tracked case aliases were explicitly preserved in the Git tree because Windows has a case-insensitive filesystem.

## Latest user addition: billing-code suggestions

User also requested a compact Billing Code field that suggests company names after three typed characters. They will provide a spreadsheet of potential codes and usage rules. This addition is awaiting that spreadsheet; no guessed mappings, company billing changes, or unverified checkout parameters were published.

An existing verified Maxim mapping is in `data/maxim_billing_rules.json`: Maxim/Homecare #031, MaximDSP/Direct Support #502, MaximBH/Behavioral #0852. The spreadsheet must be reviewed for the final directory, display labels, active status, course restrictions, and any usage/approval limits. AssistedCare was named by the user but its exact active code and rules have not yet been confirmed.

Next concrete action: review the uploaded spreadsheet, then add the shared autocomplete and verify the real registration handoff. Do not expose internal-only or inactive codes without resolving their intended public use. This is separate from calendar availability; a billing choice must never manufacture sessions or override family/time constraints.

The homepage employer/program requirements Smart Finder remains deferred and untouched.

## Release and recovery

Production host is GitHub Pages from `main:/docs`. Follow the scoped PR through deployment and verify `/bls.html`, `/acls.html`, and both versioned assets. At this receipt's creation the branch is committed locally; push/merge/deployment are not yet asserted.

Failure evidence is a missing asset/control, browser script error, timing result absent from the authoritative feed, or enrollment target mismatch. Recovery is a focused correction/revert of the shared assets and hooks; no schedule rebuild is needed. This is a one-time UI update, not a new persistent worker/monitor. Existing schedule-refresh health is outside this change.

User action required only for the billing addition: provide the spreadsheet. No account action is currently required for the calendar release.
