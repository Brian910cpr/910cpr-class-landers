# Issue 216 — R3 board resilience and proof gates

- Assignment: Brian910cpr/910cpr-class-landers#216
- Timestamp: 2026-10-14T20:26:18Z
- Local branch: codex/issue216-dispatch-20261014-r3
- Push destination: codex/issue216-proof-20261012; existing PR https://github.com/Brian910cpr/910cpr-class-landers/pull/388
- Substantive commit: 364dd1a257fbbcd1b630f3a2a2ad61e3a5882123. Receipt is in the subsequent commit; discover its SHA from the pushed tip.
- Work-item state: PR_OPEN for backend change; BLOCKED for full acceptance.
- Evidence: BUILT and validated locally for this change. Historical dashboard partial CONNECTED; no authenticated PROVEN, MONITORED or HEALTHY claim.

## Execution and scope

Read complete issue body and all comments, checkout AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Original checkout lacks the protocol; read it from the existing isolated issue216 checkout before implementation. Execution acknowledgement: https://github.com/Brian910cpr/910cpr-class-landers/issues/216#issuecomment-6177676958.

Preserved E:/GitHub/910cpr-class-landers and prior issue216 dirty checkouts. Created E:/GitHub/910cpr-issue216-20261014-r3 from fetched existing PR #388 tip 3fbdcb0e2dfad26071025867da68dc4c6a273f69. Windows case-collision dirt in docs/Earl/index.html and docs/Jackson/index.html appeared at checkout and remains uncommitted; no cleanup attempted.

## Findings and work performed

Reproduced three backend crashes before change:
- boardPrompts(null): TypeError: Cannot read properties of null (reading 'filter')
- boardPrompts({}): TypeError: cards.filter is not a function
- boardPrompts([null]): TypeError: Cannot read properties of null (reading 'implementation_status')

The endpoint calls boardPrompts(data.board) after source reads settle, so a missing list or null row could prevent the response despite available fulfillment/finance reads. Added a list guard and skipped non-object/array rows. No owner task is fabricated from malformed data. Valid translated actions, deduplication, completed-card suppression and source drill-through remain intact. No auth, SQL, schema, public asset, finance contract or Enrollware dependency changed. This is backend resilience within the existing deep stream.

## Exact intended files

- supabase/functions/owner-dashboard/core.mjs
- tests/owner-dashboard/core.test.mjs
- Codex_Reply_Issue216_Dispatch_20261014T202618Z_R3.md

## Validation

- node --test tests/owner_dashboard.test.mjs tests/owner-dashboard/core.test.mjs: 11 tests, 11 pass, 0 fail.
- node --check supabase/functions/owner-dashboard/core.mjs: pass.
- git diff --check: pass.
- Reviewed intended source/test diff; source commit contains exactly those two files (17 additions, 1 deletion).
- Supabase changelog HTTP 200, breaking-change index reviewed; plain JavaScript-only guard does not change a Supabase API or configuration.
- No generator, broad rebuild, database mutation, credential change, merge or deployment.

## Exact remaining blockers and useful evidence

1. Authenticated owner NOW read and fulfillment/decision drill-through: computer-use inventory returned {"apps":[],"browsers":[]}. This session has no connected browser surface to inspect/use an existing owner session. No bypass or credential request was created. This does not prove no owner session exists elsewhere. Next: expose an existing authorized browser session through the normal connected browser flow, then verify current read -> counts -> source drill-through. Coordinate existing auth work #215; do not replace it.
2. Trusted current finance source: scoped repository search in scripts, ops/owner-dashboard and .github/workflows found the documented private snapshot contract but no connected bank-available-balance plus complete-obligations ingester. Exact contract: ops/owner-dashboard/README.md, owner_dashboard_finance_snapshots; core gate: supabase/functions/owner-dashboard/core.mjs. Other finance-named scripts concern checkout balances or unrelated historical/schedule processing and do not establish bank-source authority. No bank values, reserves or bill completeness invented. Next: identify an authorized source and its freshness/completeness ownership before wiring a writer.
3. Independent observer: no new independent health proof obtained. Existing monitor tab is not independent supervision. Coordinate #373 rather than duplicate its implementation. Routine manual Brian checks remain an unresolved dependency if no observer is established.

Expected end-to-end outcome: authorized owner session -> current source reads -> accurate prompt/count -> exact roster/order/decision. Expected cadence: visible dashboard reads 60 seconds; repository cache five minutes; source stale after two minutes; finance independently expires. Last authenticated end-to-end proof: none established in this dispatch or cited owner acceptance record. Historical September 23 SQL/RPC/assets are component evidence only. Observer health: unproven. Recovery: restore normal authorized browser access and verified source connections, perform bounded reads, preserve diagnostics. Escalation boundary: actual account-level authorization or business-source decisions only; no speculative Brian chore created.

## Queue and deployment safety

Swept open [CODEX] issue titles. #215 auth, #368 fulfillment and #373 activity monitor remain OPEN and preserve their assignments. Continued independent eligible backend work within #216. No competing deep implementation or arbitrary third-party authorization. #372 checked OPEN/DRAFT and left untouched. Owner instruction keeps #388 open/unmerged/undeployed. No new PR, merge, deployment, broad rebuild, or ops/handoff/next_task.md use.

## Handoff and next action

Persisted locally and committed; push this receipt and source commit to existing PR #388, then verify receipt by GitHub Contents API. ChatGPT should review the exact source/test paths above and coordinate the three remaining proof gates. No account-level action has been proven necessary beyond making already authorized access available to this session. Full issue remains open and blocked for acceptance; backend follow-up is reviewable, not deployed.
