# Issue 390: calendar filter attention

Timestamp: 2026-10-13T21:22:00Z
Branch: fix/filter-attention-390
Commit: d2e946b9f15ec6c0b897bb0288c22a0412b598bb
State: MERGED
PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/391

Shared calendar filter adds approved copy and an 8-second, three-cycle glow. Checkbox change, Smart filter input and animation end remove the attention class. Clear does not restore it. Reduced-motion users receive no animation. Text stays steady. Source filtering logic is preserved.

Files: docs/assets/calendar-time-filters.js, docs/assets/calendar-time-filters.css, docs/bls.html, docs/acls.html, docs/pals.html, docs/heartsaver.html.

Checks: node syntax validation and focused DOM test passed for wording, change/input/end dismissal, no restart after Clear, existing filter constraints/callback, CSS duration/cycle count and reduced-motion override. Full browser visual verification unavailable locally because Chromium is absent. No broad generators or schedule changes.

Evidence level: BUILT; merged. Production asset verification pending at receipt creation. Next action: verify versioned assets and family pages on production after Pages deployment. No owner/account action required.
