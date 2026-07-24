# Live Availability Snapshot Preview Report

This is a read-only scaffold. It did not call Google Calendar, call Enrollware, create appointments, modify public pages, write docs output, or enable Worker creation.

## Summary

- Configured calendar sources found: 3
- Local snapshot found: /home/runner/work/910cpr-class-landers/910cpr-class-landers/data/runtime/calendar_snapshots
- Instructors mapped: 2
- Blocks generated: 300
- Blocks blocked/placeheld: 4
- Inverse-generated availability blocks: 185
- Inverse blocking event blocks: 115
- DNS markers found: 0

## Blocked Reason Counts

- `inverse_gap_shorter_than_minimum_consumption`: 4

## Missing Calendar Source Config / Snapshots

- None

## Calendar Sources Blocked Or Placeholdered

| Source | Type | Reason | Message |
| --- | --- | --- | --- |
| brian_do_not_schedule | inverse_google_calendar | `inverse_gap_shorter_than_minimum_consumption` | Inverse-generated open gap is shorter than the configured minimum course consumption window. |
| brian_do_not_schedule | inverse_google_calendar | `inverse_gap_shorter_than_minimum_consumption` | Inverse-generated open gap is shorter than the configured minimum course consumption window. |
| brian_do_not_schedule | inverse_google_calendar | `inverse_gap_shorter_than_minimum_consumption` | Inverse-generated open gap is shorter than the configured minimum course consumption window. |
| brian_do_not_schedule | inverse_google_calendar | `inverse_gap_shorter_than_minimum_consumption` | Inverse-generated open gap is shorter than the configured minimum course consumption window. |

## Instructors Mapped

| Calendar Source | Person | Person ID |
| --- | --- | --- |
| amy_availability | Amy Arnold | `instructor_4180671442` |
| brian_do_not_schedule | Brian Ennis | `instructor_24057895173` |

## Next Safest Step

- Add a local/mock calendar event snapshot fixture and verify normalization before any live Google Calendar integration.
