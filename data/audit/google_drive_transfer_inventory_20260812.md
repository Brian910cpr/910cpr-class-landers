# Google Drive transfer infrastructure inventory

## Scope and safety status

Preparation only. No candidate files were copied, moved, deleted, untracked, or rewritten. No production build or deployment was run. Drive inspection was read-only.

## Repository baseline

- Repository: `E:\GitHub\910cpr-class-landers`
- Review branch created for this work: `codex/drive-transfer-infrastructure`
- Starting branch: `codex/maxim-authoritative-availability` (ahead of its remote by one commit)
- Starting HEAD: `6f9687d431a5e288551009f61bc33c061f00b4fd`
- Working tree before this task: heavily dirty, with many modified generated/audit/runtime/site files and untracked site/review files. These were preserved and were not staged by this task.
- Working-tree content size excluding `.git`: 2,022,089,918 bytes (1.88 GiB), 54,106 files.
- `.git` size: 1,085,645,511 bytes (1.01 GiB).
- Git object summary: 39.06 MiB loose objects plus 813.64 MiB packed objects; no reported garbage.

## Largest top-level directories

| Directory | Bytes | Approx. size |
|---|---:|---:|
| `data` | 1,298,421,814 | 1.21 GiB |
| `debug` | 560,793,633 | 534.8 MiB |
| `docs` | 131,277,992 | 125.2 MiB |
| `CUSTOMER_images` | 10,731,296 | 10.2 MiB |
| `scripts` | 5,237,974 | 5.0 MiB |

## Largest current working-tree files

| Path | Bytes | Classification | Reference/risk note |
|---|---:|---|---|
| `data/runtime/audit_previews/public_sellable_offers_preview.json` | 347,616,127 | SAFE LOCAL/GENERATED — POSSIBLY IGNORE | Untracked and ignored, but explicitly produced/read by tests and audit tooling. Reproducible cache is a better fit than Drive migration. |
| `data/runtime/audit_previews/dynamic_offers_preview.json` | 314,619,917 | SAFE LOCAL/GENERATED — POSSIBLY IGNORE | Same path family is referenced by generators, tests, reports, and `data/config/course_master.json`; do not remove blindly. |
| `data/schedule.json` | 96,434,379 | NEEDS INVESTIGATION | Operational data; size alone is not evidence for migration. |
| `data/audit/heartsaver_block_schedule.json` | 72,984,870 | NEEDS INVESTIGATION | Tracked generated/audit output with active report/build context. |
| `data/runtime/enrollware_sync/reconciliation_20260427-074902.json` | 53,820,664 | NEEDS INVESTIGATION | Historical-looking operational record; path family is referenced by sync tooling. |
| `data/audit/bls_block_schedule_pilot.json` | 37,499,533 | NEEDS INVESTIGATION | Tracked audit/build artifact. |
| `data/state/session_manifest.json` | 36,455,668 | KEEP IN GITHUB | Durable session state is operationally authoritative under repository rules. |
| `data/schedule_all.json` | 35,138,754 | NEEDS INVESTIGATION | Operational scheduling data; reference review required. |
| `data/audit/live_availability_snapshot_trace.json` | 33,908,263 | NEEDS INVESTIGATION | Debug trace, but actively connected to availability audit workflow. |
| `debug/internal_missing_links_audit.json` | 31,289,873 | SAFE LOCAL/GENERATED — POSSIBLY IGNORE | Generated audit output; should be reproducible/ignored if policy allows. |
| `docs/images/files (11).zip` | 27,865,379 | CANDIDATE FOR GOOGLE DRIVE | Tracked archive; no filename reference found, but it sits under deployed `docs`, so verify public intent before removal. |
| `docs/images/files (12).zip` | 18,808,741 | CANDIDATE FOR GOOGLE DRIVE | Same caution as above. |

## Candidate directory findings

| Path | Bytes | Files | Git state | Classification |
|---|---:|---:|---|---|
| `data/backups/stale_offer_suppression` | 65,192,088 | 5 | tracked | CANDIDATE FOR GOOGLE DRIVE |
| `data/audit/untracked_quarantine_20260704_203633` | 11,986,421 | 36 | untracked | CANDIDATE FOR GOOGLE DRIVE |
| `debug/screenshots` | 14,351,358 | 34 | tracked | CANDIDATE FOR GOOGLE DRIVE |
| `debug/approved_name_apply_screenshots` | 48,617,354 | 41 | tracked | CANDIDATE FOR GOOGLE DRIVE |
| `data/runtime/enrollware_sync` | 73,862,022 | 6 | tracked | NEEDS INVESTIGATION before approval |
| `scripts/__pycache__` | 2,280,101 | 85 | 79 tracked / 6 untracked | SAFE LOCAL/GENERATED — POSSIBLY IGNORE |
| `tests/__pycache__` | 248,590 | 14 | 12 tracked / 2 untracked | SAFE LOCAL/GENERATED — POSSIBLY IGNORE |

The seven pending manifest entries total 260,583,363 bytes (248.5 MiB). This is a proposal total, not an approved-transfer total. The two untracked `audit_previews` files add 662,236,044 bytes (631.6 MiB) of generated local cache but are intentionally excluded from the transfer manifest because their paths are active in code/tests and they are reproducible.

## Other file-type observations

- Tracked screenshots exist under `debug/screenshots` and `debug/approved_name_apply_screenshots`; they are review artifacts, not deployed site images.
- PDFs and newly added product images under `docs/images`/`docs/assets` may be production content. They remain KEEP IN GITHUB or NEEDS INVESTIGATION until page references and ownership are settled.
- `data/enrollware_export.xlsx` is a tracked operational workbook (1,511,114 bytes). It is not a migration candidate without confirming whether current import/sync scripts depend on it.
- Large tracked CSV/JSON audit outputs should be evaluated individually. Their generated appearance does not authorize removing them because some are test inputs, operational traces, or current contracts.
- Duplicate-looking untracked product images appear in both `docs/images` and `docs/assets/products` with matching names and sizes. These are part of current untracked website work and were not added to the manifest.
- Identifiable history counts for bulky candidates: both ZIP archives appear in 3 commits; `debug/screenshots` in 2; `debug/approved_name_apply_screenshots` in 1; stale-offer backups in 5; `data/runtime/enrollware_sync` in 1; and `data/enrollware_export.xlsx` in 1. This confirms binary/archive history contributes to Git weight, but no history rewrite is proposed or authorized.

## Google Drive capability

- Google Drive for Desktop 129.0.1.0 is installed at `C:\Program Files\Google\Drive File Stream\129.0.1.0\GoogleDriveFS.exe`.
- It was not running during inspection, and no DriveFS-mounted drive letter was present.
- `C:\Users\ten77\Google Drive` exists but currently exposes only a `ShiftCommander` folder and was last modified in 2025; it is not proven to be a live/reliable Drive mount.
- `J:\Google_Drive` is an old local archive tree with legacy Google placeholder files; it is not a current Drive for Desktop mount and must not be used as the new authoritative target.
- `rclone` was not found on PATH and no usable rclone configuration was identified.
- The connected Google Drive account was searched read-only. No folder named `LanderWare` was found. Existing 910CPR-related folders include `910CPR Instructor Packets`, `910CPR Enrollware images`, and `910CPR COM`, but none is an obvious single project infrastructure root. Reuse should be decided by Brian rather than merging into these specialized trees.

## Recommended transport and Drive structure

First choice: start and authenticate the already-installed Google Drive for Desktop, confirm its mounted or mirrored filesystem root, create exactly one approved `LanderWare` root there, and set `LANDERWARE_DRIVE_ROOT` to that machine-specific path. This avoids adding software and lets the PowerShell utility use ordinary verified copies.

If Drive for Desktop cannot provide a stable filesystem path, install/authenticate `rclone` only after Brian approves the login. The present utility is filesystem-based; an rclone adapter can be added in Phase 2 after a remote is authorized.

Proposed single tree:

```text
LanderWare/
  Projects/
  Reference/
    Enrollware/
    AHA/
    Scheduling/
    Corporate Clients/
  Operational Data/
    Imports/
    Exports/
    Historical/
  Documents/
    Templates/
    Class Packets/
    Reports/
  Development Artifacts/
    Screenshots/
    Review Builds/
    Test Data/
  Archive/
```

No Drive folders were created in this phase.

## Protection and next approval gate

- Manifest entries are all `pending`; the utility refuses to transfer them.
- Default mode is dry-run. Actual copies require both an `approved` manifest entry and `-Execute`.
- The utility never deletes sources, never syncs `.git`, rejects secret/auth paths, refuses newer-destination overwrite, logs operations outside Git, and verifies actual copies with size and SHA-256.
- Recommended `.gitignore` follow-up (report only): review tracked `__pycache__`/`*.pyc`, ensure generated debug/audit outputs are ignored only after confirming they are reproducible, and do not change ignore rules until ownership of existing tracked files is decided.

CyberPC is not optional yet because there is no confirmed live Drive filesystem path, the proposed root has not been approved/created, all candidates remain pending, and several large operational/generated paths need owner review before their retention model changes.

## Local validation results

- PowerShell parser: 0 errors.
- Manifest JSON: parsed successfully.
- `inventory`: 7 entries enumerated; actual byte totals matched the manifest inventory.
- Pending-entry push test: refused with exit code 1 before copying.
- Approved `.git/config` safety test using a temporary manifest: refused with exit code 1.
- `status`: correctly reported no configured/available Drive root and exit code 2.
- `git diff --check` on the four task files: passed.
- Deployment status: not deployed; no build or public page was changed.
