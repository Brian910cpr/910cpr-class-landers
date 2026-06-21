# Course Catalog Rules Patch Review

Generated: 2026-06-18T21:52:12.286699-04:00

This is a Brian-review draft only. It does not modify `data/config/course_catalog.json`, public pages, scheduler behavior, Enrollware behavior, appointment URLs, or Worker settings.

`UNKNOWN` means the value was not confidently available from local files.

| Course ID | Title | Duration | Capacity | Appointment? | Instructor Requirement | Resources | Needs Brian Review? |
|---|---|---:|---:|---|---|---|---|
| **AHA BLS** |  |  |  |  |  |  |  |
| 209806 | AHA BLS Provider | 120 | 6 | Yes | UNKNOWN | UNKNOWN | Yes |
| 359474 | AHA BLS Provider Renewal | 120 | 6 | Yes | UNKNOWN | UNKNOWN | Yes |
| 210549 | AHA HeartCode BLS | 60 | 1 | Yes | UNKNOWN | UNKNOWN | Yes |
| 440431 | BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing) | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Yes |
| **AHA ACLS** |  |  |  |  |  |  |  |
| 209811 | AHA ACLS HeartCode | 240 | 1 | Yes | UNKNOWN | UNKNOWN | Yes |
| 241108 | AHA ACLS Provider (Initial) | 240 | 6 | Yes | UNKNOWN | UNKNOWN | Yes |
| 209818 | AHA ACLS Provider (Renewal) | 240 | 6 | Yes | UNKNOWN | UNKNOWN | Yes |
| **AHA PALS** |  |  |  |  |  |  |  |
| 209812 | AHA PALS HeartCode | 240 | 1 | Yes | UNKNOWN | UNKNOWN | Yes |
| 209805 | AHA PALS Provider | 240 | 6 | Yes | UNKNOWN | UNKNOWN | Yes |
| 251496 | AHA PALS Renewal | 240 | 6 | Yes | UNKNOWN | UNKNOWN | Yes |
| **AHA Heartsaver** |  |  |  |  |  |  |  |
| 344085 | AHA Heartsaver CPR AED | 120 | 10 | Yes | UNKNOWN | UNKNOWN | Yes |
| 209808 | AHA Heartsaver CPR AED Online | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Yes |
| 209809 | AHA Heartsaver First Aid CPR AED | 150 | 10 | Yes | UNKNOWN | UNKNOWN | Yes |
| 329495 | AHA Heartsaver First Aid CPR AED - Blended | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Yes |
| 351632 | AHA Heartsaver Pediatric First Aid / CPR / AED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Yes |
| 251545 | AHA Heartsaver Pediatric First Aid CPR AED Online | 120 | 10 | Yes | UNKNOWN | UNKNOWN | Yes |
| **ARC** |  |  |  |  |  |  |  |
| 369209 | American Red Cross Adult and Pediatric First Aid/CPR/AED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Yes |
| 410694 | American Red Cross Adult and Pediatric First Aid/CPR/AED Blended Learning | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Yes |
| 444919 | American Red Cross BLS Challenge | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Yes |
| 248288 | American Red Cross Basic Life Support | 120 | 6 | Yes | UNKNOWN | UNKNOWN | Yes |
| 248287 | American Red Cross Basic Life Support - Blended Learning | 120 | 6 | Yes | UNKNOWN | UNKNOWN | Yes |
| **HSI** |  |  |  |  |  |  |  |
| 374378 | HSI Adult First Aid / CPR AED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Yes |
| 422270 | HSI Adult First Aid / CPR AED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Yes |
| 371954 | HSI Adult First Aid / CPR AED - Blended Learning | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Yes |
| 463743 | HSI BLS Challenge | 120 | 6 | Yes | UNKNOWN | UNKNOWN | Yes |
| 445670 | HSI BLS and Adult First Aid / Blended Learning | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Yes |
| 448630 | HSI Basic Life Support | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Yes |
| 449422 | HSI Pediatric First Aid / CPR AED - Blended | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Yes |
| **USCG** |  |  |  |  |  |  |  |
| 253768 | USCG Elementary First Aid / CPR (AHA Heartsaver) | 240 | 10 | Yes | UNKNOWN | UNKNOWN | Yes |
| 359827 | USCG Elementary First Aid / CPR - Blended | 120 | 10 | Yes | UNKNOWN | UNKNOWN | Yes |

## Review Notes

- Values already known in `course_catalog.json` were preserved.
- Unknown values were not inferred from course names or Enrollware IDs.
- Instructor requirements and resources need explicit Brian review before this becomes operational scheduler input.
