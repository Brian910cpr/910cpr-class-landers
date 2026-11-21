# Codex Reply — Issue371 scheduled supervisor proof, October10 R1

Timestamp: 2026-10-10T19:23:00-04:00 (America/New_York).
Branch: codex/issue371-supervision-evidence-20261010.
Base commit: 1a306ec13029643ee1a0b5711ba7a7c88607b21d; CRM source commit5d15a8825d39fd8f96642305c283f16424532bd4. This receipt's commit is the branch head reported on Issue371 after push.
Work item: PR_OPEN / IN_PROGRESS in existing draft PR372, unmerged, CRM undeployed.
Persistent evidence: scheduled stopped-launcher detection and recovery PROVEN; existing supervisor path MONITORED. No blanket permanent HEALTHY claim.

Root cause: the ChatGPT handoff convention/supervisors were not Codex job launchers. The actual Windows Startup Codex Wake intake required repair; prior repairs restored real automatic sessions, owner-only issue intake, locks/assignment preservation, pushed receipt validation and backoff. The remaining monitoring gap was that the supervisors could miss a stopped local launcher when no repository delta appeared and could not read each other's private execution traces. Existing tasks now fetch a live whitelist-only heartbeat EVERY run; Delta publishes one durable observer receipt, independently checked by Deep. No competing scheduler or new recurring automation.

Both tasks edited in place after Brian's browser sign-in: Delta6aa07a7161408191b146dc743eeab786 hourly; Deep6aabf6372ba88191abb345d1202dff6d original morning/evening Eastern. Full original duties retained and reopened editor text verified. Exact full instructions persisted in the audit text files below. Tasks Push configured; device receipt itself cannot be observed.

Real acceptance: idle loop33536 stopped22:13:39.1179457Z, last actual publication22:13:28.9411805Z unchanged. No active job killed. One-time bounded guard19520 restored SAME installed loop as32372 at23:19:25.5234694Z; fresh heartbeat23:19:31.2937082Z. All pre-test assignment keys preserved. No user restart/check required.

Actual scheduled Deep independently detected STALE23:04:55Z and generated visible19:06Eastern alert: Issue371#issuecomment-6103141637. Actual hourly Delta independently detected STALE23:17:58.442Z: #issuecomment-6103248580. SAME scheduled Delta independently verified FRESH23:19:54.482Z and receipt transition STALE->FRESH: #issuecomment-6103253453; visible19:20Eastern recovery response. No manual Run now was used for these failure/recovery observations. Separate manual baselines are explicitly distinguished in the audit. Detection took51m16s Deep /64m19s Delta from actual stop, consistent with existing schedules, not instant monitoring. Deep first flagged the initialization-only Delta receipt UNKNOWN; later scheduled Delta publication resolved it.

Exact changed files this evidence commit:
- docs/CODEX_WAKE_SUPERVISION.md
- data/audit/issue371_supervisor_stop_proof.json
- data/audit/issue371_delta_watch_instructions.txt
- data/audit/issue371_deep_stability_instructions.txt
- Codex_Reply_Issue371_SupervisorProof_20261010_R1.md

Review launcher sources already in PR: ops/scripts/Invoke-CodexWake.ps1, Start-CodexWakeLoop.ps1, Publish-CodexWakeHealth.ps1, Install-CodexWake.ps1. Live signal PR372#issuecomment-6102455692; observer PR372#issuecomment-6102801791. Do not mutate issue activity for heartbeats or clear assignments.

Validation: node --test tests/codex_wake.test.mjs =>4passed,0failed; node --test tests/codex_wake_health.test.mjs =>2passed,0failed; PowerShell publisher parser =>PASS. CRM increment this session: 35 CRM/auth tests passed including local real PGlite migration/RPC suites; Deno check endpoint =>exit0. git diff --check =>exit0. JSON parses locally. Real scheduled browser/GitHub evidence is distinct from these local fixture tests.

CRM kept moving in SAME PR372: canonical case_id/interaction_id filters on existing interactions/tasks collection reads, composing status/bounded keyset pagination; malformed/duplicate queries rejected before storage. Exact source/review paths supabase/functions/customer-interactions/handler.ts, tests/customer_interaction_pagination.test.mjs, docs/CUSTOMER_INTERACTION_STORAGE.md. No new schema, privilege, origin, duplicateCRM or production change. Prior case-recovery handoff genuinely acknowledged by ChatGPT. Durable schema/RPC work remains in PR; operational UI connection/conflict/retry/remote persistence still needs preview proof.

Owner action required only for remote CRM preview: identify authorized isolated Supabase project reference and approve https://feat-customer-learning-studi.910cpr-class-landers.pages.dev as its browser origin. No credentials in issue. Production Supabase list_branches returned[]; do not assume a preview or provision billed infrastructure without authorization.

Remaining reliability boundary: Windows computer/user session must stay available; GitHub/Codex authorization/capacity must remain valid. Existing hourly Delta and twice-daily Deep detect stale/missing/failed data and observer failure, deduplicate unchanged alerts, notify recovery. They do not remotely power on an offline PC. Device push delivery not directly verified. Next Deep run must keep validating Delta receipt within90minutes. Continue authorized queue/primary371, retain existing assignments, and review this receipt under durable protocol; Codex never creates a Codex_Read file.

Known unrelated dirty files docs/Earl/index.html and docs/Jackson/index.html and untracked supabase/.temp/ intentionally excluded/preserved. No broad generator, merge, deployment or cleanup. Final evidence branch and same PR branch pushed; latest full receipt SHA reported on371.
