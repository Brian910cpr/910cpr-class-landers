# August BLS Seed Quality Audit

Status: read-only audit. No deploy was performed.

## Plain Answer

The selected BLS seeds are safe URL-backed candidates, but the current times are early because the seed strategy policy prefers BLS `08:30` then `09:00`, and the August public-sellable BLS set only contains `08:00`, `08:15`, and `08:30` starts.

- August BLS-text public sellable offers: 24
- Selected August BLS seeds: 4
- Selected by date: {'2026-08-03': 1, '2026-08-04': 1, '2026-08-10': 1, '2026-08-11': 1}
- Selected by course: {'209806 AHA BLS Provider': 2, '359474 AHA BLS Provider Renewal': 2}
- Public sellable by start time: {'08:30': 4, '08:00': 12, '08:15': 8}

## Common Public Time Bands

- `09:15`: dynamic candidates 78, public-sellable candidates 0, selected 0, hidden reasons {'max_offers_per_course_per_week_exceeded': 44, 'course_id_not_enabled': 26, 'course_family_disabled': 13, 'course_family_not_enabled': 13, 'max_total_offers_per_day_exceeded': 8}
- `12:30`: dynamic candidates 78, public-sellable candidates 0, selected 0, hidden reasons {'max_offers_per_course_per_week_exceeded': 44, 'course_id_not_enabled': 26, 'course_family_disabled': 13, 'course_family_not_enabled': 13, 'max_total_offers_per_day_exceeded': 8}
- `18:15`: dynamic candidates 72, public-sellable candidates 0, selected 0, hidden reasons {'max_offers_per_course_per_week_exceeded': 40, 'course_id_not_enabled': 24, 'course_family_disabled': 12, 'course_family_not_enabled': 12, 'max_total_offers_per_day_exceeded': 8}
- `18:45`: dynamic candidates 72, public-sellable candidates 0, selected 0, hidden reasons {'max_offers_per_course_per_week_exceeded': 40, 'course_id_not_enabled': 24, 'course_family_disabled': 12, 'course_family_not_enabled': 12, 'max_total_offers_per_day_exceeded': 8}

## Selected Seeds

| Date | Time | Course | courseId | appointmentDayId | Reason |
| --- | --- | --- | --- | --- | --- |
| 2026-08-03 | 08:30 | AHA BLS Provider | 209806 | 260713 | public_sellable_offer;selected_as_stack_seed;read_only_seed_preview_not_public_menu |
| 2026-08-04 | 08:00 | AHA BLS Provider Renewal | 359474 | 260714 | public_sellable_offer;selected_as_stack_seed;read_only_seed_preview_not_public_menu |
| 2026-08-10 | 08:30 | AHA BLS Provider | 209806 | 260720 | public_sellable_offer;selected_as_stack_seed;read_only_seed_preview_not_public_menu |
| 2026-08-11 | 08:00 | AHA BLS Provider Renewal | 359474 | 260721 | public_sellable_offer;selected_as_stack_seed;read_only_seed_preview_not_public_menu |

See `august_bls_public_sellable_24.csv` for all 24 public-sellable BLS-text offers and rejection reasons.
