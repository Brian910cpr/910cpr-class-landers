# Seed Simulation vs Live Snapshot Codepath

## Path A: Seed Simulation

1. `scripts/build_seed_simulation_report.py::run` calls `build_candidate_report_payload`.
2. `scripts/build_candidate_slot_report.py::build_inverse_blocking_candidates` loads `data/config/candidate_horizons.json`.
3. Brian's report-only horizon starts `2026-08-01` and uses `lookahead_days=45`.
4. `data/config/seed_selection_rules.json` then thins the first `window_days=14` days into selected proposals.
5. Resulting seed simulation range: 2026-08-03 through 2026-09-14.

## Path B: Active Live Snapshot

1. `scripts/export_calendar_snapshots.py::export_calendar_snapshots` fetches ICS data and sets a 60-day export window.
2. `scripts/export_calendar_snapshots.py::parse_ics_events` keeps VEVENT records whose master `DTSTART` falls inside the window.
3. `parse_ics_events` expands `RRULE`, `RDATE`, and `EXDATE` into concrete occurrences inside the export window.
4. `data/runtime/calendar_snapshots/brian_do_not_schedule.json` now contains runtime rows through 2026-08-28.
5. `scripts/build_live_availability_snapshot.py::load_runtime_snapshots` prefers `data/runtime/calendar_snapshots/*.json`.
6. `scripts/build_live_availability_snapshot.py::build_snapshot` and `expand_inverse_availability` can only subtract/expand from the event rows available in that runtime snapshot.
7. Resulting live snapshot range: 2026-06-29 through 2026-08-28.

## First Divergence

`scripts/export_calendar_snapshots.py::parse_ics_events` was the first function where the live path stopped matching the seed-simulation path. After the RRULE expansion fix, the live path materializes recurrence instances before the live snapshot is built.
