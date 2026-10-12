# Issue 297 — changed-source gate review

- Timestamp: 2026-10-12T08:25:09-04:00 (America/New_York).
- Assignment: Brian910cpr/910cpr-class-landers#297.
- State: BLOCKED at authoritative current complete-roster acquisition; diagnostic review validated locally.
- Branch: codex/issue297-dispatch-20261012-r36.
- Reviewed base commit: 2f70f6949ffe8aa30caa60d82f5b545ae9df4986. Receipt commit is the pushed branch tip, reported on the originating issue and in the dispatch response; no application commit was made.
- Local worktree: E:\GitHub\910cpr-issue297-dispatch-r36.
- Execution acknowledged before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/297#issuecomment-6124178340.

## Findings and exact blocker

The owner update at https://github.com/Brian910cpr/910cpr-class-landers/issues/297#issuecomment-6124122865 supersedes earlier statements that no source is available. It reports read-only review of Enrollware-export (71).xlsx: 11,875 rows, 26 distinct future email/class registrations, 22 already canonical, two non-session renewal-deadline rows, and two missing assignments repaired in production. These are owner-reported results, not new database/export verification by this dispatch. Do not repeat those repairs or undo the accepted October 13 correction.

The same owner update explicitly states that this export lacks exact numeric external registration IDs and is outside the 60-minute source window. It therefore cannot establish complete current rosters or renew reconciliation timestamps. The exact remaining blocker is authorization/provision of an unattended authenticated source supplying exact class/registration identities, current observations, and complete roster/lifecycle coverage, including empty rosters and cancellations/reschedules. An email/class match is not an external registration ID. Do not invent IDs, set a new source watermark on old data, or infer zero from missing rows.

Existing code was inspected at this base:

- scripts/import_enrollware_registration_events.py: --complete-roster selects the existing operational path; --apply requires that mode.
- scripts/enrollware_roster_reconciliation.py: prepare_snapshot validates enrollware-complete-roster.v1, unique numeric external_class_id/external_registration_id, committed/complete_roster flags, exact roster_count and timestamp age (at most 3600 seconds, at most 300 seconds future skew). The fingerprint includes the source watermark.
- supabase/migrations/20260927034822_reconcile_operational_enrollware_rosters.sql: reconcile_enrollware_roster_batch also validates source_kind/source_url and canonical course/location/instructor mappings; absent registrations can be canceled only against a complete roster. This is why the incomplete export must not be replayed.
- .github/workflows/verify-canonical-participants.yml: existing observer and issue notification path retained.

Scoped scripts/workflow search found the importer and observer, but did not establish an authorized unattended roster collector. No endpoint or credential was guessed, and no source-login attempt was made.

## Work performed and validation

Read issue body and paginated history, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos and proof standard. Reviewed latest owner source update and existing #371/#380 queue gates. Existing draft PR #372 remains the primary CRM stream; #381 already owns production-board backend work. No independent unassigned narrow backend repair was established, so neither stream was duplicated or displaced. No new PR was created for this receipt-only dispatch.

Commands and exact relevant results:

```text
python -B -m unittest tests.test_enrollware_roster_reconciliation -v
Ran 6 tests in 0.001s
OK

AST syntax validation of scripts/enrollware_roster_reconciliation.py
and scripts/audit_enrollware_reconciliation.py:
Syntax: 2 files passed
```

Inspected existing scheduled run 38192972069 through GitHub API: completed/failure, updated 2026-10-12T01:43:31Z. Source comparison and artifact upload succeeded; the condition-notification step failed the reconciliation-health job. verify-demand, verify-publication-watchdog and verify-production were skipped. This is inspection of existing evidence, not a new verifier execution or proof that the prior 42-gap count is current. No duplicate alert or retry was triggered.

## Persistence, scope and unrelated failures

Only intended changed file: Codex_Reply_Issue297_Dispatch_20261012_R36.md. It is persisted locally and committed/pushed to the named remote branch. Remote receipt bytes and exact commit file scope must be checked before reporting completion.

The original E:\GitHub\910cpr-class-landers checkout has unrelated dirty/untracked pages, data, caches, temporary Supabase state and prior receipts; none were staged or altered by this dispatch. Normal git fetch failed with bad object 6e61cabca5981d1389e52c60d95424d9893bb50f and bad reference refs/remotes/origin/codex/group-training-experience. No reference cleanup, reset or repack repair was attempted. The receipt can be pushed through the GitHub Git/Contents API if ordinary push remains blocked.

The separate worktree also reports unexpected modifications to docs/Earl/index.html and docs/Jackson/index.html (122 insertions, 15 deletions combined). This dispatch ran no generator and made neither edit. Their cause is unverified; they were preserved and excluded from the receipt commit. No broad command, staging or deployment follows those changes.

No importer apply, production database mutation, generator, build, merge or deployment was performed. PR #372 and #381 were checked open/draft. PR #372 remains unmerged and undeployed. No secrets or participant PII are included here.

## Persistent-system proof and next action

Evidence level: existing implementation BUILT and historically CONNECTED/PROVEN; current unattended end-to-end recovery remains BLOCKED, not HEALTHY. Historical successful source proof was recorded on September 27 at 05:56:16.932 UTC and expired one hour later; this dispatch does not renew it. The existing canonical verifier observes stale/missing relationships and suppresses unchanged notifications; its inspected scheduled run above shows execution, not current end-to-end health. Observer-of-observer health was not freshly proven here.

Success requires authorized current complete rosters -> existing importer/RPC -> exact canonical joins -> protected owner counts/rosters -> PII-free public selector/Anchor preservation -> a later genuine scheduled refresh. Keep #297 open and Stage 6 gated.

Next action for ChatGPT: retain the owner's changed-source finding and bounded repairs; provision/authorize the existing unattended authenticated source with exact registration identities. Validate privately with `python scripts/import_enrollware_registration_events.py --input <private-current-complete-roster.json> --complete-roster` before any approved apply. Then prove protected/public/scheduled recovery. Source authorization is the account-level escalation boundary; no additional action is required for the two already repaired assignments. Do not redispatch an unchanged-source review merely because this required receipt exists. Preserve #371 as the next ordinary claim and all existing assignments.
