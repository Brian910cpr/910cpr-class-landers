# Minimum Safe Forward Horizon Fix

Do not deploy from this branch.

## Smallest Safe Fix

Add RRULE/RDATE expansion to `scripts/export_calendar_snapshots.py::parse_ics_events` for occurrences inside the existing `EXPORT_DAYS` window, then regenerate runtime calendar snapshots and `live_availability_snapshot_preview.json`.

Do not solve this by changing Course Master, public sellable filters, or appointment URL generation. The active path already declares a 60-day window; the missing piece is materializing recurring event occurrences before the live snapshot builder reads runtime events.

## Horizon

The current runtime export horizon is `EXPORT_DAYS = 60`. That is enough to reach mid-August from the June 19 snapshot generation date and is not the July 4 limiter. If the approved business forward-seeding horizon is longer than 60 days, make that a named config value rather than another hardcoded constant.

## Guardrail

Keep the audit/test that fails loudly when seed simulation sees August BLS availability but live snapshot/dynamic generation has zero August rows without explicit blocker reasons.
