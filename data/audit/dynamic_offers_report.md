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
- Available blocks read from selected source: 11
- Availability source reason: valid_live_available_blocks_found
- Availability windows read: 11
- Scheduler-enabled instructors considered: 2
- Courses considered: 30
- Local occupancy blocks read: 442
- Offers generated: 856

## Offers Rejected By Reason

- `course_family_not_allowed_by_window`: 127
- `course_does_not_fit_window`: 85

## Top 20 Example Offers

| Date | Time | Course | Instructor | Location |
| --- | --- | --- | --- | --- |
| 2026-06-23 | 18:00-19:30 | AHA ACLS HeartCode | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 18:15-19:45 | AHA ACLS HeartCode | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 18:30-20:00 | AHA ACLS HeartCode | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 18:45-20:15 | AHA ACLS HeartCode | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 19:00-20:30 | AHA ACLS HeartCode | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 19:15-20:45 | AHA ACLS HeartCode | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 19:30-21:00 | AHA ACLS HeartCode | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 19:45-21:15 | AHA ACLS HeartCode | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 18:00-20:00 | AHA BLS Provider | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 18:15-20:15 | AHA BLS Provider | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 18:30-20:30 | AHA BLS Provider | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 18:45-20:45 | AHA BLS Provider | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 19:00-21:00 | AHA BLS Provider | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 19:15-21:15 | AHA BLS Provider | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 18:00-20:00 | AHA BLS Provider Renewal | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 18:15-20:15 | AHA BLS Provider Renewal | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 18:30-20:30 | AHA BLS Provider Renewal | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 18:45-20:45 | AHA BLS Provider Renewal | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 19:00-21:00 | AHA BLS Provider Renewal | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| 2026-06-23 | 19:15-21:15 | AHA BLS Provider Renewal | Amy Arnold | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |

## Blockers Preventing More Offers

- `course_family_not_allowed_by_window`: 127
- `course_does_not_fit_window`: 85

## Next Safest Step

- Review the generated offer list with Brian, then add a read-only policy layer for which course families/formats should be public sellable before any public UI or appointment bridge uses these offers.
