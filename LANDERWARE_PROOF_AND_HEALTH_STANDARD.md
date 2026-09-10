# LanderWare Persistent Systems Proof and Health Standard

## Purpose

LanderWare is an operational system. Persistent features, agents, syncs, automations, schedulers, ingestion pipelines, registration flows, deployment paths, and background/recovery processes must not be declared working merely because code exists, a commit was pushed, or a single component ran once.

The governing lesson is simple:

> Prove the smallest useful end-to-end process. Keep observing it until it is trustworthy. When proven components are composed into a larger process, move the primary health check upward to the larger outcome while retaining lower-level diagnostics for failure investigation.

The owner must not be the monitoring layer, the reminder system, or the person who discovers that a supposedly persistent process silently stopped.

## Completion states

Persistent systems use these states:

1. **BUILT** — implementation exists.
2. **CONNECTED** — the required components can communicate or exchange state.
3. **PROVEN** — a real end-to-end cycle has completed successfully with evidence.
4. **MONITORED** — the system has an observable success signal, stale/failure detection, and a defined observer/escalation path.
5. **HEALTHY** — the system is currently within its expected operating window and has recent evidence of successful end-to-end operation.

Do not use **DONE**, **WORKING**, **LIVE**, or **HEALTHY** as shorthand for merely BUILT or DEPLOYED.

When reporting status, state the actual level reached and the evidence supporting it.

## Required proof contract

Every persistent process must identify:

- **Expected outcome:** what useful real-world result is supposed to occur.
- **Success evidence:** what durable evidence proves that outcome occurred.
- **Expected cadence/window:** how often or by when success should normally occur.
- **Last successful proof:** timestamp and durable evidence reference when practical.
- **Failure/staleness condition:** what indicates the process is late, stuck, disconnected, or producing invalid output.
- **Observer:** what process, dashboard, watcher, or supervisor notices that failure/staleness condition.
- **Observer health:** what proves the watcher itself is still running. A monitor that nobody monitors is not sufficient.
- **Recovery path:** the smallest safe action to diagnose or restore service.
- **Escalation boundary:** which failures Codex/ChatGPT/LanderWare can repair automatically and which genuinely require Brian or another account-level human action.

## Monitoring hierarchy

Do not permanently create a separate top-level alarm for every implementation detail.

### Stage 1: prove the nugget

When a new component or narrow workflow is introduced, observe it directly until its behavior is understood and repeatable.

Examples:

- Gmail/Enrollware source event -> durable LanderWare ingest record.
- Available session -> public offer -> working registration path.
- Registration -> payment -> participant attached to the correct session.
- Codex assignment -> pushed reply -> ChatGPT acknowledgement.

### Stage 2: compose proven pieces

When proven components are joined into a larger workflow, the larger workflow becomes the primary health boundary.

For example, once registration, payment, participant projection, and session attachment are individually proven, the preferred ongoing proof is the larger student lifecycle outcome rather than four independent green lights that can disagree.

### Stage 3: keep drill-down diagnostics

Lower-level instrumentation remains available for fault isolation, audits, and targeted recovery. It should not force Brian to manually inspect every gear during normal operation.

### Stage 4: move the health boundary upward

As more workflows become trustworthy, compose them into larger operational proofs.

Example health hierarchy:

- source ingestion healthy
- schedule truth healthy
- public inventory healthy
- registration lifecycle healthy
- class completion lifecycle healthy
- overall LanderWare operational loop healthy

Ultimately the desired heartbeat is a real-world loop such as:

> Real inputs arrive -> LanderWare correctly understands reality -> customers see correct choices -> transactions work -> operations receive the result -> completion is recorded.

## End-to-end truth beats component optimism

A successful database write does not prove the public site works.

A successful build does not prove deployment works.

A successful deployment does not prove the customer path works.

A watcher configuration does not prove the watcher is running.

A reply file convention does not prove either agent is actually checking it.

A green component should never override contradictory evidence from the real end-to-end outcome.

## Evidence over memory

Questions such as these must be answered from current evidence when practical:

- Is this process still running?
- When did it last succeed?
- Is Codex still processing work?
- Is public inventory current?
- Are calendar conflicts actually blocking offers?
- Is registration still reaching payment and session attachment?
- Is a scheduled sync still ingesting source changes?

Do not answer these from recollection of having built the feature months ago.

## Silent failure is a first-class defect

For persistent systems, a process that stops without creating a detectable stale/failure condition is defective even if its core logic is otherwise correct.

When adding or repairing a persistent process, explicitly consider:

1. What if the process never starts?
2. What if it starts and hangs?
3. What if credentials or source access fail?
4. What if it succeeds technically but produces no useful end-to-end result?
5. What if its monitor stops running?
6. How would LanderWare/ChatGPT/Codex notice without Brian remembering to ask?

## Recovery and fallback doctrine

Recovery mechanisms are part of the product, not afterthoughts.

- Prefer automatic recovery for repository-side, deterministic, and safely reversible failures.
- Preserve durable failure evidence before destructive repair.
- Deduplicate recurring failures by root cause rather than creating endless duplicate incidents.
- Escalate only when the remaining action genuinely requires human/account authority or a business decision.
- A fallback should itself have observable use and health. A fallback that silently never runs is not a fallback.

## Reporting language

For persistent systems, prefer precise status language:

- `BUILT: code committed; no end-to-end proof yet.`
- `CONNECTED: source and destination exchanged test data.`
- `PROVEN: real end-to-end cycle succeeded at <timestamp>.`
- `MONITORED: stale condition and observer are active; observer heartbeat last seen at <timestamp>.`
- `HEALTHY: end-to-end success last observed at <timestamp>; no stale/failure condition currently active.`

Avoid saying `done`, `fixed`, `working`, or `healthy` without evidence appropriate to that claim.

## Application to LanderWare projects

This standard applies by default to persistent or operational work, including but not limited to:

- Codex/ChatGPT handoffs
- Production Board processing
- Gmail/Enrollware ingestion
- schedule and availability reconciliation
- Google Calendar conflict blocking
- public class inventory generation
- registration and payment workflows
- participant/session projection
- student and instructor portals
- Atlas/public class publishing
- eCard and completion workflows
- recurring syncs, scheduled jobs, recovery sweeps, and watchdogs
- deployment and production verification processes

A task may explicitly be one-time/nonpersistent; in that case this standard should not create unnecessary monitoring infrastructure.

## Owner burden rule

Brian may choose priorities and business rules, but routine system health must not depend on Brian remembering that a process exists, remembering when to check it, carrying messages between agents, or manually discovering stale work.

When a persistent system still requires that behavior, report it as an unresolved operational dependency rather than describing the system as fully healthy.

## Relationship to Codex handoff protocol

`CODEX_HANDOFF_PROTOCOL.md` is one concrete implementation of this doctrine. The mailbox provides durable state; the pickup and fallback watchers provide observation; the reply/read transition provides end-to-end acknowledgement evidence.

The handoff system should itself be evaluated under this standard rather than treated as an exception.
