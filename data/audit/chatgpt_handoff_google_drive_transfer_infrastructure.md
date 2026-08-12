# ChatGPT handoff — Google Drive transfer infrastructure

## Primary audit/report

Read the full report at `data/audit/google_drive_transfer_inventory_20260812.md`. It contains the repository baseline, size tables, classifications, Drive capability findings, proposed tree, safety gates, and remaining blockers.

## Machine-readable manifest

`data/migration/google_drive_transfer_manifest.json`

- Schema version: 1
- Entry count: 7
- Total proposed candidate bytes: 260,583,363
- Every `approval_status`: `pending`
- Important fields: `source_path`, `proposed_drive_destination`, `size_bytes`, `tracked_status`, `reason_for_migration`, `known_code_references`, `disposition_recommendation`, `approval_status`

## Source/config/test files for review

- `scripts/drive-transfer.ps1` — dry-run-first transfer utility
- `data/migration/google_drive_transfer_manifest.json` — pending proposal only
- `data/audit/google_drive_transfer_inventory_20260812.md` — complete inventory and decision record
- `.gitignore` — inspected only; no change made
- `AGENTS.md` and `lore/dockmaster.md` — repository rules read before implementation

## Exact baseline command results

```text
repository: E:\GitHub\910cpr-class-landers
starting branch: codex/maxim-authoritative-availability
review branch: codex/drive-transfer-infrastructure
HEAD: 6f9687d431a5e288551009f61bc33c061f00b4fd
starting branch remote state: ahead 1
working tree bytes excluding .git: 2022089918
.git bytes: 1085645511
working tree file count: 54106
git loose objects: 39.06 MiB
git packed objects: 813.64 MiB
git garbage: 0 bytes
```

The pre-existing working tree contained a large number of modified and untracked files. This task intentionally stages only the four files listed under Changed files below.

## Drive findings

```text
Google Drive for Desktop: installed, version 129.0.1.0
DriveFS running during inspection: no
confirmed current DriveFS mount: no
C:\Users\ten77\Google Drive: exists, stale/unproven, only ShiftCommander visible
J:\Google_Drive: legacy local archive, not suitable as current mount
rclone on PATH: no
connected Drive folder named LanderWare: none found
```

The connected Drive read-only search did find specialized 910CPR folders (`910CPR Instructor Packets`, `910CPR Enrollware images`, `910CPR COM`). Do not create a duplicate structure inside those without owner confirmation.

## Changed files

```text
scripts/drive-transfer.ps1
data/migration/google_drive_transfer_manifest.json
data/audit/google_drive_transfer_inventory_20260812.md
data/audit/chatgpt_handoff_google_drive_transfer_infrastructure.md
```

## Validation results

```text
PowerShell parser errors: 0
manifest JSON parse: pass
inventory: pass (7 entries; actual sizes matched)
pending entry push: refused, exit 1
approved .git/config test: refused, exit 1
status without configured Drive root: unavailable, exit 2
git diff --check: pass
actual copies: none
deployment: none
```

## Open questions / assumptions

1. Brian must choose whether the specialized existing 910CPR Drive folders should remain separate and approve one single `LanderWare` root.
2. Brian must start/sign in to Drive for Desktop and confirm the reliable mounted/mirrored path, or approve rclone installation/authentication.
3. Each manifest entry needs explicit review; no blanket approval is assumed.
4. `data/runtime/enrollware_sync` should be split into current versus historical material before approval.
5. Tracked generated files and `__pycache__` need a separate Git policy decision; no `.gitignore` or history change was made.
