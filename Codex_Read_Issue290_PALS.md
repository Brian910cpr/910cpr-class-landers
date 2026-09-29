# Issue 290: corrected PALS baby hero

- Timestamp: 2026-09-25T02:42:51.962274+00:00
- Branch: `codex/pals-baby-art`
- Artwork/config commit: `2cfad1999549ce46745ce22750027d488ab1370f`
- State at this receipt: validated locally and pushed; production merge/deployment verification follows.

## Requested and implemented

Preserve the original **You got dis!** saying, with **Don't make this weird.** as the smaller tagline. Remove jumper lettering and the entire mask/bag/adult-hand equipment assembly. Remove colored matte fringes. Publish on the existing PALS selector.

The final artwork uses the original owner's speech bubble and the equipment-free baby edit already produced during this conversation. After the owner asked not to redraw it, final composition and edge cleanup were processed deterministically and locally with Sharp. The navy/white bubble and its wording were preserved from the original, not retypeset or regenerated. The stethoscope and heart remain on the jumper.

## Exact files

- `CUSTOMER_images/approved-course-characters/PALS-owner-original.png`: preserved user input.
- `CUSTOMER_images/approved-course-characters/PALS-baby-edit-source.png`: preserved equipment-free intermediate used for the body.
- `CUSTOMER_images/approved-course-characters/PALS-1.png`: final transparent master.
- `CUSTOMER_images/approved-course-characters/manifest.json`: provenance, dimensions, hash, derivative sizes.
- `scripts/prepare_pals_character.cjs`: deterministic connected-component extraction and inward edge antialiasing; uses existing bundled Sharp through NODE_PATH.
- `docs/images/characters/PALS-1.webp`: 960px version, 125214 bytes.
- `docs/images/characters/PALS-1-480.webp`: 480px version, 52600 bytes.
- `data/config/block_schedule_pages.json`: PALS hero source, alt text, character layout only.
- `docs/pals.html`, `docs/PALS.html`: narrowly regenerated selectors.
- `tests/test_family_course_art.py`: permits adding assets while asserting all required original and PALS sources are present; preserves size checks for every manifest asset.
- `Codex_Reply_Issue290_PALS.md`: this receipt.

## Local checks

- Character unit tests: 4 pass after updating the old hardcoded four-asset assertion for the new fifth asset.
- `node --check scripts/prepare_pals_character.cjs`: pass.
- Source integrity and `git diff --check`: pass.
- Browser inspected at 1280x900 desktop and 392x844 mobile: correct complete hero, clean edges on dark background, no horizontal overflow, two adjacent AHA logos, registration link present.
- Registration target: Enrollware ID 14130389. No registration was submitted.
- No schedule, course ID, price or booking logic changed. Renderer refreshes the existing availability query timestamp and versioned unchanged hero script reference.
- Existing Windows case-collision differences at `docs/Earl/index.html` and `docs/Jackson/index.html` are left unstaged and excluded.

## Production proof

Pending at this commit. Do not treat local validation as deployed. The agent will merge, wait for GitHub Pages, compare both public HTML URLs and both WebP assets, inspect desktop/mobile live rendering, and report the production result.

Recommended supervisor action: inspect this receipt and the final public PALS image. No owner action is required to continue deployment.
