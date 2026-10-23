# Issue #360 ARC catalog dispatch
Timestamp: 20261015T041428Z (UTC)
Branch: codex/issue360-arc-catalog-20261015
Substantive commit: 0d5c186827eef332e4219cdb9a9c8d2ceb2bd21d
State: IN_PROGRESS; catalog foundation BUILT, activation BLOCKED.

Execution acknowledged on originating issue before implementation. Full issue/comments, AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos and proof standard read. Dependencies #359/#342 and draft #372 inspected. Existing open PRs and owner queue scanned; no separate safe backend quick win selected because current unrelated work has existing assignments/PRs and should not be duplicated.

Reused eight existing primary ARC products and six skills fulfillment rows. Added exact source names/effective date, two commercial routes per primary product, online-completion proof requirements, pricing field references and SEO identities. Decimal quote projection computes approved totals; unsupported fulfillment returns BLOCKED with null total. No new canonical course rows or guessed identifiers.

Exact files changed:
- data/config/course_catalog.json
- scripts/arc_catalog_pricing.py
- tests/test_arc_catalog_pricing.py
- docs/ARC_R25_CATALOG_PREPARATION.md
- Codex_Reply_Issue360_ARCCatalog_20261015T041428Z.md

Tests: python -B -m unittest tests.test_arc_catalog_pricing -v: 5 passed. AST syntax checks passed. JSON comparison: all non-ARC rows identical, all course IDs and existing capacities preserved. git diff --cached --check passed. No generator executed.

Exact blockers: Pediatric CPR/AED and BLS skills-only lack confirmed fulfillment SKU/cost policy in supplied source. Full price-list document not independently inspected; owner transcription preserved. #359/#403 still lacks complete holds/paid-seat projection, transactional last-seat proof and composed #342 shadow/customer proof. No production cutover authorized by this catalog preparation.

Deployment: persisted locally, intended files committed; this receipt is being pushed with branch. Not merged, not deployed, no customer-page/checkout proof. #372 untouched. Last successful production end-to-end proof: none for these commercial choices. Observer/observer health: unestablished; no new persistent process introduced.

Unrelated work preserved: original E:/GitHub/910cpr-class-landers dirty files untouched. Isolated worktree has unstaged docs/Earl/index.html and docs/Jackson/index.html edits; neither staged nor pushed. No cleanup or competing implementation stream.

Review handoff: docs/ARC_R25_CATALOG_PREPARATION.md contains exact reconciliation and gates; course JSON commercial_choices, pricing_rule, customer_product and arc_source_name fields plus both Python files are primary review targets. Existing issue #360 has no matching open PR; create a draft for these intended files only.

Next safe action: review catalog projection, confirm missing fulfillment rules against source document, finish #403 safety gates before activation. User/account action: no credential action required; business/source confirmation required for unsupported fulfillment mappings. Do not merge or deploy #372.
