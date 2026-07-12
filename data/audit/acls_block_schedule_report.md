# ACLS Schedule

Local build artifact for a customer-facing block schedule page. Enrollware was not called, course IDs were not changed, and appointment URL behavior uses the existing URL builder.

## Summary

- Availability source used: `live_availability_snapshot`
- Availability fallback used: `False`
- Horizon days: `180`
- Minimum lead hours: `24`
- Whole block presented as class: `False`
- Public-selectable offers: `14`
- Public-selectable dates: `7`
- Public-selectable start times: `7`
- Rejected course/start evaluations: `5346`
- Suppressed stale/orphaned offers: `0`

## Sample Public-Selectable URLs

| Date | Start | Course | appointmentDayId | URL |
| --- | --- | --- | ---: | --- |
| 2026-07-15 | 2:00 PM | AHA ACLS Provider (Initial) (`241108`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673159` |
| 2026-07-15 | 2:00 PM | AHA ACLS Provider (Renewal) (`209818`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673169` |
| 2026-07-16 | 2:00 PM | AHA ACLS Provider (Initial) (`241108`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673160` |
| 2026-07-16 | 2:00 PM | AHA ACLS Provider (Renewal) (`209818`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673170` |
| 2026-07-20 | 2:00 PM | AHA ACLS Provider (Initial) (`241108`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673161` |
| 2026-07-20 | 2:00 PM | AHA ACLS Provider (Renewal) (`209818`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673171` |
| 2026-07-21 | 2:00 PM | AHA ACLS Provider (Initial) (`241108`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673162` |
| 2026-07-21 | 2:00 PM | AHA ACLS Provider (Renewal) (`209818`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673172` |
| 2026-07-24 | 2:00 PM | AHA ACLS Provider (Initial) (`241108`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673163` |
| 2026-07-24 | 2:00 PM | AHA ACLS Provider (Renewal) (`209818`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673173` |

## Top Rejection Reasons

- `course_family_not_allowed_by_availability`: 5346
- `instructor_lacks_required_certification`: 5346
- `outside_public_dynamic_hours`: 2670
- `conflicts_with_existing_enrollware_occupancy`: 1779
- `does_not_fit_inside_availability_after_duration_and_buffers`: 1293
- `inside_minimum_lead_time`: 12

## Final Live Availability Guard

- Enabled: `True`
- Rendered dates: `2026-07-15, 2026-07-16, 2026-07-20, 2026-07-21, 2026-07-24, 2026-07-29, 2026-07-30`
- Source blocks used: `14`
- Suppressed available block dates: `none`
- Suppressed stale/orphaned offer dates: `none`

## Source Files

- `liveAvailabilitySnapshot`: `E:\lw-emergency\data\audit\live_availability_snapshot_preview.json`
- `courseConsumptionRules`: `E:\lw-emergency\data\inventory\course_consumption_rules.json`
- `courseCatalog`: `E:\lw-emergency\data\config\course_catalog.json`
- `peopleCatalog`: `E:\lw-emergency\data\config\people_catalog.json`
- `publicOfferPolicy`: `E:\lw-emergency\data\config\public_offer_policy.json`
- `publicLocationPolicy`: `E:\lw-emergency\data\config\public_location_policy.json`
- `appointmentContainers`: `E:\lw-emergency\data\inventory\appointment_containers.json`
- `sessionsCurrent`: `E:\lw-emergency\data\sessions_current.json`
- `scheduleFuture`: `E:\lw-emergency\docs\data\schedule_future.json`
- `blockSchedulePages`: `E:\lw-emergency\data\config\block_schedule_pages.json`
