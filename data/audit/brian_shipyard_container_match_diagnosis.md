# Brian + Shipyard Container Match Diagnosis

Status: read-only diagnosis. No public pages, Enrollware calls, appointments, appointment URL changes, Worker routes, deploys, or commits were performed.

## Summary

- Brian + Shipyard live availability blocks found: 1
- Dynamic offers generated from those blocks: 0
- Dynamic offers with Brian + Shipyard labels: 0
- Public sellable offers kept overall: 0
- Issue classification: other: live block generated no dynamic offers tied to source window
- First failing comparison: none

## Public Filter Container Reasons Overall

- `missing_container_for_instructor`: 465
- `location_mismatch`: 229

## Source Brian + Shipyard Blocks

- source `4jgsd3masf2ccq7algku6rs7j8@google.com`: Brian Ennis / NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office / 2026-07-04 00:00-00:00

## Appointment Container Considered

- `shipyard_brian_continuous_20260621_20270430`: instructor `Brian`, location `NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office`, dates `2026-06-21` to `2027-04-30`, appointmentDayId `260670` to `260983`

## First Failing Comparison

- None found among source offers.


## Dynamic Rejections For Brian + Shipyard Source Block

The Brian + Shipyard live block exists, but it is normalized as `2026-07-04 00:00-00:00`, so no course can fit inside it. Dynamic offer generation rejects all courses for that source before public container matching can succeed.

Rejection counts for that source window:

- `course_family_not_allowed_by_window`: 18
- `course_does_not_fit_window`: 12

This means the first failing comparison is not the appointment container itself. It is the availability-window duration feeding the offer generator.

## Diagnosis

The live Brian + Shipyard block did not produce dynamic offers tied to that source window because the normalized block is zero-length (`00:00-00:00`). The first failure is upstream of container matching: availability-window duration versus course duration.

## Smallest Safe Fix

Fix the source calendar/snapshot interpretation so Brian inverse availability produces a real start/end Shipyard window, or remove the zero-length event from offerable availability. Do not change appointment container config until an offer from that block exists.
