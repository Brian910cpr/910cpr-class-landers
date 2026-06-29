# Live Availability Snapshot Trace

Status: read-only trace. No deploy was performed.

## Files And Flow

- Snapshot builder: `scripts/build_live_availability_snapshot.py`
- Snapshot inputs: `data/config/calendar_sources.json`, `data/config/people_catalog.json`, `data/config/course_catalog.json`, `data/inventory/appointment_containers.json`, `data/runtime/calendar_snapshots/*.json`
- Active dynamic input: `data/audit/live_availability_snapshot_preview.json`
- Active dynamic generator: `scripts/generate_dynamic_offers.py`
- Active dynamic output: `data/audit/dynamic_offers_preview.json`

## Date Ranges

- Seed simulation: 2026-08-03 to 2026-09-14
- Runtime calendar snapshots: 2026-06-19 to 2026-07-04
- Live availability snapshot: 2026-06-21 to 2026-07-04
- Dynamic offers: 2026-06-21 to 2026-07-04

## August Counts

- Seed simulation August BLS blocks/proposals: 8
- Runtime August events: 0
- Runtime events with August RRULE not expanded: 1
- Live snapshot August blocks: 0
- Dynamic August offers: 0

## First Divergence

`data/audit/live_availability_snapshot_preview.json` is the first file where August availability is absent. Seed simulation has August report-only base-horizon BLS windows; the live snapshot consumed by dynamic generation does not.

## Why This Happens

live snapshot/runtime calendar snapshots contain no expanded August availability blocks; dynamic generation correctly uses the nonempty live snapshot and therefore never evaluates seed-simulation August base-horizon windows

See `seed_sim_vs_active_generation_diff.csv` for the row-level comparison.
