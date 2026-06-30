# August BLS Seed Quality Audit

Status: read-only audit. No deploy was performed.

## Plain Answer

The selected BLS seeds are safe URL-backed candidates, but the current times are early because the seed strategy policy prefers BLS `08:30` then `09:00`, and the August public-sellable BLS set only contains `08:00`, `08:15`, and `08:30` starts.

- August BLS-text public sellable offers: 24
- Selected August BLS seeds: 6
- Selected by date: {'2026-08-03': 1, '2026-08-04': 1, '2026-08-05': 1, '2026-08-10': 1, '2026-08-11': 1, '2026-08-12': 1}
- Selected by course: {'359474 AHA BLS Provider Renewal': 3, '209806 AHA BLS Provider': 3}
- Public sellable by start time: {'09:15': 18, '08:00': 2, '08:15': 2, '08:30': 2}

## Common Public Time Bands

- `09:15`: dynamic candidates 78, public-sellable candidates 18, selected 6, hidden reasons {'max_offers_per_course_per_week_exceeded': 32, 'course_id_not_enabled': 26, 'course_family_disabled': 13, 'course_family_not_enabled': 13, 'max_total_offers_per_day_exceeded': 2}
- `12:30`: dynamic candidates 78, public-sellable candidates 0, selected 0, hidden reasons {'max_offers_per_course_per_week_exceeded': 50, 'course_id_not_enabled': 26, 'course_family_disabled': 13, 'course_family_not_enabled': 13, 'max_total_offers_per_day_exceeded': 2}
- `18:15`: dynamic candidates 72, public-sellable candidates 0, selected 0, hidden reasons {'max_offers_per_course_per_week_exceeded': 46, 'course_id_not_enabled': 24, 'course_family_disabled': 12, 'course_family_not_enabled': 12, 'max_total_offers_per_day_exceeded': 2}
- `18:45`: dynamic candidates 72, public-sellable candidates 0, selected 0, hidden reasons {'max_offers_per_course_per_week_exceeded': 46, 'course_id_not_enabled': 24, 'course_family_disabled': 12, 'course_family_not_enabled': 12, 'max_total_offers_per_day_exceeded': 2}

## Selected Seeds

| Date | Time | Course | courseId | appointmentDayId | Reason |
| --- | --- | --- | --- | --- | --- |
| 2026-08-03 | 09:15 | AHA BLS Provider Renewal | 359474 | 260713 | public_sellable_offer;selected_as_stack_seed;read_only_seed_preview_not_public_menu |
| 2026-08-04 | 09:15 | AHA BLS Provider | 209806 | 260714 | public_sellable_offer;selected_as_stack_seed;read_only_seed_preview_not_public_menu |
| 2026-08-05 | 09:15 | AHA BLS Provider Renewal | 359474 | 260715 | public_sellable_offer;selected_as_stack_seed;read_only_seed_preview_not_public_menu |
| 2026-08-10 | 09:15 | AHA BLS Provider | 209806 | 260720 | public_sellable_offer;selected_as_stack_seed;read_only_seed_preview_not_public_menu |
| 2026-08-11 | 09:15 | AHA BLS Provider Renewal | 359474 | 260721 | public_sellable_offer;selected_as_stack_seed;read_only_seed_preview_not_public_menu |
| 2026-08-12 | 09:15 | AHA BLS Provider | 209806 | 260722 | public_sellable_offer;selected_as_stack_seed;read_only_seed_preview_not_public_menu |

See `august_bls_public_sellable_24.csv` for all 24 public-sellable BLS-text offers and rejection reasons.
