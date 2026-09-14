# Issue 214: owner inputs received and a targeted change prepared

Owner input date: September 14, 2026. This is new input from Brian in the active Codex conversation, not a repeat of the earlier blocked assessments.

- Receipt timestamp: 2026-09-14T16:27:17-04:00.
- Work-item state: PR_OPEN; starter intake/source-copy verification complete.
- Persistent application evidence: BUILT; complete operational proof remains unestablished.
- Courier branch: `codex/issue-214-owner-input-receipt-20260914`.
- Courier file: `Codex_Reply_ShiftCommanderOwnerInputs_20260914_R1.md`; verified courier commit is reported after push.

## Owner decisions now established

1. Initial supervisors: Brett Toney, Lynnsey Benson and Brian Ennis.
2. Brian supplied a 22-member starter roster. He says little has changed and explicitly accepts adding missing people after seeing the workflow work. Treat roster completeness as an iterative pilot task, not a reason to withhold the first private demonstration.
3. Brian does not know whether the previously reported bridge credential was replaced. Record unknown; do not claim incident resolution or ask him to paste credential values.
4. Brian designated the existing ADR ShiftCommanderData Drive folder for continuity copies. Private folder/source references are retained locally rather than exposed in this public receipt.

## Application change, commit and review

- Repository: Brian910cpr/shiftcommander_v2.
- Branch: `codex/issue-214-owner-intake-20260914`.
- Commit: `4005dc60f4d89eaded4509ccd7e1b6d4cd216814`.
- Draft PR: https://github.com/Brian910cpr/shiftcommander_v2/pull/11
- Base: existing `codex/issue-214-release-gate-verification-r9`.
- Exact changed files: `data/members.json`, `data/audit/owner_intake_20260914.json`, `docs/OWNER_INPUTS_ISSUE214_20260914.md`.

Only member 186 gains `access.supervisor=true`. Members 159 and 188 already have supervisor access. All 41 existing application members and all other fields remain unchanged. The actual application role helper recognizes exactly these three supervisor IDs. This changes the review candidate only; no account was provisioned or activated.

## Source and continuity evidence

The owner's local file and the existing Drive `members.json` are byte-for-byte identical: 17,592 bytes; SHA-256 `978ef060e2c965eb3f5ca4e4e5f7bdb35621f1f7c26871a38a37babe3c47008b`. Embedded source update date is February 9, 2026; owner starter approval is September 14, 2026. No duplicate source upload was needed.

Drive inventory found 54 files and 7 duplicated availability filenames; 13 relevant files were downloaded and inspected. All 22 stable-ID/ADR-number CSV mappings agree with the starter. Against the richer 41-member application roster, 15 source rows match both name and number, 7 require identity review, and 6 have conflicting active status. Preserve richer records and disputed mappings; do not bulk replace the existing roster or silently transfer history by reused ADR number.

An ADR continuity README was uploaded and its folder membership, size and full text verified. The folder is owned by Brian's account and has named ADR collaborators plus anyone-with-link edit access. The owner was asked how to handle that sharing; no permissions changed, no ownership transfer was claimed, and no new full personnel archive was uploaded. The requested starter source copy already exists and is verified.

Historical files are useful references. Their 07:00/19:00 shift settings must not override the later confirmed 06:00/18:00 rules. Old availability is not fresh consent; duplicated files must be identified by Drive ID. Missing members alone should not block a private demonstration, while disputed qualifications and unknown availability remain explicit.

## Exact local/private artifacts

- Review checkout: `E:\GitHub\shiftcommander_v2_codex_issue214_owner_intake`.
- Ignored source and full analysis: `debug/owner_intake_20260914/members.source.json`, `debug/owner_intake_20260914/full_intake.json`, `debug/owner_intake_20260914/drive_inventory.json` in that checkout.
- User-facing detailed report/archive: `C:\Users\ten77\Documents\Codex\2026-09-13\re-visit-214\outputs\ShiftCommander-Owner-Intake-20260914.md`, corresponding `.json` and `.zip`.
- Reproduction/intake script: `C:\Users\ten77\Documents\Codex\2026-09-13\re-visit-214\work\adr-intake-20260914\build_intake.py`. It writes local artifacts and the two intake reports; do not rerun it against unrelated branches or publish its private output as-is.

## Validation and next concrete work

Seven local intake/role checks passed: valid source JSON, unique source IDs, unique ADR numbers, exact Drive/source byte equality, all 22 CSV mappings, exactly the three owner-approved supervisors through the real helper, and structural equality except Lynnsey's new flag. Repository JSON validation, server Python syntax and explicit-file diff checks passed. Private source records/full conflict rows/Drive links are excluded from the public branch. No broader behavioral test or login/release proof is claimed.

Use this changed owner evidence to continue the same workstream. Prepare the private pilot and persistent auth configuration for these named supervisors, collect fresh availability in the application, and demonstrate save/readback and a legal explained scheduling pass. Resolve ambiguous roster rows incrementally without dropping richer existing records.

The service credential family is `SC_D1_BRIDGE_TOKEN`, used by the Flask live-state consumer and Worker validator. Prepare exact coordinated replacement/rollback and old-token rejection checks using actual serving metadata. No value was retrieved, printed, copied, or rotated here. Owner understanding is not a technical prerequisite; the worker should prepare the repair and surface only an exact account action when required.

Status: changed in repository, locally validated, committed and pushed; Drive source verified and continuity note saved. Draft PR remains unmerged. No deployment, login activation, routing/calendar cutover, paid service, member communication or second implementation worker was started. Original dirty checkouts, the R9 assessment, unpublished commits and existing worker controls remain preserved.

The connector's PR-create request returned 403 Resource not accessible by integration. The PC's existing authenticated GitHub CLI successfully created PR #11; no retry of that failing connector path or credential change was made.

Operational proof still needed: one authenticated real availability save, durable restart/readback, legal reviewed publication and matching views. Last complete real-world success is not established. Confirmed publication cadence remains Wednesday 23:59; lost saves, stale data, illegal assignments or differing revisions are failures. Whole-system observer and its heartbeat remain unproven. Recovery should preserve current storage and credentials, use a separately verified store, and avoid resurrecting revoked sessions. This one-time intake creates no new monitor or timer. The worker should own the next technical step, asking Brian only for an exact unavailable account action or substantive business decision.
