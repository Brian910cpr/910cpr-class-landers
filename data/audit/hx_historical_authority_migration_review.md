# Hx Historical Authority Migration Review

Review only: no production migration, historical import, or application deployment occurred.

## Full 8,199-record dry run

- Mode: **review_only_dry_run**
- Production Mutated: **False**
- Historical Import Performed: **False**
- Production Schema Rollback Validation: **{'independent_transactions_passed': 2, 'residual_schema_changes': 0, 'locations_after_rollback': 36, 'class_sessions_after_rollback': 365}**
- Preexisting Production State: **{'enrollware_history_sessions': 352, 'historical_key_locations': 27, 'unknown_historical_instructor_sentinels': 1, 'changed_by_this_review': False}**
- Source Records Examined: **8199**
- Historical Location Candidates: **126**
- Historical Location Rows Resolvable: **3837**
- Fully Canonicalized Sessions Before: **2063**
- Fully Canonicalized Sessions After Locations: **3439**
- Sessions Accepted Under Historical Contract: **3570**
- Sessions Accepted With Unknown Instructor: **105**
- Sessions Accepted With Unknown Duration: **27**
- Sessions Accepted With Both Unknown: **1**
- Remaining Unresolved Locations: **421**
- Remaining Course Ambiguity: **17**
- Remaining Identity Conflicts: **27**
- Deterministic Hash: **db2599897fc7de26021d0a7cffc1bf6a1e3906fe3121c5aa55de6f5df9e05527**
- Independent Hash: **db2599897fc7de26021d0a7cffc1bf6a1e3906fe3121c5aa55de6f5df9e05527**
- Independent Run Equality: **True**
- Replay Additional Operations: **0**
- Replay Additional Assertions: **0**
- Unexplained Mismatches: **0**
- Course Policy: **17 generic/ambiguous course rows remain review-required; no guessed merge**

## Candidate collision review

- Duplicate Candidate Keys: **0**
- Duplicate Candidate Names: **0**
- Exact Collisions With Existing Canonical Locations: **0**
- Source Only Not Created: **10**
- Ambiguous Not Created: **6**
- Production Drift Note: **27 pre-existing hist_location_* rows are source-distinct legacy placeholders; none exactly matches the 126 reviewed source labels**

## Production-state warning

Production already contains 352 `enrollware_history` sessions, 27 `hist_location_*` rows, and an Unknown Historical Instructor sentinel. They pre-date this review and were not created or changed here. The reviewed migration removes future sentinel substitution but does not rewrite those existing historical rows.

## Pre-existing security advisory

Supabase's advisor reports RLS disabled on seven pre-existing tables, including historical ingestion and compliance tables. This proposal does not touch them; its new audit table has RLS enabled and zero browser grants. The advisory requires a separate access-policy decision before those existing tables are browser-safe.
