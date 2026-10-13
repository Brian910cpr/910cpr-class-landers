# Issue 334 — R47 independent cloud recovery gate

Timestamp: 2026-10-13T19:45:00Z (UTC)
Branch: codex/issue334-cloud-gate-20261013-r47
Evidence commit: 9cf3cf590c02ae5f52abc6d47dcf232307199ca4
State: BLOCKED for independent cloud recovery; read-only diagnostics completed.
Persistent evidence: PROVEN publication; overall HEALTHY unproven. Keep #334 open.

Execution acknowledged before evidence writes:
https://github.com/Brian910cpr/910cpr-class-landers/issues/334#issuecomment-6153737942

## Findings and exact blocker

2026-10-13T19:43:18Z bounded live sample: all eight families evaluated 208/208 windows, zero failures; 427 input/normalized sources. BLS 4149 offers/89 dates; Heartsaver 8641/89 dates. Both unexpired through approximately 19:50:08Z. October 14 Heartsaver retains 17:30 and 19:30. ACLS/PALS retain 3/2 seated offers, zero dynamic offers; expired payload timestamps do not invalidate seated classes. Both canonical HTML GETs returned HTTP 200. This is feed/HTTP proof, not fresh browser, checkout/payment or continuous availability proof.

Exact authenticated repository health-variable query result: gh: Not Found (HTTP 404), with JSON status 404. This does not prove secret absence. Existing secure provisioning gate remains: approve/create a repository-restricted fine-grained GitHub credential with Actions read/write and store it only as Cloudflare encrypted GITHUB_ACTIONS_TOKEN. No credentials inspected or transmitted; no activation retry or duplicate owner alert.

Latest natural observer 38429046400 succeeded 16:16:04Z; preceding start gap 7h48m06s does not prove five-minute cadence. Existing R44 artifact retained without repeat download. Latest completed admin 38455433243 and Pages 38456108284 succeeded; admin 38456765805 running at bounded check. No competing recovery dispatched.

## Files and validation

Only intended files changed:
- data/audit/issue334_cloud_gate_r47_live.json
- data/audit/issue334_cloud_gate_r47_health.txt
- data/audit/issue334_cloud_gate_r47_observer.json
- data/audit/issue334_cloud_gate_r47_runs.json
- data/audit/issue334_cloud_gate_r47_http.json
- Codex_Reply_Issue334_CloudGate_20261013_R47.md

Live audit exit 0; python -B -m unittest tests.test_family_publication_coverage: 4 tests PASS. Audit source AST syntax and all four JSON evidence files parse; staged whitespace PASS. No known local validation failure. No application source changes, generators, migrations, timer/infrastructure mutation, registration or payment.

Original dirty E:/GitHub/910cpr-class-landers preserved. Root protocol missing there; read current instructions from healthy issue334-r46 checkout. Isolated worktree E:/GitHub/910cpr-issue334-r47 based on origin/main d8efed1d2. No original Git-object repair or cleanup. All existing assignments/PRs preserved, draft #372 untouched; no duplicate PR, merge or deployment. Persisted locally, committed and pushed; GitHub receipt verification recorded on originating issue. No intentionally untracked work in isolated tree. Never used ops/handoff/next_task.md.

Open issue/PR queue swept: narrow backend streams 219/389, 216/388, 380/381, 266/375, 254/374 and 215/218 already assigned. Other candidates require broader implementation or unresolved dependencies. No safe unassigned narrow backend quick win identified; no stream displaced.

## Proof contract and next action

Expected outcome: real selectable appointments renewed before authoritative source expiry. Success chain: natural timer -> publisher -> Pages -> public inventory. Expected observer cadence five minutes; effective source freshness approximately 15 minutes. Last bounded inventory proof 19:43:18Z; latest natural observer success 16:16:04Z. Failure/staleness: expired dynamic inventory, failed coverage windows or missed observer cadence. Observer verify-public-booking-inventory.yml has natural successes but sustained cadence/independent observer health are unproven. Local containment still depends on CYBERPC awake, online and logged in. Brian must not remain the routine monitoring layer.

Next concrete action: satisfy existing secure account provisioning gate; then verify independent cloud timer/authenticated health, configure AVAILABILITY_WATCHDOG_HEALTH_URL and prove natural recovery through Pages/customer inventory plus observer heartbeat. Account-level action required at existing gate; never post credentials in chat/issues. Preserve local containment and source/conflict freshness protections. No activation retry or competing monitor while unchanged.
