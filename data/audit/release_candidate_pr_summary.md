# Release Candidate PR Summary

## Problem Fixed
August public schedule visibility was thin because the active dynamic-offer pipeline did not carry valid recurring August availability through to selected, rendered public BLS appointment rows.

## Root Causes Found
- Live availability snapshots originally stopped too early because recurring calendar availability was not expanded into August.
- AHA BLS course IDs were not enabled in the public-offer policy.
- Public-sellable caps were applied before BLS preferred-time ordering, so early low-preference times consumed caps.
- Seed selection favored Initial over Renewal until the selector balanced AHA BLS Initial/Renewal rows.
- Selected BLS appointment seeds had URL proof before they were wired into the `docs/bls.html` stacked-row rendering path.

## Key Fixes
- Expanded RRULE/RDATE/EXDATE availability into the live snapshot path.
- Narrowly enabled reviewed AHA BLS course IDs `209806`, `359474`, and `210549`.
- Applied AHA-BLS-only preferred-time ordering before public-sellable caps without increasing caps or enabling non-AHA rows.
- Balanced selected BLS Initial/Renewal seeds while preserving preferred 09:15 timing.
- Wired selected appointment seeds into BLS page rendering without hardcoded August rows.
- Added release-candidate audits for rendered proof, booking URL sanity, copy cleanup, and large-file policy.

## Current Rendered Result
- 6 August AHA BLS appointment seeds render in `docs/bls.html`.
- Existing real Enrollware BLS rows still render.
- Duplicate selected seed rows: 0.
- Seed buttons use customer-facing `Book This Class` copy.

## Safety Checks
- `UNKNOWN` rows remain suppressed.
- HSI pediatric `449422` remains suppressed.
- `344085` remains off the HSI page and is not mapped as HSI CPR/AED.
- Course Master gates remain downstream.
- RRULE expansion does not create public rows by itself; generated offers still require normal selection/gating/rendering.
- Public offer integrity passed.

## Tests and Audits Run
- `python -m scripts.audit_august_bls_seed_quality`
- `python -m scripts.audit_bls_seed_time_preference`
- `python -m scripts.audit_bls_public_offer_policy_enablement`
- `python -m scripts.audit_august_offer_explosion`
- `python -m scripts.audit_live_availability_snapshot_trace`
- `python -m scripts.audit_august_seed_breakpoint`
- `python -m scripts.public_offer_integrity_audit`
- `python -m unittest discover -s tests` (`163` tests OK)

## Known Remaining Issue
Large generated previews remain tracked:
- `data/audit/dynamic_offers_preview.json` about 98.57 MiB
- `data/audit/public_sellable_offers_preview.json` about 96.43 MiB

Recommendation: keep them for PR review only, then split a large-preview migration into a follow-up branch before deploy unless Brian explicitly approves keeping them tracked.

## Deployment Recommendation
Do not deploy from this PR yet. Human-review the release candidate and large generated preview decision first. Deploy only after the large-file decision is approved and the selected release path is validated.
