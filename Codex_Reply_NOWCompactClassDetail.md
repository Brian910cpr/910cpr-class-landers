# NOW compact class detail

- Assignment: Make the NOW upcoming class panel useful without sending a simple roster lookup into the oversized month calendar.
- Recorded: 2026-09-23 19:47 UTC
- Branch: `fix/now-compact-class-detail`
- Implementation commit: `ca9664c48fc183af1f8bc6face727fcd4b32280b`
- Work-item state at receipt: `PR_OPEN`, PR #280.

## Finding and work

The owner snapshot supplied eight upcoming records, but NOW displayed only five. Each row linked directly to the top of the large All Classes calendar, so the number had too little context and the click overshot the requested answer.

NOW now shows every returned upcoming record. Selecting one reveals a compact inline class summary and names/statuses from the canonical session workspace. The roster is read only when selected, using the existing authenticated endpoint. An explicit full-record link remains. A deep link into All Classes scrolls to the selected class detail.

Changed: `docs/admin/now.html`, `docs/admin/now.js`, `docs/admin/now-class-focus.css`, `docs/admin/all-classes.html`, `docs/admin/all-classes.js`.

## Proof and limits

- `node --check` passed for both modified JavaScript files; `git diff --check` passed.
- A local Playwright interaction test was prepared for count, selection, roster, empty roster, close, and sign-out clearing, but could not run because Chromium is absent from this workspace. No UI pass is claimed.
- Deployment and owner-authenticated live verification were pending when this receipt was written. The real roster read and deep-link landing must be checked on the deployed page.
- Persistent-system evidence level: `BUILT`. The existing owner dashboard updates each minute, reports last successful read, and marks stale data. This UI change adds no background process or new monitor. There is no last successful end-to-end proof yet for this new interaction.
- Failure condition: a selected class remains in loading/error state or opens the wrong full record; the panel shows a roster read error. The owner can use the full-record link. A developer should inspect the canonical session endpoint and auth on failure.
- Known unrelated failures: none observed in the touched paths. No claims about other dashboard sections or the group-training incident.

Next action: merge PR #280, wait for Pages, then verify the owner-authenticated selection and full-record landing in production. No user or account-level action is required unless owner authentication is unavailable to the verifier.
