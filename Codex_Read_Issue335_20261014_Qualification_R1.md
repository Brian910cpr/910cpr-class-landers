# Issue #335 dispatch receipt

Timestamp: 2026-10-14T21:28:08.4619679-04:00
Branch: codex/issue335-availability-20261014
Substantive commit: 92e28a692f151de679660ea28733d7c41c761caa
Work-item state: IN_PROGRESS; production activation BLOCKED; draft review only.
Persistent-system evidence: BUILT (read-only qualification audit only). The requested native availability program has no demonstrated end-to-end proof or established observer health.

Execution acknowledged on originating issue before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/335#issuecomment-6182223300

## Work performed and exact files

- scripts/audit_instructor_intake_qualification.py — stdout-only, non-authorizing qualification preflight; no source mutation or remote calls.
- tests/test_audit_instructor_intake_qualification.py — six local behavioral tests.
- data/audit/issue335_readiness_20261014.md — full scope, source references, blockers, dependency map, validation, proof contract and next steps. Read this report in full for review.
- Codex_Reply_Issue335_20261014_Qualification_R1.md — unique repository-root receipt.

## Findings / exact activation blockers

Amy's data/config/instructor_catalog.json record has no can_teach_course_ids, UNKNOWN credential expiry, and HSI provenance text referring to Brian. data/config/instructors.json allows BLS while her catalog lists only ACLS/PALS. Current preflight reports exact_course_qualifications_unreviewed, certification_expiry_unreviewed, profile_and_qualification_family_mismatch. These are review gates, not authority to infer credentials or remove offers.

Current supabase/functions/landerware-calendar/index.ts is owner-token-only, unfiltered by instructor; do not give Amy LANDERWARE_ICAL_TOKEN. No actual instructor calendar subscription add/change/cancel proof exists in this dispatch. Repository search did not identify the 4018 scanner source path or connected worker. Scanner access, matching/attachment and observer heartbeat are unproven; lack of a repository match is not proof no external worker exists.

Paid-seat atomic Anchor transition, native durable intake, communications, migration classification, scoped stale-roster uncertainty and live customer proof remain required. Preserve active PRs #383/#387/#393 and #334 work; do not implement competing replacements. No existing 335 PR was found before this slice. Open queue was swept; other eligible backend items have existing assignments/draft PRs and were preserved.

## Validation

6/6 unittest tests passed locally. AST syntax checks passed for both Python files. git diff --check and staged diff checks passed. Audit command printed the three review reasons above and intentionally returns 2. No integration test, calendar subscription, current roster query or public customer proof was claimed.

Known unrelated state: original E:/GitHub/910cpr-class-landers dirty work remains untouched. Isolated worktree has pre-existing-after-checkout tracked docs/Earl/index.html and docs/Jackson/index.html changes, left unstaged. No cleanup or reset. Test-created cache files are ignored, not staged.

## Deployment and recovery

Persisted locally and committed; this receipt is being pushed on the named review branch. No merge, deployment, generator, production database change, live payment, notification or speculative session. Draft PR #372 remains unmerged/undeployed and untouched. No ops/handoff/next_task.md use.

Expected end-to-end success and failure/observer/recovery contract are recorded in data/audit/issue335_readiness_20261014.md. Last successful real end-to-end proof: none for this program. Expected cadence/refresh SLA, observer, observer health and escalation remain unestablished; do not call this HEALTHY or rely on Brian to monitor it manually.

Next action for ChatGPT: review the report and preflight, resolve qualification evidence through authorized records/owner confirmation, coordinate the existing payment/scheduling branches, then implement native availability intake against canonical identities in the same review stream. Discover scanner source and worker before enabling file intake. Calendar requires separate scoped credential/identity design and actual subscriber proof. Full issue remains open.

Owner/account action: only if Amy credential/identity evidence or scanner path/access cannot be recovered from authorized records. No secrets belong in issue comments. The issue comment asks for these missing factual inputs; no broad permission request or production release is implied.
