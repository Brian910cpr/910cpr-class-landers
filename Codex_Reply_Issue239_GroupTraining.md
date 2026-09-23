# Issue #239 — group training conversion incident

Timestamp: 2026-09-23 UTC
Branch: `fix/group-training-incident`
Implementation commit: `371d32a6761856988b5b35867d9f61c1e0d57332`
Work-item state at this receipt: `IN_PROGRESS` — locally validated, production deployment and live verification pending.

## Findings and root cause

The live desktop page displayed the group request copy inside a 78 px date-tile column because the shared `.slug-pill` grid expected three children while group cards supplied two. The form's shared `.request-form-grid` reserved a sidebar column although the group form has only one child. The hero retained an empty image column, and four program tabs wrapped unevenly. The existing group Edge Function inserted a Production Board decision card without the structured `context_manifest.owner_action` now required by NOW's `boardPrompts`, so a received request would be missing from Brian's actionable NOW prompts.

Connected database read-only audit found zero `requirement_inquiries` matching group page/title/course and zero `production_board_cards` for `910CPR Group Training` at inspection time. Those counts do not measure page visits, abandoned submissions, or lost leads. GA4/GSC connector calls returned `INVALID_ARGUMENT`; historical visitor exposure is unresolved.

## Work performed

- Scoped layout overrides to `group-training-page`, including full-width group cards and form, four desktop program tabs, and responsive stacking.
- Updated the authoritative slug hub generator and its deployed group page, with a versioned CSS URL.
- Updated the group request Edge Function to attribute records to the canonical page and include a structured owner action that NOW can display.
- Updated the existing request test for canonical attribution and NOW prompt compatibility.

Changed files: `docs/css/lander.css`, `docs/group-training.html`, `scripts/build_slug_hubs.py`, `supabase/functions/group-request/index.ts`, `tests/group_request.test.mjs`.

## Validation and proof state

`node --test tests/group_request.test.mjs`: 4 passed, 0 failed. `python -m py_compile scripts/build_slug_hubs.py` and `git diff --check` passed. A targeted `render_page` and group-panel invocation confirmed the generator emits the layout hooks. No broad generator/build was run. Live before-state reproduced visually in a browser. This is `BUILT`, with database connection previously inspected; it is not yet `PROVEN`, `MONITORED`, or `HEALTHY` until merged, deployed, and real-surface checks pass. The group request endpoint currently reports active v1 with JWT verification enabled.

## Remaining work and exact next action

Push this branch, open and review a narrow PR tied to #239, merge after reporting verification, wait for GitHub Pages propagation, deploy the merged `group-request` source with `verify_jwt=true`, then verify desktop/mobile layout and a controlled end-to-end request with database receipt and NOW prompt. Remove synthetic test records after evidence capture. Audit traffic through a working analytics source before estimating affected visitors. No user-level or account-level action is needed for the repair.
