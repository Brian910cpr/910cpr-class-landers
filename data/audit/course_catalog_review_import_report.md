# Course Catalog Review Import Report

- Generated at: 2026-06-18T23:08:36.879452-04:00
- Spreadsheet file read: `d:\Users\ten77\Downloads\Untitled11.csv`
- Worksheet: `Untitled11.csv`
- Header row: 1
- Rows processed: 37
- Rows updated: 30
- Rows skipped: 7

Safety: this import updates only scheduler-critical fields in `data/config/course_catalog.json` by matching `course_id`. It does not touch public pages, Enrollware behavior, appointment URLs, Worker settings, product systems, or generated HTML.

## Mapped Columns

- `appointment_allowed`
- `course_id`
- `default_capacity`
- `duration_minutes`
- `needs brian review?`
- `per participant resources`
- `required_instructor_certifications`
- `resources`
- `title`

## Fields Updated By Course

| Course ID | Title | Fields Updated |
|---|---|---|
| 209806 | AHA BLS Provider | required_instructor_certifications |
| 359474 | AHA BLS Provider Renewal | required_instructor_certifications |
| 210549 | AHA HeartCode BLS | required_instructor_certifications |
| 440431 | BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing) | duration_minutes, default_capacity, appointment_allowed, required_instructor_certifications |
| 209811 | AHA ACLS HeartCode | duration_minutes, required_instructor_certifications |
| 241108 | AHA ACLS Provider (Initial) | required_instructor_certifications |
| 209818 | AHA ACLS Provider (Renewal) | required_instructor_certifications |
| 209812 | AHA PALS HeartCode | duration_minutes, required_instructor_certifications |
| 209805 | AHA PALS Provider | required_instructor_certifications |
| 251496 | AHA PALS Renewal | required_instructor_certifications |
| 344085 | AHA Heartsaver CPR AED | duration_minutes, required_instructor_certifications |
| 209808 | AHA Heartsaver CPR AED Online | duration_minutes, default_capacity, appointment_allowed, required_instructor_certifications |
| 209809 | AHA Heartsaver First Aid CPR AED | duration_minutes, default_capacity, required_instructor_certifications |
| 329495 | AHA Heartsaver First Aid CPR AED - Blended | duration_minutes, default_capacity, appointment_allowed, required_instructor_certifications |
| 351632 | AHA Heartsaver Pediatric First Aid / CPR / AED | duration_minutes, default_capacity, appointment_allowed, required_instructor_certifications |
| 251545 | AHA Heartsaver Pediatric First Aid CPR AED Online | duration_minutes, default_capacity, required_instructor_certifications |
| 369209 | American Red Cross Adult and Pediatric First Aid/CPR/AED | duration_minutes, default_capacity, appointment_allowed, required_instructor_certifications |
| 410694 | American Red Cross Adult and Pediatric First Aid/CPR/AED Blended Learning | duration_minutes, default_capacity, appointment_allowed, required_instructor_certifications |
| 444919 | American Red Cross BLS Challenge | duration_minutes, default_capacity, appointment_allowed, required_instructor_certifications |
| 248288 | American Red Cross Basic Life Support | duration_minutes, required_instructor_certifications |
| 248287 | American Red Cross Basic Life Support - Blended Learning | duration_minutes, required_instructor_certifications |
| 374378 | HSI Adult First Aid / CPR AED | duration_minutes, default_capacity, appointment_allowed, required_instructor_certifications |
| 422270 | HSI Adult First Aid / CPR AED | duration_minutes, default_capacity, appointment_allowed, required_instructor_certifications |
| 371954 | HSI Adult First Aid / CPR AED - Blended Learning | duration_minutes, default_capacity, appointment_allowed, required_instructor_certifications |
| 463743 | HSI BLS Challenge | duration_minutes, default_capacity, required_instructor_certifications |
| 445670 | HSI BLS and Adult First Aid / Blended Learning | duration_minutes, default_capacity, appointment_allowed, required_instructor_certifications |
| 448630 | HSI Basic Life Support | duration_minutes, default_capacity, appointment_allowed, required_instructor_certifications |
| 449422 | HSI Pediatric First Aid / CPR AED - Blended | duration_minutes, default_capacity, appointment_allowed, required_instructor_certifications |
| 253768 | USCG Elementary First Aid / CPR (AHA Heartsaver) | duration_minutes, required_instructor_certifications |
| 359827 | USCG Elementary First Aid / CPR - Blended | duration_minutes, required_instructor_certifications |

## Skipped Rows

| Row | Course ID | Title | Reason |
|---:|---|---|---|
| 2 | AHA BLS |  | missing_course_id_or_group_row |
| 7 | AHA ACLS |  | missing_course_id_or_group_row |
| 11 | AHA PALS |  | missing_course_id_or_group_row |
| 15 | AHA Heartsaver |  | missing_course_id_or_group_row |
| 22 | ARC |  | missing_course_id_or_group_row |
| 28 | HSI |  | missing_course_id_or_group_row |
| 36 | USCG |  | missing_course_id_or_group_row |

## Unknowns Remaining After Import

### Missing Duration

- None

### Missing Capacity

- None

### Missing Appointment Allowed

- None

### Missing Required Instructor Certifications

- None
