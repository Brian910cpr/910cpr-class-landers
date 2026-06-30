# Dynamic Offers Preview Report

This is a read-only V0 dynamic offer generator. It did not modify public pages, Enrollware behavior, appointment URLs, Worker settings, generated HTML, or docs output.

## Files Read

- `appointment_containers`
- `course_catalog`
- `instructor_availability`
- `live_availability_snapshot`
- `location_resource_map`
- `people_catalog`
- `schedule_future`
- `seed_strategy_policy`

## Files Missing Or Unreadable

- `sessions_current`: missing

## Summary

- Availability source used: live_availability_snapshot
- Availability fallback used: False
- Available blocks read from selected source: 68
- Availability source reason: valid_live_available_blocks_found
- Availability windows read: 68
- Scheduler-enabled instructors considered: 2
- Courses considered: 30
- Local occupancy blocks read: 208
- Offers generated: 42993

## Offers Rejected By Reason

- `conflicts_with_existing_occupancy`: 17588
- `course_family_not_allowed_by_window`: 748
- `course_does_not_fit_window`: 9

## Top 20 Example Offers

| Date | Time | Course | Instructor | Location |
| --- | --- | --- | --- | --- |
| 2026-06-29 | 15:45-16:45 | AHA HeartCode BLS | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 16:00-17:00 | AHA HeartCode BLS | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 16:15-17:15 | AHA HeartCode BLS | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 15:45-16:30 | HSI Adult First Aid | CPR AED - Blended Learning | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 16:00-16:45 | HSI Adult First Aid | CPR AED - Blended Learning | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 16:15-17:00 | HSI Adult First Aid | CPR AED - Blended Learning | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 16:30-17:15 | HSI Adult First Aid | CPR AED - Blended Learning | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 15:45-16:30 | HSI BLS Challenge | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 16:00-16:45 | HSI BLS Challenge | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 16:15-17:00 | HSI BLS Challenge | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 16:30-17:15 | HSI BLS Challenge | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 15:45-16:30 | HSI BLS and Adult First Aid | Blended Learning | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 16:00-16:45 | HSI BLS and Adult First Aid | Blended Learning | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 16:15-17:00 | HSI BLS and Adult First Aid | Blended Learning | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 16:30-17:15 | HSI BLS and Adult First Aid | Blended Learning | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 15:45-16:30 | HSI Pediatric First Aid | CPR AED - Blended | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 16:00-16:45 | HSI Pediatric First Aid | CPR AED - Blended | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 16:15-17:00 | HSI Pediatric First Aid | CPR AED - Blended | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 16:30-17:15 | HSI Pediatric First Aid | CPR AED - Blended | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-29 | 15:45-17:15 | AHA Heartsaver CPR AED | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |

## Blockers Preventing More Offers

- `conflicts_with_existing_occupancy`: 17588
- `course_family_not_allowed_by_window`: 748
- `course_does_not_fit_window`: 9

## Next Safest Step

- Review the generated offer list with Brian, then add a read-only policy layer for which course families/formats should be public sellable before any public UI or appointment bridge uses these offers.
