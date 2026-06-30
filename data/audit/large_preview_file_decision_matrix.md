# Large Preview File Decision Matrix

Recommendation: keep for PR review only; split large-file migration into a follow-up branch before deploy

## A_keep_large_previews_tracked_for_this_pr

Pros:
- Lowest functional risk for this release-candidate review
- Preserves exact audit reproducibility for the branch
- Avoids changing scheduling/build behavior during PR prep

Cons:
- GitHub will continue warning on files over 50 MiB
- Keeps nearly 195 MiB of generated JSON in the review branch
- Normalizes a repo hygiene problem if merged unchanged

Risk: Functional risk low; repository hygiene and GitHub warning risk high.
Recommendation: Acceptable for PR review only, not ideal for final merge/deploy.

## B_move_large_previews_to_ignored_runtime_debug_storage_now

Pros:
- Removes GitHub large-file warning from future commits if history is also handled
- Aligns generated previews with runtime/debug artifact policy
- Forces tests to depend on compact summaries instead of giant snapshots

Cons:
- Not trivial in this branch: many scripts, audits, docs-generation paths, and tests read exact current paths
- Would require a behavior-neutral but broad path/config migration
- Risk of invalidating the release candidate after all scheduling/rendering validation passed

Risk: Medium to high if done inside this release-candidate branch; low as a separate focused migration.
Recommendation: Do not implement inside this PR-prep step.

## C_merge_release_candidate_then_follow_up_before_deploy

Pros:
- Lets humans review the functional August fix immediately
- Separates scheduling/rendering risk from repo artifact policy risk
- Provides a clear gate: merge/review candidate now, migration before deploy

Cons:
- If merged before migration, large generated files remain in branch history
- Requires discipline not to deploy until follow-up is complete or explicitly waived
- May still require Git history/file-size policy decision

Risk: Operational risk low if deploy remains blocked; repo hygiene risk remains until follow-up completes.
Recommendation: Recommended path: PR review now, follow-up large-file migration before deploy unless Brian explicitly accepts keeping previews tracked.

## Exact Dependencies

### data/audit/dynamic_offers_preview.json
- Size: 98.57 MiB
- Tracked: True
- Required at runtime: False
- Required for static HTML runtime: False
- Required for docs generation: False
- Required for audits: True
- Required for tests: True
- Compact summary could replace full file: True

scripts (16):
- `scripts/audit_august_bls_seed_quality.py`
- `scripts/audit_august_offer_explosion.py`
- `scripts/audit_august_seed_breakpoint.py`
- `scripts/audit_bls_preferred_time_cap_blockers.py`
- `scripts/audit_bls_public_offer_policy_enablement.py`
- `scripts/audit_bls_seed_time_preference.py`
- `scripts/audit_forward_seeding_limiter.py`
- `scripts/audit_live_availability_snapshot_trace.py`
- `scripts/audit_release_candidate.py`
- `scripts/audit_rrule_expansion_fix.py`
- `scripts/build_universal_offer_inventory.py`
- `scripts/check_first_dynamic_booking_status.py`
- `scripts/filter_public_sellable_offers.py`
- `scripts/generate_dynamic_offers.py`
- `scripts/public_dynamic_inventory_proof.py`
- `scripts/public_offer_integrity_audit.py`

tests (3):
- `tests/test_august_offer_explosion.py`
- `tests/test_generate_dynamic_offers.py`
- `tests/test_public_offer_integrity_audit.py`

docs (2):
- `docs/enrollware_exit_roadmap_2027.md`
- `docs/scheduler_pipeline_operator_runbook.md`

data_reports (22):
- `data/audit/august_offer_explosion_breakdown.json`
- `data/audit/august_selected_seed_audit.json`
- `data/audit/bls_public_offer_policy_enablement_report.json`
- `data/audit/brian_shipyard_container_match_diagnosis.json`
- `data/audit/enrollware_exit_roadmap_summary.json`
- `data/audit/first_brian_shipyard_bls_filter_trace.json`
- `data/audit/first_brian_shipyard_bls_filter_trace.md`
- `data/audit/first_dynamic_booking_status.json`
- `data/audit/first_dynamic_booking_status_report.md`
- `data/audit/forward_seeding_limiter_trace.json`
- `data/audit/forward_seeding_limiter_trace.md`
- `data/audit/large_generated_audit_file_policy.md`
- `data/audit/live_availability_snapshot_trace.json`
- `data/audit/live_availability_snapshot_trace.md`
- `data/audit/minimum_fix_to_light_up_august.md`
- `data/audit/pii_worktree_audit_report.md`
- `data/audit/public_cta_display_layer_investigation.md`
- `data/audit/public_offer_policy_safety_check.md`
- `data/audit/release_candidate_final_report.json`
- `data/audit/release_candidate_large_file_policy.json`
- `data/audit/release_candidate_large_file_policy.md`
- `data/audit/seed_sim_vs_active_generation_diff.csv`

data_config (0):

### data/audit/public_sellable_offers_preview.json
- Size: 96.43 MiB
- Tracked: True
- Required at runtime: False
- Required for static HTML runtime: False
- Required for docs generation: True
- Required for audits: True
- Required for tests: True
- Compact summary could replace full file: True

scripts (21):
- `scripts/audit_august_bls_seed_quality.py`
- `scripts/audit_august_offer_explosion.py`
- `scripts/audit_august_seed_breakpoint.py`
- `scripts/audit_bls_initial_renewal_seed_balance.py`
- `scripts/audit_bls_preferred_time_cap_blockers.py`
- `scripts/audit_bls_public_offer_policy_enablement.py`
- `scripts/audit_bls_seed_render_handoff.py`
- `scripts/audit_bls_seed_time_preference.py`
- `scripts/audit_release_candidate.py`
- `scripts/audit_rrule_expansion_fix.py`
- `scripts/build_course_master.py`
- `scripts/build_slug_hubs.py`
- `scripts/build_universal_offer_inventory.py`
- `scripts/check_first_dynamic_booking_status.py`
- `scripts/dynamic_offer_presentation_policy.py`
- `scripts/export_course_master_review_sheet.py`
- `scripts/filter_public_sellable_offers.py`
- `scripts/public_dynamic_inventory_proof.py`
- `scripts/public_offer_integrity_audit.py`
- `scripts/rendered_dynamic_offer_proof.py`
- `scripts/select_schedule_seeds.py`

tests (3):
- `tests/test_august_offer_explosion.py`
- `tests/test_filter_public_sellable_offers.py`
- `tests/test_public_offer_integrity_audit.py`

docs (3):
- `docs/enrollware_exit_roadmap_2027.md`
- `docs/first_successful_dynamic_booking_checklist.md`
- `docs/scheduler_pipeline_operator_runbook.md`

data_reports (20):
- `data/audit/august_offer_explosion_breakdown.json`
- `data/audit/august_selected_seed_audit.json`
- `data/audit/bls_public_offer_policy_enablement_report.json`
- `data/audit/bls_seed_render_before_after.csv`
- `data/audit/bls_seed_render_handoff_trace.json`
- `data/audit/bls_seed_render_handoff_trace.md`
- `data/audit/brian_shipyard_container_match_diagnosis.json`
- `data/audit/dynamic_offer_presentation_policy_report.json`
- `data/audit/enrollware_exit_roadmap_summary.json`
- `data/audit/first_dynamic_booking_status.json`
- `data/audit/first_dynamic_booking_status_report.md`
- `data/audit/generated_preview_file_size_policy.md`
- `data/audit/large_generated_audit_file_policy.md`
- `data/audit/pii_worktree_audit_report.md`
- `data/audit/public_cta_display_layer_investigation.md`
- `data/audit/public_offer_policy_safety_check.md`
- `data/audit/release_candidate_final_report.json`
- `data/audit/release_candidate_large_file_policy.json`
- `data/audit/release_candidate_large_file_policy.md`
- `data/audit/schedule_seeds_preview.json`

data_config (1):
- `data/config/course_master.json`
