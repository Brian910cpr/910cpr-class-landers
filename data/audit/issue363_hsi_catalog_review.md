# Issue 363 HSI catalog review

2026-10-15, catalog-only, locally validated. No public build, scheduling cutover, merge or deployment.

## Findings and design

The existing seed `data/config/course_catalog.json` already contained all requested delivery rows and pediatric digital prices. This change adds explicit `certification_identity` independently of `delivery_type`, preserves numeric Enrollware identifiers and internal LW identifiers, and reconciles `external_hsi_product_id` with already recorded `hsi_product_code`. Missing BLS product identifiers remain `UNKNOWN`.

Incumbent evidence: `data/audit/hsi_public_course_matrix.md`, `data/audit/hsi_course_meaning_audit.md` and the catalog's seven legacy HSI Enrollware rows. Legacy broad course names do not establish exact age coverage. They remain preserved without guessing aliases to the new exact configurations. This preserves provenance while making internal identities independent of Enrollware. It is catalog preparation toward independence, not proof of a native operational replacement.

All 14 FA/CPR/AED and pediatric configurations plus BLS have exactly one explicit certification/delivery pair for BL and CHALLENGE (30 rows). Existing HSI BLS classroom 448630 is preserved. Legacy numeric rows coexist as unresolved legacy identities, not newly duplicated exact configurations.

Challenge rows require a written exam and skills evaluation with no instruction during evaluation. The separate optional non-certifying review starts at T-60; Challenge-only arrival is T; the existing 45-minute evaluation template is retained. That template is owner requested, not proof of a tested program-specific duration. Failure policy remains purchase the appropriate blended course and return later.

Existing RSV product references now explicitly prohibit substitution for in-person skills and require a separate delivery path. Loaner products are identified as logistics. Four owner-supplied five-unit print/guide products are preserved under `hsi_support_products` as support inventory references, not default fulfillment or stock records. Prices are per pack, not per card. No stock quantity or cost-per-student inference was added. Missing HRSV-PED-CI25 discounted price remains UNKNOWN.

## Validation

- `python -B -m unittest tests.test_hsi_catalog -v`: 4 passed. Read-only; no generator.
- Python AST syntax check and JSON parse passed.
- Compared against branch base: all 72 course IDs/keys preserved, all non-HSI course rows identical, and duration, buffers, capacity, appointment permission, relationships and delivery type unchanged for every course.
- `git diff --check`: passed.
- Provider counts: HSI 36; AHA 17; ARC 17; USCG/AHA 2. No new course rows were necessary.
- Known unrelated catalog defect: two non-HSI rows use course_key UNKNOWN; not changed.

## Limits and next action

Review the metadata and tests before merging this catalog-only PR. `data/config/course_master.json` remains a non-authoritative review artifact and was not regenerated. Promotion requires scheduling, pricing, card, eligibility and rendering review. Internal rows already contained scheduling defaults; this change neither validates nor activates those defaults. No public inventory or customer-facing output was changed; none is claimed verified. No recurring process was introduced (monitoring not applicable). Evidence level: BUILT with local catalog validation only.

Review paths: `data/config/course_catalog.json`, `tests/test_hsi_catalog.py`, this report, and the unique root Codex_Reply receipt. No account action is required for this review. Live fulfillment/scheduling proof remains a separate gated task.
