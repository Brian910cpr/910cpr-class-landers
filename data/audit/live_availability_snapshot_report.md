# Live Availability Snapshot Preview Report

This is a read-only scaffold. It did not call Google Calendar, call Enrollware, create appointments, modify public pages, write docs output, or enable Worker creation.

## Summary

- Configured calendar sources found: 3
- Local snapshot found: E:\GitHub\910cpr-class-landers\data\runtime\calendar_snapshots
- Instructors mapped: 2
- Blocks generated: 12
- Blocks blocked/placeheld: 8
- DNS markers found: 0

## Blocked Reason Counts

- `local_calendar_snapshot_missing`: 1
- `overnight_not_allowed`: 5
- `event_missing_parseable_start_or_end`: 1
- `non_standard_time_increment`: 1

## Missing Calendar Source Config / Snapshots

- None

## Calendar Sources Blocked Or Placeholdered

| Source | Type | Reason | Message |
| --- | --- | --- | --- |
| nick_availability | google_calendar | `local_calendar_snapshot_missing` | No local/mock calendar event snapshot found for this source; no availability blocks generated. |
| brian_do_not_schedule | inverse_google_calendar | `overnight_not_allowed` | Calendar event crosses midnight and allow_overnight_availability is false; no offerable availability was generated. |
| brian_do_not_schedule | inverse_google_calendar | `overnight_not_allowed` | Calendar event crosses midnight and allow_overnight_availability is false; no offerable availability was generated. |
| brian_do_not_schedule | inverse_google_calendar | `event_missing_parseable_start_or_end` | Calendar event did not include parseable start/end datetimes. |
| brian_do_not_schedule | inverse_google_calendar | `non_standard_time_increment` | Calendar event start/end is not on a standard 15-minute increment and allow_non_standard_time_increment is false; no offerable availability was generated. |
| brian_do_not_schedule | inverse_google_calendar | `overnight_not_allowed` | Calendar event crosses midnight and allow_overnight_availability is false; no offerable availability was generated. |
| brian_do_not_schedule | inverse_google_calendar | `overnight_not_allowed` | Calendar event crosses midnight and allow_overnight_availability is false; no offerable availability was generated. |
| brian_do_not_schedule | inverse_google_calendar | `overnight_not_allowed` | Calendar event crosses midnight and allow_overnight_availability is false; no offerable availability was generated. |

## Instructors Mapped

| Calendar Source | Person | Person ID |
| --- | --- | --- |
| amy_availability | Amy Arnold | `instructor_4180671442` |
| brian_do_not_schedule | Brian Ennis | `instructor_24057895173` |

## Next Safest Step

- Add a local/mock calendar event snapshot fixture and verify normalization before any live Google Calendar integration.
