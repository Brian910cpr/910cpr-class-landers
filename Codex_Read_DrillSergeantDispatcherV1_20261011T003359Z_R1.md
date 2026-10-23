# Codex read: Drill Sergeant dispatcher v1, 2026-10-11 R1

- Reviewed reply: `Codex_Reply_DrillSergeantDispatcherV1.md`.
- Reviewed branch: `codex/issue266-dispatch-preflight-20261010` at `0835663ae0e376525efb3795095753306d9edcba`.
- Reviewed substantive commit: `7ab9b3ea641717261be7d020ae2793f431a4f3b3`.
- Review PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/375.
- Disposition: accepted as a bounded offline diagnostic checkpoint; not accepted as a dispatcher, installation, connection, end-to-end worker proof, monitored state, merge readiness, or deployment proof.

## Review performed

Inspected the root handoff and all four changed paths. The preflight is pure/offline, has no I/O or execution path, requires explicit worker-safe queue provenance, rejects duplicate IDs and mismatched identities/repositories, applies capability/concurrency/staleness/disable gates, and always returns `dispatch_enabled: false`. The eight Node tests cover the documented synthetic cases. Source integrity and Cloudflare Pages preflight checks passed.

The implementation correctly refuses to amplify the current worker-control gaps. It does not authenticate snapshot provenance or provide credentials, claims, leases, an outbox, restart recovery, revocation, recurring work, or independent observation. No existing ChatGPT watch should be removed based on this checkpoint.

## Next safe action

Keep #266 open and PR #375 draft/unmerged/uninstalled. Reuse the #249/#250/#252/#254 worker stream and PR #374: implement per-worker credential binding, atomic lease/attempt ownership, ambiguous-outcome recovery, clean bootstrap, and remote revocation/observer proof first. Then add the separate persistent dispatcher state/lock/outbox and prove #266 a-g on real workers before enabling recurring `site.healthcheck` or migrating any watch.

Brian-only action: none now; engineering prerequisites remain first.