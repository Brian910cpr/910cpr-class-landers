# Issue 290 PALS: production verified

- State: VERIFIED; deployed on GitHub Pages.
- Verification time: 2026-09-25T02:44:49.050626+00:00
- Branch: `codex/pals-baby-art` (pushed).
- Source commit: `a6b4ed9fad4559d15d8129d588bf49dd4ab962e1`.
- Production merge: `f2ffc730b7f8e5f3fd34371f1ed98dd7b669cf4f`.
- Merged PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/293
- Successful production run: https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36087451153
- Public page: https://www.910cpr.com/pals.html

The final live image preserves the original **You got dis!** saying and **Don't make this weird.** tagline. The mask, bag and adult hand are removed; jumper lettering is removed; stethoscope/heart icons remain. Final composition and transparent edge cleanup were processed locally from existing art after the owner requested no more drawing.

All five checked URLs returned HTTP 200 and matched committed bytes: `/pals.html`, `/PALS.html`, both versioned PALS WebP images, and the referenced shared hero script. Exact hashes and URLs are in `data/audit/pals_baby_art_live_verification.json`.

Live browser proof: 1280x900 desktop and 392x844 mobile rendered the correct complete image with no horizontal overflow. Two adjacent AHA logos were present, the hero loaded, and the Enrollware registration link for ID 14130389 resolved from the selector. No registration was submitted. The live desktop/mobile screenshots were inspected in the browser tool, not saved as repo files.

Four focused character tests passed, along with source integrity, approved case-collision checks, Node syntax and diff validation. PR checks and Cloudflare preview passed. `Codex_Reply_Issue290_PALS.md` lists exact changed source/artwork files and explains the original four-asset assertion update.

Existing case-collision changes at `docs/Earl/index.html` and `docs/Jackson/index.html` remain unstaged, unrelated and excluded. All intended files are persisted and pushed; nothing intentionally left untracked. This final evidence-only commit is pushed on the review branch; PR 293 already deployed all public changes.

Recommended next action: review the live PALS page. No owner action is required to complete publishing. Issue 290 stays open for owner's broader acceptance.
