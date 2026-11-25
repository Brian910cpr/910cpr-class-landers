# Codex Reply — Issue371 Supabase preview discovery, October19 R1

Timestamp: 2026-10-19, America/New_York.
Assignment: #371; existing draft PR372.
Branch: codex/issue371-preview-target-20261019.
Substantive commit: bc5505458898a7212920e9a9be69a9a425d87782; receipt commit is the pushed branch head.
Implementation base: 67585b94a9b4bae246d2cc3089d2ca546ba9197f.
State: PR_OPEN / BLOCKED for provisioning. Evidence: READ_ONLY_DISCOVERY; no new remote operational proof.

Brian authorized connected Supabase account discovery and continuation in an isolated preview with production untouched. Read current AGENTS, durable handoff/health/design rules and latest Path A/runner gate receipts; latest PR code reused, no parallel CRM. Applied Supabase skill, fetched current changelog and relevant branch inheritance/TLS deprecation docs. October19 cloud request permits a cloud preview path; older local-only checkpoints do not constitute permission to charge or alter production.

Live connected list_projects found only LanderWare wktwgcnwdvbebcobgyey and ShiftCommander cskcgwjvgsgawxwncjrf, both ACTIVE_HEALTHY in us-east-1, organization kukukymsnhicxzwsvxgo. list_branches returned[] for EACH. First is known production; second is a separate app, not a disposable preview. No safe existing isolated target identified. No customer rows, keys, sessions, production migrations/functions or account settings touched.

Recommended NEW dedicated project landerware-issue371-preview, us-east-1, project_ref currently null. No resource created. Branches copy deployed functions/settings and enable database webhooks despite default data exclusion; a blank dedicated project reduces inherited outbound-side-effect risk. See full report for exact source, prerequisites and safeguards.

Exact next owner boundary: select billing organization kukukymsnhicxzwsvxgo (or a different organization). Connected get_cost explicitly says organization must be user-selected; selection authorizes QUOTE only. Pending async question asks this. Then obtain exact project cost, report amount/currency/recurrence and obtain explicit agreement to nonzero cost through tool confirmation flow. No get_cost/confirm_cost/create call has occurred; no price fabricated. Current general isolated-work authorization covers later reversible preview implementation, not production rollout or unquoted charges. A genuine preview owner-session test may require interactive sign-in, without copying a production session. Proposed exact preview origin is the existing PR branch origin; validate it before binding.

Code readiness finding: current CRM client and admin-auth service/refresh/logout/session lifecycle target production, while shared owner auth and handler CORS reject preview origins. Do NOT enable the Studio meta flag merely because a preview project exists. Need preview-only target/auth/session isolation and negative production-egress tests; retain default production code behavior and release gates. Canonical people/auth prerequisites must be reviewed narrowly, not a bulk replay of unrelated migrations. Existing loopback-only concurrency runner remains guarded; no cloud DSN widening or synthetic PGlite evidence substituted for real lock proof.

Changed files:
- docs/CUSTOMER_INTERACTION_SUPABASE_PREVIEW.md — full target decision, exact cost/authorization boundary, deployment manifest and routing/proof plan.
- data/audit/issue371_supabase_preview_20261019.json — sanitized live inventory/results and unresolved approvals.
- Codex_Reply_Issue371_SupabasePreview_20261019_R1.md — this handoff.

Validation: audit JSON ConvertFrom-Json PASS; git diff --check PASS; source paths/dependencies reviewed against current PR. No application source or schema changed, so no redundant synthetic regression run. No remote SQL, deployment, paid resource, credential fetch, production mutation, public page change, gate enable, merge, scheduler change or duplicate implementation. Overall CRM remains BUILT with prior local proof only; concurrency, genuine owner-session/Edge/PostgREST/UI recovery and backup/restore gates still open. A preview is on-demand, no deployed observer/observer-health or successful preview timestamp claimed. Recovery remains preserve drafts/uncertain request identity, resolve conflicts from current state; owner must not become routine monitor.

GitHub blocker: gh issue view371 --comments --json body,comments returned repository has disabled issues. Do not change repository settings. Report checkpoint on existing PR372 and push this immutable root receipt. No Codex_Read state manufactured. Unrelated docs/Earl/index.html, docs/Jackson/index.html and supabase/.temp remain dirty/untracked, intentionally excluded and preserved. No destructive cleanup/rebase/reset/force push.

ChatGPT next: review substantive commit/report; obtain billing organization selection and exact quote consent; provision only the isolated confirmed reference, implement preview routing and synthetic integration proof in SAME PR372. Do not claim target exists or preview E2E passed at this checkpoint. Production remains untouched and separately NO-GO until operational gates and explicit rollout authorization.
