# HSI Tab Mapping Fix Report

Generated: `2026-06-28T15:24:41`

## Source Change

Updated only `scripts/build_slug_hubs.py` in `APPOINTMENT_COURSE_TAB_IDS`. No public filters, course IDs, presentation compaction, Amy/ARC/USCG, lead time, Course Master authority, or confirmed-container requirements were changed.

## Reviewed Course Keys

| courseId | course_key | mapping decision | tab/card |
|---|---|---|---|
| 463743 | `hsi_bls_challenge` | added | hsi-bls |
| 371954 | `hsi_adult_first_aid_cpr_aed_blended` | added | hsi-first-aid-cpr-aed |
| 449422 | `hsi_pediatric_first_aid_cpr_aed_blended` | not added | No HSI pediatric card/tab exists; not forced into adult HSI First Aid/CPR/AED. |

## Before / After

| metric | before | after |
|---|---:|---:|
| presentation-selected dynamic offers | 8 | 8 |
| rendered dynamic offers | 5 | 7 |
| missing selected dynamic offers | 3 | 1 |

Rendered proof status: `PARTIAL`
Public offer integrity PASS: `True`
Tests: `137 tests OK`

## Rendered HSI Offers

| courseId | course name | card/tab | date | time | appointmentDayId | href |
|---|---|---|---|---|---:|---|
| 371954 | HSI Adult First Aid \| CPR AED - Blended Learning | HSI First Aid/CPR/AED / `hsi-first-aid-cpr-aed` | 2026-07-04 | 2:45 PM | 260683 | https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A45%20PM&courseId=371954 |
| 445670 | HSI BLS and Adult First Aid \| Blended Learning | HSI BLS + Adult First Aid / `hsi-bls-fa` | 2026-07-04 | 2:45 PM | 260683 | https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A45%20PM&courseId=445670 |
| 463743 | HSI BLS Challenge | HSI BLS / `hsi-bls` | 2026-07-04 | 2:45 PM | 260683 | https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A45%20PM&courseId=463743 |

## Selected But Not Rendered

| courseId | course name | offer_id | reason |
|---|---|---|---|
| 449422 | HSI Pediatric First Aid \| CPR AED - Blended | `offer-449422-instructor_24057895173-20260704-1445` | No existing reviewed HSI pediatric tab/card mapping; intentionally left unmapped. |

## 344085 / HSI CPR AED

`344085` is AHA Heartsaver CPR AED and remains on the Heartsaver page only. It was not mapped to `hsi-cpr-aed`. The HSI CPR/AED card should remain without a dynamic offer until a true HSI CPR AED courseId is reviewed and approved.

## Verdict

The reviewed adult HSI mappings fixed two of the three missing HSI offers. `449422` should remain enabled but not rendered until an HSI pediatric card/tab is created or Brian explicitly approves a destination.
