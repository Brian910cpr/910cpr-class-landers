# Issue 363 — HSI catalog review and correction

- Timestamp: 2026-10-15 (America/New_York, UTC-04:00).
- Branch: codex/issue363-hsi-catalog-20261015
- Substantive commit SHA: be48e3cb45fd10161e7283f70ec5ab3fbe6f0011
- State: PR_OPEN — https://github.com/Brian910cpr/910cpr-class-landers/pull/405
- Evidence level: BUILT, validated locally. No operational end-to-end claim.

## Findings and work

Read full issue #363 and owner comment, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md, LANDERWARE_PROOF_AND_HEALTH_STANDARD.md and docs/CODEX_INSTRUCTIONS.md. Execution acknowledged on originating issue before implementation:
https://github.com/Brian910cpr/910cpr-class-landers/issues/363#issuecomment-6185207619

Original PR #364 was already merged. Existing catalog already had all requested rows. No duplicate course rows added; follow-up PR #405 contains explicit certification identities independent of delivery mode, reconciled product-code provenance, separate non-substitutable RSV and loaner logistics metadata, and owner print/guide five-unit pack prices as support inventory references. Missing values remain UNKNOWN. Existing 45-minute challenge template remains owner-requested metadata, not evidence of a tested program duration.

All 72 IDs/keys and scheduling fields preserved; all non-HSI rows unchanged. Exact coverage: 15 certification configurations x BL/CHALLENGE, one pair each. HSI BLS classroom 448630 preserved. Provider counts: HSI 36, AHA 17, ARC 17, USCG/AHA 2.

## Exact intended files

- data/config/course_catalog.json
- tests/test_hsi_catalog.py
- data/audit/issue363_hsi_catalog_review.md
- Codex_Reply_Issue363_HSICatalog_20261015TExecution_R1.md

Primary report and review entry: data/audit/issue363_hsi_catalog_review.md. Important JSON paths: courses[*].certification_identity, courses[*].external_hsi_product_id, courses[*].optional_review_template, courses[*].hsi_alternate_fulfillment_products, hsi_support_products.

## Validation

Command: python -B -m unittest tests.test_hsi_catalog -v
Result: Ran 4 tests in 0.003s; OK.

AST syntax validation, JSON parse and git diff --check passed. Base comparison proved all 72 course identities, duration, setup/cleanup buffers, default capacities, appointment permissions, relationships and delivery types preserved, and non-HSI rows identical.

Known unrelated catalog defect: duplicate course_key UNKNOWN on two non-HSI rows. Initial broad uniqueness assertion exposed it; HSI scope validated without changing those rows.

## Preservation and deployment

Original E:/GitHub/910cpr-class-landers dirty checkout was left untouched. Separate worktree E:/GitHub/910cpr-issue363-20261015 used. Unrelated modifications to docs/Earl/index.html and docs/Jackson/index.html appeared during execution in this worktree; preserved and excluded from explicit staging. No intentionally untracked artifacts from this assignment remain after receipt commit. No cleanup, reset, rebase or broad generator ran.

Substantive work pushed. Receipt is committed separately and pushed; final UI/issue receipt provides the pushed tip SHA (avoids self-referential SHA). No merge, deployment, remote migration, public HTML generation or scheduling cutover. Draft PR #372 untouched. Existing deep assignments preserved. Queue titles scanned; did not claim or disrupt other assigned streams.

## Limits and next action

No implementation blocker for this catalog correction. Review PR #405, especially catalog JSON, tests and primary audit. Merging and operational activation remain separate; issue is not claimed fully implemented at a customer surface. Legacy broad numeric titles retain unresolved age coverage and must not be guessed into exact configuration aliases. Course Master remains non-authoritative and unregenerated. Scheduling/card/eligibility and customer fulfillment proof remain required before activation.

No recurring process introduced; cadence, staleness monitor, observer health and last successful live proof are not applicable to this one-time catalog correction. No account-level action required for review. No new dependency on Brian as routine monitor introduced.
