# Draft PR and validation-only scope

Owner approval on October 11 at 23:27 UTC authorizes pushing this preserved branch as a draft PR and running a validation-only check with existing CI access. It does not authorize merge, production deployment, live booking changes, customer sends, or credential changes.

Remote main inspected: `bd3db41cbc9e5cf03883d86605a0e8be7f6c3a54`. Scheduling source/configuration has no changes relative to the implementation base `e663209d1e3db7d582079008250da622a2a01856`. No duplicate PR existed for this branch at inspection.

The earlier local production-refresh staging proposal is removed from the net PR diff. `.github/workflows/refresh-public-site.yml` and `.github/workflows/refresh-admin-availability.yml` remain unchanged. Commitment history is stored under ignored `data/runtime/layered_verified_commitments.json`, not publicly committed state. Production continuity of private history remains a separate release integration decision; a fresh runner cannot invent earlier positive demand. Unknown current intervals remain conservatively occupied.

A regression additionally covers canonical zero on the real iCal mirror shape, where course ID is nested rather than present at the row's top level. Exact canonical identity clears that class inventory mirror while preserving independently blocked calendar commitments.

The new `.github/workflows/v2-validation-only.yml` runs on pushes to this specific review branch. It checks out the exact event SHA with persisted credentials disabled and `contents: read` permission. No default-branch merge or production workflow dispatch is required. Only the read-only source step receives the existing HOT_SYNC_ADMIN_KEY through supported repository-secret injection. No secret is retrieved through the CLI, printed, configured, or serialized.

`scripts/validate_v2_real_sources.py` refreshes Enrollware timing, public configured calendars, and authenticated canonical demand. Inputs and calculations remain in runner-local storage. Its pure future-schedule projection reuses the existing production helper functions without invoking class-page generators. It compares pinned current baseline scheduling code against the PR code using identical fresh inputs and a frozen comparison clock, checks occupied-interval retention, and probes actual calculated public windows and links in offline desktop/mobile Chrome.

Only `sanitized/summary.json` and `sanitized/report.md` are uploaded. Raw inputs, counts per private session, source identities, calendar event bodies, exception bodies, credentials, and raw feeds are excluded. Conflict reason suffixes containing source IDs are removed. Public-offer date/time/course/type tuples may be reported because they are calculated public inventory, rather than private attendee source data.

Local checks before push: focused scheduling suite 103 executions passed; validation-driver privacy/occupancy checks 3 passed; Python compile and whitespace checks passed. The prior five browser/pipeline and 51 Node checks passed. CI source validation and the final real before/after are pending at this receipt's creation.
