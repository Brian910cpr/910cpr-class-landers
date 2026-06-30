# Post-Merge Deploy Readiness Report

Generated: 2026-06-30T14:45:25
Branch: `codex/post-merge-deploy-blocker-sweep`
Base main commit: `f08e705221de82407d5a1e3ccaca3aacb924a22e`
Deploy performed: no

## Result

**Ready for deploy after Brian approval.**

## Copy Fixes

- `scripts/build_slug_hubs.py`: Heartsaver public inventory text now says `Don't see a time that works? Request a private or group class.`
- `scripts/build_universal_offer_inventory.py`: public-copy-shaped display note/report label no longer uses `appointment-backed`.

## Customer-Facing Jargon Sweep

- Public rendered pages scanned: 15
- Visible internal jargon hits: 0
- Public-copy source exact hits: 0
- `appointment-backed` remains in scanned rendered public docs: False
- No visible customer-facing internal jargon found in scanned public pages.

## BLS Rendered Proof

- August AHA BLS appointment seeds rendered: 6
- Initial / Renewal / HeartCode: 3 / 3 / 0
- Preferred 09:15 time preserved: True
- Duplicate selected seed rows: 0

## Large Preview Cleanup

- Giant preview JSON tracked files: 0
- Compact summaries tracked: 4
- Runtime previews ignored: True

## Validation Results

- PASS `python -m scripts.audit_august_bls_seed_quality`: 24 August BLS public sellable offers; 6 selected seeds; 6 rendered
- PASS `python -m scripts.audit_bls_seed_time_preference`: 6 rendered August BLS seeds; duplicate selected seed rows 0
- PASS `python -m scripts.audit_bls_public_offer_policy_enablement`: 24 August BLS public sellable offers; 6 selected seeds; 6 total selected seeds
- PASS `python -m scripts.audit_august_offer_explosion`: 20,901 August dynamic offers; 6,666 August BLS dynamic offers; 60 August public sellable offers; 6 selected seeds
- PASS `python -m scripts.audit_live_availability_snapshot_trace`: First divergence resolved_after_rrule_expansion; 29 August live blocks; 20,901 August dynamic offers
- PASS `python -m scripts.audit_august_seed_breakpoint`: First breakpoint resolved_at_dynamic_offers_preview
- PASS `python -m scripts.public_offer_integrity_audit`: Audit failed: False; public sellable total 418
- PASS `python -m unittest discover -s tests`: Ran 163 tests; OK

## Remaining Blockers

- None found. Human approval is still required before deployment.
