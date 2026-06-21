# Solver Audit Report

This is a read-only scheduler redesign audit. It did not modify public pages, runtime data, Enrollware behavior, appointments, Worker settings, or generated HTML.

## Files Read

- `availability_window_policies`
- `calendar_sources`
- `course_catalog`
- `course_consumption_rules`
- `course_map`
- `instructor_availability`
- `instructor_catalog`
- `people_catalog`
- `schedule_future`
- `sessions_current`

## Files Missing Or Unreadable

- None

## Assumptions Avoided

- Did not invent Enrollware course IDs.
- Did not assume overnight should or should not be offered.
- Did not fetch Google Calendar or Enrollware live data.
- Did not treat debug reports as source of truth.
- Did not generate candidates without an explicit local availability window.

## Summary

- Active courses understood: 30
- Course families found: ACLS, ARC, BLS, HSI, Heartsaver, PALS, USCG
- Instructors found: 7
- Active instructors: 3
- Instructors with UNKNOWN certifications: 7
- People catalog read: True
- People with certifications: 79
- People scheduler-enabled: 2
- Availability instructors matched to People: 2
- Remaining `missing_instructor_qualification` rejections: 166
- Existing occupancy blocks normalized: 566
- Candidates generated: 190
- Rejections created: 231

## Top 10 Blockers

- `missing_instructor_qualification`: 166
- `outside_configured_policy_window`: 43
- `course_family_only_available_as_manual_fallback`: 22

## People Catalog Qualification Bridge

| Availability Instructor | Matched Person | Scheduler Enabled | Certification Codes |
| --- | --- | --- | --- |
| Amy | Amy Arnold (`instructor_4180671442`) | True | `AHA_ACLS_INSTRUCTOR`, `AHA_BLS_INSTRUCTOR`, `AHA_HEARTSAVER_INSTRUCTOR`, `AHA_PALS_INSTRUCTOR`, `AHA_PEARS_INSTRUCTOR` |
| Brian | Brian Ennis (`instructor_24057895173`) | True | `AHA_BLS_INSTRUCTOR`, `AHA_HEARTSAVER_INSTRUCTOR` |

- Courses with scheduler-enabled qualified instructor: 18
- Courses qualified only through availability bridge: 0

## Occupancy Notes

- Occupancy examples inspected: 10
- 2026-06-01 00:00-UNKNOWN | AHA - PALS Instructor Renewal | {'location_name': ':: Wilmington; Shipyard Blvd', 'location_display': ':: Wilmington; Shipyard Blvd', 'client': '910CPR'} | source `data/sessions_current.json`
- 2026-06-01 00:00-UNKNOWN | AHA - PALS Instructor Renewal | {'location_name': ':: Wilmington; Shipyard Blvd', 'location_display': ':: Wilmington; Shipyard Blvd', 'client': '910CPR'} | source `data/sessions_current.json`
- 2026-06-01 00:00-UNKNOWN | AHA - BLS Instructor Renewal | {'location_name': ':: Wilmington; Shipyard Blvd', 'location_display': ':: Wilmington; Shipyard Blvd', 'client': '910CPR'} | source `data/sessions_current.json`
- 2026-06-01 08:30-11:30 | AHA BLS for the Prehospital Provider | {'location_name': 'Rocky Point VFC', 'location_display': 'Rocky Point VFC', 'client': None} | source `data/sessions_current.json`
- 2026-06-01 18:00-21:00 | AHA BLS for the Prehospital Provider | {'location_name': 'Rocky Point VFC', 'location_display': 'Rocky Point VFC', 'client': None} | source `data/sessions_current.json`
- 2026-06-02 08:30-09:15 | AHA HeartCode BLS | {'location_name': ':: Wilmington; Shipyard Blvd', 'location_display': ':: Wilmington; Shipyard Blvd', 'client': None} | source `data/sessions_current.json`
- 2026-06-02 11:45-12:30 | AHA HeartCode BLS | {'location_name': ':: Wilmington; Shipyard Blvd', 'location_display': ':: Wilmington; Shipyard Blvd', 'client': None} | source `data/sessions_current.json`
- 2026-06-02 12:30-14:30 | AHA BLS Provider | {'location_name': ':: Wilmington; Shipyard Blvd', 'location_display': ':: Wilmington; Shipyard Blvd', 'client': None} | source `data/sessions_current.json`
- 2026-06-02 17:30-18:15 | AHA HeartCode BLS | {'location_name': ':: Wilmington; Shipyard Blvd', 'location_display': ':: Wilmington; Shipyard Blvd', 'client': None} | source `data/sessions_current.json`
- 2026-06-02 18:15-20:15 | AHA Heartsaver First Aid CPR AED | {'location_name': ':: Wilmington; Shipyard Blvd', 'location_display': ':: Wilmington; Shipyard Blvd', 'client': None} | source `data/sessions_current.json`

## Safest Next Steps

1. Confirm the active source-of-truth files with Brian before promoting any solver output.
2. Add a canonical course/format model that links course IDs, duration, capacity, appointment eligibility, and public labels.
3. Replace prototype availability blocks with audited local snapshots from the intended calendar model.
4. Add explicit room/resource conflict rules before using candidates publicly.
5. Keep generated candidates read-only until click-time recheck and Enrollware bridge behavior are specified.
