# HSI CPR, First Aid & BLS Classes

Local build artifact for a customer-facing block schedule page. Enrollware was not called, course IDs were not changed, and appointment URL behavior uses the existing URL builder.

## Summary

- Availability source used: `live_availability_snapshot`
- Availability fallback used: `False`
- Horizon days: `180`
- Minimum lead hours: `24`
- Whole block presented as class: `False`
- Public-selectable offers: `913`
- Public-selectable dates: `31`
- Public-selectable start times: `462`
- Rejected course/start evaluations: `2651`
- Suppressed stale/orphaned offers: `0`

## Sample Public-Selectable URLs

| Date | Start | Course | appointmentDayId | URL |
| --- | --- | --- | ---: | --- |
| 2026-07-15 | 6:00 PM | HSI BLS + Adult First Aid (`445670`) | 260694 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260694&startTime=6%3A00%20PM&courseId=445670` |
| 2026-07-16 | 12:30 PM | HSI BLS Challenge (`463743`) | 260695 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260695&startTime=12%3A30%20PM&courseId=463743` |
| 2026-07-16 | 12:30 PM | HSI BLS + Adult First Aid (`445670`) | 260695 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260695&startTime=12%3A30%20PM&courseId=445670` |
| 2026-07-16 | 1:00 PM | HSI BLS Challenge (`463743`) | 260695 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260695&startTime=1%3A00%20PM&courseId=463743` |
| 2026-07-16 | 1:00 PM | HSI BLS + Adult First Aid (`445670`) | 260695 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260695&startTime=1%3A00%20PM&courseId=445670` |
| 2026-07-17 | 9:30 AM | HSI BLS Challenge (`463743`) | 260696 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260696&startTime=9%3A30%20AM&courseId=463743` |
| 2026-07-17 | 9:30 AM | HSI BLS + Adult First Aid (`445670`) | 260696 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260696&startTime=9%3A30%20AM&courseId=445670` |
| 2026-07-17 | 10:00 AM | HSI BLS Challenge (`463743`) | 260696 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260696&startTime=10%3A00%20AM&courseId=463743` |
| 2026-07-17 | 10:00 AM | HSI BLS + Adult First Aid (`445670`) | 260696 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260696&startTime=10%3A00%20AM&courseId=445670` |
| 2026-07-17 | 10:30 AM | HSI BLS Challenge (`463743`) | 260696 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260696&startTime=10%3A30%20AM&courseId=463743` |

## Top Rejection Reasons

- `outside_public_dynamic_hours`: 1780
- `starts_before_current_time`: 756
- `conflicts_with_existing_enrollware_occupancy`: 720
- `does_not_fit_inside_availability_after_duration_and_buffers`: 125
- `inside_minimum_lead_time`: 70

## Final Live Availability Guard

- Enabled: `True`
- Rendered dates: `2026-07-15, 2026-07-16, 2026-07-17, 2026-07-18, 2026-07-19, 2026-07-22, 2026-07-23, 2026-07-24, 2026-07-25, 2026-07-26, 2026-07-27, 2026-07-28, 2026-07-29, 2026-07-30, 2026-07-31, 2026-08-01, 2026-08-02, 2026-08-03, 2026-08-04, 2026-08-05, 2026-08-06, 2026-08-07, 2026-08-08, 2026-08-09, 2026-08-10, 2026-08-11, 2026-08-12, 2026-08-13, 2026-08-14, 2026-08-15, 2026-08-16`
- Source blocks used: `32`
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
