# August full availability vs public selected seeds

Audit-only report. No deploy, rendering change, gate loosening, course ID change, or policy change was performed.

## Plain-English answer
All August availability is not represented publicly because the system intentionally compresses many generated 15-minute dynamic candidates through reviewed course IDs/families, public hour windows, day/week/course caps, selected-seed strategy, duplicate avoidance, and rendered-page guards. The broad availability exists; public pages currently show only the selected/render-safe subset.

## Source files
- availability: `data/audit/live_availability_snapshot_preview.json`
- dynamic_offers: `data/runtime/audit_previews/dynamic_offers_preview.json`
- public_sellable: `data/runtime/audit_previews/public_sellable_offers_preview.json`
- selected_seed_audit: `data/audit/august_bls_seed_quality_audit.json`
- rendered_html_scanned: `['docs/bls.html', 'docs/acls.html', 'docs/pals.html', 'docs/heartsaver.html', 'docs/hsi.html', 'docs/courses/heartsaver-cpr-aed.html', 'docs/courses/heartsaver-first-aid-cpr-aed.html']`
- selected_seed_source: `data/audit/schedule_seeds_preview.json`
- appointment_url_preview_source: `data/audit/seed_appointment_url_preview.json`

## August pipeline totals
- august_availability_windows_with_generated_offers: 13
- august_dynamic_offers: 20901
- august_public_sellable_offers: 60
- august_hidden_dynamic_offers: 20841
- selected_august_bls_seeds_from_quality_audit: 6
- known_policy_enabled_course_ids: ['209806', '209808', '209809', '210549', '251545', '329495', '344085', '351632', '359474', '445670']
- selected_august_seeds_all_families: 6
- appointment_url_previews_august_all_families: 6
- rendered_selected_august_seed_urls_scanned: 6

## By course family
| Family | Availability windows | Generated candidates | Unique date/start pairs | 15-min starts | Reviewed course-ID candidates | Public sellable | Selected seeds | Rendered selected seed URLs scanned | Top hidden reasons |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| BLS | 13 | 4366 | 1137 | 1137 | 3307 | 18 | 6 | 6 | {'outside_public_dynamic_hours': 2120, 'max_offers_per_course_per_week_exceeded': 1669, 'course_id_not_enabled': 1059} |
| ACLS | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | {} |
| PALS | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | {} |
| Heartsaver First Aid CPR AED | 13 | 4366 | 1150 | 1150 | 4366 | 24 | 0 | 0 | {'outside_public_dynamic_hours': 2120, 'max_offers_per_course_per_week_exceeded': 1886, 'max_total_offers_per_day_exceeded': 336} |
| Heartsaver CPR AED | 13 | 2261 | 1150 | 1150 | 2261 | 12 | 0 | 0 | {'outside_public_dynamic_hours': 1132, 'max_offers_per_course_per_week_exceeded': 949, 'max_total_offers_per_day_exceeded': 168} |
| HSI | 13 | 7725 | 1150 | 1150 | 1150 | 6 | 0 | 0 | {'course_family_disabled': 6575, 'course_id_not_enabled': 6575, 'course_family_not_enabled': 6575, 'outside_public_dynamic_hours': 3788, 'max_offers_per_course_per_week_exceeded': 476, 'max_total_offers_per_day_exceeded': 84} |

## Selected August seeds
- 2026-08-03 09:15 AHA BLS Provider Renewal `359474` (BLS), window `brian_do_not_schedule:inverse_gap:58`, rendered in scanned pages: True
- 2026-08-04 09:15 AHA BLS Provider `209806` (BLS), window `brian_do_not_schedule:inverse_gap:59`, rendered in scanned pages: True
- 2026-08-05 09:15 AHA BLS Provider Renewal `359474` (BLS), window `brian_do_not_schedule:inverse_gap:60`, rendered in scanned pages: True
- 2026-08-10 09:15 AHA BLS Provider `209806` (BLS), window `brian_do_not_schedule:inverse_gap:65`, rendered in scanned pages: True
- 2026-08-11 09:15 AHA BLS Provider Renewal `359474` (BLS), window `brian_do_not_schedule:inverse_gap:66`, rendered in scanned pages: True
- 2026-08-12 09:15 AHA BLS Provider `209806` (BLS), window `brian_do_not_schedule:inverse_gap:67`, rendered in scanned pages: True

## What happens per availability window
See `data/audit/august_availability_window_public_comparison.csv` for every August source window. Each row includes possible 15-minute starts, families that fit, customer-friendly starts, public-sellable count, selected count, and top filter reasons.

- `brian_do_not_schedule:inverse_gap:56` 2026-08-01 00:00-00:00: 96 possible 15-minute starts; families fit: BLS; HSI; Heartsaver CPR AED; Heartsaver First Aid CPR AED; customer-friendly starts: 09:15; 10:30; 12:30; 13:00; 18:00; 18:15; 18:45; generated 1656; reviewed-ID candidates 878; public sellable 0; selected 0. Top filters: outside_public_dynamic_hours:801; course_id_not_enabled:778; course_family_disabled:694; course_family_not_enabled:694; max_offers_per_course_per_week_exceeded:450. Selected: none.
- `brian_do_not_schedule:inverse_gap:57` 2026-08-02 00:00-00:00: 96 possible 15-minute starts; families fit: BLS; HSI; Heartsaver CPR AED; Heartsaver First Aid CPR AED; customer-friendly starts: 09:15; 10:30; 12:30; 13:00; 18:00; 18:15; 18:45; generated 1656; reviewed-ID candidates 878; public sellable 0; selected 0. Top filters: outside_public_dynamic_hours:801; course_id_not_enabled:778; course_family_disabled:694; course_family_not_enabled:694; max_offers_per_course_per_week_exceeded:450. Selected: none.
- `brian_do_not_schedule:inverse_gap:58` 2026-08-03 00:00-00:00: 96 possible 15-minute starts; families fit: BLS; HSI; Heartsaver CPR AED; Heartsaver First Aid CPR AED; customer-friendly starts: 09:15; 10:30; 12:30; 13:00; 18:00; 18:15; 18:45; generated 1656; reviewed-ID candidates 878; public sellable 24; selected 1. Top filters: outside_public_dynamic_hours:801; course_id_not_enabled:778; course_family_disabled:694; course_family_not_enabled:694; max_total_offers_per_day_exceeded:294; max_offers_per_course_per_week_exceeded:132. Selected: 2026-08-03 09:15 AHA BLS Provider Renewal 359474.
- `brian_do_not_schedule:inverse_gap:59` 2026-08-04 00:00-00:00: 96 possible 15-minute starts; families fit: BLS; HSI; Heartsaver CPR AED; Heartsaver First Aid CPR AED; customer-friendly starts: 09:15; 10:30; 12:30; 13:00; 18:00; 18:15; 18:45; generated 1656; reviewed-ID candidates 878; public sellable 3; selected 1. Top filters: outside_public_dynamic_hours:801; course_id_not_enabled:778; course_family_disabled:694; course_family_not_enabled:694; max_offers_per_course_per_week_exceeded:447. Selected: 2026-08-04 09:15 AHA BLS Provider 209806.
- `brian_do_not_schedule:inverse_gap:60` 2026-08-05 00:00-00:00: 96 possible 15-minute starts; families fit: BLS; HSI; Heartsaver CPR AED; Heartsaver First Aid CPR AED; customer-friendly starts: 09:15; 10:30; 12:30; 13:00; 18:00; 18:15; 18:45; generated 1656; reviewed-ID candidates 878; public sellable 3; selected 1. Top filters: outside_public_dynamic_hours:801; course_id_not_enabled:778; course_family_disabled:694; course_family_not_enabled:694; max_offers_per_course_per_week_exceeded:447. Selected: 2026-08-05 09:15 AHA BLS Provider Renewal 359474.
- `brian_do_not_schedule:inverse_gap:61` 2026-08-06 00:00-00:00: 96 possible 15-minute starts; families fit: BLS; HSI; Heartsaver CPR AED; Heartsaver First Aid CPR AED; customer-friendly starts: 09:15; 10:30; 12:30; 13:00; 18:00; 18:15; 18:45; generated 1656; reviewed-ID candidates 878; public sellable 0; selected 0. Top filters: outside_public_dynamic_hours:801; course_id_not_enabled:778; course_family_disabled:694; course_family_not_enabled:694; max_offers_per_course_per_week_exceeded:450. Selected: none.
- `brian_do_not_schedule:inverse_gap:62` 2026-08-07 00:00-00:00: 96 possible 15-minute starts; families fit: BLS; HSI; Heartsaver CPR AED; Heartsaver First Aid CPR AED; customer-friendly starts: 09:15; 10:30; 12:30; 13:00; 18:00; 18:15; 18:45; generated 1656; reviewed-ID candidates 878; public sellable 0; selected 0. Top filters: outside_public_dynamic_hours:801; course_id_not_enabled:778; course_family_disabled:694; course_family_not_enabled:694; max_offers_per_course_per_week_exceeded:450. Selected: none.
- `brian_do_not_schedule:inverse_gap:63` 2026-08-08 00:00-00:00: 96 possible 15-minute starts; families fit: BLS; HSI; Heartsaver CPR AED; Heartsaver First Aid CPR AED; customer-friendly starts: 09:15; 10:30; 12:30; 13:00; 18:00; 18:15; 18:45; generated 1656; reviewed-ID candidates 878; public sellable 0; selected 0. Top filters: outside_public_dynamic_hours:801; course_id_not_enabled:778; course_family_disabled:694; course_family_not_enabled:694; max_offers_per_course_per_week_exceeded:450. Selected: none.
- `brian_do_not_schedule:inverse_gap:64` 2026-08-09 00:00-00:00: 96 possible 15-minute starts; families fit: BLS; HSI; Heartsaver CPR AED; Heartsaver First Aid CPR AED; customer-friendly starts: 09:15; 10:30; 12:30; 13:00; 18:00; 18:15; 18:45; generated 1656; reviewed-ID candidates 878; public sellable 0; selected 0. Top filters: outside_public_dynamic_hours:801; course_id_not_enabled:778; course_family_disabled:694; course_family_not_enabled:694; max_offers_per_course_per_week_exceeded:450. Selected: none.
- `brian_do_not_schedule:inverse_gap:65` 2026-08-10 00:00-00:00: 96 possible 15-minute starts; families fit: BLS; HSI; Heartsaver CPR AED; Heartsaver First Aid CPR AED; customer-friendly starts: 09:15; 10:30; 12:30; 13:00; 18:00; 18:15; 18:45; generated 1656; reviewed-ID candidates 878; public sellable 24; selected 1. Top filters: outside_public_dynamic_hours:801; course_id_not_enabled:778; course_family_disabled:694; course_family_not_enabled:694; max_total_offers_per_day_exceeded:294; max_offers_per_course_per_week_exceeded:132. Selected: 2026-08-10 09:15 AHA BLS Provider 209806.
- `brian_do_not_schedule:inverse_gap:66` 2026-08-11 00:00-00:00: 96 possible 15-minute starts; families fit: BLS; HSI; Heartsaver CPR AED; Heartsaver First Aid CPR AED; customer-friendly starts: 09:15; 10:30; 12:30; 13:00; 18:00; 18:15; 18:45; generated 1656; reviewed-ID candidates 878; public sellable 3; selected 1. Top filters: outside_public_dynamic_hours:801; course_id_not_enabled:778; course_family_disabled:694; course_family_not_enabled:694; max_offers_per_course_per_week_exceeded:447. Selected: 2026-08-11 09:15 AHA BLS Provider Renewal 359474.
- `brian_do_not_schedule:inverse_gap:67` 2026-08-12 00:00-00:00: 96 possible 15-minute starts; families fit: BLS; HSI; Heartsaver CPR AED; Heartsaver First Aid CPR AED; customer-friendly starts: 09:15; 10:30; 12:30; 13:00; 18:00; 18:15; 18:45; generated 1656; reviewed-ID candidates 878; public sellable 3; selected 1. Top filters: outside_public_dynamic_hours:801; course_id_not_enabled:778; course_family_disabled:694; course_family_not_enabled:694; max_offers_per_course_per_week_exceeded:447. Selected: 2026-08-12 09:15 AHA BLS Provider 209806.
- `brian_do_not_schedule:inverse_gap:68` 2026-08-13 00:00-15:45: 63 possible 15-minute starts; families fit: BLS; HSI; Heartsaver CPR AED; Heartsaver First Aid CPR AED; customer-friendly starts: 09:15; 10:30; 12:30; 13:00; generated 1029; reviewed-ID candidates 548; public sellable 0; selected 0. Top filters: outside_public_dynamic_hours:608; course_id_not_enabled:481; course_family_disabled:430; course_family_not_enabled:430; max_offers_per_course_per_week_exceeded:228. Selected: none.

## Why the rest are not rendered
- Dynamic generation expands availability into many 15-minute candidate starts and course variants.
- Public sellable filtering keeps only reviewed/enabled course IDs and families, public hours, confirmed appointment container-backed rows, and capped day/week/course counts.
- Seed strategy then intentionally selects a small public-facing subset, currently balancing AHA BLS Initial/Renewal and preferred times.
- Render guards suppress incomplete appointment URLs and only render rows with a complete reviewed booking tuple.
- Unselected public-sellable rows are candidates, not public classes.

## Middle-ground public strategy
Recommendation: **B plus D**.
- A: Safest operationally, but hides too much real August availability and makes the public schedule look sparse.
- B: Best middle ground if capped and preference-driven: expose a few customer-friendly starts per window after reviewed course ID, public hours, occupancy, appointment tuple, and Course Master gates.
- C: Correct for admin/debug views only; public exposure would create overwhelming duplicate choices and higher risk of confusing customers.
- D: Good companion to B because it captures demand without rendering every 15-minute candidate. The CTA must use a reviewed full appointment tuple or a non-booking inquiry flow, not appointmentDayId-only links.

Do not expose every 15-minute start publicly. Keep that internal for audits/admin. If Brian wants more public depth, expose 2-4 preferred starts per eligible availability window after the same safety gates, and pair it with a customer-facing request CTA tied to the availability window.
