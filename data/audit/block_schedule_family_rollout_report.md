# Block Schedule Family Rollout Report

Read-only rollout audit for config-driven block schedule pages. Enrollware course IDs and appointment URL behavior were not changed.

## Summary

- `bls` (BLS): ready; offers `1597`, dates `39`, start times `573`
- `acls` (ACLS): blocked; offers `0`, dates `0`, start times `0`
- `pals` (PALS): blocked; offers `0`, dates `0`, start times `0`
- `heartsaver` (Heartsaver): ready; offers `1507`, dates `39`, start times `512`
- `hsi` (HSI): blocked; offers `1103`, dates `43`, start times `591`
- `arc` (ARC): blocked; offers `0`, dates `0`, start times `0`

## Details

### bls

- Family: `BLS`
- Certifying body: `AHA`
- Output path: `docs/bls-schedule.html`
- Course IDs: `209806, 359474, 210549`
- Ready for generation: `True`
- Public-selectable offers: `1597`
- Public-selectable dates: `39`
- Public-selectable start times: `573`
- Rejected course/start evaluations: `3752`

Issues:
- None

Top rejection reasons:
- `outside_public_dynamic_hours`: 2670
- `conflicts_with_existing_enrollware_occupancy`: 1187
- `does_not_fit_inside_availability_after_duration_and_buffers`: 443
- `inside_minimum_lead_time`: 18

### acls

- Family: `ACLS`
- Certifying body: `AHA`
- Output path: `docs/acls-schedule.html`
- Course IDs: `241108, 209818, 209811`
- Ready for generation: `False`
- Public-selectable offers: `0`
- Public-selectable dates: `0`
- Public-selectable start times: `0`
- Rejected course/start evaluations: `5349`

Issues:
- `no_public_selectable_offers`

Top rejection reasons:
- `course_family_not_allowed_by_availability`: 5349
- `instructor_lacks_required_certification`: 5349
- `outside_public_dynamic_hours`: 2670
- `conflicts_with_existing_enrollware_occupancy`: 1563
- `does_not_fit_inside_availability_after_duration_and_buffers`: 1302
- `inside_minimum_lead_time`: 18

### pals

- Family: `PALS`
- Certifying body: `AHA`
- Output path: `docs/pals-schedule.html`
- Course IDs: `209805, 251496, 209812`
- Ready for generation: `False`
- Public-selectable offers: `0`
- Public-selectable dates: `0`
- Public-selectable start times: `0`
- Rejected course/start evaluations: `5349`

Issues:
- `no_public_selectable_offers`

Top rejection reasons:
- `course_family_not_allowed_by_availability`: 5349
- `instructor_lacks_required_certification`: 5349
- `outside_public_dynamic_hours`: 2670
- `conflicts_with_existing_enrollware_occupancy`: 1563
- `does_not_fit_inside_availability_after_duration_and_buffers`: 1302
- `inside_minimum_lead_time`: 18

### heartsaver

- Family: `Heartsaver`
- Certifying body: `AHA`
- Output path: `docs/heartsaver-schedule.html`
- Course IDs: `344085, 209809, 251545`
- Ready for generation: `True`
- Public-selectable offers: `1507`
- Public-selectable dates: `39`
- Public-selectable start times: `512`
- Rejected course/start evaluations: `3842`

Issues:
- None

Top rejection reasons:
- `outside_public_dynamic_hours`: 2670
- `conflicts_with_existing_enrollware_occupancy`: 1274
- `does_not_fit_inside_availability_after_duration_and_buffers`: 629
- `inside_minimum_lead_time`: 18

### hsi

- Family: `HSI`
- Certifying body: `HSI`
- Output path: `docs/hsi-schedule.html`
- Course IDs: `463743, 445670`
- Ready for generation: `False`
- Public-selectable offers: `1103`
- Public-selectable dates: `43`
- Public-selectable start times: `591`
- Rejected course/start evaluations: `2463`

Issues:
- `family_disabled_by_public_offer_policy_requires_explicit_approval`

Top rejection reasons:
- `outside_public_dynamic_hours`: 1780
- `conflicts_with_existing_enrollware_occupancy`: 753
- `does_not_fit_inside_availability_after_duration_and_buffers`: 251
- `inside_minimum_lead_time`: 12

### arc

- Family: `ARC`
- Certifying body: `ARC`
- Output path: `docs/arc-schedule.html`
- Course IDs: `248288, 248287`
- Ready for generation: `False`
- Public-selectable offers: `0`
- Public-selectable dates: `0`
- Public-selectable start times: `0`
- Rejected course/start evaluations: `3566`

Issues:
- `family_disabled_by_public_offer_policy_requires_explicit_approval`
- `no_public_selectable_offers`

Top rejection reasons:
- `instructor_lacks_required_certification`: 3566
- `outside_public_dynamic_hours`: 1780
- `conflicts_with_existing_enrollware_occupancy`: 830
- `does_not_fit_inside_availability_after_duration_and_buffers`: 378
- `inside_minimum_lead_time`: 12

## Generated Pages

- `E:\GitHub\910cpr-class-landers\docs\heartsaver-schedule.html`
