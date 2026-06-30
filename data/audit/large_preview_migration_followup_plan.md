# Large Preview Migration Follow-Up Plan

Decision: do not implement this migration inside the release-candidate PR-prep step. It is not trivial because current generators, docs-build scripts, audit scripts, and tests read the exact `data/audit/*_preview.json` paths.

## Proposed Follow-Up Branch
- Branch: `codex/large-preview-runtime-migration`
- Move full generated previews to ignored runtime/debug storage, for example `data/runtime/dynamic_offers_preview.json` and `data/runtime/public_sellable_offers_preview.json`.
- Keep compact tracked summaries under `data/audit/dynamic_offers_preview_summary.json` and `data/audit/public_sellable_offers_preview_summary.json`.
- Add representative small fixtures under `tests/fixtures/` for unit tests.
- Update `.gitignore` for full runtime previews.

## Code Changes Needed
- Update producers: `scripts/generate_dynamic_offers.py`, `scripts/filter_public_sellable_offers.py`.
- Update consumers: `scripts/build_slug_hubs.py`, `scripts/build_universal_offer_inventory.py`, `scripts/select_schedule_seeds.py`, `scripts/dynamic_offer_presentation_policy.py`, `scripts/public_offer_integrity_audit.py`, and the August/BLS audit scripts.
- Replace tests that assert large tracked files with compact summary and fixture assertions.
- Keep rendered HTML generation behavior unchanged.

## Validation Commands
- `python -m scripts.public_offer_integrity_audit`
- `python -m scripts.audit_august_bls_seed_quality`
- `python -m scripts.audit_bls_seed_time_preference`
- `python -m scripts.audit_bls_public_offer_policy_enablement`
- `python -m scripts.audit_august_offer_explosion`
- `python -m scripts.audit_live_availability_snapshot_trace`
- `python -m scripts.audit_august_seed_breakpoint`
- `python -m unittest discover -s tests`

## Safety Gate
Do not deploy until either this migration is complete and validated or Brian explicitly approves keeping the large generated previews tracked for the deploy branch.
