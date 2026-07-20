# Minimum Safe Forward Horizon Fix

Do not deploy from this branch.

## Smallest Safe Fix

Add RRULE/RDATE expansion to `scripts/export_calendar_snapshots.py::parse_ics_events` for occurrences inside the existing `EXPORT_DAYS` window, then regenerate runtime calendar snapshots and `live_availability_snapshot_preview.json`.

Do not solve this by changing Course Master, public sellable filters, or appointment URL generation. The active path declares a 120-day window; the missing piece is materializing recurring event occurrences before the live snapshot builder reads runtime events.

## Horizon

The current runtime export horizon is `EXPORT_DAYS = 120`. The live public window remains rolling from build time and is separate from report-only candidate horizons.

## Guardrail

Keep the audit/test that fails loudly when seed simulation sees August BLS availability but live snapshot/dynamic generation has zero August rows without explicit blocker reasons.
