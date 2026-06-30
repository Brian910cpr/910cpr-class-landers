# August Offer Explosion Breakdown

Status: read-only audit. No deploy was performed.

## Plain Answer

29 August live availability blocks became 20901 August dynamic offers because dynamic generation fans each availability window out across every eligible course, duration, and quarter-hour start that fits the window before public-sellable policy is applied. These are candidates, not public classes.

For BLS-text courses, 6666 generated candidates survive dynamic generation. Of those, 4366 are AHA BLS course candidates. After enabling the reviewed AHA BLS course IDs, 24 August BLS offers reach public sellable and seed selection selects BLS seeds.

## August Dynamic Offers By Course Family

- `HSI`: 7725
- `Heartsaver`: 6627
- `BLS`: 4366
- `USCG`: 2183

## August Dynamic Offers By Course ID

- `209808`: 1150
- `251545`: 1150
- `329495`: 1150
- `359827`: 1150
- `371954`: 1150
- `445670`: 1150
- `449422`: 1150
- `463743`: 1150
- `210549`: 1137
- `344085`: 1111
- `209806`: 1085
- `359474`: 1085
- `440431`: 1059
- `448630`: 1059
- `209809`: 1033
- `253768`: 1033
- `351632`: 1033
- `374378`: 1033
- `422270`: 1033

## August Dynamic Offers By Date

- `2026-08-01`: 1656
- `2026-08-02`: 1656
- `2026-08-03`: 1656
- `2026-08-04`: 1656
- `2026-08-05`: 1656
- `2026-08-06`: 1656
- `2026-08-07`: 1656
- `2026-08-08`: 1656
- `2026-08-09`: 1656
- `2026-08-10`: 1656
- `2026-08-11`: 1656
- `2026-08-12`: 1656
- `2026-08-13`: 1029

## August Dynamic Offers By Start Time

- `00:00`: 247
- `00:15`: 247
- `00:30`: 247
- `00:45`: 247
- `01:00`: 247
- `01:15`: 247
- `01:30`: 247
- `01:45`: 247
- `02:00`: 247
- `02:15`: 247
- `02:30`: 247
- `02:45`: 247
- `03:00`: 247
- `03:15`: 247
- `03:30`: 247
- `03:45`: 247
- `04:00`: 247
- `04:15`: 247
- `04:30`: 247
- `04:45`: 247
- `05:00`: 247
- `05:15`: 247
- `05:30`: 247
- `05:45`: 247
- `06:00`: 247
- `06:15`: 247
- `06:30`: 247
- `06:45`: 247
- `07:00`: 247
- `07:15`: 247

## August Dynamic Offers Hidden Before Public Sellable - Top Reasons

- `outside_public_dynamic_hours`: 10220
- `course_id_not_enabled`: 9817
- `course_family_disabled`: 8758
- `course_family_not_enabled`: 8758
- `max_offers_per_course_per_week_exceeded`: 4980
- `max_total_offers_per_day_exceeded`: 588

## August BLS By Date

- `2026-08-01`: 528
- `2026-08-02`: 528
- `2026-08-03`: 528
- `2026-08-04`: 528
- `2026-08-05`: 528
- `2026-08-06`: 528
- `2026-08-07`: 528
- `2026-08-08`: 528
- `2026-08-09`: 528
- `2026-08-10`: 528
- `2026-08-11`: 528
- `2026-08-12`: 528
- `2026-08-13`: 330

## August BLS By Start Time

- `00:00`: 78
- `00:15`: 78
- `00:30`: 78
- `00:45`: 78
- `01:00`: 78
- `01:15`: 78
- `01:30`: 78
- `01:45`: 78
- `02:00`: 78
- `02:15`: 78
- `02:30`: 78
- `02:45`: 78
- `03:00`: 78
- `03:15`: 78
- `03:30`: 78
- `03:45`: 78
- `04:00`: 78
- `04:15`: 78
- `04:30`: 78
- `04:45`: 78
- `05:00`: 78
- `05:15`: 78
- `05:30`: 78
- `05:45`: 78
- `06:00`: 78
- `06:15`: 78
- `06:30`: 78
- `06:45`: 78
- `07:00`: 78
- `07:15`: 78

## August BLS By Duration

- `45`: 2300
- `120`: 2170
- `60`: 1137
- `150`: 1059

## August BLS By Course ID

- `445670`: 1150
- `463743`: 1150
- `210549`: 1137
- `209806`: 1085
- `359474`: 1085
- `440431`: 1059

## August BLS By Variant

- `HeartCode/skills`: 2196
- `BLS + First Aid`: 1150
- `BLS Challenge`: 1150
- `Initial/provider`: 1085
- `Renewal`: 1085

## Compression Pipeline

| Stage | In | Out | Hidden | Expected? |
| --- | ---: | ---: | ---: | --- |
| live_dynamic_generation | 20901 | 20901 | 0 | Expected high fan-out: every eligible course/start combination is still a candidate. |
| public_sellable_filter | 20901 | 60 | 20841 | Expected: policy hides disabled families/course IDs, off-hours starts, and caps per course/week. |
| seed_strategy | 60 | 6 | 54 | Expected: stack strategy intentionally selects a small number of daily seeds. |
| appointment_url_preview | 6 | 6 | 0 | Expected: selected seeds have container-backed appointmentDayId/courseId URL previews. |
| rendered_seed_rows_schedule_future | 6 | 0 | 6 | Expected in this branch: reports only; selected seed rows were not written into schedule_future. |
| rendered_seed_rows_public_schedule | 6 | 0 | 6 | Expected in this branch: no deploy and no public page rewrite. |
| existing_august_enrollware_schedule_future | 0 | 6 | 0 | Supplemental context only: existing real August inventory already present in schedule_future. |
| existing_august_enrollware_public_schedule | 0 | 2 | 0 | Supplemental context only: existing real August inventory already present in public_schedule. |

See `august_offer_compression_pipeline.csv` for exact top rejection reasons by stage.
