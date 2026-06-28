# HSI Course ID / Container Unlock Plan

Generated: 2026-06-28T14:39:38

## Direct Answers

- **safe_course_ids_to_add_to_enabled_course_ids**: `["371954", "374378", "422270", "449422", "463743"]`
- **course_ids_lacking_confirmed_brian_appointment_containers**: `[]`
- **course_ids_with_containers_but_still_blocked**: `["344085", "371954", "374378", "422270", "445670", "449422", "463743"]`
- **missing_or_incomplete_card_page_mappings**: `[]`
- **expected_additional_public_sellable_if_safe_ids_enabled**: `15`
- **expected_additional_rendered_if_safe_ids_enabled**: `"requires rerun; likely <= additional public sellable after anchor-stack compaction"`
- **wrong_course_location_time_risk**: `"Sample URLs for already container-supported IDs are likely low risk but must be manually opened only to verify course/location/time, never submitted. IDs without confirmed containers are high risk for wrong-course/wrong-time behavior."`

## Course/Card Matrix

| Card | courseId | Course name | ID enabled | Family enabled | Generated | Public | Rendered | Reasons | Container | appointmentDayId | URL constructable | Mapping | Risk | Action |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| HSI BLS | `463743` | HSI BLS Challenge | False | True | 35 | 0 | 0 | `{"course_id_not_enabled": 35, "inside_minimum_lead_time": 30, "outside_public_dynamic_hours": 7}` | True | 260670, 260671, 260672, 260683 | True | present | medium | safe_after_brian_approval_add_course_id_only |
| HSI BLS + Adult First Aid | `445670` | HSI BLS and Adult First Aid | Blended Learning | True | True | 35 | 3 | 1 | `{"inside_minimum_lead_time": 30, "outside_public_dynamic_hours": 7, "max_offers_per_course_per_week_exceeded": 2}` | True | 260670, 260671, 260672, 260683 | True | present | low | safe_now_already_enabled_container_supported |
| HSI First Aid CPR AED | `371954` | HSI Adult First Aid | CPR AED - Blended Learning | False | True | 35 | 0 | 0 | `{"course_id_not_enabled": 35, "inside_minimum_lead_time": 30, "outside_public_dynamic_hours": 7}` | True | 260670, 260671, 260672, 260683 | True | present | medium | safe_after_brian_approval_add_course_id_only |
| HSI First Aid CPR AED | `374378` | HSI Adult First Aid | CPR AED | False | True | 4 | 0 | 0 | `{"course_id_not_enabled": 4, "inside_minimum_lead_time": 4}` | True | 260670, 260671 | True | present | medium | safe_after_brian_approval_add_course_id_only |
| HSI First Aid CPR AED | `422270` | HSI Adult First Aid | CPR AED | False | True | 4 | 0 | 0 | `{"course_id_not_enabled": 4, "inside_minimum_lead_time": 4}` | True | 260670, 260671 | True | present | medium | safe_after_brian_approval_add_course_id_only |
| HSI First Aid CPR AED | `449422` | HSI Pediatric First Aid | CPR AED - Blended | False | True | 35 | 0 | 0 | `{"course_id_not_enabled": 35, "inside_minimum_lead_time": 30, "outside_public_dynamic_hours": 7}` | True | 260670, 260671, 260672, 260683 | True | present | medium | safe_after_brian_approval_add_course_id_only |
| HSI CPR AED | `344085` | AHA Heartsaver CPR AED | True | True | 20 | 2 | 1 | `{"inside_minimum_lead_time": 18, "outside_public_dynamic_hours": 2}` | True | 260670, 260671, 260683 | True | present | low | safe_now_already_enabled_container_supported |

## Sample Enrollware Appointment URLs

### HSI BLS / 463743
- `2026-06-22T06:00:00` appointmentDayId `260671`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=463743&appointmentDayId=260671 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
- `2026-06-22T06:15:00` appointmentDayId `260671`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=463743&appointmentDayId=260671 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
- `2026-06-22T06:30:00` appointmentDayId `260671`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=463743&appointmentDayId=260671 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
### HSI BLS + Adult First Aid / 445670
- `2026-07-04T14:30:00` appointmentDayId `260683`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=445670&appointmentDayId=260683 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
- `2026-07-04T14:45:00` appointmentDayId `260683`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=445670&appointmentDayId=260683 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
- `2026-07-04T15:00:00` appointmentDayId `260683`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=445670&appointmentDayId=260683 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
### HSI First Aid CPR AED / 371954
- `2026-06-22T06:00:00` appointmentDayId `260671`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=371954&appointmentDayId=260671 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
- `2026-06-22T06:15:00` appointmentDayId `260671`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=371954&appointmentDayId=260671 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
- `2026-06-22T06:30:00` appointmentDayId `260671`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=371954&appointmentDayId=260671 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
### HSI First Aid CPR AED / 374378
- `2026-06-22T12:00:00` appointmentDayId `260671`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=374378&appointmentDayId=260671 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
- `2026-06-22T12:15:00` appointmentDayId `260671`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=374378&appointmentDayId=260671 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
- `2026-06-21T17:00:00` appointmentDayId `260670`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=374378&appointmentDayId=260670 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
### HSI First Aid CPR AED / 422270
- `2026-06-22T12:00:00` appointmentDayId `260671`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=422270&appointmentDayId=260671 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
- `2026-06-22T12:15:00` appointmentDayId `260671`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=422270&appointmentDayId=260671 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
- `2026-06-21T17:00:00` appointmentDayId `260670`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=422270&appointmentDayId=260670 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
### HSI First Aid CPR AED / 449422
- `2026-06-22T06:00:00` appointmentDayId `260671`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=449422&appointmentDayId=260671 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
- `2026-06-22T06:15:00` appointmentDayId `260671`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=449422&appointmentDayId=260671 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
- `2026-06-22T06:30:00` appointmentDayId `260671`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=449422&appointmentDayId=260671 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
### HSI CPR AED / 344085
- `2026-07-04T14:30:00` appointmentDayId `260683`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=344085&appointmentDayId=260683 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)
- `2026-07-04T14:45:00` appointmentDayId `260683`: https://www.enrollware.com/sitefiles/expresstraining/olr.cgi?course=344085&appointmentDayId=260683 (low if Enrollware appointmentDayId is truly course-compatible; verify manually before submit)

## Prioritized HSI Unlock List

### Safe now
- `445670` HSI BLS + Adult First Aid - safe_now_already_enabled_container_supported
- `344085` HSI CPR AED - safe_now_already_enabled_container_supported

### Safe after Brian approval
- `463743` HSI BLS - Add 463743 to data/config/public_offer_policy.json enabled_course_ids
- `371954` HSI First Aid CPR AED - Add 371954 to data/config/public_offer_policy.json enabled_course_ids
- `374378` HSI First Aid CPR AED - Add 374378 to data/config/public_offer_policy.json enabled_course_ids
- `422270` HSI First Aid CPR AED - Add 422270 to data/config/public_offer_policy.json enabled_course_ids
- `449422` HSI First Aid CPR AED - Add 449422 to data/config/public_offer_policy.json enabled_course_ids

### Needs container mapping
- None

### Needs course/page mapping
- None

### Leave disabled intentionally
- None identified by this audit.
