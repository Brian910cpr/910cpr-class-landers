# Calendar Snapshot Export Report

This is a read-only local export. It did not call Enrollware, create appointments, change appointment URLs, modify public pages, write docs output, or enable Worker creation.

Private event descriptions are stored only inside the local runtime snapshot JSON files and are not printed in this report.

## Summary

- Calendar sources found: 4
- Snapshots written: 4
- Total events exported: 167
- Date range exported: 2026-09-01T23:58:40.297066+00:00 through 2026-11-30T23:58:40.297066+00:00
- Private calendar secrets loaded: False

## Events Exported Per Source

| Source | Calendar ID Present | ICS URL Attempted | URL Source | Type | Status | Failure Reason | Events | Snapshot | Warning Count |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | ---: |
| amy_availability | True | https://calendar.google.com/...m/public/basic.ics | derived_public_ics_from_calendar_id | google_calendar | ok |  | 0 | `/home/runner/work/910cpr-class-landers/910cpr-class-landers/data/runtime/calendar_snapshots/amy_availability.json` | 0 |
| nick_availability | True | https://calendar.google.com/...m/public/basic.ics | derived_public_ics_from_calendar_id | google_calendar | ok |  | 0 | `/home/runner/work/910cpr-class-landers/910cpr-class-landers/data/runtime/calendar_snapshots/nick_availability.json` | 0 |
| brian_primary_calendar | False | UNKNOWN | missing_source_url | occupancy_calendar | failed | no usable Google Calendar ICS URL (missing_source_url) | 0 | `/home/runner/work/910cpr-class-landers/910cpr-class-landers/data/runtime/calendar_snapshots/brian_primary_calendar.json` | 1 |
| brian_do_not_schedule | True | https://calendar.google.com/...m/public/basic.ics | derived_public_ics_from_calendar_id | inverse_google_calendar | ok |  | 167 | `/home/runner/work/910cpr-class-landers/910cpr-class-landers/data/runtime/calendar_snapshots/brian_do_not_schedule.json` | 0 |

## Warnings

- brian_primary_calendar: no usable Google Calendar ICS URL (missing_source_url); likely needs a Secret iCal URL or Google API auth
