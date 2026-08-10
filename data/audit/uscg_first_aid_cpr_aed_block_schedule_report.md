# USCG-Approved First Aid / CPR / AED

Local build artifact for a customer-facing block schedule page. Enrollware was not called, course IDs were not changed, and appointment URL behavior uses the existing URL builder.

## Summary

- Availability source used: `live_availability_snapshot`
- Availability fallback used: `False`
- Horizon days: `180`
- Minimum lead hours: `24`
- Whole block presented as class: `False`
- Public-selectable offers: `2564`
- Public-selectable dates: `85`
- Public-selectable start times: `1316`
- Rejected course/start evaluations: `4801`
- Suppressed stale/orphaned offers: `0`

## Sample Public-Selectable URLs

| Date | Start | Course | appointmentDayId | URL |
| --- | --- | --- | ---: | --- |
| 2026-08-12 | 8:00 AM | In-person AHA Heartsaver First Aid CPR AED (`209809`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=8%3A00%20AM&courseId=209809` |
| 2026-08-12 | 8:00 AM | Online learning + in-person skills session (`329495`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=8%3A00%20AM&courseId=329495` |
| 2026-08-12 | 8:30 AM | In-person AHA Heartsaver First Aid CPR AED (`209809`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=8%3A30%20AM&courseId=209809` |
| 2026-08-12 | 8:30 AM | Online learning + in-person skills session (`329495`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=8%3A30%20AM&courseId=329495` |
| 2026-08-12 | 9:00 AM | In-person AHA Heartsaver First Aid CPR AED (`209809`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=9%3A00%20AM&courseId=209809` |
| 2026-08-12 | 9:00 AM | Online learning + in-person skills session (`329495`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=9%3A00%20AM&courseId=329495` |
| 2026-08-12 | 9:30 AM | In-person AHA Heartsaver First Aid CPR AED (`209809`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=9%3A30%20AM&courseId=209809` |
| 2026-08-12 | 9:30 AM | Online learning + in-person skills session (`329495`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=9%3A30%20AM&courseId=329495` |
| 2026-08-12 | 10:00 AM | In-person AHA Heartsaver First Aid CPR AED (`209809`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=10%3A00%20AM&courseId=209809` |
| 2026-08-12 | 10:00 AM | Online learning + in-person skills session (`329495`) | 260722 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260722&startTime=10%3A00%20AM&courseId=329495` |

## Top Rejection Reasons

- `outside_public_dynamic_hours`: 3882
- `does_not_fit_inside_availability_after_duration_and_buffers`: 1527
- `conflicts_with_existing_enrollware_occupancy`: 1226
- `scheduled_day_already_has_public_class`: 488
- `inside_minimum_lead_time`: 88
- `starts_before_current_time`: 2

## Final Live Availability Guard

- Enabled: `True`
- Rendered dates: `2026-08-12, 2026-08-14, 2026-08-16, 2026-08-17, 2026-08-18, 2026-08-19, 2026-08-20, 2026-08-21, 2026-08-22, 2026-08-23, 2026-08-25, 2026-08-26, 2026-08-27, 2026-08-28, 2026-08-29, 2026-08-30, 2026-08-31, 2026-09-01, 2026-09-02, 2026-09-03, 2026-09-04, 2026-09-05, 2026-09-06, 2026-09-07, 2026-09-08, 2026-09-09, 2026-09-10, 2026-09-11, 2026-09-12, 2026-09-13, 2026-09-14, 2026-09-15, 2026-09-16, 2026-09-17, 2026-09-18, 2026-09-19, 2026-09-20, 2026-09-21, 2026-09-22, 2026-09-23, 2026-09-24, 2026-09-25, 2026-09-26, 2026-09-27, 2026-09-28, 2026-09-29, 2026-09-30, 2026-10-01, 2026-10-02, 2026-10-03, 2026-10-04, 2026-10-05, 2026-10-06, 2026-10-07, 2026-10-08, 2026-10-09, 2026-10-10, 2026-10-11, 2026-10-12, 2026-10-13, 2026-10-14, 2026-10-15, 2026-10-16, 2026-10-17, 2026-10-18, 2026-10-19, 2026-10-20, 2026-10-21, 2026-10-22, 2026-10-23, 2026-10-24, 2026-10-25, 2026-10-26, 2026-10-27, 2026-10-28, 2026-10-29, 2026-10-30, 2026-10-31, 2026-11-01, 2026-11-02, 2026-11-03, 2026-11-04, 2026-11-05, 2026-11-06, 2026-11-07`
- Source blocks used: `141`
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
