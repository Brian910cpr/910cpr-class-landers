# PALS Certification Classes

Local build artifact for a customer-facing block schedule page. Enrollware was not called, course IDs were not changed, and appointment URL behavior uses the existing URL builder.

## Summary

- Availability source used: `live_availability_snapshot`
- Availability fallback used: `False`
- Horizon days: `180`
- Minimum lead hours: `24`
- Whole block presented as class: `False`
- Public-selectable offers: `4`
- Public-selectable dates: `2`
- Public-selectable start times: `2`
- Rejected course/start evaluations: `14634`
- Suppressed stale/orphaned offers: `0`

## Sample Public-Selectable URLs

| Date | Start | Course | appointmentDayId | URL |
| --- | --- | --- | ---: | --- |
| 2026-07-29 | 2:00 PM | AHA PALS Provider (`209805`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673183` |
| 2026-07-29 | 2:00 PM | AHA PALS Renewal (`251496`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673194` |
| 2026-07-30 | 2:00 PM | AHA PALS Provider (`209805`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673184` |
| 2026-07-30 | 2:00 PM | AHA PALS Renewal (`251496`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673195` |

## Top Rejection Reasons

- `course_family_not_allowed_by_availability`: 14634
- `instructor_lacks_required_certification`: 14634
- `outside_public_dynamic_hours`: 8025
- `does_not_fit_inside_availability_after_duration_and_buffers`: 5538
- `conflicts_with_existing_enrollware_occupancy`: 3492
- `inside_minimum_lead_time`: 129

## Final Live Availability Guard

- Enabled: `True`
- Rendered dates: `2026-07-29, 2026-07-30`
- Source blocks used: `4`
- Suppressed available block dates: `none`
- Suppressed stale/orphaned offer dates: `none`

## Source Files

- `liveAvailabilitySnapshot`: `E:\GitHub\910cpr-class-landers\data\audit\live_availability_snapshot_preview.json`
- `courseConsumptionRules`: `E:\GitHub\910cpr-class-landers\data\inventory\course_consumption_rules.json`
- `courseCatalog`: `E:\GitHub\910cpr-class-landers\data\config\course_catalog.json`
- `peopleCatalog`: `E:\GitHub\910cpr-class-landers\data\config\people_catalog.json`
- `publicOfferPolicy`: `E:\GitHub\910cpr-class-landers\data\config\public_offer_policy.json`
- `publicLocationPolicy`: `E:\GitHub\910cpr-class-landers\data\config\public_location_policy.json`
- `appointmentContainers`: `E:\GitHub\910cpr-class-landers\data\inventory\appointment_containers.json`
- `sessionsCurrent`: `E:\GitHub\910cpr-class-landers\data\sessions_current.json`
- `scheduleFuture`: `E:\GitHub\910cpr-class-landers\docs\data\schedule_future.json`
- `blockSchedulePages`: `E:\GitHub\910cpr-class-landers\data\config\block_schedule_pages.json`
