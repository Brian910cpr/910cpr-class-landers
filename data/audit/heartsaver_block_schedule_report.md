# BLS Block-Based Schedule Pilot

Local build artifact for the customer-facing BLS pilot. Enrollware was not called, course IDs were not changed, and appointment URL behavior uses the existing URL builder.

## Summary

- Availability source used: `live_availability_snapshot`
- Availability fallback used: `False`
- Horizon days: `180`
- Minimum lead hours: `24`
- Whole block presented as class: `False`
- Public-selectable offers: `3014`
- Public-selectable dates: `39`
- Public-selectable start times: `512`
- Rejected course/start evaluations: `7678`
- Suppressed stale/orphaned offers: `0`

## Sample Public-Selectable URLs

| Date | Start | Course | appointmentDayId | URL |
| --- | --- | --- | ---: | --- |
| 2026-07-03 | 9:30 AM | AHA Heartsaver CPR AED (`344085`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=9%3A30%20AM&courseId=344085` |
| 2026-07-03 | 9:30 AM | AHA Heartsaver CPR AED Online (`209808`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=9%3A30%20AM&courseId=209808` |
| 2026-07-03 | 9:30 AM | AHA Heartsaver First Aid CPR AED - Blended (`329495`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=9%3A30%20AM&courseId=329495` |
| 2026-07-03 | 9:30 AM | AHA Heartsaver Pediatric First Aid CPR AED (`251545`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=9%3A30%20AM&courseId=251545` |
| 2026-07-03 | 2:30 PM | AHA Heartsaver CPR AED (`344085`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=2%3A30%20PM&courseId=344085` |
| 2026-07-03 | 2:30 PM | AHA Heartsaver CPR AED Online (`209808`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=2%3A30%20PM&courseId=209808` |
| 2026-07-03 | 2:30 PM | AHA Heartsaver First Aid CPR AED (`209809`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=2%3A30%20PM&courseId=209809` |
| 2026-07-03 | 2:30 PM | AHA Heartsaver First Aid CPR AED - Blended (`329495`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=2%3A30%20PM&courseId=329495` |
| 2026-07-03 | 2:30 PM | AHA Heartsaver Pediatric First Aid / CPR / AED (`351632`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=2%3A30%20PM&courseId=351632` |
| 2026-07-03 | 2:30 PM | AHA Heartsaver Pediatric First Aid CPR AED (`251545`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=2%3A30%20PM&courseId=251545` |

## Top Rejection Reasons

- `outside_public_dynamic_hours`: 5340
- `conflicts_with_existing_enrollware_occupancy`: 2546
- `does_not_fit_inside_availability_after_duration_and_buffers`: 1246
- `inside_minimum_lead_time`: 24

## Final Live Availability Guard

- Enabled: `True`
- Rendered dates: `2026-07-03, 2026-07-05, 2026-07-06, 2026-07-07, 2026-07-09, 2026-07-10, 2026-07-11, 2026-07-12, 2026-07-13, 2026-07-14, 2026-07-16, 2026-07-17, 2026-07-18, 2026-07-19, 2026-07-20, 2026-07-23, 2026-07-24, 2026-07-25, 2026-07-26, 2026-07-27, 2026-07-28, 2026-07-30, 2026-07-31, 2026-08-01, 2026-08-02, 2026-08-03, 2026-08-04, 2026-08-05, 2026-08-06, 2026-08-07, 2026-08-08, 2026-08-09, 2026-08-10, 2026-08-11, 2026-08-12, 2026-08-13, 2026-08-14, 2026-08-15, 2026-08-16`
- Source blocks used: `40`
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
