# Class Report Ingest Audit

## Source
- File used: `E:\GitHub\910cpr-class-landers\data\Class Report.xlsx`
- Modified: 2026-06-19T13:08:37.415105
- Worksheet: Sheet1
- Header row: 1
- Rows read: 255

## Output
- `data/sessions_current.json` sessions: 255
- `docs/data/schedule_future.json` sessions: 249
- Occupancy records from `data/sessions_current.json`: 255
- Usable start/end conflict blocks from `data/sessions_current.json`: 253
- Occupancy records from `docs/data/schedule_future.json`: 249
- Usable start/end conflict blocks from `docs/data/schedule_future.json`: 248
- Occupancy records read by dynamic offer generation: 504
- Usable start/end conflict blocks total: 501

## Instructors Found
- B.  Ennis: 223
- N.  Tripp: 22
- A.  Arnold: 10

## Brian/Amy Occupancy
- Amy sessions found: 10
- Brian sessions found: 223

## Data Quality
- Sessions with unknown course_id: 3
- Sessions with unknown end time: 2
- schedule_future sessions with unknown end time: 1
- Unmapped sessions reported by build_sessions_current: 3

## Skipped Rows
- build_sessions_current reported skipped_no_session_id=0.
- build_schedule_future suppressed non-public locations from public schedule JSON; those records still remain in `data/sessions_current.json` for occupancy.

## Safety
- No public HTML was generated.
- No Enrollware calls were made.
- No appointments were created.
- No Worker route was enabled.

Note: `generate_dynamic_offers` reads occupancy records even when an end time is unknown, but those records do not participate in overlap matching until the missing end time is resolved.
