# Family & Friends CPR

Local build artifact for a customer-facing block schedule page. Enrollware was not called, course IDs were not changed, and appointment URL behavior uses the existing URL builder.

## Summary

- Availability source used: `live_availability_snapshot`
- Availability fallback used: `False`
- Horizon days: `180`
- Minimum lead hours: `24`
- Whole block presented as class: `False`
- Public-selectable offers: `1313`
- Public-selectable dates: `83`
- Public-selectable start times: `1313`
- Rejected course/start evaluations: `2368`
- Suppressed stale/orphaned offers: `0`

## Sample Public-Selectable URLs

| Date | Start | Course | appointmentDayId | URL |
| --- | --- | --- | ---: | --- |
| 2026-08-12 | 8:00 AM | Family & Friends CPR (`252737`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=8%3A00%20AM&courseId=252737` |
| 2026-08-12 | 8:30 AM | Family & Friends CPR (`252737`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=8%3A30%20AM&courseId=252737` |
| 2026-08-12 | 9:00 AM | Family & Friends CPR (`252737`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=9%3A00%20AM&courseId=252737` |
| 2026-08-12 | 9:30 AM | Family & Friends CPR (`252737`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=9%3A30%20AM&courseId=252737` |
| 2026-08-12 | 10:00 AM | Family & Friends CPR (`252737`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=10%3A00%20AM&courseId=252737` |
| 2026-08-12 | 10:30 AM | Family & Friends CPR (`252737`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=10%3A30%20AM&courseId=252737` |
| 2026-08-12 | 11:00 AM | Family & Friends CPR (`252737`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=11%3A00%20AM&courseId=252737` |
| 2026-08-12 | 11:30 AM | Family & Friends CPR (`252737`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=11%3A30%20AM&courseId=252737` |
| 2026-08-12 | 12:00 PM | Family & Friends CPR (`252737`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=12%3A00%20PM&courseId=252737` |
| 2026-08-16 | 8:00 AM | Family & Friends CPR (`252737`) | 260726 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260726&startTime=8%3A00%20AM&courseId=252737` |

## Top Rejection Reasons

- `outside_public_dynamic_hours`: 1941
- `does_not_fit_inside_availability_after_duration_and_buffers`: 663
- `conflicts_with_existing_enrollware_occupancy`: 549
- `scheduled_day_already_has_public_class`: 244
- `inside_minimum_lead_time`: 44
- `starts_before_current_time`: 1

## Final Live Availability Guard

- Enabled: `True`
- Rendered dates: `2026-08-12, 2026-08-16, 2026-08-18, 2026-08-19, 2026-08-20, 2026-08-21, 2026-08-22, 2026-08-23, 2026-08-25, 2026-08-26, 2026-08-27, 2026-08-28, 2026-08-29, 2026-08-30, 2026-08-31, 2026-09-01, 2026-09-02, 2026-09-03, 2026-09-04, 2026-09-05, 2026-09-06, 2026-09-07, 2026-09-08, 2026-09-09, 2026-09-10, 2026-09-11, 2026-09-12, 2026-09-13, 2026-09-14, 2026-09-15, 2026-09-16, 2026-09-17, 2026-09-18, 2026-09-19, 2026-09-20, 2026-09-21, 2026-09-22, 2026-09-23, 2026-09-24, 2026-09-25, 2026-09-26, 2026-09-27, 2026-09-28, 2026-09-29, 2026-09-30, 2026-10-01, 2026-10-02, 2026-10-03, 2026-10-04, 2026-10-05, 2026-10-06, 2026-10-07, 2026-10-08, 2026-10-09, 2026-10-10, 2026-10-11, 2026-10-12, 2026-10-13, 2026-10-14, 2026-10-15, 2026-10-16, 2026-10-17, 2026-10-18, 2026-10-19, 2026-10-20, 2026-10-21, 2026-10-22, 2026-10-23, 2026-10-24, 2026-10-25, 2026-10-26, 2026-10-27, 2026-10-28, 2026-10-29, 2026-10-30, 2026-10-31, 2026-11-01, 2026-11-02, 2026-11-03, 2026-11-04, 2026-11-05, 2026-11-06, 2026-11-07`
- Source blocks used: `138`
- Suppressed available block dates: `none`
- Suppressed stale/orphaned offer dates: `none`

## Source Files

- `liveAvailabilitySnapshot`: `E:\GitHub\910cpr-class-landers-existing-inventory-final\data\audit\live_availability_snapshot_preview.json`
- `courseConsumptionRules`: `E:\GitHub\910cpr-class-landers-existing-inventory-final\data\inventory\course_consumption_rules.json`
- `courseCatalog`: `E:\GitHub\910cpr-class-landers-existing-inventory-final\data\config\course_catalog.json`
- `peopleCatalog`: `E:\GitHub\910cpr-class-landers-existing-inventory-final\data\config\people_catalog.json`
- `publicOfferPolicy`: `E:\GitHub\910cpr-class-landers-existing-inventory-final\data\config\public_offer_policy.json`
- `publicLocationPolicy`: `E:\GitHub\910cpr-class-landers-existing-inventory-final\data\config\public_location_policy.json`
- `appointmentContainers`: `E:\GitHub\910cpr-class-landers-existing-inventory-final\data\inventory\appointment_containers.json`
- `sessionsCurrent`: `E:\GitHub\910cpr-class-landers-existing-inventory-final\data\sessions_current.json`
- `scheduleFuture`: `E:\GitHub\910cpr-class-landers-existing-inventory-final\docs\data\schedule_future.json`
- `blockSchedulePages`: `E:\GitHub\910cpr-class-landers-existing-inventory-final\data\config\block_schedule_pages.json`
