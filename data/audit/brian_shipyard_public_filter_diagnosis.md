# Brian + Shipyard Public Filter Diagnosis

Status: read-only diagnosis. No public pages, Enrollware calls, appointments, appointment URL changes, Worker routes, deploys, or commits were performed.

## Summary

- Brian + Shipyard availability blocks found: 1
- Brian + Shipyard timed availability blocks found: 1
- Dynamic offers created from timed Brian + Shipyard blocks: 0
- Dynamic offers created from all Brian + Shipyard blocks: 0
- First failing stage: `dynamic_offer_generation`
- First failing comparison: `offers_created_from_timed_brian_shipyard_blocks`
- Smallest safe fix: Fix live availability snapshot interpretation for overnight/cross-midnight timed events, or correct the calendar event so end is after start on the intended date. Do not change appointment containers or Shipyard aliases for this blocker.


## Critical Timing Finding

The current Brian + Shipyard block is timed but invalid for same-date offer generation:

- Date: `2026-07-04`
- Start: `16:01`
- End: `03:59`

The offer generator interprets both times on `2026-07-04`, so the end is before the start. No course can fit inside that window, and the public confirmed-container filter never gets a valid Brian + Shipyard offer to evaluate.

This is not a Shipyard alias problem and not an appointmentDayId/container range problem yet.

## Hidden Reasons For Timed Brian + Shipyard Offers

- None

## Brian + Shipyard Availability Blocks

- `4jgsd3masf2ccq7algku6rs7j8@google.com`: 2026-07-04 16:01-03:59 / Brian Ennis / NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office / timed

## First Failing Comparison

```json
{
  "stage": "dynamic_offer_generation",
  "comparison": "offers_created_from_timed_brian_shipyard_blocks",
  "reason": "No dynamic offers were created from timed Brian + Shipyard blocks.",
  "rejection_counts": {
    "course_family_not_allowed_by_window": 18,
    "course_does_not_fit_window": 12
  }
}
```

## Offer Filter Decisions

No timed Brian + Shipyard dynamic offers exist in the current artifacts, so public filter decisions cannot be evaluated for timed Brian + Shipyard offers yet.
