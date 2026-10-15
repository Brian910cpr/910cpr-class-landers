# Issue #276 — compact completed-class preparation

Timestamp: 2026-10-14 America/New_York
Branch: codex/issue276-compact-20261014
Substantive commit: 49713d34cbfc69a17ebcd6200fa1b51a3d2f292a
State: IN_PROGRESS; customer-facing integration BLOCKED on shared routing release gates.
Evidence: BUILT only; no production end-to-end proof.

## Execution and findings
Read the complete #276 body and all six owner comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Acknowledged actual execution before implementation at https://github.com/Brian910cpr/910cpr-class-landers/issues/276#issuecomment-6180361195.

Existing retirement code is in scripts/build_landers.py:retire_expired_static_lander_html; canonical completed presentation is lifecycle_presentation. Current completed pages retain the large ordinary template. Existing selector catalog is data/config/block_schedule_pages.json; public feeds are docs/data/block-selector-availability/*.json. No competing catalog was created.

Owner routing requirements: inline two-radio chooser under selected Register; needs HeartCode default goes to Enrollware bundle/payment/keycode fulfillment; already purchased/completed stays in LanderWare skills scheduling; selection is not payment/completion evidence; no change-course link.

Exact integration blocker: the universal scheduling gateway PR #275 is draft, BUILT only, unmerged with migration/function undeployed and database/adversarial proof gates outstanding. Shared selector/intake PR #382 remains WIP and its body explicitly prohibits merge/deployment as completion. #270 remains open. Implementing a second routing/calendar stack here would compete with those assignments. No existing #276 implementation PR was found in open PR inventory or searches; this branch is a narrow preparatory review slice and does not supersede #275/#382.

## Work performed
- scripts/completed_class_content.py: pure compact body renderer accepting trusted shared-calendar and crawlable fallback renderer output. Passed notice precedes calendar; fallback follows calendar; original course/date/location context remains; generic sales sections omitted. Caller must retain canonical head and diagnostics.
- Same module: exact course-ID resolver against existing selector configuration; unknown IDs fail closed. IDs 209809 and 329495 occur in both Heartsaver and USCG pages and deliberately fail closed until source context resolves ambiguity. No title-based family guesses, course substitutions, eligibility or payment assumptions.
- tests/test_completed_class_content.py: catalog mapping/feed existence, ambiguity/unknown handling, HTML escaping, ordering, compact size and absence of expired registration wording.

The module is intentionally NOT wired into scripts/build_landers.py. There is no claimed completed-page repair yet. Public acceptance checks, roughly-half-length comparison, calendar interactions, active-page byte comparison and browser/live verification remain outstanding. No generated public artifact was changed. No generator, database mutation, payment, merge or deployment ran.

## Local validation
Command: python -m unittest tests.test_completed_class_content tests.test_public_session_landers tests.test_retire_expired_public_pages
Result: Ran 16 tests in 0.041s; OK.
Syntax: AST parsing of both new Python files passed.
git diff --check: passed.
Tests exercise rendered component HTML in memory; this is not customer-facing proof.

Initial new mapping test exposed four catalog occurrences sharing two IDs; test now explicitly verifies those ambiguous IDs fail closed rather than declaring every catalog entry unique.

## Git hygiene and deployment
Original E:/GitHub/910cpr-class-landers dirty files, caches, receipts, and assignments preserved. Separate worktree E:/GitHub/910cpr-issue276-20261014 used. Unrelated docs/Earl/index.html and docs/Jackson/index.html became modified in the separate worktree during this run; origin of those concurrent changes is unknown. They were not staged or modified by this implementation, and were left intact.
Broad fetch failed with connection reset; targeted git fetch origin main --depth=1 succeeded. Base: 8e08de5ca5e (full base available via git parent).
Only the two new source/test files and this receipt are intended commits. PR #372 remains untouched, draft, unmerged and undeployed. No other assignments changed. No ops/handoff/next_task.md used.

Open issue queue and open PR inventory were scanned. Existing independent backend work already has review PRs (#397 payment provenance, #398 navigation, #396 overnight rules, #389 document validation, #381 execution preflight). This run advanced safe independent presentation/mapping backend preparation within #276 rather than starting another deep workstream or editing their branches.

## Next action and proof boundary
Continue existing #275/#382 shared routing workstreams. Once their reusable selector and approved routing contract are available, inject that renderer into this compact body, integrate both canonical and orphan retirement paths, and resolve ambiguous IDs using verified page/course context. Run a targeted one-page generation for /classes/14083302.html only after declaring its exact command/output count, preserve active pages, and validate browser/mobile/no-JS behavior and chooser destinations. Then follow normal reviewed production rollout gates; do not merge this preparatory slice as issue completion.

No account action is needed for the local component. #270/PR #387 separately records owner approval of isolated production-equivalent staging as an outstanding gate; this dispatch does not grant it. No health monitor or owner-as-observer dependency is introduced. Last production end-to-end proof for this feature: none. Success requires a current matching offer through the correct registration/fulfillment path from the expired public URL; monitoring/observer proof belongs to the eventual shared scheduling operational release.
