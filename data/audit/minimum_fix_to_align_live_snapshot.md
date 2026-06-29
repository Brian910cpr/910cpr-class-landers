# Minimum Fix To Align Live Snapshot

Do not deploy from this branch.

## Safest Minimal Fix

Refresh or regenerate `data/runtime/calendar_snapshots/*.json` so the live snapshot builder has calendar data through August, including expanded recurring events where applicable, then rerun `scripts/build_live_availability_snapshot.py` and `scripts/generate_dynamic_offers.py`.

If live calendar access cannot produce August rows quickly, add an explicit reviewed August availability merge into the live snapshot builder from the same base-horizon source used by seed simulation. That merge should be opt-in, report-only/audited, limited to Brian/Wilmington BLS, and still flow through existing dynamic generation, public sellable filtering, seed selection, appointmentDayId mapping, and public integrity checks.

## Guardrail

Add/keep an audit failure when seed simulation has future August BLS availability and active dynamic generation has zero August offers without explicit blocker reasons. Do not solve this by loosening Course Master or public filters first.
