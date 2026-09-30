# Issue 290 — deployed artwork and branding repair

- Assignment: https://github.com/Brian910cpr/910cpr-class-landers/issues/290
- Timestamp: 2026-09-25T02:13:00Z (2026-09-24 22:13 EDT)
- Branch: `codex/issue-290-course-art`, pushed.
- Implementation commit: `00863e84733aa085fd592d1e94baa578702b81c5`.
- Implementation PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/291 (merged).
- Production merge commit: `b61c05157fb4d0ea6d588e75ced2a3b8b53f0ef6`.
- Work-item state: **VERIFIED** — persisted locally, committed, pushed, merged, deployed through production GitHub Pages, and verified against the public site.
- Evidence level: **PROVEN** for this bounded visual repair. No claim that unrelated operational systems are healthy or continuously monitored.
- Production build: https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36085026581, success. Pages API reports `built`, commit `b61c05157fb4d0ea6d588e75ced2a3b8b53f0ef6`, updated 2026-09-25T02:10:02Z.

## Result and evidence

The first response in the Codex task opened the unrelated `openai/codex` issue 290. The correct assignment was then located in `Brian910cpr/910cpr-class-landers` and implemented.

BLS now uses responsive derivatives of the owner's 1312 × 1199 Anjla original, replacing the enlarged 150 × 137 source. ACLS shows the supplied RN, paramedic, and pharmacist artwork one per reload, starting with RN for a new session. The original poses, messages, banners, and transparent treatment are retained. No redraws or substitute artwork.

AHA logos appear beside course artwork in BLS, ACLS, PALS, Heartsaver, and Family & Friends selectors. The shared generator and numbered-file discovery make this survive normal rebuilds. Content hashes version changed image/script URLs. Existing useful decision copy was audited and retained.

At 2026-09-25T02:10:38.608298Z, all **19 public URLs returned HTTP 200 and matched the local committed content**: nine canonical/alias HTML pages, the changed JavaScript asset, the AHA logo, and all eight responsive character files. Exact URLs, hashes, lengths, and per-file results are in `data/audit/issue_290_live_verification.json`.

Live browser verification followed deployment at 1280 × 900 desktop and 392 × 844 mobile CSS viewports. All five pages loaded their hero art, showed an AHA logo beside each course image, populated calendars, and rendered registration links. No document horizontal overflow at either tested size. Logo/card counts were 2/2 BLS, 2/2 ACLS, 2/2 PALS, 3/3 Heartsaver, 1/1 Family & Friends. Production ACLS reloads visibly selected RN → paramedic → pharmacist. Local screenshots were inspected for BLS, ACLS, and Heartsaver; DOM checks covered every family at both sizes.

## Checks

- 24 Python tests passed: `tests.test_family_course_art` and `tests.test_family_cpr_page`.
- 8 Node tests passed: `tests/family_hero.test.mjs`; 1, 2, 3, 5, and 12-image rotation, disabled storage, removed previous file, failed-image fallback.
- Python syntax: four changed Python files; JavaScript syntax: new asset and ten inline scripts in the five rendered pages.
- Source-integrity, allowed case-collision inventory, and `git diff --check`: passed.
- PR checks: Source integrity and Cloudflare Pages preflight passed on push/PR; Cloudflare preview also passed. Production is GitHub Pages, independently verified above.
- Five HTML pages retain identical `courseOptions`, `optionGroups`, `availabilityUrl`, and `unsupportedOptions` compared with baseline `8529dc2910f37245b5582e4a5a9fb314d519c52c`.
- No changes to `docs/data/schedule_future.json` or `docs/data/block-selector-availability/`.
- Local mobile BLS Renewal selection produced course `359474`, dates, a start-time choice, and the expected Enrollware registration link. No customer registration was submitted.

The existing `tests.test_selector_mobile_progression` has two test methods with nine failing assertions expecting `function scrollToNextStep(targetId)`. That function was absent in all nine baseline paths before this change; current code uses `LanderWareMotion.progress`. This unrelated stale test was neither suppressed nor rewritten.

## Exact review files

Primary audit: `data/audit/issue_290_course_art.md`.

Live audit: `data/audit/issue_290_live_verification.json`.

Source/config/tests:

- `data/config/block_schedule_pages.json` — `pages.bls.hero_image`, `pages.acls.hero_image`.
- `scripts/build_bls_block_schedule_pilot.py` — hero rendering, size rules, grouped/ungrouped AHA image insertion.
- `scripts/family_course_art.py` — existing-file discovery, numeric order, hashes, responsive markup.
- `scripts/refresh_selector_presentation.py` — named-page HTML-only regeneration.
- `docs/assets/family-hero.js` — one character per visit/reload, bounded fallback.
- `tests/test_family_course_art.py`.
- `tests/family_hero.test.mjs`.

Rendered HTML:

- `docs/bls.html`, `docs/BLS.html`.
- `docs/acls.html`, `docs/ACLS.html`.
- `docs/pals.html`, `docs/PALS.html`.
- `docs/heartsaver.html`, `docs/HEARTSAVER.html`.
- `docs/family-cpr.html`.

Preserved originals and provenance:

- `CUSTOMER_images/approved-course-characters/BLS-1.png`.
- `CUSTOMER_images/approved-course-characters/ACLS-1.png`.
- `CUSTOMER_images/approved-course-characters/ACLS-2.png`.
- `CUSTOMER_images/approved-course-characters/ACLS-3.png`.
- `CUSTOMER_images/approved-course-characters/manifest.json`.

Public derivatives:

- `docs/images/characters/BLS-1.webp`, `docs/images/characters/BLS-1-480.webp`.
- `docs/images/characters/ACLS-1.webp`, `docs/images/characters/ACLS-1-480.webp`.
- `docs/images/characters/ACLS-2.webp`, `docs/images/characters/ACLS-2-480.webp`.
- `docs/images/characters/ACLS-3.webp`, `docs/images/characters/ACLS-3-480.webp`.

All 30 implementation files are listed by `git show --stat 00863e84733aa085fd592d1e94baa578702b81c5`. This receipt and the live audit are the subsequent evidence-only commit.

## Remaining conditions and next action

No binary-asset, credential, permission, or deployment blocker remains. No user/account action is required. The existing lower-panel dark-mode contrast and stale mobile-progression tests are outside this artwork repair. An exploratory 294-pixel viewport overflowed; the supported verification here is the measured 392-pixel mobile viewport, which passed.

The original checkout remains on its Rachel phone-intake branch. The isolated worktree is `D:/Users/ten77/Documents/2020 -_ 2025 & Enrollware/910cpr-issue-290`. Five unrelated local modifications are intentionally excluded: `docs/Earl/index.html`, `docs/Jackson/index.html`, and tracked bytecode for `build_seed_appointment_url_preview`, `generate_dynamic_offers`, and `local_data_paths`. These arose from Windows case-alias checkout and initial Python import. No intentional source or audit is left untracked after the evidence commit.

ChatGPT next action: inspect the linked PR and live BLS/ACLS pages, read the two audit files and original-image manifest, then acknowledge this receipt using the established protocol. Issue 290 remains open for owner/supervisor acceptance; the public repair itself is deployed and verified.
