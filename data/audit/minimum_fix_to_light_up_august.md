# Minimum Fix To Light Up August

Do not deploy from this audit branch.

## Smallest Change

Keep reviewed recurring availability expanding into the active availability source used by `data/audit/dynamic_offers_preview.json`. Then rerun the existing pipeline without bypassing public filters.

The prior first break was not page rendering and not Course Master gating. After RRULE expansion, August no longer vanishes before active dynamic offers.

## Rows Expected After Fix

- 2026-08-03 09:00 aha_bls_renewal at shipyard with brian
- 2026-08-03 13:00 aha_bls_initial at shipyard with brian
- 2026-08-04 09:00 aha_bls_renewal at shipyard with brian
- 2026-08-04 13:00 aha_bls_initial at shipyard with brian
- 2026-08-05 09:00 aha_bls_renewal at shipyard with brian
- 2026-08-05 13:00 aha_bls_initial at shipyard with brian
- 2026-08-06 09:00 aha_bls_heartcode_skills at shipyard with brian
- 2026-08-07 09:00 aha_bls_heartcode_skills at shipyard with brian

## Required Rerun And Checks

1. Regenerate dynamic offers.
2. Regenerate public sellable offers.
3. Regenerate selected seeds.
4. Regenerate appointment URL preview.
5. Regenerate public inventory and hubs.
6. Run public offer integrity checks and render verification.

## Risks If Enabled

- Report-only base-horizon availability may be too broad unless reviewed.
- Appointment containers must still provide valid August `appointmentDayId` values.
- Course ID mappings must remain exact.
- UNKNOWN or unreviewed Course Master rows must remain suppressed.
- Existing Enrollware classes and occupied scheduler windows must remain blockers.
