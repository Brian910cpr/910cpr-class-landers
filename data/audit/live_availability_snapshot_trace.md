# Live Availability Snapshot Trace

Status: read-only trace. No deploy was performed.

## Files And Flow

- Snapshot builder: `scripts/build_live_availability_snapshot.py`
- Snapshot inputs: `data/config/calendar_sources.json`, `data/config/people_catalog.json`, `data/config/course_catalog.json`, `data/inventory/appointment_containers.json`, `data/runtime/calendar_snapshots/*.json`
- Active dynamic input: `data/audit/live_availability_snapshot_preview.json`
- Active dynamic generator: `scripts/generate_dynamic_offers.py`
- Active dynamic output: `data/runtime/audit_previews/dynamic_offers_preview.json`

## Date Ranges

- Seed simulation: 2026-08-03 to 2026-09-14
- Runtime calendar snapshots: 2026-06-29 to 2026-08-28
- Live availability snapshot: 2026-06-29 to 2026-08-28
- Dynamic offers: 2026-06-29 to 2026-08-13

## August Counts

- Seed simulation August BLS blocks/proposals: 8
- Runtime August events: 16
- Runtime events with August RRULE not expanded: 0
- Live snapshot August blocks: 29
- Dynamic August offers: 20901

## First Divergence

The prior divergence is resolved after RRULE expansion. Seed simulation, runtime calendar snapshots, the live availability snapshot, and dynamic offers now all carry August rows.

## Why This Happens

resolved: runtime calendar snapshots now contain expanded August recurrence instances, the live snapshot contains August availability blocks, and dynamic generation evaluates August offers before Course Master/public gates

See `seed_sim_vs_active_generation_diff.csv` for the row-level comparison.
