# Calendar Snapshot Export Report

This is a read-only local export. It did not call Enrollware, create appointments, change appointment URLs, modify public pages, write docs output, or enable Worker creation.

Private event descriptions are stored only inside the local runtime snapshot JSON files and are not printed in this report.

## Summary

- Calendar sources found: 3
- Snapshots written: 3
- Total events exported: 49
- Date range exported: 2026-06-29T15:37:34.470018-04:00 through 2026-08-28T15:37:34.470018-04:00
- Private calendar secrets loaded: False

## Events Exported Per Source

| Source | Calendar ID Present | ICS URL Attempted | URL Source | Type | Status | Failure Reason | Events | Snapshot | Warning Count |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | ---: |
| amy_availability | True | https://calendar.google.com/...m/public/basic.ics | derived_public_ics_from_calendar_id | google_calendar | ok |  | 0 | `E:\GitHub\910cpr-class-landers_august_seed_breakpoint\data\runtime\calendar_snapshots\amy_availability.json` | 0 |
| nick_availability | True | https://calendar.google.com/...m/public/basic.ics | derived_public_ics_from_calendar_id | google_calendar | ok |  | 0 | `E:\GitHub\910cpr-class-landers_august_seed_breakpoint\data\runtime\calendar_snapshots\nick_availability.json` | 0 |
| brian_do_not_schedule | True | https://calendar.google.com/...m/public/basic.ics | derived_public_ics_from_calendar_id | inverse_google_calendar | ok |  | 49 | `E:\GitHub\910cpr-class-landers_august_seed_breakpoint\data\runtime\calendar_snapshots\brian_do_not_schedule.json` | 0 |

## Warnings

- None
