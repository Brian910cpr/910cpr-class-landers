# August Public Visibility Sufficiency

## Answer

No. Two August selected seeds are not enough by themselves to make August look alive on the public schedule.

Current selected August seeds: 2. Current August rendered seed rows in `docs/data/schedule_future.json`: 0. Current real August Enrollware rows in that file: 6.

The limiting point is not RRULE expansion anymore. The limiter is downstream public sellable policy: AHA BLS dynamic offers exist, but AHA BLS course IDs are not enabled in `data/config/public_offer_policy.json`, so no August AHA BLS offers reach seed selection. The seed strategy then selects one Heartsaver seed per available August date.

## Minimal Safe Adjustment

Do not widen dynamic generation. First decide whether AHA BLS course IDs 209806/359474/210549 should be enabled in public_offer_policy.enabled_course_ids; today they are generated but rejected before seed selection, so the seed strategy has zero August AHA BLS candidates.

Do not loosen all filters. Keep Course Master, appointment container, occupancy, lead-time, and UNKNOWN-course suppression in place.
