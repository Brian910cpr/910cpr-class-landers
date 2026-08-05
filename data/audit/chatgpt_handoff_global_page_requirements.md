# ChatGPT handoff: GLOBAL_PAGE_REQUIREMENTS

## Primary report

See the full report at `data/audit/global_page_requirements_compliance.md` (included in the same commit). Its result is: all 755 generated HTML artifacts pass the parser audit with zero violations; `docs/404.html` is the single documented canonical exclusion.

## Repository and branch

- Repository: `Brian910cpr/910cpr-class-landers`
- Remote: `https://github.com/Brian910cpr/910cpr-class-landers.git`
- Branch: `codex/global-page-requirements`
- Starting commit: `d7cb554a1154528237acdbee2e63778287253069`
- Architecture decision: one authoritative source/build/deployment repository; no dependency on `ew2landers`

## Important review files

- `scripts/global_page_requirements.py`
- `scripts/audit_global_page_requirements.py`
- `scripts/ensure_analytics_tags.py`
- `config/global-page-requirements-exclusions.json`
- `build/full_validated_public_build.bat`
- `.github/workflows/refresh-public-site.yml`
- `tests/test_global_page_requirements.py`
- `docs/architecture/GLOBAL_PAGE_REQUIREMENTS.md`
- `docs/assets/css/global.css`
- `docs/favicon.svg`

## Exact validation results

```text
python -m py_compile scripts/global_page_requirements.py scripts/audit_global_page_requirements.py scripts/ensure_analytics_tags.py
PASS

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

python -m unittest discover -s tests
Ran 368 tests in 30.580s
FAILED (failures=53, errors=25)
```

## Review notes

- The enforcer deliberately preserves page-specific content and replaces only globally owned markup.
- It removes duplicate/legacy doctypes, icon links, global CSS links, GTM snippets, charset, and viewport before inserting one normalized contract.
- Existing valid canonical URLs are preserved. Missing canonicals are derived from the `docs` path. Invalid or duplicate canonicals are repaired.
- The workflow uses an audit-only pull-request job; scheduled/manual refresh continues through the existing full validated build.
- Generated HTML changes are intentionally broad because the task establishes a sitewide invariant.
- Test execution rewrote three unrelated tracked Course Master JSON timestamps. Those files are explicitly excluded from staging and the PR.
- Python bytecode caches produced by local tests are explicitly excluded from staging.
- No production deployment or post-deploy live smoke test has occurred.
