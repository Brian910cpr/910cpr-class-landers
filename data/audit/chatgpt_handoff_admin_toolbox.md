# ChatGPT handoff: ADMIN Toolbox

## Owner request

Create an ADMIN toolbox that surfaces existing admin tools and projects, including a clearly labeled Beta section for useful projects that may otherwise be hard to discover.

## Implemented result

- Added `/admin/toolbox.html` as a searchable internal tool directory.
- Added the toolbox as the first item in the shared admin navigation.
- Cataloged 22 existing tools across daily operations, money, clients/students, diagnostics, and the Beta dock.
- Web tools open directly. Local scripts expose copyable repository-root commands. A separate, unhosted add-on workbench is visible but explicitly marked as needing integration.
- Beta status is defined on the page and never presented as production proof.

## Repository scan findings used

Existing web surfaces:

- `docs/admin/dashboard.html`
- `docs/admin/production.html`
- `docs/admin/scheduling-landscape.html`
- `docs/admin/refresh-availability.html`
- `docs/admin/financial.html`
- `docs/admin/payments.html`
- `docs/admin/admin-port.html`
- `docs/admin/schedule-reader.html`
- `docs/admin/nhcso-training-workspace-v6.html`
- `docs/admin/instructor-class-intake-prototype.html`
- `docs/corp/maxim.html`
- `docs/group-training.html`

Existing local utilities surfaced:

- `scripts/check_schedule_integrity.py`
- `scripts/public_offer_integrity_audit.py`
- `scripts/audit_sitewide_links.py`
- `scripts/run_lander_safety_preflight.py`
- `scripts/start_inventory_control.ps1`
- `scripts/schedule_manager_admin_server.py`
- `supervisor/main.py`

A separate repository, `addon-catalog`, was found in the Codex workspace. It is represented as a Beta project with no fake or guessed production URL.

## Changed files

- `docs/admin/admin-nav.js`
- `docs/admin/toolbox.html`
- `docs/admin/toolbox.css`
- `docs/admin/toolbox.js`
- `tests/admin_toolbox.test.cjs`
- `data/audit/chatgpt_handoff_admin_toolbox.md`

## Validation

Commands:

```text
node --check docs/admin/toolbox.js
node --check docs/admin/admin-nav.js
node --test tests/admin_toolbox.test.cjs tests/dashboard_ops.test.cjs
python -m unittest tests.test_admin_port
git diff --check
```

Results:

```text
Node tests: 16 passed, 0 failed.
Admin Port tests: 3 passed.
JavaScript syntax checks: passed.
Rendered locally at http://127.0.0.1:8765/admin/toolbox.html.
Browser verification confirmed 22 tools on the full index and 7 items under the Beta filter.
```

## Important behavior and assumptions

- This is an index and discovery layer; it does not add new backend privileges or execute local scripts from the browser.
- Existing authentication behavior belongs to each destination tool and remains unchanged.
- `Canonical Day Inspector` is classified Beta because it is a newer read-only truth surface.
- No generator or sitewide build was run.
- Unrelated generated course-page modifications observed in the worktree were intentionally not staged.

## Deployment state

Changed in repo and validated locally. Not merged or deployed at the time this handoff was written.
