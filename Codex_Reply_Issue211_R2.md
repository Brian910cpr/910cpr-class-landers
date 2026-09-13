# Codex reply: Issue 211, round 2

- Timestamp: 2026-09-13 UTC
- Assignment: exclude internal/admin traffic and repair `910cpr.com` self-referral attribution
- Delivery branch: `codex/issue-211-analytics-attribution`
- Substantive commit: `a5caad9fd5dbe641c522bd90561021b8bd2c57b5`
- Merged production commit: `a751acbcb75bd90b02207636ad8078ef9c79a012`
- Pull request: #212, https://github.com/Brian910cpr/910cpr-class-landers/pull/212
- Work-item state: `VERIFIED` for internal exclusion and URL-level handoff; settled purchase attribution remains pending
- Persistent-system evidence: internal exclusion `PROVEN`; Enrollware handoff `PROVEN` at the URL boundary; purchase attribution not yet `HEALTHY`

## Findings and root cause

The internal-page leak was caused by an analytics normalizer that treated every rendered HTML file as public. The conversion-channel distortion was compounded by 910CPR-to-Enrollware handoffs that did not carry the current acquisition source, allowing `910cpr.com / referral` to become the apparent conversion source. The public and Enrollware measurement histories remain separate and unchanged.

## Work performed

- Removed GTM from all rendered `admin/`, `control-center/`, `internal/`, and `drafts/` pages and made that policy durable in the normalizer.
- Added a no-login, device-local analytics exclusion page. The public bootstrap checks the exclusion cookie before loading GTM.
- Added a public attribution bridge that decorates Enrollware enrollment URLs with source, medium, campaign, and page/session context.
- Added `begin_registration` at the outbound Enrollware handoff without duplicating the dated-availability event.
- Kept apex and `www` 910CPR traffic first party and preserved genuine `chatgpt.com / ai-assistant` attribution.
- Updated lander, selector, schedule, and index generators so scheduled rebuilds retain the repair.
- Did not change prices, advertising, customer commitments, GA4 account settings, GTM account configuration, or Enrollware measurement IDs.

## Exact files changed

- Analytics policy and bridge: `scripts/ensure_analytics_tags.py`, `docs/assets/analytics-attribution.js`, `docs/assets/date-availability.js`, `docs/admin/admin-nav.js`
- Durable generators: `scripts/build_landers.py`, `scripts/build_date_availability_pages.py`, `scripts/build_index.py`, `scripts/build_index_and_sitemap.py`, `scripts/build_schedule.py`, `scripts/build_public_schedule_json.py`, `scripts/build_bls_block_schedule_pilot.py`
- Device controls: `docs/analytics-preferences/index.html`, `docs/internal/analytics-preferences.html`
- Tests/audit: `tests/test_analytics_attribution.mjs`, `tests/test_ensure_analytics_tags.py`, `data/audit/issue_211_analytics_attribution.md`
- Rendered output: all 990 public HTML pages received the guarded loader and attribution bridge; all 34 internal/preference HTML pages are tag-free. The exact manifest is the changed-file list on PR #212.

## Tests and proof

- `python -m unittest tests.test_ensure_analytics_tags`: 6 passed.
- `node --test tests/test_analytics_attribution.mjs`: 4 passed.
- `python scripts/ensure_analytics_tags.py --check`: 1,024 scanned; 990 public pages correct; 34 internal pages clean; zero missing, duplicate, stale, malformed, or internally tagged pages.
- Cloudflare branch preview: deployed successfully and passed rendered checks.
- Production: four representative internal prefixes loaded zero GTM; the one-click exclusion state prevented GTM on a public page; an included public BLS page loaded GTM and decorated a real Enrollware class link with the original Google/organic attribution.
- Enrollware rendered `Class Enrollment` and retained the complete UTM query string.

## Remaining risk and next evidence gate

GA4 purchase attribution is not instantaneous and was not altered directly. The next normal reporting window must show a real post-deployment registration/purchase retaining its original source and a material reduction in `910cpr.com / referral` key events. Until then, do not label channel-to-purchase attribution `HEALTHY`.

Recommended next action: let normal traffic run, then compare Enrollware key events by source/medium after settled data arrives. User/account-level action is not required for the deployed code repair; a GA4 administrator is needed only if the URL bridge does not reduce self-referrals enough and account-side unwanted-referral or linker settings must then be changed.
