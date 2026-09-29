# Issue 305: zero-duration Enrollware occupancy

- Timestamp: 2026-09-29 (America/New_York)
- Branch: fix/zero-duration-occupancy
- Implementation commit: 6d15a96fe980bf532023e85ce0b016b0c31588a6
- State: PR_OPEN; BUILT and locally validated. Production proof pending.

## Findings and scope

At baseline 87e883fcd62b0d34139bafaaf63250b355467ffe, five of the six reported source events already had positive canonical occupied windows. Family & Friends (14495100) was absent from the legacy course map. The later identity resolver recognized its name but supplied no course ID, leaving zero duration in the public and admin schedule and allowing conflict checks to miss its occupied window.

Existing authoritative catalog identifies Family & Friends as 252737; its existing course consumption rule is 120 minutes. Catalog source_trace documents this as a conservative operational reservation, not a claim about exact teaching time. No course durations or scheduling policies were changed.

## Data path

Enrollware ICS -> build_sessions_current (legacy mapping, exact canonical catalog fallback, existing course consumption rule) -> sessions_current -> build_schedule_future / publish_admin_schedule -> schedule_future / admin_schedule / landerware.ics.

Both sessions_current and schedule_future feed generate_dynamic_offers.normalize_occupancy and block_start_time_selector.build_occupancy before conflicts and public candidate generation. Anchor promotion consumes schedule_future end_at. The independent Google availability snapshots establish availability windows; normalized class occupancy vetoes overlapping offers. The Enrollware-owned raw subscription feed is not rewritten by this repair.

## Changes

- Resolve unique exact catalog identities when the legacy map lacks the course. No fuzzy matching or invented IDs.
- Scope consumption-rule cache to its input metadata snapshot.
- Preserve legitimate positive source intervals; reuse existing rule for missing/nonpositive intervals.
- Fail import before writing output when a current/future class has unresolved occupied duration. Historical unresolved rows remain historical evidence.
- Carry inference provenance into public/admin projections and enumerate inferred windows in ingestion audit.
- Run regression gate in both refresh workflows and trigger refresh when course metadata/rules change, even if iCal hash is unchanged.

Files: .github/workflows/refresh-admin-availability.yml; .github/workflows/refresh-public-site.yml; scripts/build_sessions_current.py; scripts/build_schedule_future.py; scripts/publish_admin_schedule.py; tests/test_zero_duration_pipeline.py; tests/fixtures/enrollware_zero_duration_20260929.json; this receipt.

## Verification

72 targeted tests pass: zero_duration_pipeline, enrollware_ical_import, generate_dynamic_offers, anchor_state, apply_anchor_policy, publish_admin_schedule, canonical_schedule_hot_sync, build_live_availability_snapshot. git diff --check passes.

New regression uses all six real source IDs and titles: ingestion -> public/admin projection -> canonical iCal -> synthetic demand anchor promotion -> selector/dynamic occupancy -> conflict checks, including last-minute overlap and exact end adjacency. Synthetic demand exists only in tests; this repair does not invent registrations or promote real anchors without demand.

Offer-generation regression: 6 synthetic availability windows, 106 candidate starts before occupancy, 82 rejected for existing occupancy, 24 nonconflicting offers retained. These are fixture counts, not production totals.

Fresh live source read: 262 events; all 163 legitimate positive durations preserved exactly. 98 nonpositive intervals resolved with existing rules (including historical rows); one unresolved historical ARC row from August 10 remains historical. All 9 upcoming zero-duration events resolve, including the 6 requested.

| Session | Date | Occupied time (Eastern) | Minutes |
|---|---|---|---:|
|14288234|Sep 29|18:00–20:30|150|
|14400433|Sep 30|17:30–19:30|120|
|14495100|Oct 2|08:45–10:45|120|
|14382096|Oct 2|10:45–12:45|120|
|14501248|Oct 2|12:45–14:45|120|
|14186226|Oct 3|10:00–11:00|60|

Broader block_start_time_selector suite: 60 tests, 19 failures, 18 errors, identical test IDs on patched and unchanged baseline. Missing untracked sessions_current snapshot and stale generated artifact assertions are pre-existing; do not claim this suite is green.

## Production proof / recovery

Next: merge after CI, observe admin and public refresh, then fetch production schedule/admin/iCal and selector feeds; verify all six ends, positive durations, and no conflicting dynamic offers. Normal publisher output is expected to update schedule JSON, ICS, selector feeds, audit/status files and affected generated class pages; do not manually patch generated outputs.

Observer: refresh workflow regression gate plus existing publication validation and Actions failure status. Cadence: admin every 10 minutes, public half-hourly and source-code/metadata push. New unresolved current/future duration raises an actionable session-specific error before offers are built. A failed run must retain last published output. Observer heartbeat and broader monitoring health are not independently proven in this task.

Rollback: revert the implementation commit and republish with the existing workflows. No database migration, credentials, course-rule changes, or Enrollware writes. No user/account action currently required. Do not close the incident solely on local proof.
