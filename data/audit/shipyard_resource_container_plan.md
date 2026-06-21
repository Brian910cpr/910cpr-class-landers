# Shipyard Resource / Appointment Container Capacity Plan

Review-only plan. No public pages, Enrollware calls, appointments, appointment URL behavior, Worker routes, deploys, or commits were changed.

## Public Location

- Customer-facing location: NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office
- Customer-facing display should remain one Shipyard office unless Brian explicitly wants internal room/resource labels shown.

## Internal Resources To Model

| Internal resource | Confirmed appointment container? | Safe for public dynamic use now? | Notes |
| --- | --- | --- | --- |
| :: Wilmington; Shipyard Blvd - C (Other) | False | False | No matching active appointment container is currently configured for this exact resource. |
| :: Wilmington; Shipyard Blvd - B | False | False | No matching active appointment container is currently configured for this exact resource. |
| :: Wilmington; Shipyard Blvd - A | False | False | No matching active appointment container is currently configured for this exact resource. |

## Currently Configured Shipyard Container

| Container ID | Instructor | Location | Room/Resource | Date Range | AppointmentDayId Range |
| --- | --- | --- | --- | --- | --- |
| `shipyard_brian_continuous_20260621_20270430` | Brian | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office | Shipyard Office | 2026-06-21 to 2027-04-30 | 260670 to 260983 |

## Can The Current Brian Shipyard Container Represent All 3 Resources?

- Conservative answer: **No, not yet.**
- Safe assumption: the current container represents only one public-resource lane until Brian/Enrollware confirms otherwise.
- Reason: the container is validated as an owned Brian/Shipyard range, but it does not explicitly identify A, B, or C. The deterministic appointment URL may encode resource behavior through `appointmentDayId`, so treating one range as three concurrent resources would be unsafe without proof.

## Overlap Checks

- Resource-level: allow overlap only when each class uses a different confirmed internal resource.
- Instructor-level: never allow the same instructor to overlap across resources.
- Public-location-level: Shipyard can show one public office while internally enforcing resource capacity.
- Unconfirmed resource behavior: do not generate public deterministic offers for unconfirmed resources.

## Customer-Facing Display

- Display as one Shipyard office: `NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office`.
- Do not expose A/B/C labels publicly unless needed for arrival instructions.
- Internal resource labels should stay in audit/admin data until Brian decides otherwise.

## Required Brian / Enrollware Confirmation

- Exact Enrollware location/resource names for A, B, and C.
- Whether each resource has its own appointment container / appointmentDayId range.
- First valid date and first valid appointmentDayId per resource.
- Last valid date, last valid appointmentDayId, and first invalid boundary per resource.
- Which instructors can use which resource for public dynamic scheduling.
- Whether customer-facing display should remain one Shipyard office for all resources.

## Safest Next Step

- Recommended now: `keep_one_shipyard_resource_until_tested`.
- Alternative after confirmation: add confirmed containers per resource for A, B, and C with explicit appointmentDayId ranges and tests.

Do not add containers just because a resource name exists. Add them only after Brian/Enrollware confirms deterministic URL behavior for that resource.
