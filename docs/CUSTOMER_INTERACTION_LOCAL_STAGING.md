# Issue 371 local staging checkpoint — October 11, 2026

Owner chose CyberPC local isolated staging; earlier cloud-preview gate is superseded. No paid project or branch is needed.

## Observed prerequisites

Host: CyberPC. WSL executable exists, but `wsl --status` explicitly reports Windows Subsystem for Linux is not installed (exit 1). Docker is absent from PATH and `C:/Program Files/Docker/Docker/resources/bin/docker.exe`; common Program Files, Scoop apps and local Programs inspection found no Docker/Podman installation. No usable container runtime was established. Disk free: C approximately 1.57 TB, E approximately 1.20 TB. Disk capacity is not the blocker.

`Get-SmbMapping` returned no mappings. No approved Synology UNC destination is supplied. NAS reachability, read/write access and security remain UNKNOWN; no NAS data was written and no arbitrary network path was guessed.

## Safe bounded progress

`tests/customer_interaction_restart.test.mjs` executes all three existing CRM migrations against an isolated disk-backed PGlite database with synthetic content. It saves and interrupts, closes/reopens storage, verifies original idempotent receipt, raw checkpoint and selection, audit link and versions, rejects a stale save, resumes and reopens again, then verifies authenticated-role privacy denial. Temporary synthetic database is removed after close. Existing production schema/functions/auth/UI are untouched.

36 CRM/auth tests passed, 0 failed. Syntax check passed. This is local database restart evidence, not owner-session/browser/PostgREST/Edge Runtime proof, power-loss proof or concurrent-process proof. PGlite cannot substitute for final local Supabase integration acceptance. No operational CRM monitor exists yet; overall foundation remains BUILT.

## Resume safely

### Completed-task restart evidence (October 11 follow-up)

The restart suite also persists a synthetic completed follow-up, closes/reopens storage, and replays both the original create request and completion request. The original create receipt remains an immutable historical response while the current task remains complete at version 2; it does not re-enter the pending queue. Changed-actor retries, stale updates and duplicate source imports are rejected. Completion evidence and original provenance survive reopening, with exactly two audit events. Both anon and authenticated database roles are denied task/audit reads and RPC execution. This does not prove frontend handling of a delayed historical response; the UI must reload current state rather than overwrite it with an old receipt.

37 CRM/auth tests passed, zero failures; Node syntax and diff checks passed. This remains bounded synthetic SQL restart evidence, not owner-session/UI/API or concurrent-process proof. Runtime preflight reconfirmed WSL not installed, Docker absent from PATH/common Docker executable path. Installation approval and the approved Synology destination remain unresolved. No production or browser code changed.

Owner approval is required for privileged container/WSL installation, per the local staging directive. Request approval for a suitable Docker Desktop/WSL2 installation (including any required Windows feature/reboot) after checking platform prerequisites. Do not install or clean destructively without that approval. Ask for the intended Synology UNC backup folder and security expectations; keep credentials out of GitHub. Verify access before storing artifacts.

Once a usable runtime exists, configure an isolated localhost-only development stack, synthetic owner-session fixtures and explicit development-only origin policy without modifying production auth. Apply CRM additive migrations with a faithful canonical person-table prerequisite. Then prove owner session -> UI -> API -> storage -> reload/interrupt/resume before connecting operational capture. Existing Studio stays explicitly a tab-local prototype. Keep PR372 draft/unmerged and production undeployed.
