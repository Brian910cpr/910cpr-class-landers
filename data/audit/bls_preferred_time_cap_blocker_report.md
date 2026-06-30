# BLS preferred time cap blocker report

## Plain answer
Yes. Before this fix, earlier 08:00/08:30 rows could consume public-sellable caps before 09:15/12:30/evening rows. The cap limiter lived in scripts/filter_public_sellable_offers.py::apply_offer_limits and sorted by date, start_time, course_id before applying weekly/day/course caps.

## Preferred-time summary
| Start | Generated | AHA BLS | Non-AHA/BLS-like | Public sellable | Top rejection buckets |
| --- | ---: | ---: | ---: | ---: | --- |
| 09:15 | 78 | 39 | 39 | 18 | weekly_cap:32; course_or_family_disabled:26; kept:18; day_cap:2 |
| 12:30 | 78 | 39 | 39 | 0 | weekly_cap:50; course_or_family_disabled:26; day_cap:2 |
| 18:15 | 72 | 36 | 36 | 0 | weekly_cap:46; course_or_family_disabled:24; day_cap:2 |
| 18:45 | 72 | 36 | 36 | 0 | weekly_cap:46; course_or_family_disabled:24; day_cap:2 |

## Selected August AHA BLS after cap ordering
| Date | Time | CourseId | Course |
| --- | --- | --- | --- |
| 2026-08-03 | 09:15 | 209806 | AHA BLS Provider |
| 2026-08-04 | 09:15 | 209806 | AHA BLS Provider |
| 2026-08-05 | 09:15 | 209806 | AHA BLS Provider |
| 2026-08-10 | 09:15 | 209806 | AHA BLS Provider |
| 2026-08-11 | 09:15 | 209806 | AHA BLS Provider |
| 2026-08-12 | 09:15 | 209806 | AHA BLS Provider |
