# Group form cleanup

- Timestamp: 2026-09-26 America/New_York
- Branch: codex/group-form-cleanup
- Implementation commit: ced355e75a04690e33a62288bf28e0d7e6dab92f
- State: IN_PROGRESS; validated locally, production verification follows merge.
- Request: Remove the Request on-site BLS hero button and move explanatory content below the form.
- Changed: scripts/build_slug_hubs.py and docs/group-training.html. Removed the hero action and placed the complete audience/service-area/FAQ section after the request form.
- Validation: Python syntax compilation and git diff --check passed. Headless Edge at 1280px and 390px confirmed guidance below the entire form, button absence, and PALS tab updating the program field. No requests submitted.
- Existing suite blocked: tests.test_growth_seo_surfaces cannot import missing supervisor.status_snapshot. Importing its dependency also rewrote docs/Earl/index.html, docs/Jackson/index.html and four tracked Python caches; these are intentionally excluded from commits and remain uncommitted in the isolated worktree.
- No CSS or JavaScript changed. No broad generator run.
- Next action: merge the narrow PR, wait for GitHub Pages, verify live HTML and rendered order. No user action required.
