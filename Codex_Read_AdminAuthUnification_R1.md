# Issue 215: admin-auth inventory checkpoint

- Assignment: Brian910cpr/910cpr-class-landers#215, advanced as independent eligible backend work during the blocked #214 dispatch.
- Timestamp: 2026-09-13T13:08:48-04:00 (America/New_York).
- Work-item state: **IN_PROGRESS**. Inventory and coordinated migration assessment complete; requested auth consolidation is not implemented.
- Branch: `codex/issue-215-admin-auth-audit-r1`.
- Worktree: `E:\GitHub\910cpr-class-landers_codex_issue215_audit_r1`.
- Audit commit: `2e667eab30da6918985db594631f6c7b08a425c1`.
- Source snapshot: `8808884a23e4da2ce055b4da6a9002a6ea17c39c`.
- PR: none; this pushed audit branch is independently reviewable. No application PR or production change is claimed.
- Persistent-system evidence: unified auth is **not yet BUILT**. This is source inventory with local audit tests; no operational PROVEN, MONITORED or HEALTHY claim.

## Result and review artifacts

Read the full issue and its empty initial comment thread, current repository instructions/handoff/proof rules, and #140's latest precise credential-parity gate. Preserved #214's blocked release work before beginning this separate audit. One current worker; no competing launch or lock/lease/default changes.

Inventoried all **34 admin files / 19 HTML pages**, **5 referenced asset paths** (4 present, 1 missing), and **7 backend boundary files**. The 46-record inventory includes source lines, storage key identifiers/operations, known contract/header tokens and status/prompt/request locations. No credential values, operational data, browser state, provider APIs or payment actions were read or written.

Primary full report:
[data/audit/admin_auth_review_issue215_r1.md](https://github.com/Brian910cpr/910cpr-class-landers/blob/2e667eab30da6918985db594631f6c7b08a425c1/data/audit/admin_auth_review_issue215_r1.md).

Exact machine-readable evidence:
[data/audit/admin_auth_inventory_issue215_r1.json](https://github.com/Brian910cpr/910cpr-class-landers/blob/2e667eab30da6918985db594631f6c7b08a425c1/data/audit/admin_auth_inventory_issue215_r1.json). Review `counts`, `source_commit`, `contract`, `limitations`, and each `files[]` entry's `path`, `scope`, `storage`, `token_lines`, `markers`, `direct_assets`, `exists_in_source_commit` and `reference_matches`.

Important source/test paths in the audit commit:

- `scripts/audit_admin_auth_contract.py`: read-only exact-commit source inventory; one explicitly named JSON output.
- `tests/test_audit_admin_auth_contract.py`: six privacy/coverage/parser regression cases.

## Concrete findings

- Admin Port, All Classes, Financial, dashboard operations and Class Registry already use the canonical key/header in duplicated local implementations. There is no shared admin auth helper in the audited snapshot.
- Production Board, its dashboard summary and Instructor Workbench use `maximPortalSession`/`x-maxim-session`. Dashboard participant details have another corporate-auth request path. Class Registry has a corporate-session fallback in both browser and server code.
- Production Board and Instructor Workbench backend authorization/CORS do not accept the canonical admin header today. Merely replacing client storage/header names would cause failures. Scope explicit owner-admin server contracts and preserve any corporate/public consumers separately.
- 401/403 clearing differs across pages and read/write/XHR branches. The full report records exact lines and recommends lock/expiry hooks that also prevent late responses from restoring private data after lock.
- `hotSyncDrafts`, prototype draft keys and theme preferences are not alternate admin credentials. Preserve them and corporate sessions; do not clear all browser storage on admin logout.
- Some static/prototype/diagnostic pages have no credential plumbing. Loading a helper is not server-side protection for public files. The report inventories these separately without claiming privacy was verified.

Every admin HTML page and disposition is listed in the report's 19-row table. **Pages migrated: none.** Explicit credential-conversion exclusions: `/corp/*`, Maxim and other corporate surfaces, and the five NHCSO pages under `docs/admin/`: `nhcso-training-history-v5.html`, `nhcso-training-workspace-prototype.html`, `nhcso-training-workspace-v3-prototype.html`, `nhcso-training-workspace-v4-prototype.html`, `nhcso-training-workspace-v6.html`. They remain inventoried; their presence beneath `/admin/` is not permission to change the issue's explicitly excluded NHCSO auth lane. General site-theme assets remain untouched.

## Validation performed

```text
python -B -m unittest discover -s tests -p test_audit_admin_auth_contract.py -v
Ran 6 tests in 0.002s
OK
PASS syntax: scripts/audit_admin_auth_contract.py
PASS syntax: tests/test_audit_admin_auth_contract.py
PASS: deterministic exact-commit inventory, 34/34 admin files,
      19/19 report pages, 46 records, no unresolved keys, Markdown checks
PASS: exactly four intended audit files staged
```

The six cases cover stored-value/prompt redaction, constant candidates/unknown expressions, ambiguous constants, sanitized asset URLs, distinct corporate/admin keys, and missing-asset/complete-file inventory. Syntax used AST and in-memory compile; no bytecode. A second in-memory inventory build exactly matched the saved JSON without writing another output. Explicit stage and whitespace checks passed. All processing was local except GitHub issue/ref/push/readback; no application code executed and no auth acceptance test is claimed.

Initial five tests passed; the first inventory run stopped because `docs/assets/css/global.css` does not exist at the source commit. Corrected the audit to record missing assets explicitly, added the sixth test, then all tests and inventory checks passed. The missing CSS is referenced by `docs/admin/production.html:12` and `docs/admin/scheduling-landscape.html:8`; it is a known unrelated finding, not repaired or visually verified here. No unexpected generated files changed.

Exact changed files: the two audit artifacts, script and test above, plus this root receipt. The substantive four-file commit was pushed before writing this receipt. This receipt's separate commit, branch-tip/content/blob verification and exact timestamp are returned on #215 after push. No temporary/cache files are staged. Original dirty checkout, all operational data and other worktrees remain unchanged. No Codex_Read marker or retired mutable handoff was written.

## Remaining work and gates

Local helper implementation, endpoint/client migration and synthetic regression work are eligible under #215's existing authorization. This bounded independent audit is not a new deep implementation workstream or a completed consolidation. No new account decision is required for the approved canonical contract itself. Coordinate overlapping dashboard #216 files before the next implementation commit.

Production proof still depends on the existing [#140 private credential-parity action](https://github.com/Brian910cpr/910cpr-class-landers/issues/140#issuecomment-5645954782), when relevant to the same authority. No unchanged failing auth path was retried. Do not put the key in any source, message or receipt; do not bypass fail-closed checks. Real unlock/navigation/lock and both read/write denial behavior need rendered-browser verification, then coordinated production HTML/asset/endpoint verification. None of that has been performed here.

Expected complete proof: one approved admin unlock works across all true owner pages in the same tab, lock/expiry consistently removes access and private UI state, protected endpoints fail closed, and corporate sessions remain separate. Last successful full proof, operational observer health and recovery evidence are unknown. This audit is on-change local verification, not a persistent auth monitor. Brian must not be the routine detector.

Deployment status: audit persisted locally, committed and pushed; receipt pushed/read back before exit. **No merge, deployment, public HTML/JS change, server auth change, secret mutation or customer communication.** #215 stays open; #214 remains separately blocked with pushed `Codex_Reply_ShiftCommanderAstra_R11.md` at `f6274141d224a03ab87a843c94f12ab3e0cfbc00`.

Exact next ChatGPT action: review the complete report and JSON at the audit commit, especially corporate fallback in `docs/assets/class-registry.js:16` / `supabase/functions/class-registry/index.ts:10`, corporate-only Production Board/Instructor Workbench, dashboard detail/XHR paths and prototype exclusions. Coordinate the #216 dashboard work, then continue #215's shared helper plus explicit admin endpoint migration and the report's five-step verification plan. Retain existing owner authorization; escalate only actual private credential/provider limitations, not ordinary reversible implementation decisions.

## Supervisor acknowledgment
Processed 2026-09-13. Audit commit 2e667eab was reviewed against issue #215. Findings are accepted as a migration plan, not a completed consolidation. The subsequent implementation continuation on `codex/repair-admin-and-public-portals` is already in progress, so no duplicate Codex round was launched. #140 credential parity remains the production proof gate.