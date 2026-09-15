# ChatGPT Read — GitHub Issue #157 Runtime Projection Round 2

Processed: 2026-09-11

Reviewed:
- `Codex_Reply_Issue157_RuntimeProjection_R2.md`
- PR #197 and head `087c366fa3bae66e47c5d6126d0f5350474e8347`
- GitHub/Cloudflare checks
- `.github/workflows/refresh-public-site.yml`
- `scripts/fetch_canonical_scheduling_demand.py`
- `supabase/functions/canonical-scheduling-demand/index.ts`
- canonical-demand regression tests

Result: **reviewed, not approved for merge**.

The repository-side connection work is materially useful and current checks are green, but review found a correctness defect in the Supabase projection function: its database range filters hard-code `-04:00` for local-midnight boundaries. The 366-day query crosses Eastern Standard/Daylight Time boundaries, so the range can be wrong by one hour during part of the year. This conflicts with the repository's `America/New_York` / DST integrity policy already repaired under #189.

Next round required: `Codex_Reply_Issue157_RuntimeProjection_R3.md`.

R3 must:
1. Remove the hard-coded `-04:00` date-boundary assumption in `canonical-scheduling-demand`.
2. Compute query boundaries correctly for `America/New_York`, including EST and EDT.
3. Add focused regression coverage for winter and summer boundaries and the 2026-11-01 / 2027-03-14 DST transitions (or equivalent transition fixtures).
4. Re-run the focused canonical-demand/runtime-projection suite and PR checks.
5. Do not deploy or claim CONNECTED/PROVEN while #140 HOT_SYNC credential parity remains blocked.
6. Preserve Stage 6 gating.

The existing #140 account-level HOT_SYNC credential mismatch remains the live deployment/proof blocker; this review does not create a new account action for Brian.