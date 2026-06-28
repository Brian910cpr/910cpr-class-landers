# HSI Unmapped Pediatric Offer Block Report

Generated: `2026-06-28T15:49:00`

## Summary

The presentation policy now suppresses public sellable appointment offers that do not have a reviewed appointment tab/card render target before they can be selected for rendering.

| metric | before | after |
|---|---:|---:|
| selected dynamic offers | 8 | 7 |
| rendered dynamic offers | 7 | 7 |
| missing selected dynamic offers | 1 | 0 |

Rendered proof: `PASS`
Public offer integrity PASS: `True`
Tests: `138 tests OK`

## 449422 Suppression

Selected after fix: `False`
Suppressed as unmapped: `True`
Reason: Suppressed because course_key `UNKNOWN` and courseId `449422` have no reviewed appointment tab/card mapping.

## Rendered HSI Offers

| courseId | course name | card/tab | date | time | appointmentDayId | href |
|---|---|---|---|---|---:|---|
| 371954 | HSI Adult First Aid \| CPR AED - Blended Learning | HSI First Aid/CPR/AED / `hsi-first-aid-cpr-aed` | 2026-07-04 | 2:45 PM | 260683 | https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A45%20PM&courseId=371954 |
| 445670 | HSI BLS and Adult First Aid \| Blended Learning | HSI BLS + Adult First Aid / `hsi-bls-fa` | 2026-07-04 | 2:45 PM | 260683 | https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A45%20PM&courseId=445670 |
| 463743 | HSI BLS Challenge | HSI BLS / `hsi-bls` | 2026-07-04 | 2:45 PM | 260683 | https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A45%20PM&courseId=463743 |

## Safety Confirmations

- No HSI pediatric card/tab was added.
- `449422` was not mapped to an existing adult/wrong card.
- `344085` remains AHA Heartsaver only and is not mapped to HSI CPR/AED.
- Public filters, lead time, confirmed-container requirements, Course Master authority, Amy, ARC, and USCG were not changed.
