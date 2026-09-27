# Issue 294, round 2: remove redundant mobile jump button

- Timestamp: 2026-09-26 10:18 UTC
- Branch: `fix/mobile-home-tighten-294`
- Implementation commit: `22c25b3bc2669ad903552b6f78faa51b2f68c1f4`
- State: PR_OPEN, pending checks, merge, deployment, and live verification
- Pull request: https://github.com/Brian910cpr/910cpr-class-landers/pull/296

Brian's mobile screenshot showed the newly added button scrolling to the immediately adjacent course tiles while occupying the opening screen. Removed the button from the homepage generator and generated HTML, shortened the hero sentence, and hid the duplicate finder heading/copy only on mobile. Desktop keeps its finder heading and all course links remain.

Changed files: `docs/index.html`, `docs/css/lander.css`, `scripts/build_index_and_sitemap.py`, `tests/test_growth_seo_surfaces.py`. Targeted homepage render test passed; `git diff --check` passed. No bulk generator run. The local browser executable remains unavailable for a mobile pixel screenshot. Deployment is pending as of this receipt; no user/account action currently required.

Next action: merge after checks, compare live HTML/CSS to the changed files, and confirm on a mobile viewport that course tiles appear directly after the short introduction.
