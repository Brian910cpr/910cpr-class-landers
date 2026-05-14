# Inventory Controller Audit

Scenario: `no_anchor_case`

- Total availability blocks: 14
- Total candidates: 910
- Public offerings: 156
- Suppressed offerings: 754
- Invalid out-of-range offerings: 52
- Anchor-required blocks: 1

## Suppression Examples

- 2026-06-22 12:30 PM AHA BLS Provider (Brian): suppressed because owned_appointment_container, course_family_allowed_by_block, course_fits_contiguous_block, remaining_fragment_too_small, duplicate_same_course_too_close_in_block, score_below_public_threshold
- 2026-06-22 1:30 PM AHA BLS Provider (Brian): suppressed because owned_appointment_container, course_family_allowed_by_block, course_does_not_fit_contiguous_block
- 2026-06-22 2:30 PM AHA BLS Provider (Brian): suppressed because owned_appointment_container, course_family_allowed_by_block, course_does_not_fit_contiguous_block
- 2026-06-22 12:30 PM AHA BLS Provider Renewal (Brian): suppressed because owned_appointment_container, course_family_allowed_by_block, course_fits_contiguous_block, remaining_fragment_too_small, duplicate_same_course_too_close_in_block, score_below_public_threshold
- 2026-06-22 1:30 PM AHA BLS Provider Renewal (Brian): suppressed because owned_appointment_container, course_family_allowed_by_block, course_does_not_fit_contiguous_block
- 2026-06-22 2:30 PM AHA BLS Provider Renewal (Brian): suppressed because owned_appointment_container, course_family_allowed_by_block, course_does_not_fit_contiguous_block
- 2026-06-22 10:30 AM AHA HeartCode BLS (Brian): suppressed because owned_appointment_container, course_family_allowed_by_block, course_fits_contiguous_block, remaining_fragment_can_support_small_course, duplicate_same_course_too_close_in_block, score_below_public_threshold
- 2026-06-22 11:30 AM AHA HeartCode BLS (Brian): suppressed because owned_appointment_container, course_family_allowed_by_block, course_fits_contiguous_block, remaining_fragment_can_support_small_course, duplicate_same_course_too_close_in_block, score_below_public_threshold
- 2026-06-22 12:30 PM AHA HeartCode BLS (Brian): suppressed because owned_appointment_container, course_family_allowed_by_block, course_fits_contiguous_block, remaining_fragment_can_support_small_course, duplicate_same_course_too_close_in_block, score_below_public_threshold
- 2026-06-22 1:30 PM AHA HeartCode BLS (Brian): suppressed because owned_appointment_container, course_family_allowed_by_block, course_fits_contiguous_block, remaining_fragment_too_small, duplicate_same_course_too_close_in_block, score_below_public_threshold
- 2026-06-22 2:30 PM AHA HeartCode BLS (Brian): suppressed because owned_appointment_container, course_family_allowed_by_block, course_does_not_fit_contiguous_block
- 2026-06-22 9:30 AM AHA ACLS Provider (Initial) (Brian): suppressed because owned_appointment_container, course_family_allowed_by_block, course_fits_contiguous_block, remaining_fragment_can_support_small_course, duplicate_same_course_too_close_in_block, score_below_public_threshold
