# GLOBAL_PAGE_REQUIREMENTS compliance report

Date: 2026-08-04

## Result

The production repository `Brian910cpr/910cpr-class-landers` now owns one post-generation contract for every `docs/**/*.html` artifact. The legacy `ew2landers` repository is not part of the build, synchronization, or deployment path.

The local parser audit passed all 755 HTML files with zero violations. `docs/404.html` is the only documented canonical exclusion; it still receives every other global requirement.

## Enforced contract

- One leading HTML5 doctype and one `html`, `head`, and `body` element.
- `lang="en"`, UTF-8 charset, viewport, and a non-empty title.
- Root-relative favicon package (`ico`, SVG, 32px, 16px, and Apple touch icon).
- Root-relative `/assets/css/global.css` global stylesheet.
- Exactly one approved Google Tag Manager container, `GTM-PQS8DCBH`, in both head and body positions.
- Exactly one absolute `https://www.910cpr.com` canonical except documented exclusions.
- No contradictory `index` and `noindex` robots directives.

## Ownership and execution

- Contract/enforcer: `scripts/global_page_requirements.py`
- Independent parser audit: `scripts/audit_global_page_requirements.py`
- Canonical exclusions: `config/global-page-requirements-exclusions.json`
- Build integration: `build/full_validated_public_build.bat`
- Pull-request and refresh enforcement: `.github/workflows/refresh-public-site.yml`
- Generated artifacts and deployable assets: `docs/`

The enforcer is idempotent and runs after page generation. The audit runs after enforcement and before the refresh workflow can commit generated output.

## Validation evidence

```text
python -m scripts.global_page_requirements
HTML pages scanned: 755
Pages updated: 51

python -m scripts.global_page_requirements --check
HTML pages scanned: 755
Pages requiring updates: 0

python -m scripts.audit_global_page_requirements
GLOBAL PAGE REQUIREMENTS PASSED
Eligible pages scanned: 755
Documented exclusions: 1
Violations: 0

python -m unittest tests.test_global_page_requirements tests.test_ensure_analytics_tags
Ran 8 tests
OK
```

Python syntax compilation also passed. The broad pre-existing repository suite currently reports 368 tests with 53 failures and 25 errors; those failures are outside this focused contract and include fixture/generated-state assumptions. It is therefore recorded, not represented as a passing gate for this change.

## Deployment status

Persisted locally and validated locally. The branch is intended for a draft pull request. It has not been merged or deployed, so live-site smoke checks must occur after GitHub Pages publishes the merge.
