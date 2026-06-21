# Seed Appointment Blocker Diagnosis

Read-only diagnosis. No public pages, Enrollware calls, appointments, appointment URL behavior, Worker routes, deploys, or commits were changed.

## Summary

- Blocked seeds reviewed: 9
- Active appointment containers: 1
- Blocked reason counts:
  - `no_matching_appointment_container`: 9
- Issue category counts:
  - `location mismatch`: 5
  - `missing container for instructor`: 4

## Instructors Involved

- Brian Ennis: 5
- Amy Arnold: 4

## Locations Involved

- 4045 College Rd\, Wilmington\, NC 28412\, USA: 2
- Wilmington International Airport\, 1740 Airport Blvd\, Wilmington\, NC 28405\, USA: 1
- NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office: 4
- 420 Windchime Dr\, Wilmington\, NC 28412\, USA: 2

## Courses Involved

- 209806 | AHA BLS Provider: 2
- 329495 | AHA Heartsaver First Aid CPR AED - Blended: 1
- 210549 | AHA HeartCode BLS: 2
- 209809 | AHA Heartsaver First Aid CPR AED: 3
- 209811 | AHA ACLS HeartCode: 1

## Per-Seed Diagnosis

### seed-offer-209806-instructor_24057895173-20260622-0600

- Date/time: 2026-06-22 06:00
- Course: 209806 | AHA BLS Provider
- Instructor: Brian Ennis
- Location: 4045 College Rd\, Wilmington\, NC 28412\, USA
- Blocking reason: `no_matching_appointment_container`
- Issue category: location mismatch

Candidate containers considered:

| Container | Instructor Match | Location Match | Date/ID In Range | Computed appointmentDayId | Why Not Matched |
| --- | --- | --- | --- | ---: | --- |
| shipyard_brian_continuous_20260621_20270430 | True | False | True | 260671 | location_mismatch |

### seed-offer-329495-instructor_24057895173-20260622-0630

- Date/time: 2026-06-22 06:30
- Course: 329495 | AHA Heartsaver First Aid CPR AED - Blended
- Instructor: Brian Ennis
- Location: 4045 College Rd\, Wilmington\, NC 28412\, USA
- Blocking reason: `no_matching_appointment_container`
- Issue category: location mismatch

Candidate containers considered:

| Container | Instructor Match | Location Match | Date/ID In Range | Computed appointmentDayId | Why Not Matched |
| --- | --- | --- | --- | ---: | --- |
| shipyard_brian_continuous_20260621_20270430 | True | False | True | 260671 | location_mismatch |

### seed-offer-210549-instructor_24057895173-20260623-0830

- Date/time: 2026-06-23 08:30
- Course: 210549 | AHA HeartCode BLS
- Instructor: Brian Ennis
- Location: Wilmington International Airport\, 1740 Airport Blvd\, Wilmington\, NC 28405\, USA
- Blocking reason: `no_matching_appointment_container`
- Issue category: location mismatch

Candidate containers considered:

| Container | Instructor Match | Location Match | Date/ID In Range | Computed appointmentDayId | Why Not Matched |
| --- | --- | --- | --- | ---: | --- |
| shipyard_brian_continuous_20260621_20270430 | True | False | True | 260672 | location_mismatch |

### seed-offer-209809-instructor_4180671442-20260623-1800

- Date/time: 2026-06-23 18:00
- Course: 209809 | AHA Heartsaver First Aid CPR AED
- Instructor: Amy Arnold
- Location: NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office
- Blocking reason: `no_matching_appointment_container`
- Issue category: missing container for instructor

Candidate containers considered:

| Container | Instructor Match | Location Match | Date/ID In Range | Computed appointmentDayId | Why Not Matched |
| --- | --- | --- | --- | ---: | --- |
| shipyard_brian_continuous_20260621_20270430 | False | True | True | 260672 | instructor_mismatch |

### seed-offer-210549-instructor_4180671442-20260626-1700

- Date/time: 2026-06-26 17:00
- Course: 210549 | AHA HeartCode BLS
- Instructor: Amy Arnold
- Location: NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office
- Blocking reason: `no_matching_appointment_container`
- Issue category: missing container for instructor

Candidate containers considered:

| Container | Instructor Match | Location Match | Date/ID In Range | Computed appointmentDayId | Why Not Matched |
| --- | --- | --- | --- | ---: | --- |
| shipyard_brian_continuous_20260621_20270430 | False | True | True | 260675 | instructor_mismatch |

### seed-offer-209809-instructor_4180671442-20260626-1800

- Date/time: 2026-06-26 18:00
- Course: 209809 | AHA Heartsaver First Aid CPR AED
- Instructor: Amy Arnold
- Location: NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office
- Blocking reason: `no_matching_appointment_container`
- Issue category: missing container for instructor

Candidate containers considered:

| Container | Instructor Match | Location Match | Date/ID In Range | Computed appointmentDayId | Why Not Matched |
| --- | --- | --- | --- | ---: | --- |
| shipyard_brian_continuous_20260621_20270430 | False | True | True | 260675 | instructor_mismatch |

### seed-offer-209811-instructor_4180671442-20260626-1830

- Date/time: 2026-06-26 18:30
- Course: 209811 | AHA ACLS HeartCode
- Instructor: Amy Arnold
- Location: NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office
- Blocking reason: `no_matching_appointment_container`
- Issue category: missing container for instructor

Candidate containers considered:

| Container | Instructor Match | Location Match | Date/ID In Range | Computed appointmentDayId | Why Not Matched |
| --- | --- | --- | --- | ---: | --- |
| shipyard_brian_continuous_20260621_20270430 | False | True | True | 260675 | instructor_mismatch |

### seed-offer-209806-instructor_24057895173-20260704-1630

- Date/time: 2026-07-04 16:30
- Course: 209806 | AHA BLS Provider
- Instructor: Brian Ennis
- Location: 420 Windchime Dr\, Wilmington\, NC 28412\, USA
- Blocking reason: `no_matching_appointment_container`
- Issue category: location mismatch

Candidate containers considered:

| Container | Instructor Match | Location Match | Date/ID In Range | Computed appointmentDayId | Why Not Matched |
| --- | --- | --- | --- | ---: | --- |
| shipyard_brian_continuous_20260621_20270430 | True | False | True | 260683 | location_mismatch |

### seed-offer-209809-instructor_24057895173-20260704-1700

- Date/time: 2026-07-04 17:00
- Course: 209809 | AHA Heartsaver First Aid CPR AED
- Instructor: Brian Ennis
- Location: 420 Windchime Dr\, Wilmington\, NC 28412\, USA
- Blocking reason: `no_matching_appointment_container`
- Issue category: location mismatch

Candidate containers considered:

| Container | Instructor Match | Location Match | Date/ID In Range | Computed appointmentDayId | Why Not Matched |
| --- | --- | --- | --- | ---: | --- |
| shipyard_brian_continuous_20260621_20270430 | True | False | True | 260683 | location_mismatch |

## Recommended Config-Only Fixes

- Add or confirm appointment containers for Amy Arnold if Amy-owned deterministic appointment URLs should be previewable.
- Add or confirm appointment containers for Brian off-site locations if Brian public seeds should use those locations.
- Normalize live calendar event locations to the owned appointment container location only when the slot is truly intended for Shipyard Office appointments.
- Consider filtering seed selection to appointment-container-backed locations until new containers are validated.

## Primary Finding

The live-calendar seed pipeline is producing valid-looking seeds at locations/instructors that do not have matching deterministic appointment containers. The existing appointment container inventory currently has one active container: Brian at the Shipyard office. Seeds for Amy, and Brian seeds at College Road, ILM airport, or Windchime Drive, cannot build deterministic appointment URLs from that single container.
