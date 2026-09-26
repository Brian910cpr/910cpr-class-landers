# Issue 294: Mobile homepage class finder

- Timestamp: 2026-09-26 10:10 UTC
- Branch: `fix/mobile-home-finder-294`
- Implementation commit: `57d83240bfc14147dabfc5dba58a5925df2203c5`
- Work-item state: PR_OPEN, pending checks, merge, deployment, and customer-facing verification
- Pull request: https://github.com/Brian910cpr/910cpr-class-landers/pull/295

## Finding and change

On widths of 700px or less, the homepage uses a flex column. The FAQ had no explicit `order` and therefore appeared before the hero, course finder, and provider badges. The mobile screenshot showed this failure. Explicit mobile order now shows hero, finder, badges, trust, FAQ, then locality. The hero and finder copy is shorter and the hero links directly to `#class-finder`. Course links, FAQ contents, metadata, and schema are preserved.

Files changed: `docs/css/lander.css`, `docs/index.html`, `scripts/build_index_and_sitemap.py`, `tests/test_growth_seo_surfaces.py`.

## Validation and limits

Targeted homepage render test passed; `git diff --check` passed. No bulk generator was run. Browser screenshot validation was unavailable locally because the Playwright Chromium executable is not installed. The existing course finder links to course pages where dates appear; this change does not add a calendar directly to the homepage.

Deployment status: branch and PR published; not yet merged or verified in production at the time of this receipt. Persistent-system proof classification does not apply to this static layout repair. No user or account action is required unless repository checks or merge protection demand it.

Next action: wait for source integrity checks, merge PR 295, confirm GitHub Pages deployment, and verify on the public mobile homepage that the hero and finder precede FAQ and badges, CTA reaches finder, and linked CSS is current.
