# Brian + Shipyard Offer Generation Trace

Status: read-only trace. No public pages, Enrollware calls, appointments, appointment URL changes, Worker routes, deploys, or commits were performed.

## Summary

- Brian + Shipyard blocks found: 1
- First failing condition: `window_end_after_start`
- Reason code: `course_does_not_fit_window`
- Smallest safe fix: Fix cross-midnight/overnight interpretation in live availability normalization, or correct the calendar event so end is after start on the same intended date.

## Blocks

### Block 1

- Source: `4jgsd3masf2ccq7algku6rs7j8@google.com`
- Instructor/person: Brian Ennis / `instructor_24057895173`
- Date/time: 2026-07-04 16:01-03:59
- Location: NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office
- Normalized location/resource: NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office / NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office
- Allowed families: `['BLS', 'Heartsaver', 'USCG']`
- Reasons: `['read_only_preview', 'local_calendar_snapshot', 'offerable_calendar_window']`
- Existing BLS offers from this block: 0
- First fail: `window_end_after_start` / `course_does_not_fit_window`

| Check | Passed | Reason if failed | Details |
|---|---:|---|---|
| availability_status_available | True | `availability_window_not_available` | `{"availability_status": "available"}` |
| window_start_parseable | True | `unknown_availability_window_time` | `{"date": "2026-07-04", "start_time": "16:01"}` |
| window_end_parseable | True | `unknown_availability_window_time` | `{"date": "2026-07-04", "end_time": "03:59"}` |
| window_end_after_start | False | `course_does_not_fit_window` | `{"window_start": "2026-07-04T16:01:00", "window_end_same_date": "2026-07-04T03:59:00", "duration_minutes": -722.0}` |
| scheduler_enabled_person_match | True | `missing_scheduler_enabled_person` | `{"window_person_id": "instructor_24057895173", "window_instructor_name": "Brian Ennis", "matched_person_id": "instructor_24057895173", "matched_person_name": "Brian Ennis"}` |
| course_appointment_allowed | True | `appointment_not_allowed` | `{"course_id": "209806", "appointment_allowed": true}` |
| family_allowed_by_window | True | `course_family_not_allowed_by_window` | `{"course_family": "BLS", "allowed_course_families": ["BLS", "Heartsaver", "USCG"]}` |
| course_duration_numeric | True | `missing_course_duration` | `{"duration_minutes": 120}` |
| course_capacity_numeric | True | `missing_course_capacity` | `{"default_capacity": 6}` |
| required_instructor_certification_present | True | `missing_required_instructor_certification` | `{"requirements": ["AHA_BLS_INSTRUCTOR"]}` |
| instructor_certification_match | True | `instructor_lacks_required_certification` | `{"person_codes": ["AHA_BLS_INSTRUCTOR", "AHA_HEARTSAVER_INSTRUCTOR"], "requirements": ["AHA_BLS_INSTRUCTOR"], "intersection": ["AHA_BLS_INSTRUCTOR"]}` |
| course_fits_window | False | `course_does_not_fit_window` | `{"window_start": "2026-07-04T16:01:00", "window_end": "2026-07-04T03:59:00", "duration_minutes": 120, "latest_start": "2026-07-04T01:59:00", "candidate_start_count": 0, "candidate_starts": []}` |
| no_existing_occupancy_conflict_for_any_candidate | False | `conflicts_with_existing_occupancy` | `{"conflicting_candidate_count": 0, "total_candidate_count": 0, "first_conflicts": []}` |

