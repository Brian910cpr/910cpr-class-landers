# Minimum Fix To Align Live Snapshot

Do not deploy from this branch.

## Safest Minimal Fix

Keep `scripts/export_calendar_snapshots.py` expanding recurring calendar events into concrete instances before `scripts/build_live_availability_snapshot.py` runs, then rerun dynamic generation and downstream public filters from the regenerated live snapshot.

If live calendar access cannot produce August rows quickly, add an explicit reviewed August availability merge into the live snapshot builder from the same base-horizon source used by seed simulation. That merge should be opt-in, report-only/audited, limited to Brian/Wilmington BLS, and still flow through existing dynamic generation, public sellable filtering, seed selection, appointmentDayId mapping, and public integrity checks.

## Guardrail

Add/keep an audit failure when seed simulation has future August BLS availability and active dynamic generation has zero August offers without explicit blocker reasons. Do not solve this by loosening Course Master or public filters first.
