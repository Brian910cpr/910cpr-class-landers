# Public Offer Policy Safety Check

Status: report only. No files were deleted, moved, deployed, or published.

## Safety Checks

- `unknown_course_key_rows_remain_suppressed`: True
- `unmapped_hsi_pediatric_449422_remains_suppressed`: True
- `hsi_344085_not_mapped_to_hsi_cpr_aed`: True
- `existing_real_enrollware_rows_still_render`: True
- `public_offer_integrity_passes`: True
- `course_master_review_gates_not_bypassed`: True
- `no_wrong_course_card_receives_bls_rows`: True
- `no_raw_enrollware_mirror_behavior_introduced`: True

## Large Generated Files

- `data/runtime/audit_previews/dynamic_offers_preview.json`: 98.69 MB
- `data/runtime/audit_previews/public_sellable_offers_preview.json`: 96.62 MB

Recommendation: keep these full generated previews only for short-lived review branches. Long-term, commit compact summaries and regenerate full previews locally or store them as CI/artifact outputs.
