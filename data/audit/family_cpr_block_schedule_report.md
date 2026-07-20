# Family & Friends CPR

Local build artifact for a customer-facing block schedule page. Enrollware was not called, course IDs were not changed, and appointment URL behavior uses the existing URL builder.

## Summary

- Availability source used: `live_availability_snapshot`
- Availability fallback used: `False`
- Horizon days: `180`
- Minimum lead hours: `24`
- Whole block presented as class: `False`
- Public-selectable offers: `54`
- Public-selectable dates: `53`
- Public-selectable start times: `54`
- Rejected course/start evaluations: `4824`
- Suppressed stale/orphaned offers: `0`

## Sample Public-Selectable URLs

| Date | Start | Course | appointmentDayId | URL |
| --- | --- | --- | ---: | --- |
| 2026-07-22 | 6:00 PM | Family & Friends CPR (`252737`) | 260701 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260701&startTime=6%3A00%20PM&courseId=252737` |
| 2026-07-23 | 12:30 PM | Family & Friends CPR (`252737`) | 260702 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260702&startTime=12%3A30%20PM&courseId=252737` |
| 2026-07-24 | 8:30 AM | Family & Friends CPR (`252737`) | 260703 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260703&startTime=8%3A30%20AM&courseId=252737` |
| 2026-07-27 | 8:30 AM | Family & Friends CPR (`252737`) | 260706 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260706&startTime=8%3A30%20AM&courseId=252737` |
| 2026-07-28 | 2:30 PM | Family & Friends CPR (`252737`) | 260707 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260707&startTime=2%3A30%20PM&courseId=252737` |
| 2026-07-30 | 8:30 AM | Family & Friends CPR (`252737`) | 260709 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260709&startTime=8%3A30%20AM&courseId=252737` |
| 2026-08-03 | 6:00 PM | Family & Friends CPR (`252737`) | 260713 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260713&startTime=6%3A00%20PM&courseId=252737` |
| 2026-08-04 | 6:00 PM | Family & Friends CPR (`252737`) | 260714 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260714&startTime=6%3A00%20PM&courseId=252737` |
| 2026-08-05 | 8:00 AM | Family & Friends CPR (`252737`) | 260715 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260715&startTime=8%3A00%20AM&courseId=252737` |
| 2026-08-10 | 8:00 AM | Family & Friends CPR (`252737`) | 260720 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260720&startTime=8%3A00%20AM&courseId=252737` |

## Top Rejection Reasons

- `outside_public_dynamic_hours`: 2675
- `max_offers_per_course_per_week_exceeded`: 1782
- `does_not_fit_inside_availability_after_duration_and_buffers`: 826
- `conflicts_with_existing_enrollware_occupancy`: 588
- `inside_minimum_lead_time`: 43

## Final Live Availability Guard

- Enabled: `True`
- Rendered dates: `2026-07-22, 2026-07-23, 2026-07-24, 2026-07-27, 2026-07-28, 2026-07-30, 2026-08-03, 2026-08-04, 2026-08-05, 2026-08-10, 2026-08-11, 2026-08-12, 2026-08-17, 2026-08-18, 2026-08-19, 2026-08-24, 2026-08-25, 2026-08-26, 2026-08-31, 2026-09-01, 2026-09-02, 2026-09-07, 2026-09-08, 2026-09-09, 2026-09-14, 2026-09-15, 2026-09-16, 2026-09-21, 2026-09-22, 2026-09-23, 2026-09-28, 2026-09-29, 2026-09-30, 2026-10-05, 2026-10-06, 2026-10-07, 2026-10-12, 2026-10-13, 2026-10-14, 2026-10-19, 2026-10-20, 2026-10-21, 2026-10-26, 2026-10-27, 2026-10-28, 2026-11-02, 2026-11-03, 2026-11-04, 2026-11-09, 2026-11-10, 2026-11-11, 2026-11-16, 2026-11-17`
- Source blocks used: `53`
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
