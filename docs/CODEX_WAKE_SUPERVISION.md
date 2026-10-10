# Existing supervisor health contract

Single remote signal: https://github.com/Brian910cpr/910cpr-class-landers/pull/372#issuecomment-6102455692

API: `GET /repos/Brian910cpr/910cpr-class-landers/issues/comments/6102455692`.
Read the current comment body, never a search snippet or cached task summary.
This comment is on a PR deliberately: publication must not change an intake issue's updatedAt and create self-dispatch loops.

The existing Windows Codex Wake loop updates this one comment approximately every minute during idle and execution. No extra service/schedule is introduced. Local `health-publish.json` contains only `comment_id: 6102455692`; GitHub authentication uses the existing gh login. Only explicitly allowed operational fields leave the machine. Raw failures, local paths and prompts never leave it. A failed publication does not terminate intake; the remote timestamp becomes stale.

## Append to the existing 910CPR Delta Watch instructions

Keep the existing schedule and all existing duties. At EVERY scheduled run, independently retrieve the current launcher health comment linked above, even when there are no new handoffs or business changes. Compare published_at to current UTC. A missing/unreadable/malformed/future timestamp is UNKNOWN/monitoring failure, never healthy. Older than 5 minutes is STALE: launcher, machine or publication path may be unavailable; do not assert which without evidence. A live signal with manual_hold true reports a held implementation stream, not a stopped launcher. A live signal with last_launch_status failed reports an execution failure. A recent publication with execution_process_alive true proves supervisor liveness during a long job; old last_check_at then is not by itself evidence of a stopped loop. With no execution or hold, last_check_at older than 30 minutes is a stalled intake check.

Notify Brian through the task's existing enabled notification delivery on first failure/stale transition, meaningful cause changes and recovery. Include current UTC, last published_at, last_check_at, last_session_id, signal URL, and the next repair action: inspect/restart the SAME Codex Wake loop after checking active execution and locks. Remain quiet on unchanged healthy state and unchanged already-reported failures. Do not create another task/dispatcher, change assignments, or infer health from a GitHub acknowledgment. Retain the last observed failure/recovery state in the supervisor conversation. If a task run cannot access the comment or deliver notifications, report that as an observer failure requiring account/notification repair.

## Append to the existing 910CPR Deep Stability Review instructions

Keep the existing morning/evening schedule and duties. Apply the same health evaluation and notification rules above independently. Also review the latest Delta Watch scheduled execution and whether its launcher check ran successfully within 90 minutes. If this execution evidence cannot be read, explicitly report observer health UNKNOWN; do not infer success from its configured enabled state. Escalate a missing/failed Delta Watch run as an observer failure. Never add a duplicate monitor.

## Required real stopped-launcher acceptance test (pending task access)

1. Save both existing task IDs, unchanged schedules, revised instructions and enabled notification channel. Observe each task reading a fresh live signal.
2. Ensure no active Codex execution; retain assignments and workstream hold. Record actual live loop PID/start time and published_at.
3. Stop only that verified idle loop. Leave the shared signal untouched: no synthetic stale timestamp. Record stop time.
4. Wait for the EXISTING hourly Delta Watch scheduled run. Obtain its run evidence and delivered stale alert without Brian polling or manually running the task. Expected detection: five-minute stale threshold plus up to one hourly interval (about 65 minutes, excluding scheduler delay).
5. Restart the same loop, verify a newer publication, and obtain the supervisor's recovery observation. Always restore the loop after the bounded test window, including failed/unknown observer outcomes.

Do not stop the real launcher before the observer can access the signal. Local mocked tests prove payload/privacy/error behavior only; they cannot prove scheduled detection or delivered notifications. A browser login is currently required to edit the existing ChatGPT tasks. No unattended alert proof is claimed yet.
