# Retired legacy handoff snapshots

The mutable `ops/handoff/` workflow was retired when the repository-root `CODEX_HANDOFF_PROTOCOL.md` mailbox became authoritative.

## Retained historical material

- `MUST_REMEMBER.md` preserves scheduling doctrine.
- `chatgpt_notes.md` preserves task-specific safety notes.
- `latest_codex_report.md`, `latest_validation_run.txt`, `latest_git_status.txt`, and `latest_chatgpt_bundle.md` are historical snapshots from the last use of the former workflow.
- `next_task.md` is an explicit retirement marker.

These files are inert reference material. They are not an inbox, an unread/read state, a polling target, or a required Codex output. Do not update the `latest_*` files for new assignments.

## Current authoritative channels

- Inbound owner/ChatGPT instructions: `[CODEX]` GitHub Issues, documented in `docs/CODEX_INSTRUCTIONS.md`.
- Outbound Codex replies and ChatGPT acknowledgements: root `Codex_Reply_*` / `Codex_Read_*` files, documented in `CODEX_HANDOFF_PROTOCOL.md`.

The former helper `ops/scripts/show_handoff.ps1` was removed so it cannot continue presenting the retired workflow as active.
