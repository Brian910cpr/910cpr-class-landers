# Issue 290 — approved course artwork repair

Validated locally on 2026-09-25 UTC. Production verification will be recorded in the root Codex reply receipt after deployment.

## Findings and implementation

- The live BLS hero was `/images/bls-9to1-nurse.webp`, a 150 × 137 raster enlarged in the hero. The approved original is 1312 × 1199.
- ACLS used generic course artwork in the hero, with none of the supplied nurse, medic, or pharmacist characters.
- Both course-card render branches created only the course image; neither appended the AHA logo.
- Original owner-provided PNGs are preserved under `CUSTOMER_images/approved-course-characters/`. `manifest.json` records the original attachment filenames, SHA-256 hashes, dimensions, and derivative sizes. No artwork was generated or redrawn.
- Responsive 480/960-pixel WebP derivatives retain the original poses, lettering, banners, and transparency. Mobile derivatives range from 46,468 to 94,508 bytes. Conversion used Pillow RGBA, Lanczos proportional reduction, WebP quality 90, method 6; no upscaling.
- `scripts/family_course_art.py` discovers only existing `ACLS-<number>.webp` files, sorts numerically, and emits content-versioned URLs and optional responsive variants. Gaps are supported. Additional approved numbered WebPs join the next normal build; no browser probing for nonexistent filenames.
- `docs/assets/family-hero.js` selects the nurse first, then advances one character on reload using session storage. There is no timer or slideshow. Disabled storage retains a usable default; missing images fall back through the published list with bounded retries.
- `scripts/build_bls_block_schedule_pilot.py` renders the approved hero assets and puts `/images/0aha.png` next to course art in grouped and ungrouped AHA cards.
- `scripts/refresh_selector_presentation.py` provides a narrow presentation-only rebuild. The ordinary production builder uses the same renderer and artwork discovery.
- The existing useful BLS/ACLS/PALS/Heartsaver decision copy was preserved. Family & Friends already states audience, adult/child/infant CPR, AED, choking response, $45 per person, no certification card, and no test; those facts were preserved.

## Scope

Command: `python -m scripts.refresh_selector_presentation bls acls pals heartsaver family_cpr`

HTML output scope: `docs/bls.html`, `docs/BLS.html`, `docs/acls.html`, `docs/ACLS.html`, `docs/pals.html`, `docs/PALS.html`, `docs/heartsaver.html`, `docs/HEARTSAVER.html`, `docs/family-cpr.html`.

No availability rebuild, full site generator, course-ID edit, price edit, registration-route edit, or schedule JSON change. The authoritative renderer also refreshes the existing static confirmed-class section from the unchanged canonical public schedule.

## Local validation

```
python -m unittest tests.test_family_course_art tests.test_family_cpr_page
Ran 24 tests
OK

node --test tests/family_hero.test.mjs
tests 8 / pass 8 / fail 0

Python syntax OK: 4 files
Inline JavaScript syntax OK: 10 scripts across the five pages
Source integrity OK: no tool-truncation markers detected.
Validated 6 approved collision groups; no new collisions found.
git diff --check: passed
```

Compared the five new HTML pages against baseline commit `8529dc2910f37245b5582e4a5a9fb314d519c52c`: `courseOptions`, `optionGroups`, `availabilityUrl`, and `unsupportedOptions` are identical. `docs/data/schedule_future.json` and `docs/data/block-selector-availability/` have no diff.

Browser checks used actual CSS viewports of 1280 × 900 and 392 × 844. All five pages had no document horizontal overflow; hero images loaded, every course-art card had its adjacent AHA image, calendars populated, and registration links rendered. Card/logo counts: BLS 2/2, ACLS 2/2, PALS 2/2, Heartsaver 3/3, Family & Friends 1/1. Screenshots were visually inspected in the Codex browser.

BLS Renewal was selected in the mobile browser: selected course ID `359474`, 8 date controls, 1 start-time control, and registration link to Enrollware class `14135037`. No registration was submitted.

Actual ACLS reload checks: RN → paramedic → pharmacist → RN; all selected files loaded. Automated tests cover 1, 2, 3, 5, and 12 assets, missing numbers, removed previous assets, disabled storage, and failed-image fallback.

## Existing unrelated failures and workspace conditions

`tests.test_selector_mobile_progression` has two test methods with nine failing assertions requiring the old `function scrollToNextStep(targetId)`. That function was already absent in all nine tested baseline paths, including untouched pages and the generator. The current implementation uses `LanderWareMotion.progress`; this artwork change does not alter it. The stale test was not rewritten to hide the failure.

Existing dark-mode contrast problems in lower supporting-info panels were visible during inspection; the artwork/card changes do not modify global theme assets.

The original checkout remains on `codex/rachel-phone-intake-20260910`. Work is isolated in `D:/Users/ten77/Documents/2020 -_ 2025 & Enrollware/910cpr-issue-290`, branch `codex/issue-290-course-art`. Windows checkout produces existing Earl/Jackson case-alias differences; three tracked Python bytecode files also changed on initial import. None are staged or part of this repair.
