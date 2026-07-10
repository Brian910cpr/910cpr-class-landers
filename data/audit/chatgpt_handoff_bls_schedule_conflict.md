# ChatGPT Handoff: July 13 BLS Selector Scheduling Conflict

Generated: 2026-07-09

## Goal

Investigate and fix the live BLS selector conflict where Monday, July 13 showed a public AHA BLS Provider start around 3:30 PM despite an Enrollware appointment-created class occupying the same Brian/Shipyard scheduler window.

## Root cause

The live Enrollware iCal feed contained appointment-created class UID `13740038`:

- Course: `AHA Heartsaver® CPR AED Online`
- Mapped course ID: `209808`
- Start: `2026-07-13T15:30:00-04:00`
- Feed shape: `DTSTART:20260713T193000Z` and `DTEND:20260713T193000Z`
- Location: `NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office`
- Instructor: `Brian Ennis`
- URL: `https://coastalcprtraining.enrollware.com/enroll?id=13740038`

Before the fix, the local generated schedule did not contain this new class, and zero-duration appointment-created iCal events would not create a blocking occupancy window.

## Source changes

- `scripts/build_sessions_current.py`
  - Added TLS fallback for the current Enrollware iCal endpoint certificate failure.
  - Added zero/non-positive duration iCal handling.
  - If `DTEND <= DTSTART`, the importer now infers `end` from `data/inventory/course_consumption_rules.json` using mapped course ID.
  - The inferred end is annotated in `timing.end_inference_reason` and `timing.inferred_scheduler_consumption_minutes`.

- `scripts/generate_dynamic_offers.py`
  - Fixed `normalize_occupancy()` so nested iCal session fields from `data/sessions_current.json` normalize correctly:
    - `course.course_name_raw`
    - `location.location_name`
    - `staffing.lead_instructor_name`

## Tests added

- `tests/test_enrollware_ical_import.py`
  - `test_zero_duration_appointment_event_infers_scheduler_consumption_end`
  - Verifies UID `13740038` maps to course ID `209808`, starts `2026-07-13T15:30:00-04:00`, and infers end `2026-07-13T17:30:00-04:00` using 120 scheduler-consumption minutes.

- `tests/test_generate_dynamic_offers.py`
  - `test_normalize_occupancy_reads_nested_ical_session_fields`
  - Verifies nested iCal session fields become usable occupancy fields.

## Commands run

```text
python -m unittest tests.test_enrollware_ical_import -v
```

Result: 3 tests OK.

```text
python -m scripts.build_sessions_current --source enrollware_ical
```

Result:

```text
Wrote E:\GitHub\910cpr-class-landers\data\sessions_current.json
iCal events read: 497
Public sessions created: 497
Classes removed compared with prior source: 124
Wrote E:\GitHub\910cpr-class-landers\data\audit\enrollware_ical_import_summary.json
Wrote E:\GitHub\910cpr-class-landers\data\audit\enrollware_ical_import_report.md
```

```text
python -m scripts.build_schedule_future
```

Result:

```text
Loaded 497 sessions from E:\GitHub\910cpr-class-landers\data\sessions_current.json
Loaded 497 session IDs from Enrollware iCal
Future sessions written: 144
Skipped past: 351
Skipped TBD location: 2
Included by legacy mapping: 142
Included by course identity resolver: 2
```

```text
python -m unittest tests.test_enrollware_ical_import tests.test_generate_dynamic_offers -v
```

Result: 15 tests OK.

```text
python -m scripts.build_bls_block_schedule_pilot
```

Final result:

```text
Availability source used: live_availability_snapshot
Availability fallback used: False
availabilityBlocksFound: 62
availabilityBlocksEvaluated: 62
publicLocationBlocksEvaluated: 62
publicSelectableOfferCount: 1702
publicSelectableDateCount: 39
publicSelectableStartTimeCount: 606
rejectedOfferCount: 3644
suppressedStaleOrOrphanedOfferCount: 0
```

## Validation evidence

After rebuild, UID `13740038` appears in both:

- `data/sessions_current.json`
- `docs/data/schedule_future.json`

Resolved row:

```json
{
  "session_id": "13740038",
  "course_id": "209808",
  "course": "AHA Heartsaver� CPR AED Online",
  "start": "2026-07-13T15:30:00-04:00",
  "end": "2026-07-13T17:30:00-04:00",
  "instructor": "Brian Ennis",
  "location": "NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office"
}
```

Targeted BLS overlap trace for `2026-07-13T15:30:00`:

```json
{"course_id":"209806","start":"2026-07-13T15:30:00","end":"2026-07-13T17:30:00","conflict":true,"reason":"conflicts with AHA Heartsaver� CPR AED Online from data/sessions_current.json"}
{"course_id":"359474","start":"2026-07-13T15:30:00","end":"2026-07-13T17:30:00","conflict":true,"reason":"conflicts with AHA Heartsaver� CPR AED Online from data/sessions_current.json"}
{"course_id":"210549","start":"2026-07-13T15:30:00","end":"2026-07-13T16:30:00","conflict":true,"reason":"conflicts with AHA Heartsaver� CPR AED Online from data/sessions_current.json"}
```

Parsed rendered selector model in `docs/bls-schedule.html` for July 13:

```json
["9:30 AM", "10:00 AM", "10:30 AM", "2:30 PM"]
```

No July 13 `3:30 PM` BLS start group remains in the rendered model.

## Files changed by this task

Intentional source/test files:

- `scripts/build_sessions_current.py`
- `scripts/generate_dynamic_offers.py`
- `tests/test_enrollware_ical_import.py`
- `tests/test_generate_dynamic_offers.py`

Regenerated operational artifacts:

- `data/sessions_current.json`
- `docs/data/schedule_future.json`
- `data/audit/bls_block_schedule_pilot.json`
- `data/audit/bls_block_schedule_pilot_report.md`
- `docs/bls-schedule.html`
- `data/audit/enrollware_ical_import_summary.json`
- `data/audit/enrollware_ical_import_report.md`

Other status/debug artifacts were touched by existing build status machinery and should be reviewed before staging:

- `data/runtime/build_sessions_current.json`
- `data/runtime/build_schedule_future.json`
- `debug/status/build_sessions_current.json`
- `debug/status/build_schedule_future.json`
- `debug/course_identity_match_report.json`
- `debug/unmatched_courses.json`
- `data/state/supervisor_status.json`

## Deployment status

Not deployed.

Live-domain check for `https://bls-schedule.com/` failed from this environment with DNS resolution error: `getaddrinfo failed`.

## Open concern

The repository was already dirty with many unrelated modified/untracked files before this task. Do not stage broadly. Stage only the listed source/test/build artifacts after reviewing the generated diff.
