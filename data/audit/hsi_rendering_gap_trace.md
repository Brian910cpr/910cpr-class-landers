# HSI Rendering Gap Trace

Generated: 2026-06-28T14:59:21

## Summary

- Presentation-selected dynamic offers: `8`
- Rendered in HTML: `5`
- Missing from HTML: `3`
- Missing offer IDs: `['offer-371954-instructor_24057895173-20260704-1445', 'offer-449422-instructor_24057895173-20260704-1445', 'offer-463743-instructor_24057895173-20260704-1445']`

## Per-Offer Trace

| Offer | courseId | course_key | Course | Expected page | Expected tab | Public | Presentation | Hub model | HTML | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `offer-209808-instructor_24057895173-20260704-1445` | `209808` | `aha_heartsaver_cpr_aed_online` | AHA Heartsaver CPR AED Online | `docs/courses/heartsaver-cpr-aed.html` | `NO_TAB_MAPPING` | True | True | not_hsi_page | True | rendered_ok |
| `offer-251545-instructor_24057895173-20260704-1445` | `251545` | `aha_heartsaver_pediatric_first_aid_cpr_aed_online` | AHA Heartsaver Pediatric First Aid CPR AED Online | `docs/courses/heartsaver-cpr-aed.html` | `NO_TAB_MAPPING` | True | True | not_hsi_page | True | rendered_ok |
| `offer-329495-instructor_24057895173-20260704-1445` | `329495` | `aha_heartsaver_first_aid_cpr_aed_blended` | AHA Heartsaver First Aid CPR AED - Blended | `docs/courses/heartsaver-cpr-aed.html` | `NO_TAB_MAPPING` | True | True | not_hsi_page | True | rendered_ok |
| `offer-344085-instructor_24057895173-20260704-1445` | `344085` | `aha_heartsaver_cpr_aed` | AHA Heartsaver CPR AED | `docs/courses/heartsaver-cpr-aed.html` | `NO_TAB_MAPPING` | True | True | not_hsi_page | True | rendered_ok |
| `offer-371954-instructor_24057895173-20260704-1445` | `371954` | `hsi_adult_first_aid_cpr_aed_blended` | HSI Adult First Aid | CPR AED - Blended Learning | `docs/hsi.html` | `NO_TAB_MAPPING` | True | True | False | False | dropped_by_build_slug_hubs_no_APPOINTMENT_COURSE_TAB_IDS_mapping_for_course_key |
| `offer-445670-instructor_24057895173-20260704-1445` | `445670` | `hsi_bls_adult_first_aid_blended` | HSI BLS and Adult First Aid | Blended Learning | `docs/hsi.html` | `hsi-bls-fa` | True | True | False | True | rendered_ok |
| `offer-449422-instructor_24057895173-20260704-1445` | `449422` | `hsi_pediatric_first_aid_cpr_aed_blended` | HSI Pediatric First Aid | CPR AED - Blended | `docs/hsi.html` | `NO_TAB_MAPPING` | True | True | False | False | dropped_by_build_slug_hubs_no_APPOINTMENT_COURSE_TAB_IDS_mapping_for_course_key |
| `offer-463743-instructor_24057895173-20260704-1445` | `463743` | `hsi_bls_challenge` | HSI BLS Challenge | `docs/hsi.html` | `NO_TAB_MAPPING` | True | True | True | False | dropped_by_build_slug_hubs_no_APPOINTMENT_COURSE_TAB_IDS_mapping_for_course_key |

## Stage Answers
- **are_missing_assigned_to_page_card_that_does_not_render_dynamic_offers**: They are assigned to the HSI hub by family, but their course keys have no appointment tab mapping, so no HSI card/tab selects them for rendering.
- **course_key_tab_exists_but_suppressed**: No. The missing course keys do not have APPOINTMENT_COURSE_TAB_IDS entries; this is not normal suppression after tab match.
- **duplicate_course_card_dedupe**: No evidence. Presentation compaction selected these offers; duplicate-adjacent suppression already happened earlier.
- **hsi_page_only_one_dynamic_offer_per_card**: No. The page can render dynamic offers per mapped tab; only the mapped HSI BLS + Adult First Aid key renders.
- **card_course_key_mismatch**: Yes for missing HSI keys: selected course IDs are enabled, but build_slug_hubs lacks tab mappings for their course_key values.
- **course_master_vs_slug_hub_disagreement**: Course Master is non-authoritative. The operative disagreement is course_catalog course_key versus hard-coded APPOINTMENT_COURSE_TAB_IDS in scripts/build_slug_hubs.py.
- **344085_aheartsaver_on_hsi**: 344085 renders on Heartsaver page as AHA Heartsaver CPR AED. It should not be used as HSI CPR AED without explicit approval; treat as blocked fallback/mapping bug for HSI CPR AED.
- **dropped_by_build_slug_hubs**: Yes. build_slug_hubs.py builds offers but appointment_offers_for_tab only selects offers whose course_key maps to a tab in APPOINTMENT_COURSE_TAB_IDS.

## Safe Deployment Blockers
- Do not deploy HSI course ID enable-review branch while rendered proof is PARTIAL.
- Add/review HSI appointment tab mappings before enabling rendered public output for 371954, 449422, and 463743.
- Block or explicitly approve the 344085 AHA Heartsaver fallback before any HSI CPR AED card routes to it.
- Rerun rendered_dynamic_offer_proof and require PASS after any mapping fix.

## Recommended Next Fix

- File: `scripts/build_slug_hubs.py`
- Function/constant: `APPOINTMENT_COURSE_TAB_IDS / appointment_offers_for_tab`
- Recommendation: Add explicit HSI course_key to HSI tab mappings, then rerun pipeline. Likely mappings: hsi_adult_first_aid_cpr_aed_blended -> hsi-fa-cpr-aed or appropriate HSI first aid tab; hsi_pediatric_first_aid_cpr_aed_blended -> a pediatric HSI tab if present or create one deliberately; hsi_bls_challenge -> hsi-bls if Brian wants BLS Challenge on HSI BLS card. Do not map 344085 to HSI CPR AED without approval.
