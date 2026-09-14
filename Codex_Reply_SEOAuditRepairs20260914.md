# SEO audit repairs, 2026-09-14

- Assignment: Repair the public SEO inventory lifecycle and conversion funnels found in the 2026-09-14 growth audit.
- Timestamp: 2026-09-14 15:00 UTC
- Branch: `codex/seo-audit-repairs-20260914`
- Substantive commit: `288116ee686`
- State at receipt creation: `IN_PROGRESS`, locally validated and awaiting push, review, merge, deployment, and customer-facing verification.
- Persistent-system evidence level: `BUILT`. The independent retirement workflow has not yet completed a real GitHub Actions cycle.

## Findings and root cause

- HOT_SYNC authentication failures stopped the normal availability workflows, allowing expired session pages and links to survive in production.
- Crawlable schedule content relied too heavily on the volatile near-term calendar.
- The group-training search authority and conversion form were split across three indexable pages.
- BLS and Heartsaver selector payloads repeated internal source objects for every public slot.

## Work performed

- Added a credential-independent hourly lifecycle workflow that retires expired class pages, removes expired registration/Event offers, applies `noindex,follow`, prunes stale related-course links, and removes retired URLs from the existing sitemap.
- Repaired three currently expired class pages and pruned stale class links from 41 generated pages.
- Added a crawlable projection of verified public Anchor sessions exactly 14 to 21 calendar days ahead. It derives from `docs/data/schedule_future.json`, fails closed, links to real class pages, and does not create or invent inventory.
- Preserved the interactive current-offerings calendar and its direct Enrollware handoff for customers.
- Consolidated group training onto `group-training.html` by embedding the existing functional request form. `group.html` is now a canonical noindex redirect alias, and `request_group_session.html` remains functional but is noindex.
- Compacted public selector JSON to remove unused repeated internal objects while retaining the fields consumed by the browser. Estimated decoded reductions are about 60 percent for the largest BLS and Heartsaver payloads.

## Files changed

- `.github/workflows/retire-expired-public-pages.yml`
- `scripts/build_bls_block_schedule_pilot.py`
- `scripts/build_request_group_session.py`
- `scripts/build_slug_hubs.py`
- `scripts/retire_expired_public_pages.py`
- `scripts/static_public_inventory_projection.py`
- `tests/test_growth_seo_surfaces.py`
- `tests/test_retire_expired_public_pages.py`
- `tests/test_static_public_inventory_projection.py`
- `docs/group-training.html`, `docs/group.html`, `docs/request_group_session.html`, `docs/sitemap.xml`
- 44 generated `docs/classes/*.html` files for current retirement/sidebar cleanup

## Validation

- `python -m unittest -q tests.test_static_public_inventory_projection tests.test_growth_seo_surfaces tests.test_retire_expired_public_pages tests.test_public_session_landers tests.test_ensure_analytics_tags`: 25 passed.
- `node --test tests/group_request.test.mjs tests/resolved_selector_availability.test.mjs tests/test_analytics_attribution.mjs`: 12 passed.
- Focused selector URL-preservation test: passed.
- Python compilation for modified scripts: passed.
- Workflow YAML parse: passed.
- Strict public link scan: 992 files, 41,815 links/buttons, 0 broken, 0 suspicious, 3 low-confidence manual-review items.
- `git diff --check`: passed.

## Known limitations and remaining risk

- The full block-selector suite requires the ignored private `data/sessions_current.json`, which is not present in this clean worktree. The relevant focused selector behavior passed.
- HOT_SYNC still returns `401 Unauthorized`. The new lifecycle workflow reduces the danger independently, but it does not restore fresh source availability.
- The repository implementation is not yet end-to-end proven until the pull request is merged, GitHub Pages is deployed, the public pages are checked, and the hourly retirement workflow completes successfully.

## Proof contract

- Expected outcome: expired pages stop making registration claims, current customer inventory stays interactive, and crawlers receive only verified 14-to-21-day Anchor sessions.
- Success evidence: a successful hourly workflow commit/no-op plus live-page checks of expired pages, core course pages, group form submission behavior, and registration links.
- Expected cadence: hourly retirement; normal availability publishing on its existing cadence.
- Failure condition: any expired public page remains indexable/bookable after the hourly window, or schedule artifacts exceed their normal freshness window.
- Observer: GitHub Actions plus the recurring 910CPR growth audit.
- Recovery path: rerun the retirement workflow for expiry defects; repair and rerun HOT_SYNC-backed workflows for inventory freshness defects.
- Escalation boundary: synchronizing the HOT_SYNC endpoint credential with the GitHub Actions secret requires account-level access if repository automation cannot rotate both sides.

## Next action

Push the branch, open and merge the pull request after checks, wait for GitHub Pages, verify the live customer paths, and observe one retirement workflow cycle. Separately synchronize the HOT_SYNC credential and rerun both availability workflows.
