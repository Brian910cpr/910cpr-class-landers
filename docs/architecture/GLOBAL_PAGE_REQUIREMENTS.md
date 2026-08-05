# GLOBAL_PAGE_REQUIREMENTS

## Purpose

`docs/**/*.html` is the production artifact published at `https://www.910cpr.com`. Every complete browser page receives one centrally owned baseline after generators finish and before deployment.

## Architecture

`scripts/global_page_requirements.py` is the reusable contract and idempotent post-processor. It owns the static global declarations. `scripts/audit_global_page_requirements.py` independently parses the final artifact with BeautifulSoup and fails on structural or semantic violations. `scripts/ensure_analytics_tags.py` remains as a compatibility facade for existing imports.

The approved analytics implementation is Google Tag Manager container `GTM-PQS8DCBH`. Both the head loader and immediate body `noscript` fallback are required. Direct `gtag.js` installations are not approved.

## Global versus per-page requirements

The centralized global block owns UTF-8 charset, viewport, GTM, the favicon package, and `/assets/css/global.css`. Page generators continue to own title, description, robots policy, social metadata, structured data, page-specific CSS and JavaScript, and intentional canonical targets. When a page lacks a canonical, the processor derives its production URL without replacing an existing intentional canonical.

## Favicon package

The published root contains `favicon.ico`, `favicon.svg`, `favicon-32x32.png`, `favicon-16x16.png`, and `apple-touch-icon.png`. Every eligible page references all five.

## Eligibility and exclusions

All complete HTML files under `docs/` are eligible for global requirements. Narrow exclusions live in `config/global-page-requirements-exclusions.json`; every entry requires an exact path, reason, and excluded requirement. Currently only `docs/404.html` is excluded from canonical because an error response has no stable requested URL. It still receives analytics, favicon, CSS, charset, and viewport.

## Generator integration and CI

`build/full_validated_public_build.bat` runs generators, enforces the contract, then audits final HTML. The active refresh workflow blocks publication on audit failure and runs the same idempotence/audit checks on relevant pull requests.

Commands:

```powershell
python -m scripts.global_page_requirements
python -m scripts.global_page_requirements --check
python -m scripts.audit_global_page_requirements
python -m unittest tests.test_global_page_requirements tests.test_ensure_analytics_tags
```

## Troubleshooting and extension

Fix per-page title, robots, canonical intent, schema, or page-specific assets in the authoritative generator. Do not hand-copy the global block. To add a global requirement, update the contract, parser audit, tests, this document, then process and audit all final HTML. A new generator is incomplete until its output is processed idempotently and passes the final-artifact audit. Add exclusions only for a reviewed, exact path with a durable reason.
