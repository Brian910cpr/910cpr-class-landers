# Forward Seeding Limiter Trace

Status: read-only trace. No deploy was performed.

## Plain-English Answer

The live snapshot stops at July 4 because scripts/export_calendar_snapshots.py::parse_ics_events records RRULE text but does not expand recurring VEVENT instances; the runtime Brian snapshot requested a 60-day window through 2026-08-18, but only explicit VEVENT master DTSTART rows through 2026-07-04 were exported, and scripts/build_live_availability_snapshot.py then built availability only from those exported runtime events.

## Exact Limiter

- File: `scripts/export_calendar_snapshots.py`
- Function: `parse_ics_events` starting near line 195
- Constant: `EXPORT_DAYS = 60` near line 24
- Behavior: VEVENT is appended only when DTSTART is inside window; RRULE/RDATE/EXDATE are stored in recurrence but no future occurrences are materialized.

## Why July 4

- Runtime Brian snapshot declared range: 2026-06-19T17:21:21.208861-04:00 through 2026-08-18T17:21:21.208861-04:00 (60 days)
- Runtime event rows actually exported: 2026-06-19 through 2026-07-04
- Live availability snapshot built from runtime events: 2026-06-21 through 2026-07-04
- Dynamic offers built from live snapshot: 2026-06-21 through 2026-07-04

July 4 is the latest explicit exported runtime event, not the configured export horizon and not an appointmentDayId boundary.

## Seed Simulation Path

- Candidate horizon file: `data/config/candidate_horizons.json`
- `horizon_start_date`: `2026-08-01`
- `lookahead_days`: `45`
- seed selection `window_days`: `14`
- Seed simulation date range: 2026-08-03 through 2026-09-14
- August rows: 92

## Live Snapshot Path

- Runtime export script: `scripts/export_calendar_snapshots.py`
- Runtime parse function: `parse_ics_events`
- Runtime snapshot file: `data/runtime/calendar_snapshots/brian_do_not_schedule.json`
- Live snapshot script: `scripts/build_live_availability_snapshot.py`
- Live inverse horizon function: `inverse_expansion_horizon` near line 389
- `calendar_sources.json` `inverse_expansion_horizon_days`: `45`
- Live snapshot August rows: 0
- Dynamic August offers: 0

## Not The Limiter

- 14-day seed selection window
- appointmentDayId range
- Course Master
- public sellable maximum_days_out
- dynamic generation occupancy filters

See `horizon_config_candidates.csv` for all searched horizon/window candidates.
