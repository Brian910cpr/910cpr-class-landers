# Family-page Dark/Light control restoration

- Date: 2026-11-08, America/New_York.
- Branch: `codex/restore-family-theme-20261108` (pushed).
- Implementation: `6639b2014b584c46c3205be20f4900a57ca0c844` and
  `40f946135f9af343744b6743a03324b3272aa907`.
- State at receipt: locally validated; production verification follows PR merge.

The live Heartsaver and BLS pages lacked both shared theme assets. Their common
renderer emitted light defaults without the existing theme includes. CSS was
not hiding the button: `docs/assets/site-theme.js` creates it, remembers the
`910cpr-color-theme` preference and sets `html[data-theme]`;
`docs/assets/site-theme.css` supplies the shared dark palette. The earlier
November 8 palette/cache repair (#448) remains intact.

Reused `THEME_TAGS` from `scripts/inject_global_theme_assets.py` in
`scripts/build_bls_block_schedule_pilot.py`. Added those same two asset references
to exactly these generated files, without rewriting their bodies or inventory:

```text
docs/bls.html
docs/BLS.html
docs/acls.html
docs/ACLS.html
docs/pals.html
docs/PALS.html
docs/heartsaver.html
docs/HEARTSAVER.html
docs/hsi.html
docs/arc.html
docs/family-cpr.html
docs/courses/uscg-first-aid-cpr-aed.html
```

`tests/test_inject_global_theme_assets.py` now renders all eight configured
families and checks the twelve published files/aliases. Focused validation:
`python -m unittest tests.test_inject_global_theme_assets tests.test_site_theme_contrast -q`
passed 11 tests. Python syntax checks passed. No shared CSS/JavaScript was changed.
The existing stylesheet URL uses current `THEME_VERSION` (`20261108.1`).

The scoped repair called the existing `inject_html` function for only the twelve
configured paths; it asserted all page bodies stayed identical. No inventory
builder or sitewide theme injection ran. To avoid the broad public generator
triggered by changing the renderer, merge with `[skip ci]` after PR checks pass
and request a GitHub Pages-only build through the Pages builds API. Then verify
all twelve live asset references and test the button, reload persistence, and
navigation to another family in a real browser. A static asset-reference check
alone is not completion.

The old checkout's unrelated Earl/Jackson edits were preserved. A sparse real
repository worktree was used after managed worktree setup stalled. Three tracked
Python cache files changed during initial imports and remain unstaged; no cache,
runtime, or inventory data is part of this repair. The four case-only aliases
were explicitly staged by blob SHA because Windows path matching collapses them.

This is a narrow visual repair, not a new persistent service or scheduling change.
