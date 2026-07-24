# Calendar Snapshot Export Report

This is a read-only local export. It did not call Enrollware, create appointments, change appointment URLs, modify public pages, write docs output, or enable Worker creation.

Private event descriptions are stored only inside the local runtime snapshot JSON files and are not printed in this report.

## Summary

- Calendar sources found: 3
- Snapshots written: 3
- Total events exported: 115
- Date range exported: 2026-07-24T03:57:26.740581+00:00 through 2026-10-22T03:57:26.740581+00:00
- Private calendar secrets loaded: False

## Events Exported Per Source

| Source | Calendar ID Present | ICS URL Attempted | URL Source | Type | Status | Failure Reason | Events | Snapshot | Warning Count |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | ---: |
| amy_availability | True | https://calendar.google.com/...m/public/basic.ics | derived_public_ics_from_calendar_id | google_calendar | ok |  | 0 | `/home/runner/work/910cpr-class-landers/910cpr-class-landers/data/runtime/calendar_snapshots/amy_availability.json` | 0 |
| nick_availability | True | https://calendar.google.com/...m/public/basic.ics | derived_public_ics_from_calendar_id | google_calendar | ok |  | 0 | `/home/runner/work/910cpr-class-landers/910cpr-class-landers/data/runtime/calendar_snapshots/nick_availability.json` | 0 |
| brian_do_not_schedule | True | https://calendar.google.com/...m/public/basic.ics | derived_public_ics_from_calendar_id | inverse_google_calendar | ok |  | 115 | `/home/runner/work/910cpr-class-landers/910cpr-class-landers/data/runtime/calendar_snapshots/brian_do_not_schedule.json` | 0 |

## Warnings

- None
