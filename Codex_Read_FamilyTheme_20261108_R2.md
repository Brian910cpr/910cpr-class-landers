# Live theme restoration: contrast follow-up

2026-11-08, America/New_York. Branch `codex/family-theme-button-contrast-20261108`.
Implementation `bd1ced43d842d0195384ec499fb72bb6d60f788d`, pushed.

PR #449 merged as `0cb1b8829c265710cd8ce59aca98b4f48bafcc22` and deployed through
GitHub Pages at 15:23:05 UTC. All twelve live paths return HTTP 200 and both theme
assets. Native Chrome applied the saved dark preference and the restored button
successfully switched to light mode.

Live visual QA exposed a remaining conflict: the renderer's generic
`button[aria-pressed="true"]` rule colored the theme switch as a selected course,
washing out its Light label in dark mode. Excluded `.site-theme-toggle` using
`:where(:not(...))` to preserve the original selector specificity for all other
buttons. Changed this single inline CSS selector in the renderer and the twelve
published family paths listed in the prior receipt. Shared CSS/JS files and
inventory are unchanged; no new asset version is required for inline CSS.

Eleven focused tests and syntax/diff checks pass. Three pre-existing tracked
Python-cache modifications remain unstaged. This follow-up uses the same
validated-PR / `[skip ci]` merge / Pages-only deployment procedure as #449.
Final live QA must verify the readable toggle in both themes, reload persistence,
and navigation to another family. This receipt records validated source before
the follow-up merge, not a premature claim that the visual follow-up is deployed.
