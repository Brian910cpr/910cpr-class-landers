# HSI Public Family Unlock - After

Generated: 2026-06-28T14:11:51

## Before/After Totals

- HSI generated before/after: `176` / `176`
- HSI public sellable before/after: `5` / `5`
- HSI rendered before/after: `2` / `2`

## Exact HSI Offers Now Rendered
- `offer-344085-instructor_24057895173-20260704-1445` courseId `344085` AHA Heartsaver CPR AED start `2026-07-04T14:45:00` appointmentDayId `260683` href `None` location `NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` page/tab `see rendered proof page match`
- `offer-445670-instructor_24057895173-20260704-1445` courseId `445670` HSI BLS and Adult First Aid | Blended Learning start `2026-07-04T14:45:00` appointmentDayId `260683` href `None` location `NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` page/tab `see rendered proof page match`

## HSI Course Results

| Course | Generated after | Public after | Rendered after | Earliest public | Earliest rendered | Rejection reasons |
| --- | ---: | ---: | ---: | --- | --- | --- |
| HSI BLS | 35 | 0 | 0 | None | None | `{"course_id_not_enabled": 35, "inside_minimum_lead_time": 30, "outside_public_dynamic_hours": 7}` |
| HSI BLS + Adult First Aid | 35 | 3 | 1 | 2026-07-04T14:30:00 | 2026-07-04T14:45:00 | `{"inside_minimum_lead_time": 30, "outside_public_dynamic_hours": 7, "max_offers_per_course_per_week_exceeded": 2}` |
| HSI First Aid CPR AED | 78 | 0 | 0 | None | None | `{"course_id_not_enabled": 78, "inside_minimum_lead_time": 68, "outside_public_dynamic_hours": 14}` |
| HSI CPR AED | 20 | 2 | 1 | 2026-07-04T14:30:00 | 2026-07-04T14:45:00 | `{"inside_minimum_lead_time": 18, "outside_public_dynamic_hours": 2}` |

## Validation

- Rendered proof status: `PASS`
- Public offer integrity failed: `False`
- Tests: `Ran 137 tests; OK`

## Interpretation

Enabling the HSI family alone did not increase public sellable/rendered HSI inventory. The remaining blockers are course ID enablement/container/course mapping and other existing gates, while confirmed appointment-container filtering stayed enabled.
