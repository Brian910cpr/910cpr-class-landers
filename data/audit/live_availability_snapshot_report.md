# Live Availability Snapshot Preview Report

This is a read-only scaffold. It did not call Google Calendar, call Enrollware, create appointments, modify public pages, write docs output, or enable Worker creation.

## Summary

- Configured calendar sources found: 3
- Local snapshot found: E:\GitHub\910cpr-class-landers_august_seed_breakpoint\data\runtime\calendar_snapshots
- Instructors mapped: 2
- Blocks generated: 116
- Blocks blocked/placeheld: 1
- Inverse-generated availability blocks: 68
- Inverse blocking event blocks: 48
- DNS markers found: 0

## Blocked Reason Counts

- `event_missing_parseable_start_or_end`: 1

## Missing Calendar Source Config / Snapshots

- None

## Calendar Sources Blocked Or Placeholdered

| Source | Type | Reason | Message |
| --- | --- | --- | --- |
| brian_do_not_schedule | inverse_google_calendar | `event_missing_parseable_start_or_end` | Calendar event was not usable as an inverse blocking interval. |

## Instructors Mapped

| Calendar Source | Person | Person ID |
| --- | --- | --- |
| amy_availability | Amy Arnold | `instructor_4180671442` |
| brian_do_not_schedule | Brian Ennis | `instructor_24057895173` |

## Next Safest Step

- Add a local/mock calendar event snapshot fixture and verify normalization before any live Google Calendar integration.
