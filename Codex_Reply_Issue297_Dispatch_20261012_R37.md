# Issue 297 — changed observer evidence / source acquisition gate

- Assignment: Brian910cpr/910cpr-class-landers#297
- Timestamp: 2026-10-12 (America/New_York); observer evidence timestamp 2026-10-12T18:58:27.681796Z.
- State: BLOCKED at authorized complete-current-roster acquisition with exact external registration identities.
- Branch: codex/issue297-dispatch-20261012-r37
- Base commit: 3d4c573050c9d347207ab39389d26a98029c45c7. Receipt-only pushed commit is reported on the originating issue and final dispatch response to avoid a self-referential SHA.
- Local worktree: E:\GitHub\910cpr-issue297-dispatch-r37
- Execution acknowledgement: https://github.com/Brian910cpr/910cpr-class-landers/issues/297#issuecomment-6130922503

## Changed evidence and blocker

Read issue body and paginated history, repository AGENTS.md, remote CODEX_HANDOFF_PROTOCOL.md (absent in the original checkout), design ethos and persistent-system proof standard. Owner-reported export (71) review and two bounded assignment repairs are preserved. The export exists for that review, but lacks exact numeric external registration IDs and is outside the 60-minute observation window. Do not repeat the repairs or accepted October 13 attendee status correction. Gmail notice access is not proof of complete roster/lifecycle coverage.

New existing scheduled observer run 38294474365, source commit 7a9f871097993b86f6d17e6cb475453152a11ccd, updated 2026-10-12T18:58:32Z, reports 45 gaps rather than the prior 42. Signature: 5768c6daf16179ee6ef8eed295824157fcfe879f20b463f8f9dfef37977d6a4f. Deterministic comparison of the two bot reports found:

- 20 stale_reconciliation
- 13 committed_projection_without_canonical_session
- 12 external_reconciliation_required
- Added 14692513: committed_projection_without_canonical_session
- Added lw-gmail:1a0aa5e4a4b94785: external_reconciliation_required
- Added lw-gmail:1a1119122b7e1868: external_reconciliation_required
- No removed IDs or changed statuses among prior IDs.

This is changed evidence within the same incident, not a new incident. The source comparison and artifact upload succeeded; the condition-notification step failed closed. verify-demand, verify-publication-watchdog and verify-production were skipped. Artifact reconciliation-health ID 11767985648 is unexpired. This dispatch inspected run metadata and issue evidence, not private artifact contents, and triggered no retry. The bot already posted the changed signature; no duplicate alarm was created.

Exact blocker: an authorized authenticated current source with exact class/registration IDs, complete roster coverage including empty rosters, cancellations and reschedules, and observations within 60 minutes has not been established for this execution. Scoped existing-tooling review found the importer/observer but no provisioned unattended collector. No endpoint, credentials, IDs, count or new watermark was guessed.

## Existing authoritative paths and validation

- scripts/import_enrollware_registration_events.py: existing --complete-roster entry point; --apply requires operational mode.
- scripts/enrollware_roster_reconciliation.py: enrollware-complete-roster.v1 validator and existing RPC client.
- supabase/migrations/20260927034822_reconcile_operational_enrollware_rosters.sql: reconcile_enrollware_roster_batch and canonical identity/complete-roster safety gates.
- scripts/audit_enrollware_reconciliation.py: unknown/stale/missing reconciliation audit.
- .github/workflows/verify-canonical-participants.yml: existing scheduled observer.
- tests/test_enrollware_roster_reconciliation.py: six contract regressions.

Validated locally in the isolated continuation worktree:

```text
python -B -m unittest tests.test_enrollware_roster_reconciliation -v
Ran 6 tests in 0.001s
OK
AST parsing scripts/enrollware_roster_reconciliation.py and scripts/audit_enrollware_reconciliation.py
Syntax: 2 files passed
```

Deterministic report comparison confirmed 42 -> 45 and the exact three additions above. No application code changed. This does not prove production recovery.

## Scope, persistence and queue

Only intended new file: Codex_Reply_Issue297_Dispatch_20261012_R37.md. Persisted locally; receipt-only commit/remote branch publication and byte equality are verified before exit. No new implementation PR is necessary for this receipt. Existing PRs are reused as ownership references, not duplicated.

Open issue/PR inventory and #371/#380 requirements reviewed: #372 owns the deep CRM stream; #381 owns the independent Production Board backend stream. New #388/#389 also own their backend checks. No safe unassigned narrow backend repair was established; those assignments are preserved. #371 Path A remains the next ordinary queue direction, subject to active assignment reconciliation.

Original E: checkout dirty files, untracked receipts, caches and Supabase temporary state were preserved. This separate worktree reports unexpected docs/Earl/index.html and docs/Jackson/index.html modifications on checkout, consistent with prior documented case-collision behavior; this dispatch made neither edit and excludes both. Existing corrupt Git reference/object reported in R36 remains untouched; no fetch repair, reset, cleanup or repack was attempted. Remote receipt publication may use GitHub API to avoid that known transport failure.

No importer apply, production database mutation, generator, build, merge or deployment. PR #372 was freshly checked OPEN/draft, mergedAt null; it remains unmerged and undeployed. No private participant data or secrets are included.

## Proof standard and recovery

Evidence state: existing implementation BUILT, historically CONNECTED/PROVEN; current unattended end-to-end process BLOCKED, not HEALTHY. Historical successful source proof recorded September 27 at 05:56:16.932Z expired one hour later. This dispatch does not renew it. Observer execution is proven by the scheduled run above, but observer-of-observer health was not freshly proven; skipped watchdog verification is not positive evidence.

Expected outcome: current complete source -> existing importer/RPC -> exact canonical relationships -> protected owner counts/rosters -> PII-free public selector/Anchor preservation -> subsequent actual scheduled refresh. Freshness window is 60 minutes; stale/missing identities must remain unknown, never zero. Recovery is provision/authorize the unattended exact-ID current roster source, validate privately with the existing --complete-roster importer, then approved apply and protected/public/scheduled proof. Account/source authorization remains the owner escalation boundary; no new owner action is required for the two already repaired assignments.

Keep #297 open and Stage 6 gated. Do not weaken source completeness or freshness gates. This explicitly required receipt does not authorize another unchanged-source pickup.
