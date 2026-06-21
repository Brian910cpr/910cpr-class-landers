# Instructor Credentials Review

This is a Brian-reviewable, audit-only credential worksheet. It does not modify `data/config/instructor_catalog.json`, public pages, Enrollware behavior, appointment URLs, Worker behavior, or solver behavior.

## Current Solver Context

- Instructors in current catalog: 7
- Active instructors in current catalog: 3
- Unique required certification codes in course catalog: 5
- Solver candidates in last audit: 190
- Solver rejections in last audit: 231
- Remaining `missing_instructor_qualification`: 166

## How Brian Should Use This

1. Review each instructor row.
2. Replace `UNKNOWN` in `proposed_certifications` with confirmed valid certification codes only.
3. Add expiration dates only when known.
4. Leave uncertain credentials as `UNKNOWN`.
5. Return the reviewed CSV or JSON patch for a separate audited import step.

## Instructor Review Table

| Instructor ID | Display Name | Active | Current Certifications | Proposed Certifications | Can Teach Families | Expiration | Brian Review | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| a___arnold | A.  Arnold | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | NEEDS_REVIEW | Appears as lead instructor in local scheduled-class snapshot; exact certification codes are not declared in the snapshot. |
| amy | Amy | True | UNKNOWN | UNKNOWN | ACLS; PALS | UNKNOWN | NEEDS_REVIEW | Local availability lists certification ceiling ACLS_PALS; exact instructor certification codes are not confirmed here. Calendar source amy_availability is declared for this instructor; no certification code is declared. |
| b___ennis | B.  Ennis | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | NEEDS_REVIEW | Appears as lead instructor in local scheduled-class snapshot; exact certification codes are not declared in the snapshot. |
| bls_sample_instructor | BLS Sample Instructor | False | UNKNOWN | UNKNOWN | BLS; HeartCode; Heartsaver | UNKNOWN | NEEDS_REVIEW | Local availability lists certification ceiling BLS; exact instructor certification codes are not confirmed here. Name appears to be a prototype/sample instructor, not a confirmed production instructor. |
| brian | Brian | True | UNKNOWN | UNKNOWN | ACLS; BLS; Heartsaver; PALS; USCG | UNKNOWN | NEEDS_REVIEW | Local availability lists certification ceiling ACLS_PALS; exact instructor certification codes are not confirmed here. Confirmed appointment container shipyard_brian_continuous_20260621_20270430 is tied to this instructor; exact certification codes are not stated in the container. Calendar source brian_do_not_schedule is declared for this instructor; no certification code is declared. |
| n___tripp | N.  Tripp | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | NEEDS_REVIEW | Appears as lead instructor in local scheduled-class snapshot; exact certification codes are not declared in the snapshot. |
| nick | Nick | True | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | NEEDS_REVIEW | Calendar source nick_availability is declared for this instructor; no certification code is declared. |

## Valid Certification Codes From Course Catalog

| Certification Code | Course Count |
| --- | ---: |
| `AHA_ACLS_INSTRUCTOR` | 3 |
| `AHA_BLS_INSTRUCTOR` | 12 |
| `AHA_PALS_INSTRUCTOR` | 3 |
| `ARC_BLS_INSTRUCTOR` | 5 |
| `HSI_INSTRUCTOR` | 7 |

## Course Family To Required Certification

| Course Family | Required Certification Codes |
| --- | --- |
| ACLS | `AHA_ACLS_INSTRUCTOR` |
| ARC | `ARC_BLS_INSTRUCTOR` |
| BLS | `AHA_BLS_INSTRUCTOR` |
| HSI | `HSI_INSTRUCTOR` |
| Heartsaver | `AHA_BLS_INSTRUCTOR` |
| PALS | `AHA_PALS_INSTRUCTOR` |
| USCG | `AHA_BLS_INSTRUCTOR` |

## Course-Level Requirement Detail

| Family | Course ID | Course Title | Required Certification |
| --- | --- | --- | --- |
| ACLS | 209811 | AHA ACLS HeartCode | AHA_ACLS_INSTRUCTOR |
| ACLS | 209818 | AHA ACLS Provider (Renewal) | AHA_ACLS_INSTRUCTOR |
| ACLS | 241108 | AHA ACLS Provider (Initial) | AHA_ACLS_INSTRUCTOR |
| ARC | 248287 | American Red Cross Basic Life Support - Blended Learning | ARC_BLS_INSTRUCTOR |
| ARC | 248288 | American Red Cross Basic Life Support | ARC_BLS_INSTRUCTOR |
| ARC | 369209 | American Red Cross Adult and Pediatric First Aid/CPR/AED | ARC_BLS_INSTRUCTOR |
| ARC | 410694 | American Red Cross Adult and Pediatric First Aid/CPR/AED Blended Learning | ARC_BLS_INSTRUCTOR |
| ARC | 444919 | American Red Cross BLS Challenge | ARC_BLS_INSTRUCTOR |
| BLS | 209806 | AHA BLS Provider | AHA_BLS_INSTRUCTOR |
| BLS | 210549 | AHA HeartCode BLS | AHA_BLS_INSTRUCTOR |
| BLS | 359474 | AHA BLS Provider Renewal | AHA_BLS_INSTRUCTOR |
| BLS | 440431 | BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing) | AHA_BLS_INSTRUCTOR |
| HSI | 371954 | HSI Adult First Aid / CPR AED - Blended Learning | HSI_INSTRUCTOR |
| HSI | 374378 | HSI Adult First Aid / CPR AED | HSI_INSTRUCTOR |
| HSI | 422270 | HSI Adult First Aid / CPR AED | HSI_INSTRUCTOR |
| HSI | 445670 | HSI BLS and Adult First Aid / Blended Learning | HSI_INSTRUCTOR |
| HSI | 448630 | HSI Basic Life Support | HSI_INSTRUCTOR |
| HSI | 449422 | HSI Pediatric First Aid / CPR AED - Blended | HSI_INSTRUCTOR |
| HSI | 463743 | HSI BLS Challenge | HSI_INSTRUCTOR |
| Heartsaver | 209808 | AHA Heartsaver CPR AED Online | AHA_BLS_INSTRUCTOR |
| Heartsaver | 209809 | AHA Heartsaver First Aid CPR AED | AHA_BLS_INSTRUCTOR |
| Heartsaver | 251545 | AHA Heartsaver Pediatric First Aid CPR AED Online | AHA_BLS_INSTRUCTOR |
| Heartsaver | 329495 | AHA Heartsaver First Aid CPR AED - Blended | AHA_BLS_INSTRUCTOR |
| Heartsaver | 344085 | AHA Heartsaver CPR AED | AHA_BLS_INSTRUCTOR |
| Heartsaver | 351632 | AHA Heartsaver Pediatric First Aid / CPR / AED | AHA_BLS_INSTRUCTOR |
| PALS | 209805 | AHA PALS Provider | AHA_PALS_INSTRUCTOR |
| PALS | 209812 | AHA PALS HeartCode | AHA_PALS_INSTRUCTOR |
| PALS | 251496 | AHA PALS Renewal | AHA_PALS_INSTRUCTOR |
| USCG | 253768 | USCG Elementary First Aid / CPR (AHA Heartsaver) | AHA_BLS_INSTRUCTOR |
| USCG | 359827 | USCG Elementary First Aid / CPR - Blended | AHA_BLS_INSTRUCTOR |

## Source Validation Note

The existing instructor validation file reports exact certifications as unknown. Relevant source excerpt summary:

- `data/audit/instructor_catalog_validation.md` length read: 4264 characters
- Calendar ownership, schedule instructor names, and appointment containers are not treated as proof of instructor credentials.
