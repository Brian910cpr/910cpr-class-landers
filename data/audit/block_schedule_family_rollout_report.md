# Block Schedule Family Rollout Report

Read-only rollout audit for config-driven block schedule pages. Enrollware course IDs and appointment URL behavior were not changed.

## Summary

- `bls` (BLS): ready; offers `1618`, dates `39`, start times `580`
- `acls` (ACLS): blocked; offers `0`, dates `0`, start times `0`
- `pals` (PALS): blocked; offers `0`, dates `0`, start times `0`
- `heartsaver` (Heartsaver): ready; offers `1527`, dates `39`, start times `519`
- `hsi` (HSI): blocked; offers `1117`, dates `43`, start times `598`
- `arc` (ARC): blocked; offers `0`, dates `0`, start times `0`

## Details

### bls

- Family: `BLS`
- Certifying body: `AHA`
- Output path: `docs/bls-schedule.html`
- Course IDs: `209806, 359474, 210549`
- Ready for generation: `True`
- Release recommendation: `ready_for_direct_url_release`
- Public-selectable offers: `1618`
- Public-selectable dates: `39`
- Public-selectable start times: `580`
- Rejected course/start evaluations: `3803`

Issues:
- None

Top rejection reasons:
- `outside_public_dynamic_hours`: 2736
- `conflicts_with_existing_enrollware_occupancy`: 1177
- `does_not_fit_inside_availability_after_duration_and_buffers`: 450
- `inside_minimum_lead_time`: 18

### acls

- Family: `ACLS`
- Certifying body: `AHA`
- Output path: `docs/acls-schedule.html`
- Course IDs: `241108, 209818, 209811`
- Ready for generation: `False`
- Release recommendation: `do_not_release_direct_url_page_yet`
- Public-selectable offers: `0`
- Public-selectable dates: `0`
- Public-selectable start times: `0`
- Rejected course/start evaluations: `5421`

Issues:
- `no_public_selectable_offers`

Top rejection reasons:
- `course_family_not_allowed_by_availability`: 5421
- `instructor_lacks_required_certification`: 5421
- `outside_public_dynamic_hours`: 2736
- `conflicts_with_existing_enrollware_occupancy`: 1554
- `does_not_fit_inside_availability_after_duration_and_buffers`: 1323
- `inside_minimum_lead_time`: 18

### pals

- Family: `PALS`
- Certifying body: `AHA`
- Output path: `docs/pals-schedule.html`
- Course IDs: `209805, 251496, 209812`
- Ready for generation: `False`
- Release recommendation: `do_not_release_direct_url_page_yet`
- Public-selectable offers: `0`
- Public-selectable dates: `0`
- Public-selectable start times: `0`
- Rejected course/start evaluations: `5421`

Issues:
- `no_public_selectable_offers`

Top rejection reasons:
- `course_family_not_allowed_by_availability`: 5421
- `instructor_lacks_required_certification`: 5421
- `outside_public_dynamic_hours`: 2736
- `conflicts_with_existing_enrollware_occupancy`: 1554
- `does_not_fit_inside_availability_after_duration_and_buffers`: 1323
- `inside_minimum_lead_time`: 18

### heartsaver

- Family: `Heartsaver`
- Certifying body: `AHA`
- Output path: `docs/heartsaver-schedule.html`
- Course IDs: `344085, 209809, 251545`
- Ready for generation: `True`
- Release recommendation: `ready_for_direct_url_release`
- Public-selectable offers: `1527`
- Public-selectable dates: `39`
- Public-selectable start times: `519`
- Rejected course/start evaluations: `3894`

Issues:
- None

Top rejection reasons:
- `outside_public_dynamic_hours`: 2736
- `conflicts_with_existing_enrollware_occupancy`: 1261
- `does_not_fit_inside_availability_after_duration_and_buffers`: 639
- `inside_minimum_lead_time`: 18

### hsi

- Family: `HSI`
- Certifying body: `HSI`
- Output path: `docs/hsi-schedule.html`
- Course IDs: `463743, 445670`
- Ready for generation: `False`
- Release recommendation: `fix_blockers_before_release`
- Public-selectable offers: `1117`
- Public-selectable dates: `43`
- Public-selectable start times: `598`
- Rejected course/start evaluations: `2497`

Issues:
- `family_disabled_by_public_offer_policy_requires_explicit_approval`

Top rejection reasons:
- `outside_public_dynamic_hours`: 1824
- `conflicts_with_existing_enrollware_occupancy`: 748
- `does_not_fit_inside_availability_after_duration_and_buffers`: 255
- `inside_minimum_lead_time`: 12

### arc

- Family: `ARC`
- Certifying body: `ARC`
- Output path: `docs/arc-schedule.html`
- Course IDs: `248288, 248287`
- Ready for generation: `False`
- Release recommendation: `do_not_release_direct_url_page_yet`
- Public-selectable offers: `0`
- Public-selectable dates: `0`
- Public-selectable start times: `0`
- Rejected course/start evaluations: `3614`

Issues:
- `family_disabled_by_public_offer_policy_requires_explicit_approval`
- `no_public_selectable_offers`

Top rejection reasons:
- `instructor_lacks_required_certification`: 3614
- `outside_public_dynamic_hours`: 1824
- `conflicts_with_existing_enrollware_occupancy`: 822
- `does_not_fit_inside_availability_after_duration_and_buffers`: 384
- `inside_minimum_lead_time`: 12

## Generated Pages

- `E:\GitHub\910cpr-class-landers\docs\heartsaver-schedule.html`
