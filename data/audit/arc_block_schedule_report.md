# Red Cross CPR & BLS Classes

Local build artifact for a customer-facing block schedule page. Enrollware was not called, course IDs were not changed, and appointment URL behavior uses the existing URL builder.

## Summary

- Availability source used: `live_availability_snapshot`
- Availability fallback used: `False`
- Horizon days: `180`
- Minimum lead hours: `24`
- Whole block presented as class: `False`
- Public-selectable offers: `2673`
- Public-selectable dates: `85`
- Public-selectable start times: `981`
- Rejected course/start evaluations: `7800`
- Suppressed stale/orphaned offers: `0`

## Sample Public-Selectable URLs

| Date | Start | Course | appointmentDayId | URL |
| --- | --- | --- | ---: | --- |
| 2026-07-23 | 12:30 PM | American Red Cross Basic Life Support (`248288`) | 260702 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260702&startTime=12%3A30%20PM&courseId=248288` |
| 2026-07-23 | 12:30 PM | American Red Cross Adult CPR/AED (`372258`) | 260702 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260702&startTime=12%3A30%20PM&courseId=372258` |
| 2026-07-23 | 12:30 PM | American Red Cross First Aid/CPR/AED (`369209`) | 260702 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260702&startTime=12%3A30%20PM&courseId=369209` |
| 2026-07-23 | 1:00 PM | American Red Cross Basic Life Support (`248288`) | 260702 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260702&startTime=1%3A00%20PM&courseId=248288` |
| 2026-07-23 | 1:00 PM | American Red Cross Adult CPR/AED (`372258`) | 260702 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260702&startTime=1%3A00%20PM&courseId=372258` |
| 2026-07-23 | 1:00 PM | American Red Cross First Aid/CPR/AED (`369209`) | 260702 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260702&startTime=1%3A00%20PM&courseId=369209` |
| 2026-07-23 | 1:30 PM | American Red Cross Basic Life Support (`248288`) | 260702 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260702&startTime=1%3A30%20PM&courseId=248288` |
| 2026-07-23 | 1:30 PM | American Red Cross Adult CPR/AED (`372258`) | 260702 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260702&startTime=1%3A30%20PM&courseId=372258` |
| 2026-07-23 | 1:30 PM | American Red Cross First Aid/CPR/AED (`369209`) | 260702 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260702&startTime=1%3A30%20PM&courseId=369209` |
| 2026-07-23 | 2:00 PM | American Red Cross Basic Life Support (`248288`) | 260702 | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260702&startTime=2%3A00%20PM&courseId=248288` |

## Top Rejection Reasons

- `outside_public_dynamic_hours`: 5718
- `conflicts_with_brian_travel_buffer`: 1623
- `does_not_fit_inside_availability_after_duration_and_buffers`: 1452
- `conflicts_with_existing_enrollware_occupancy`: 1358
- `inside_minimum_lead_time`: 147

## Final Live Availability Guard

- Enabled: `True`
- Rendered dates: `2026-07-23, 2026-07-24, 2026-07-25, 2026-07-26, 2026-07-27, 2026-07-28, 2026-07-30, 2026-07-31, 2026-08-01, 2026-08-02, 2026-08-03, 2026-08-04, 2026-08-05, 2026-08-06, 2026-08-07, 2026-08-08, 2026-08-09, 2026-08-10, 2026-08-11, 2026-08-12, 2026-08-13, 2026-08-14, 2026-08-15, 2026-08-16, 2026-08-17, 2026-08-18, 2026-08-19, 2026-08-20, 2026-08-21, 2026-08-22, 2026-08-23, 2026-08-24, 2026-08-25, 2026-08-26, 2026-08-27, 2026-08-28, 2026-08-29, 2026-08-30, 2026-08-31, 2026-09-01, 2026-09-02, 2026-09-03, 2026-09-04, 2026-09-05, 2026-09-06, 2026-09-07, 2026-09-08, 2026-09-09, 2026-09-10, 2026-09-11, 2026-09-12, 2026-09-13, 2026-09-14, 2026-09-15, 2026-09-16, 2026-09-17, 2026-09-18, 2026-09-19, 2026-09-20, 2026-09-21, 2026-09-22, 2026-09-23, 2026-09-24, 2026-09-25, 2026-09-26, 2026-09-27, 2026-09-28, 2026-09-29, 2026-09-30, 2026-10-01, 2026-10-02, 2026-10-03, 2026-10-04, 2026-10-05, 2026-10-06, 2026-10-07, 2026-10-08, 2026-10-09, 2026-10-10, 2026-10-11, 2026-10-12, 2026-10-13, 2026-10-14, 2026-10-15, 2026-10-16`
- Source blocks used: `123`
- Suppressed available block dates: `none`
- Suppressed stale/orphaned offer dates: `none`

## Source Files

- `liveAvailabilitySnapshot`: `E:\GitHub\910cpr-class-landers_arc_selector\data\audit\live_availability_snapshot_preview.json`
- `courseConsumptionRules`: `E:\GitHub\910cpr-class-landers_arc_selector\data\inventory\course_consumption_rules.json`
- `courseCatalog`: `E:\GitHub\910cpr-class-landers_arc_selector\data\config\course_catalog.json`
- `peopleCatalog`: `E:\GitHub\910cpr-class-landers_arc_selector\data\config\people_catalog.json`
- `publicOfferPolicy`: `E:\GitHub\910cpr-class-landers_arc_selector\data\config\public_offer_policy.json`
- `publicLocationPolicy`: `E:\GitHub\910cpr-class-landers_arc_selector\data\config\public_location_policy.json`
- `appointmentContainers`: `E:\GitHub\910cpr-class-landers_arc_selector\data\inventory\appointment_containers.json`
- `sessionsCurrent`: `E:\GitHub\910cpr-class-landers_arc_selector\data\sessions_current.json`
- `scheduleFuture`: `E:\GitHub\910cpr-class-landers_arc_selector\docs\data\schedule_future.json`
- `blockSchedulePages`: `E:\GitHub\910cpr-class-landers_arc_selector\data\config\block_schedule_pages.json`
