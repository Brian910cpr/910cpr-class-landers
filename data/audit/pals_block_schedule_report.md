# PALS Certification Classes

Local build artifact for a customer-facing block schedule page. Enrollware was not called, course IDs were not changed, and appointment URL behavior uses the existing URL builder.

## Summary

- Availability source used: `live_availability_snapshot`
- Availability fallback used: `False`
- Horizon days: `180`
- Minimum lead hours: `24`
- Whole block presented as class: `False`
- Public-selectable offers: `12`
- Public-selectable dates: `6`
- Public-selectable start times: `6`
- Rejected course/start evaluations: `11043`
- Suppressed stale/orphaned offers: `0`

## Sample Public-Selectable URLs

| Date | Start | Course | appointmentDayId | URL |
| --- | --- | --- | ---: | --- |
| 2026-08-12 | 2:00 PM | AHA PALS Provider (`209805`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13828454` |
| 2026-08-12 | 2:00 PM | AHA PALS Renewal (`251496`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13828461` |
| 2026-08-13 | 2:00 PM | AHA PALS Provider (`209805`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13828455` |
| 2026-08-13 | 2:00 PM | AHA PALS Renewal (`251496`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13828462` |
| 2026-08-17 | 2:00 PM | AHA PALS Provider (`209805`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13828456` |
| 2026-08-17 | 2:00 PM | AHA PALS Renewal (`251496`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13828463` |
| 2026-08-18 | 2:00 PM | AHA PALS Provider (`209805`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13828457` |
| 2026-08-18 | 2:00 PM | AHA PALS Renewal (`251496`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13828464` |
| 2026-08-26 | 2:00 PM | AHA PALS Provider (`209805`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13828458` |
| 2026-08-26 | 2:00 PM | AHA PALS Renewal (`251496`) | None | `https://coastalcprtraining.enrollware.com/enroll?id=13828465` |

## Top Rejection Reasons

- `course_family_not_allowed_by_availability`: 11043
- `instructor_lacks_required_certification`: 11043
- `outside_public_dynamic_hours`: 5823
- `does_not_fit_inside_availability_after_duration_and_buffers`: 4401
- `conflicts_with_existing_enrollware_occupancy`: 3135
- `scheduled_day_already_has_public_class`: 732
- `inside_minimum_lead_time`: 132
- `starts_before_current_time`: 3

## Final Live Availability Guard

- Enabled: `True`
- Rendered dates: `2026-08-12, 2026-08-13, 2026-08-17, 2026-08-18, 2026-08-26, 2026-08-31`
- Source blocks used: `12`
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
