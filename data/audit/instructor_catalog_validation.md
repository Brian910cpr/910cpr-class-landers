# Instructor Catalog Validation

This read-only validation summarizes the local instructor qualification model. It does not change public pages, Enrollware behavior, appointment URLs, Worker behavior, or generated HTML.

## Summary

- Instructors found: 7
- Active instructors: 3
- Known exact certification codes: 0
- Instructors with UNKNOWN certifications: 7

## Instructors

| Instructor | Active | Can Teach Families From Local Config | Exact Certifications | Source |
| --- | --- | --- | --- | --- |
| A.  Arnold | UNKNOWN | UNKNOWN | UNKNOWN | docs/data/schedule_future.json |
| Amy | True | ACLS, PALS | UNKNOWN | data/config/calendar_sources.json, data/inventory/instructor_availability.json |
| B.  Ennis | UNKNOWN | UNKNOWN | UNKNOWN | docs/data/schedule_future.json |
| BLS Sample Instructor | False | BLS, HeartCode, Heartsaver | UNKNOWN | data/inventory/instructor_availability.json |
| Brian | True | ACLS, BLS, Heartsaver, PALS, USCG | UNKNOWN | data/config/calendar_sources.json, data/inventory/appointment_containers.json, data/inventory/instructor_availability.json |
| N.  Tripp | UNKNOWN | UNKNOWN | UNKNOWN | docs/data/schedule_future.json |
| Nick | True | UNKNOWN | UNKNOWN | data/config/calendar_sources.json |

## Courses With No Exact Qualified Instructor In Catalog

| Course ID | Title | Required Certification |
| --- | --- | --- |
| 209811 | AHA ACLS HeartCode | AHA_ACLS_INSTRUCTOR |
| 241108 | AHA ACLS Provider (Initial) | AHA_ACLS_INSTRUCTOR |
| 209818 | AHA ACLS Provider (Renewal) | AHA_ACLS_INSTRUCTOR |
| 369209 | American Red Cross Adult and Pediatric First Aid/CPR/AED | ARC_BLS_INSTRUCTOR |
| 410694 | American Red Cross Adult and Pediatric First Aid/CPR/AED Blended Learning | ARC_BLS_INSTRUCTOR |
| 444919 | American Red Cross BLS Challenge | ARC_BLS_INSTRUCTOR |
| 248288 | American Red Cross Basic Life Support | ARC_BLS_INSTRUCTOR |
| 248287 | American Red Cross Basic Life Support - Blended Learning | ARC_BLS_INSTRUCTOR |
| 209806 | AHA BLS Provider | AHA_BLS_INSTRUCTOR |
| 359474 | AHA BLS Provider Renewal | AHA_BLS_INSTRUCTOR |
| 210549 | AHA HeartCode BLS | AHA_BLS_INSTRUCTOR |
| 440431 | BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing) | AHA_BLS_INSTRUCTOR |
| 374378 | HSI Adult First Aid | CPR AED | HSI_INSTRUCTOR |
| 422270 | HSI Adult First Aid | CPR AED | HSI_INSTRUCTOR |
| 371954 | HSI Adult First Aid | CPR AED - Blended Learning | HSI_INSTRUCTOR |
| 463743 | HSI BLS Challenge | HSI_INSTRUCTOR |
| 445670 | HSI BLS and Adult First Aid | Blended Learning | HSI_INSTRUCTOR |
| 448630 | HSI Basic Life Support | HSI_INSTRUCTOR |
| 449422 | HSI Pediatric First Aid | CPR AED - Blended | HSI_INSTRUCTOR |
| 344085 | AHA Heartsaver CPR AED | AHA_BLS_INSTRUCTOR |
| 209808 | AHA Heartsaver CPR AED Online | AHA_BLS_INSTRUCTOR |
| 209809 | AHA Heartsaver First Aid CPR AED | AHA_BLS_INSTRUCTOR |
| 329495 | AHA Heartsaver First Aid CPR AED - Blended | AHA_BLS_INSTRUCTOR |
| 351632 | AHA Heartsaver Pediatric First Aid / CPR / AED | AHA_BLS_INSTRUCTOR |
| 251545 | AHA Heartsaver Pediatric First Aid CPR AED Online | AHA_BLS_INSTRUCTOR |
| 209812 | AHA PALS HeartCode | AHA_PALS_INSTRUCTOR |
| 209805 | AHA PALS Provider | AHA_PALS_INSTRUCTOR |
| 251496 | AHA PALS Renewal | AHA_PALS_INSTRUCTOR |
| 253768 | USCG Elementary First Aid | CPR (AHA Heartsaver) | AHA_BLS_INSTRUCTOR |
| 359827 | USCG Elementary First Aid | CPR - Blended | AHA_BLS_INSTRUCTOR |

## Solver Audit Integration

- Last solver candidate count: 190
- Last solver rejection count: 231
- Remaining `missing_instructor_qualification` count: 166
- Interpretation: exact instructor certification codes remain unknown, so matching allowed candidates are marked with `instructor_qualification_unknown`; the remaining qualification rejections are availability-window family exclusions or instructors without matching catalog proof.

## Notes

- `can_teach_course_families` is copied from local availability blocks and is not the same as a verified instructor certification card.
- Exact certification fields remain `UNKNOWN` unless local config/data explicitly declares a certification code.
- Brian is included because the active appointment container explicitly ties Brian to the known appointment container.
