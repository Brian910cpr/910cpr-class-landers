# Codex reply: Issue 148, round 2

- Timestamp: 2026-09-11 18:30 America/New_York (UTC-04:00)
- Assignment: GitHub issue #148, `[CODEX] Rebuild group-training business funnel with durable requests`
- Branch: `codex/issue-148-funnel-r2`
- Substantive branch commits: `cce91aad696`, `7d2d59dc4a9`, `92abee2c325`
- Work-item state: `BLOCKED`
- Persistent-system evidence state: `BUILT` (local implementation and tests exist; remote Supabase integration, alerts, production deployment, and current end-to-end proof are not established)

## Findings and root cause

The current `main` group-request form posts to `action="#"`, so Issue #148's durable persistence and staff-alert requirements remain unmet. Closed PR #149 and `origin/codex/group-training-funnel` contain a prior implementation with a guided static funnel, availability-derived preferred-time validation, an idempotent Supabase transaction, privacy-safe analytics, authority pages, and local tests. That work was never merged or production-deployed.

Issue #168 remains open, but its documented next action is external GitHub scheduler monitoring/support and it explicitly forbids further repository scheduler changes. This direct #148 dispatch was therefore treated as activation of the customer-facing workstream; no #168 files or logic were intentionally changed.

## Work performed

- Read the full Issue #148 body and all comments, Issue #168 dependency/status history, repository `AGENTS.md`, root `CODEX_HANDOFF_PROTOCOL.md`, and `LANDERWARE_PROOF_AND_HEALTH_STANDARD.md`.
- Preserved the unrelated dirty checkout at `E:\GitHub\910cpr-class-landers` and created the isolated worktree `E:\GitHub\910cpr-class-landers-issue148-r2` from `origin/main` at `a74edc0f710e1d0f24074af369f429eebce15df0`.
- Recovered the scoped substantive history from closed PR #149 onto this branch while excluding historical schedule/runtime churn and the deleted oversized archive.
- Preserved current-main `docs/sitemap.xml` during conflict reconciliation pending authoritative regeneration.
- Did not merge, deploy, modify production, or use `ops/handoff/next_task.md`.

## Intended files in the recovered implementation

- `docs/group-training.html`
- `docs/request_group_session.html`
- `docs/assets/group-training.css`
- `docs/assets/group-training.js`
- `docs/group-training/*/index.html` (12 retained industry/location pages)
- `scripts/build_group_authority_pages.py`
- `scripts/build_index_and_sitemap.py`
- `scripts/build_request_group_session.py`
- `supabase/functions/group-training/core.mjs`
- `supabase/functions/group-training/index.ts`
- `supabase/migrations/20260906010000_group_training_requests.sql`
- `tests/group_training_funnel.test.cjs`
- `tests/test_group_training_public.py`
- `data/audit/group_training_funnel_audit.md`
- `data/audit/group_training_image_inventory.md`
- `data/audit/chatgpt_handoff_group_training_funnel.md`
- `data/audit/group-training-screenshots/*`

## Tests and checks

- `node --check docs/assets/group-training.js`: PASS
- `node --check supabase/functions/group-training/core.mjs`: PASS
- `node --test tests/group_training_funnel.test.cjs`: PASS (1 suite, 1 test)
- `python -m py_compile scripts/build_group_authority_pages.py scripts/build_request_group_session.py scripts/build_index_and_sitemap.py`: PASS
- `python -m unittest tests.test_group_training_public tests.test_growth_seo_surfaces tests.test_public_css_references tests.test_public_semantic_routes`: 21 tests run; 19 PASS, 2 FAIL
  - Issue-specific failure: authority URLs were absent from the preserved current-main sitemap.
  - Known unrelated failure: 127 canonical public schedule IDs lack matching checked-in class landers in this sparse/current checkout, matching the pre-existing failure documented by PR #149.
- `git diff --check origin/main...HEAD`: PASS before the generator attempt.

## Exact blocker

Before running a generator, I reported this expected scope: `python scripts/build_index_and_sitemap.py` should write `docs/index.html` and `docs/sitemap.xml` (2 files). The command actually produced 32 worktree status entries, exceeding the repository's greater-than-10 unexpected-file stop gate:

- 7 generated/status outputs beyond the expected pair: `data/runtime/build_index_and_sitemap.json`, `data/state/supervisor_status.json`, `debug/status/build_index_and_sitemap.json`, `docs/classes/index.html`, `docs/courses/index.html`, `docs/locations/wilmington-shipyard-blvd-b.html`, plus the expected `docs/index.html`; `docs/sitemap.xml` was also changed as expected.
- 18 tracked `__pycache__/*.pyc` files changed.
- 7 untracked `__pycache__/*.pyc` files appeared.

Per the Narrow-Change Gate, execution stopped immediately. None of those uncommitted generator/cache changes were staged, committed, or pushed. They remain isolated in the round-2 worktree for scope review. The generator reported scanning 115 class pages, parsing 115, and reading 25 public sessions before writing root/classes/courses/location/sitemap outputs.

## Deployment and proof status

- Local validation: partial, as listed above.
- Push: required receipt branch push is intended; see the receipt commit/tip reported in the Codex UI.
- PR: not opened in this round because the unexpected generator scope requires review first.
- Merge: not performed.
- Production deployment: not performed.
- Supabase migration/function deployment: not performed; no current preview/production integration proof.
- Staff alert proof: absent.
- Last successful end-to-end proof: none for the durable group-request flow.
- Failure/staleness condition: a public request that does not create the expected durable request/activity records and alert staff, or accepts a stale/invalid preferred time.
- Observer: not established for the full request-to-staff-alert outcome.
- Observer health: not established.

## Remaining risks and exact next action

The recovered group hub replaces newer current-main static sales/SEO content and is not yet wired into the current authoritative `build_slug_hubs.py` source, so merging it as-is risks future regeneration drift. The Supabase schema/function also needs review against the registration/backend changes merged after PR #149.

Recommended next action for ChatGPT: review this receipt and the three substantive commits, then authorize either (a) discarding only the isolated generator/cache worktree changes and continuing a surgical reconciliation into current `build_slug_hubs.py`, or (b) accepting the broader 8-output index/sitemap generator scope. After that, rerun the issue-specific tests, review the Supabase migration/function against current schema, deploy to preview, prove persistence/idempotency/stale-choice rejection/staff alerts, perform current desktop/mobile/accessibility/GTM checks, and only then open a new PR.

User/account-level action is required later for preview/production Supabase secrets and GTM/GA4 verification if they are not available to Codex. No user action is required to preserve the current production site; this branch has not been merged or deployed.
