# BLS Block-Based Schedule Pilot

Local build artifact for the customer-facing BLS pilot. Enrollware was not called, course IDs were not changed, and appointment URL behavior uses the existing URL builder.

## Summary

- Availability source used: `live_availability_snapshot`
- Availability fallback used: `False`
- Horizon days: `180`
- Minimum lead hours: `24`
- Whole block presented as class: `False`
- Public-selectable offers: `1573`
- Public-selectable dates: `39`
- Public-selectable start times: `567`
- Rejected course/start evaluations: `4028`

## Sample Public-Selectable URLs

| Date | Start | Course | appointmentDayId | URL |
| --- | --- | --- | ---: | --- |
| 2026-07-03 | 9:30 AM | AHA BLS Provider (`209806`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=9%3A30%20AM&courseId=209806` |
| 2026-07-03 | 9:30 AM | AHA BLS Provider Renewal (`359474`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=9%3A30%20AM&courseId=359474` |
| 2026-07-03 | 9:30 AM | AHA HeartCode BLS (`210549`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=9%3A30%20AM&courseId=210549` |
| 2026-07-03 | 10:00 AM | AHA HeartCode BLS (`210549`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=10%3A00%20AM&courseId=210549` |
| 2026-07-03 | 10:30 AM | AHA HeartCode BLS (`210549`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=10%3A30%20AM&courseId=210549` |
| 2026-07-03 | 2:30 PM | AHA BLS Provider (`209806`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=2%3A30%20PM&courseId=209806` |
| 2026-07-03 | 2:30 PM | AHA BLS Provider Renewal (`359474`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=2%3A30%20PM&courseId=359474` |
| 2026-07-03 | 2:30 PM | AHA HeartCode BLS (`210549`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=2%3A30%20PM&courseId=210549` |
| 2026-07-03 | 3:00 PM | AHA BLS Provider (`209806`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=3%3A00%20PM&courseId=209806` |
| 2026-07-03 | 3:00 PM | AHA BLS Provider Renewal (`359474`) | 260682 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=3%3A00%20PM&courseId=359474` |

## Top Rejection Reasons

- `outside_public_dynamic_hours`: 2874
- `conflicts_with_existing_enrollware_occupancy`: 1309
- `does_not_fit_inside_availability_after_duration_and_buffers`: 356
- `inside_minimum_lead_time`: 108

## Source Files

- `liveAvailabilitySnapshot`: `E:\GitHub\910cpr-class-landers\data\audit\live_availability_snapshot_preview.json`
- `legacyAvailabilityFallback`: `E:\GitHub\910cpr-class-landers\data\inventory\instructor_availability.json`
- `courseConsumptionRules`: `E:\GitHub\910cpr-class-landers\data\inventory\course_consumption_rules.json`
- `courseCatalog`: `E:\GitHub\910cpr-class-landers\data\config\course_catalog.json`
- `peopleCatalog`: `E:\GitHub\910cpr-class-landers\data\config\people_catalog.json`
- `publicOfferPolicy`: `E:\GitHub\910cpr-class-landers\data\config\public_offer_policy.json`
- `publicLocationPolicy`: `E:\GitHub\910cpr-class-landers\data\config\public_location_policy.json`
- `appointmentContainers`: `E:\GitHub\910cpr-class-landers\data\inventory\appointment_containers.json`
- `sessionsCurrent`: `E:\GitHub\910cpr-class-landers\data\sessions_current.json`
- `scheduleFuture`: `E:\GitHub\910cpr-class-landers\docs\data\schedule_future.json`
