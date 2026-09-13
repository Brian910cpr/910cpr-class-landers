# Issue 211 analytics attribution audit

Audit date: 2026-09-12 EDT / 2026-09-13 UTC

## Scope and evidence

This audit covers the rendered GitHub Pages site, the published GTM container, repository analytics injection, internal/control surfaces, the device-local exclusion contract, and the public-to-Enrollware handoff. It does not claim access to the Google Analytics or Enrollware account UI.

Observed production evidence before this change:

- `https://www.910cpr.com/` returned HTTP 200 and loaded `GTM-PQS8DCBH`.
- `https://www.910cpr.com/admin/dashboard.html` returned HTTP 200 and loaded `GTM-PQS8DCBH`.
- `https://www.910cpr.com/control-center/` returned HTTP 200 and loaded `GTM-PQS8DCBH`.
- The published `GTM-PQS8DCBH` container resolved to exactly one Google tag measurement ID, `G-45PBWBK7KR`, fired on `gtm.init` without a page-path or device-exclusion predicate.
- The repository audit found 31 tagged internal pages: 18 under `docs/admin/`, 11 under `docs/control-center/`, one under `docs/internal/`, and one under `docs/drafts/`.
- Direct unauthenticated retrieval of the sampled Enrollware enrollment URL returned HTTP 403, so its rendered tag, linker parameter receipt, checkout, and purchase event could not be independently observed from this environment.

## Root cause

The repository's global tag normalizer treated every HTML file under `docs/` as public. It therefore added and preserved GTM on explicitly non-public surfaces. The live GTM container also fires its sole Google tag at initialization on every page and currently contains no detectable path or device-exclusion condition.

The `910cpr.com / referral` concentration is consistent with a broken cross-domain session between `www.910cpr.com` and `coastalcprtraining.enrollware.com`. Repository evidence proves the hostname boundary and direct Enrollware URLs, but account-side access is required to prove whether Enrollware uses `G-45PBWBK7KR`, accepts `_gl` linker decoration, preserves it through checkout, and assigns the purchase to the original session. Treat this as an inference until the production DebugView/realtime test below passes.

## Repository repair

- `scripts/ensure_analytics_tags.py` now defines `admin/`, `control-center/`, `internal/`, and `drafts/` as analytics-free internal prefixes. It removes existing GTM head and noscript blocks from those pages and will not re-add them in future builds.
- The targeted cleanup removed GTM from all 31 known internal HTML pages. It did not rebuild schedules, courses, locations, or session landers.
- `docs/internal/analytics-preferences.html` provides reversible, no-login, device-local controls. Exclusion stores the first-party `analytics_excluded=1` cookie for one year, sets the standard `ga-disable-G-45PBWBK7KR` flag for that page, and removes existing `_ga` cookies. Inclusion removes the exclusion marker.

## Required account-side configuration (blocked here)

These actions must be performed in the existing GTM/GA4 and Enrollware accounts. Do not add another measurement ID to Enrollware.

1. In `GTM-PQS8DCBH`, add an exception to the existing `G-45PBWBK7KR` Google tag when the first-party cookie `analytics_excluded` equals `1`. Publish the container. This connects the device-local preference across public pages without rewriting 985 generated public HTML files.
2. Keep an internal-path exception as defense in depth using `^/(admin|control-center|internal|drafts)(/|$)`. The repository removal remains the primary control because it prevents even the GTM container request.
3. In the existing `G-45PBWBK7KR` Google tag, configure cross-domain linking between `910cpr.com` (including `www`) and `coastalcprtraining.enrollware.com`. Do not add a second Google tag or measurement ID inside Enrollware.
4. In the same GA4 data stream, add `910cpr.com` and `www.910cpr.com` to unwanted referrals as a fallback against a new self-referral session when linker continuity fails. Do not exclude `chatgpt.com`, `openai.com`, AI Assistant, or other genuine referral sources.
5. Confirm that Enrollware still contains exactly its legacy measurement ID. If it is not `G-45PBWBK7KR`, stop: changing IDs would split or overwrite history and requires an owner-approved migration plan.
6. Use GA4 DebugView/realtime with a fresh browser session and a uniquely tagged public entry URL. Follow a real `www.910cpr.com` class CTA into Enrollware, verify `_gl` decoration/receipt, complete a safe test purchase if the account supports it, and prove that the purchase retains the original campaign/source rather than `910cpr.com / referral`.

## Proof and health contract

- Expected outcome: public visitor acquisition survives the 910CPR-to-Enrollware journey; internal and opted-out browsers emit no public GA4 events.
- Success evidence: rendered internal pages contain no GTM request; an excluded browser produces no DebugView events; an included browser does; a tagged public-to-Enrollware transaction records `G-45PBWBK7KR` purchase attribution to the original source.
- Expected cadence: repository boundary checks run on every analytics-related change; channel attribution should be reviewed after at least one normal reporting window following configuration.
- Last successful proof: repository boundary only, locally on 2026-09-12 EDT: 1,018 HTML pages scanned, 985 public pages correctly tagged, 33 internal pages tag-free, zero tagged internal pages, zero missing/malformed public tags.
- Failure/staleness condition: any internal page contains `googletagmanager`, the opt-out cookie is present while GA requests occur, a handoff loses `_gl`/session identity, or `910cpr.com / referral` again captures conversions that began on the public site.
- Observer: the full validated public build runs `scripts.ensure_analytics_tags`; its unit tests enforce internal exclusion and preference-page reversibility. Account-side GA4 attribution monitoring is not yet connected.
- Observer health: repository checks are exercised by the validated build/test suite. There is no independent account-side observer available from this repository.
- Recovery: stop attribution reporting, inspect the published GTM container/version and GA4 stream referral/cross-domain settings, then repeat the tagged end-to-end transaction proof.
- Escalation boundary: repository tag removal is Codex-owned. Publishing GTM/GA4 settings and accessing Enrollware/GA DebugView requires Brian or an authenticated account operator.

Current evidence state: **BUILT** for the device-local preference and **PROVEN** locally for repository internal-page exclusion. Cross-domain attribution remains **BLOCKED**, not CONNECTED or HEALTHY, until the account-side configuration and real transaction proof are completed.

## Round 2: source-preserving Enrollware handoff

Added a repository-owned attribution bridge that does not require a second Enrollware measurement ID. On each public 910CPR page it keeps the current tab's acquisition source/medium, decorates Enrollware enrollment links with `utm_source`, `utm_medium`, `utm_campaign=910cpr_registration`, and a page/session-safe `utm_content`, and emits `begin_registration` before the handoff. Apex and `www` 910CPR hosts are explicitly first party; genuine ChatGPT referrals remain `chatgpt.com / ai-assistant`.

Rendered browser proof on 2026-09-13 UTC opened a current Enrollware class URL containing the bridge parameters. Enrollware returned the `Class Enrollment` page and retained the full UTM query string without redirect stripping. Automated tests prove Google organic, ChatGPT/AI, apex-to-www, registration-event, and opted-out-device cases.

This raises the handoff mechanism to **CONNECTED** at the URL boundary. Purchase attribution is not yet **PROVEN** or **HEALTHY** because a settled GA4 purchase after deployment is still required. The next evidence gate is one real post-deployment registration/purchase whose Enrollware GA4 source/medium is not `910cpr.com / referral`, followed by a normal reporting window showing self-referral key events have materially declined.
