# Forward Seeding Limiter Trace

Status: read-only trace. No deploy was performed.

## Plain-English Answer

The prior live snapshot stopped at July 4 because scripts/export_calendar_snapshots.py::parse_ics_events recorded RRULE text without expanding recurring VEVENT instances. That limiter is now fixed: runtime snapshots contain expanded recurring instances into August, live_availability_snapshot_preview.json contains August blocks, and dynamic_offers_preview.json contains August offers.

## Exact Limiter

- File: `scripts/export_calendar_snapshots.py`
- Function: `parse_ics_events` starting near line 347
- Constant: `EXPORT_DAYS = 60` near line 27
- Behavior: RRULE/RDATE/EXDATE occurrences are now materialized inside the export window before the live snapshot builder reads runtime events.

## Why July 4

- Runtime Brian snapshot declared range: 2026-06-29T15:37:34.470018-04:00 through 2026-08-28T15:37:34.470018-04:00 (60 days)
- Runtime event rows actually exported: 2026-06-29 through 2026-08-28
- Live availability snapshot built from runtime events: 2026-06-29 through 2026-08-28
- Dynamic offers built from live snapshot: 2026-06-29 through 2026-08-13

July 4 was the latest explicit exported runtime event before RRULE expansion. It is no longer the live snapshot stop date.

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
- Live snapshot August rows: 29
- Dynamic August offers: 20901

## Not The Limiter

- 14-day seed selection window
- appointmentDayId range
- Course Master
- public sellable maximum_days_out
- dynamic generation occupancy filters

See `horizon_config_candidates.csv` for all searched horizon/window candidates.
