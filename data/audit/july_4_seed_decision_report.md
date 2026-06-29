# July 4 Seed Decision Report

## Confirmed July 4 Appointment Seed Rows

| course_key | courseId | course_display_name | date | time | visible_page | appointmentDayId | source_offer_id | allowed_by_rule | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hsi_bls_adult_first_aid_blended | 445670 | HSI BLS and Adult First Aid \| Blended Learning | 2026-07-04 | 2:45 PM - 3:30 PM | /hsi.html | 260683 | offer-445670-instructor_24057895173-20260704-1445 | yes | appointment_seed_allowed_by_course_master_gate |

## Decision

These rows are appointment seeds, not Class Report enroll?id rows. With the stricter Course Master gate, the Heartsaver July 4 seeds are blocked because their Course Master records still say `appointment_seed_allowed=false` and `review_needed_for_scheduling=true`.

If they were temporary proof artifacts, suppress them. If Brian wants them as valid examples, review and explicitly allowlist the exact Course Master seed behavior before rendering. August is not producing more safe rows because the generated seed path is not aligned with Course Master reviewed scheduling gates and August real Enrollware coverage is sparse.
