# BLS seed time preference report

## Summary
BLS start-time preference is now policy-driven in this order: 09:15, 12:30, 18:15, 18:45, 08:30, 09:00, 08:00, 08:15.
The selected August BLS seeds did not move because the preferred public-friendly times currently have zero public-sellable rows. They are generated dynamically, but current public offer caps and course/family filters remove them before seed selection.

## Current policy
- BLS preferred starts: ['09:15', '12:30', '18:15', '18:45', '08:30', '09:00', '08:00', '08:15']
- Max seeds per instructor/window: 4
- Max seeds per date: 8
- Max BLS seeds per date: 1
- BLS required mix: {'count': 1, 'required': True}

## Candidate availability
| Start | Generated | Public sellable | Seed eligible | Selected | Top blocker |
| --- | ---: | ---: | ---: | ---: | --- |
| 09:15 | 78 | 18 | 18 | 6 | max_offers_per_course_per_week_exceeded:32; course_id_not_enabled:26; course_family_disabled:13; course_family_not_enabled:13; max_total_offers_per_day_exceeded:2 |
| 12:30 | 78 | 0 | 0 | 0 | max_offers_per_course_per_week_exceeded:50; course_id_not_enabled:26; course_family_disabled:13; course_family_not_enabled:13; max_total_offers_per_day_exceeded:2 |
| 18:15 | 72 | 0 | 0 | 0 | max_offers_per_course_per_week_exceeded:46; course_id_not_enabled:24; course_family_disabled:12; course_family_not_enabled:12; max_total_offers_per_day_exceeded:2 |
| 18:45 | 72 | 0 | 0 | 0 | max_offers_per_course_per_week_exceeded:46; course_id_not_enabled:24; course_family_disabled:12; course_family_not_enabled:12; max_total_offers_per_day_exceeded:2 |
| 08:30 | 78 | 2 | 0 | 0 | max_offers_per_course_per_week_exceeded:50; course_id_not_enabled:26; course_family_disabled:13; course_family_not_enabled:13 |
| 09:00 | 78 | 0 | 0 | 0 | max_offers_per_course_per_week_exceeded:50; course_id_not_enabled:26; course_family_disabled:13; course_family_not_enabled:13; max_total_offers_per_day_exceeded:2 |
| 08:00 | 78 | 2 | 0 | 0 | max_offers_per_course_per_week_exceeded:50; course_id_not_enabled:26; course_family_disabled:13; course_family_not_enabled:13 |
| 08:15 | 78 | 2 | 0 | 0 | max_offers_per_course_per_week_exceeded:50; course_id_not_enabled:26; course_family_disabled:13; course_family_not_enabled:13 |

## Before/after selected August BLS seeds
| Period | Date | Time | CourseId | Course |
| --- | --- | --- | --- | --- |
| Before | 2026-08-03 | 08:30 | 209806 | AHA BLS Provider |
| Before | 2026-08-04 | 08:00 | 359474 | AHA BLS Provider Renewal |
| Before | 2026-08-10 | 08:30 | 209806 | AHA BLS Provider |
| Before | 2026-08-11 | 08:00 | 359474 | AHA BLS Provider Renewal |
| After | 2026-08-03 | 09:15 | 209806 | AHA BLS Provider |
| After | 2026-08-04 | 09:15 | 209806 | AHA BLS Provider |
| After | 2026-08-05 | 09:15 | 209806 | AHA BLS Provider |
| After | 2026-08-10 | 09:15 | 209806 | AHA BLS Provider |
| After | 2026-08-11 | 09:15 | 209806 | AHA BLS Provider |
| After | 2026-08-12 | 09:15 | 209806 | AHA BLS Provider |

## Schedule sufficiency
- August BLS rendered seed rows: 6
- Duplicate selected seed rows: 0
- Initial/Renewal balance: 6 Initial, 0 Renewal
- Evening or midday seeds are not possible without changing upstream public-sellable caps/filters.

## Safety
- existing_real_bls_enrollware_rows_still_render: True
- real_august_bls_enrollware_rows_still_render: True
- selected_bls_appointment_seeds_render: 6
- duplicate_selected_seed_rows: 0
- unknown_rows_suppressed: True
- hsi_pediatric_449422_suppressed: True
- course_344085_not_hsi: True
- public_offer_integrity_failed: False
