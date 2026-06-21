# Brian TEST Shipyard Container Filter Trace

Read-only trace. No public pages, Enrollware behavior, appointment URLs, Worker routes, or appointments were changed.

## Availability Block

- Found: True
- Source event: `37d9u0mq0lh09sngouh6alou82@google.com`
- Window: 2026-07-04 12:00-17:00
- Instructor: Brian Ennis
- Location: 4018 Shipyard Blvd\, Wilmington\, NC 28403\, USA

## Dynamic Offers

- Offers from source block: 168
- Offers by family: `{'BLS': 54, 'Heartsaver': 87, 'USCG': 27}`

## Selected Offer

- Offer ID: `offer-209806-instructor_24057895173-20260704-1200`
- Course: AHA BLS Provider
- Time: 2026-07-04 12:00-14:00
- Location: 4018 Shipyard Blvd\, Wilmington\, NC 28403\, USA

## Filter Checks

| Check | Passed | Reason | Details |
| --- | --- | --- | --- |
| `course_family_enabled` | True | `` | `{"family": "BLS", "enabled_course_families": ["ACLS", "BLS", "Heartsaver", "PALS"]}` |
| `course_family_not_disabled` | True | `` | `{"family": "BLS", "disabled_course_families": ["ARC", "HSI", "USCG"]}` |
| `course_id_enabled` | True | `` | `{"course_id": "209806", "enabled_course_ids": []}` |
| `course_id_not_disabled` | True | `` | `{"course_id": "209806", "disabled_course_ids": []}` |
| `start_minute_allowed` | True | `` | `{"start_time": "12:00", "minute": "00", "allowed_start_minutes": ["00", "30"]}` |
| `lead_time` | True | `` | `{"now": "2026-06-19T17:04:20.038220", "minimum_lead_hours": 24, "offer_start": "2026-07-04T12:00:00"}` |
| `max_days_out` | True | `` | `{"now": "2026-06-19T17:04:20.038220", "maximum_days_out": 60, "offer_start": "2026-07-04T12:00:00"}` |
| `appointment_allowed` | True | `` | `{"course_id": "209806", "appointment_allowed": true}` |
| `confirmed_container_policy_enabled` | True | `` | `{"require_confirmed_appointment_container": true}` |
| `instructor_match` | True | `` | `{"active_container_instructors": ["Brian"], "offer_instructor": "Brian Ennis"}` |
| `normalized_location_match` | False | `location_mismatch` | `{"offer_location": "4018 Shipyard Blvd\\, Wilmington\\, NC 28403\\, USA", "active_container_locations": ["NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office"], "container_traces": [{"container_id": "shipyard_brian_continuous_20260621_20270430", "normalized_location_comparison": {"offer": "4018 Shipyard Blvd\\, Wilmington\\, NC 28403\\, USA", "container": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office", "passed": false}}]}` |
| `date_range` | False | `date_outside_container_range` | `{"offer_date": "2026-07-04", "matching_location_container_ids": []}` |

## Container Trace

### shipyard_brian_continuous_20260621_20270430

- Instructor match: True (`Brian Ennis` vs `Brian`)
- Raw location match: False (`4018 Shipyard Blvd\, Wilmington\, NC 28403\, USA` vs `NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office`)
- Normalized location match: False (`4018 Shipyard Blvd\, Wilmington\, NC 28403\, USA` vs `NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office`)
- Resource match: False (`4018 Shipyard Blvd\, Wilmington\, NC 28403\, USA` vs `Shipyard Office`)
- Date range match: True
- Computed appointmentDayId: `260683`; in range: True

## Result

- First failing comparison: `normalized_location_match`
- Reason code: `location_mismatch`
- Filter container rejection reason: `location_mismatch`
- Smallest safe fix: Add a location alias mapping for the Google event location to the canonical Shipyard location. The actual offer location is "4018 Shipyard Blvd\, Wilmington\, NC 28403\, USA"; the user-facing short alias "4018 Shipyard Blvd" alone will not match this exact normalized string unless matching is broadened.

No fix was applied in this trace step.
