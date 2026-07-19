# ACLS Certification Classes

Local build artifact for a customer-facing block schedule page. Enrollware was not called, course IDs were not changed, and appointment URL behavior uses the existing URL builder.

## Summary

- Availability source used: `live_availability_snapshot`
- Availability fallback used: `False`
- Horizon days: `180`
- Minimum lead hours: `24`
- Whole block presented as class: `False`
- Public-selectable offers: `6`
- Public-selectable dates: `4`
- Public-selectable start times: `4`
- Rejected course/start evaluations: `10473`
- Suppressed stale/orphaned offers: `0`

## Sample Public-Selectable URLs

| Date | Start | Course | appointmentDayId | URL |
| --- | --- | --- | ---: | --- |
| 2026-07-20 | 2:00 PM | AHA ACLS Provider (Initial) (`241108`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673161` |
| 2026-07-24 | 2:00 PM | AHA ACLS Provider (Renewal) (`209818`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673173` |
| 2026-07-29 | 2:00 PM | AHA ACLS Provider (Initial) (`241108`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673164` |
| 2026-07-29 | 2:00 PM | AHA ACLS Provider (Renewal) (`209818`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673174` |
| 2026-07-30 | 2:00 PM | AHA ACLS Provider (Initial) (`241108`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673165` |
| 2026-07-30 | 2:00 PM | AHA ACLS Provider (Renewal) (`209818`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13673175` |

## Top Rejection Reasons

- `course_family_not_allowed_by_availability`: 10473
- `instructor_lacks_required_certification`: 10473
- `outside_public_dynamic_hours`: 5718
- `does_not_fit_inside_availability_after_duration_and_buffers`: 3807
- `conflicts_with_existing_enrollware_occupancy`: 2718
- `conflicts_with_brian_travel_buffer`: 1614
- `starts_before_current_time`: 105
- `inside_minimum_lead_time`: 57

## Final Live Availability Guard

- Enabled: `True`
- Rendered dates: `2026-07-20, 2026-07-24, 2026-07-29, 2026-07-30`
- Source blocks used: `6`
- Suppressed available block dates: `none`
- Suppressed stale/orphaned offer dates: `none`

## Source Files

- `liveAvailabilitySnapshot`: `E:\GitHub\910cpr-class-landers_family_ctas\data\audit\live_availability_snapshot_preview.json`
- `courseConsumptionRules`: `E:\GitHub\910cpr-class-landers_family_ctas\data\inventory\course_consumption_rules.json`
- `courseCatalog`: `E:\GitHub\910cpr-class-landers_family_ctas\data\config\course_catalog.json`
- `peopleCatalog`: `E:\GitHub\910cpr-class-landers_family_ctas\data\config\people_catalog.json`
- `publicOfferPolicy`: `E:\GitHub\910cpr-class-landers_family_ctas\data\config\public_offer_policy.json`
- `publicLocationPolicy`: `E:\GitHub\910cpr-class-landers_family_ctas\data\config\public_location_policy.json`
- `appointmentContainers`: `E:\GitHub\910cpr-class-landers_family_ctas\data\inventory\appointment_containers.json`
- `sessionsCurrent`: `E:\GitHub\910cpr-class-landers_family_ctas\data\sessions_current.json`
- `scheduleFuture`: `E:\GitHub\910cpr-class-landers_family_ctas\docs\data\schedule_future.json`
- `blockSchedulePages`: `E:\GitHub\910cpr-class-landers_family_ctas\data\config\block_schedule_pages.json`
