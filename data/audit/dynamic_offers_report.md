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
- `sessions_current`

## Files Missing Or Unreadable

- None

## Summary

- Availability source used: live_availability_snapshot
- Availability fallback used: False
- Available blocks read from selected source: 250
- Availability source reason: valid_live_available_blocks_found
- Availability windows read: 250
- Scheduler-enabled instructors considered: 2
- Courses considered: 30
- Local occupancy blocks read: 632
- Offers generated: 137361

## Offers Rejected By Reason

- `conflicts_with_existing_occupancy`: 9328
- `course_family_not_allowed_by_window`: 2750

## Top 20 Example Offers

| Date | Time | Course | Instructor | Location |
| --- | --- | --- | --- | --- |
| 2026-07-14 | 20:15-22:15 | AHA BLS Provider | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 20:30-22:30 | AHA BLS Provider | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 20:45-22:45 | AHA BLS Provider | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 21:00-23:00 | AHA BLS Provider | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 21:15-23:15 | AHA BLS Provider | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 20:15-22:15 | AHA BLS Provider Renewal | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 20:30-22:30 | AHA BLS Provider Renewal | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 20:45-22:45 | AHA BLS Provider Renewal | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 21:00-23:00 | AHA BLS Provider Renewal | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 21:15-23:15 | AHA BLS Provider Renewal | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 15:15-16:15 | AHA HeartCode BLS | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 15:30-16:30 | AHA HeartCode BLS | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 15:45-16:45 | AHA HeartCode BLS | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 20:15-21:15 | AHA HeartCode BLS | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 20:30-21:30 | AHA HeartCode BLS | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 20:45-21:45 | AHA HeartCode BLS | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 21:00-22:00 | AHA HeartCode BLS | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 21:15-22:15 | AHA HeartCode BLS | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 21:30-22:30 | AHA HeartCode BLS | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-07-14 | 21:45-22:45 | AHA HeartCode BLS | Brian Ennis | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |

## Blockers Preventing More Offers

- `conflicts_with_existing_occupancy`: 9328
- `course_family_not_allowed_by_window`: 2750

## Next Safest Step

- Review the generated offer list with Brian, then add a read-only policy layer for which course families/formats should be public sellable before any public UI or appointment bridge uses these offers.
