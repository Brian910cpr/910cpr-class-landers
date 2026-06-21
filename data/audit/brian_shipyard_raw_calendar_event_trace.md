# Brian + Shipyard Raw Calendar Event Trace

Status: read-only diagnosis. No public pages, Enrollware calls, appointments, appointment URL changes, Worker routes, deploys, or commits were performed.

## Summary

- Selected raw event ID: `4jgsd3masf2ccq7algku6rs7j8@google.com`
- Raw event found: True
- Raw title/summary: `Fourth of July` / `Fourth of July`
- Raw start value: `20260704T160100Z`
- Exported start value: `2026-07-04T16:01:00+00:00`
- Raw end value: `20260705T035900Z`
- Exported end value: `2026-07-05T03:59:00+00:00`
- Normalized live block: `2026-07-04 16:01-03:59`
- Location exactly as exported: ``
- Multiple 2026-07-04 Brian events found: 2
- Classification: `{'all_day': False, 'timezone_shifted': True, 'cross_midnight': True, 'stale': 'UNKNOWN'}`

## Exact Source Of 16:01 And 03:59

16:01 comes from exported event.start `2026-07-04T16:01:00+00:00`, which comes from raw DTSTART `20260704T160100Z`. 03:59 comes from exported event.end `2026-07-05T03:59:00+00:00`, which comes from raw DTEND `20260705T035900Z`.

## Raw Event

```json
{
  "raw_properties": {
    "DTSTART": "20260704T160100Z",
    "DTEND": "20260705T035900Z",
    "DTSTAMP": "20260619T195655Z",
    "UID": "4jgsd3masf2ccq7algku6rs7j8@google.com",
    "CREATED": "20260619T001758Z",
    "LAST-MODIFIED": "20260619T190834Z",
    "SEQUENCE": "1",
    "STATUS": "CONFIRMED",
    "SUMMARY": "Fourth of July",
    "TRANSP": "TRANSPARENT"
  },
  "recurrence": [],
  "start_raw": "20260704T160100Z",
  "start": "2026-07-04T16:01:00+00:00",
  "calendar_source_id": "brian_do_not_schedule",
  "calendar_id": "c_d2f947481181f460985c18b4ba5d713a67b488f408889f2483d71ef498ab2df7@group.calendar.google.com",
  "source_type": "inverse_google_calendar",
  "read_only_snapshot": true,
  "end_raw": "20260705T035900Z",
  "end": "2026-07-05T03:59:00+00:00",
  "updated": "2026-06-19T19:08:34+00:00",
  "event_id": "4jgsd3masf2ccq7algku6rs7j8@google.com",
  "created": "2026-06-19T00:17:58+00:00",
  "status": "CONFIRMED",
  "title": "Fourth of July",
  "summary": "Fourth of July",
  "description": "",
  "location": "",
  "creator": "UNKNOWN",
  "organizer": "UNKNOWN"
}
```

## Normalized Live Block

```json
{
  "source_event_id": "4jgsd3masf2ccq7algku6rs7j8@google.com",
  "date": "2026-07-04",
  "start_time": "16:01",
  "end_time": "03:59",
  "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
  "instructor_name": "Brian Ennis",
  "allowed_course_families": [
    "BLS",
    "Heartsaver",
    "USCG"
  ],
  "reasons": [
    "read_only_preview",
    "local_calendar_snapshot",
    "offerable_calendar_window"
  ]
}
```

## 2026-07-04 Events In Brian Snapshot

- `ckr62ohpc8q3gb9i6krmab9k68q6cb9o61gjgb9j6gojceb4ccqj6ohl74@google.com`: `Beya's Fourth of July` / raw `20260704T163000Z`-`20260704T210100Z` / exported `2026-07-04T16:30:00+00:00`-`2026-07-04T21:01:00+00:00`
- `4jgsd3masf2ccq7algku6rs7j8@google.com`: `Fourth of July` / raw `20260704T160100Z`-`20260705T035900Z` / exported `2026-07-04T16:01:00+00:00`-`2026-07-05T03:59:00+00:00`

## Export/Normalization Path

- export_calendar_snapshots.py stores raw DTSTART as start_raw and ics_datetime_to_iso(DTSTART) as start.
- export_calendar_snapshots.py stores raw DTEND as end_raw and ics_datetime_to_iso(DTEND) as end.
- build_live_availability_snapshot.py parses event.start/event.end, then formats start_time/end_time from those parsed datetimes.
