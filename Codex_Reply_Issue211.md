# Codex reply: Issue 211

- Timestamp: 2026-09-12 20:15 EDT (UTC-04:00)
- Assignment: GitHub issue #211, repair analytics attribution and exclude internal/admin traffic
- Branch: `codex/issue-211-analytics-attribution`
- Substantive commit: `c1e50eb21aad99c1160e09539efa9a54f4c314d5`
- Pull request: #212, https://github.com/Brian910cpr/910cpr-class-landers/pull/212
- Work-item state: `PR_OPEN`; account-side cross-domain proof is `BLOCKED`
- Persistent-system evidence: repository boundary `PROVEN` locally; device preference `BUILT`; cross-domain attribution not yet `CONNECTED`, `MONITORED`, or `HEALTHY`

## Findings and root cause

The global analytics normalizer treated all `docs/**/*.html` as public and had placed GTM on 31 internal/control pages. Before this branch, rendered production `/admin/dashboard.html` and `/control-center/` both returned HTTP 200 with `GTM-PQS8DCBH`. The published container resolves to the single Google tag `G-45PBWBK7KR`, fired on `gtm.init` with no detectable path or device-exclusion predicate.

The public site and Enrollware use separate hostnames. The observed `910cpr.com / referral` conversion concentration is consistent with missing/broken cross-domain continuity, but is not proven as the sole cause. Enrollware returned HTTP 403 to unauthenticated inspection, and this environment has no authenticated GTM/GA4/Enrollware UI. The legacy Enrollware measurement ID, `_gl` receipt, checkout continuity, and purchase attribution therefore could not be verified safely.

## Work performed

- Made `admin/`, `control-center/`, `internal/`, and `drafts/` analytics-free in the authoritative tag normalizer.
- Removed both executable and noscript GTM blocks from all 31 currently tagged internal pages.
- Added `/internal/analytics-preferences.html`, a reversible no-login device-local cookie control. It does not filter ChatGPT or any other referral source.
- Recorded the exact same-ID GTM/GA4 configuration, cross-domain, unwanted-referral, rendered transaction-proof, monitoring, and escalation gates in `data/audit/issue_211_analytics_attribution.md` under `LANDERWARE_PROOF_AND_HEALTH_STANDARD.md`.
- Did not run any schedule, course, location, session-lander, or full-stack generator.

## Exact files changed

- `scripts/ensure_analytics_tags.py`
- `tests/test_ensure_analytics_tags.py`
- `data/audit/issue_211_analytics_attribution.md`
- `docs/internal/analytics-preferences.html`
- `docs/internal/inventory.html`
- `docs/drafts/nhcso-lite/index.html`
- `docs/admin/admin-port.html`, `class-registry.html`, `dashboard.html`, `financial.html`, `instructor-class-intake-prototype.html`, `instructor-session.html`, `instructor-workbench.html`, `nhcso-training-history-v5.html`, `nhcso-training-workspace-prototype.html`, `nhcso-training-workspace-v3-prototype.html`, `nhcso-training-workspace-v4-prototype.html`, `nhcso-training-workspace-v6.html`, `payments.html`, `production.html`, `refresh-availability.html`, `schedule-reader.html`, `scheduling-landscape.html`, and `toolbox.html`
- `docs/control-center/index.html`, `inventory/index.html`, and module pages `audit-center.html`, `class-mapping-tree.html`, `diagnostics.html`, `facebook-post-machine.html`, `feature-registry.html`, `inventory-control.html`, `lander-builder.html`, `task-prompter.html`, and `theme-builder.html`

## Tests and results

- `python -m py_compile scripts/ensure_analytics_tags.py tests/test_ensure_analytics_tags.py`: passed.
- `python -m unittest tests.test_ensure_analytics_tags -v`: 5 tests passed.
- `python -m scripts.ensure_analytics_tags --root docs --check`: 1,018 pages scanned; 985 public pages correctly tagged; 33 internal pages tag-free; zero internal tagged, missing, duplicate, or malformed pages.
- Production pre-change HTTP/HTML inspection: homepage, `/admin/dashboard.html`, and `/control-center/` returned HTTP 200; all three contained the GTM container. This branch is not merged/deployed, so no post-deployment production claim is made.

## Deployment and unrelated state

- Persisted locally: yes, isolated worktree `E:\GitHub\910cpr-class-landers-issue211`.
- Pushed: yes.
- Merged: no.
- Deployed: no.
- Production verified after deployment: no.
- Known unrelated state: fresh Windows worktree checkout reports an unstaged `docs/Earl/index.html` case-collision/content mismatch. It was present before issue work, was not staged, and is not in either commit. Open PR #210 also edits two admin files; any merge conflict should preserve its content while retaining removal of the GTM blocks.

## Exact blocker and next action

An authenticated GTM/GA4 and Enrollware operator must follow `data/audit/issue_211_analytics_attribution.md`: configure the existing `G-45PBWBK7KR` tag to honor `analytics_excluded=1`, add the internal-path exception, configure `910cpr.com` to `coastalcprtraining.enrollware.com` cross-domain linking and 910CPR unwanted referrals, and verify that Enrollware already uses that same legacy ID. Do not add another Enrollware measurement ID. Then perform a fresh rendered public CTA-to-Enrollware test through purchase/DebugView and prove original-source attribution. Genuine ChatGPT/AI referrals must remain unfiltered.

Recommended ChatGPT action: review PR #212, reconcile the two small admin-file overlaps with PR #210, merge/deploy the repository boundary, verify live HTML has no GTM on all four internal prefixes and that the preference page renders, then arrange the authenticated account-side configuration and end-to-end purchase proof. User/account-level action is required for the GTM/GA4/Enrollware configuration and transaction proof.
