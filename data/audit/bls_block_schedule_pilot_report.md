# BLS Certification Classes

Local build artifact for a customer-facing block schedule page. Enrollware was not called, course IDs were not changed, and appointment URL behavior uses the existing URL builder.

## Summary

- Availability source used: `live_availability_snapshot`
- Availability fallback used: `False`
- Horizon days: `180`
- Minimum lead hours: `24`
- Whole block presented as class: `False`
- Public-selectable offers: `2664`
- Public-selectable dates: `86`
- Public-selectable start times: `958`
- Rejected course/start evaluations: `7814`
- Suppressed stale/orphaned offers: `0`

## Sample Public-Selectable URLs

| Date | Start | Course | appointmentDayId | URL |
| --- | --- | --- | ---: | --- |
| 2026-07-26 | 8:00 AM | AHA BLS Provider (`209806`) | 260705 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260705&startTime=8%3A00%20AM&courseId=209806` |
| 2026-07-26 | 8:00 AM | AHA BLS Provider Renewal (`359474`) | 260705 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260705&startTime=8%3A00%20AM&courseId=359474` |
| 2026-07-26 | 8:00 AM | AHA HeartCode BLS (`210549`) | 260705 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260705&startTime=8%3A00%20AM&courseId=210549` |
| 2026-07-26 | 8:30 AM | AHA BLS Provider (`209806`) | 260705 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260705&startTime=8%3A30%20AM&courseId=209806` |
| 2026-07-26 | 8:30 AM | AHA BLS Provider Renewal (`359474`) | 260705 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260705&startTime=8%3A30%20AM&courseId=359474` |
| 2026-07-26 | 8:30 AM | AHA HeartCode BLS (`210549`) | 260705 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260705&startTime=8%3A30%20AM&courseId=210549` |
| 2026-07-26 | 9:00 AM | AHA BLS Provider (`209806`) | 260705 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260705&startTime=9%3A00%20AM&courseId=209806` |
| 2026-07-26 | 9:00 AM | AHA BLS Provider Renewal (`359474`) | 260705 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260705&startTime=9%3A00%20AM&courseId=359474` |
| 2026-07-26 | 9:00 AM | AHA HeartCode BLS (`210549`) | 260705 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260705&startTime=9%3A00%20AM&courseId=210549` |
| 2026-07-26 | 9:30 AM | AHA BLS Provider (`209806`) | 260705 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260705&startTime=9%3A30%20AM&courseId=209806` |

## Top Rejection Reasons

- `outside_public_dynamic_hours`: 5718
- `conflicts_with_brian_travel_buffer`: 1620
- `conflicts_with_existing_enrollware_occupancy`: 1284
- `does_not_fit_inside_availability_after_duration_and_buffers`: 1273
- `same_day_family_anchor_already_seated`: 474
- `starts_before_current_time`: 105
- `inside_minimum_lead_time`: 57

## Final Live Availability Guard

- Enabled: `True`
- Rendered dates: `2026-07-23, 2026-07-24, 2026-07-25, 2026-07-26, 2026-07-27, 2026-07-28, 2026-07-29, 2026-07-30, 2026-07-31, 2026-08-01, 2026-08-02, 2026-08-03, 2026-08-04, 2026-08-05, 2026-08-06, 2026-08-07, 2026-08-08, 2026-08-09, 2026-08-10, 2026-08-11, 2026-08-12, 2026-08-13, 2026-08-14, 2026-08-15, 2026-08-16, 2026-08-17, 2026-08-18, 2026-08-19, 2026-08-20, 2026-08-21, 2026-08-22, 2026-08-23, 2026-08-24, 2026-08-25, 2026-08-26, 2026-08-27, 2026-08-28, 2026-08-29, 2026-08-30, 2026-08-31, 2026-09-01, 2026-09-02, 2026-09-03, 2026-09-04, 2026-09-05, 2026-09-06, 2026-09-07, 2026-09-08, 2026-09-09, 2026-09-10, 2026-09-11, 2026-09-12, 2026-09-13, 2026-09-14, 2026-09-15, 2026-09-16, 2026-09-17, 2026-09-18, 2026-09-19, 2026-09-20, 2026-09-21, 2026-09-22, 2026-09-23, 2026-09-24, 2026-09-25, 2026-09-26, 2026-09-27, 2026-09-28, 2026-09-29, 2026-09-30, 2026-10-01, 2026-10-02, 2026-10-03, 2026-10-04, 2026-10-05, 2026-10-06, 2026-10-07, 2026-10-08, 2026-10-09, 2026-10-10, 2026-10-11, 2026-10-12, 2026-10-13, 2026-10-14, 2026-10-15, 2026-10-16`
- Source blocks used: `125`
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
