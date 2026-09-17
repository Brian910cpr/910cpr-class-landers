# 910CPR Worker Profile

This file is the durable apples-to-apples capability profile for one worker. Each installed worker should maintain its own profile using this schema.

## Identity

- Worker name:
- Worker ID:
- Machine name:
- Physical location / role:
- Worker version:
- Profile schema version: 1
- Last profile refresh (UTC):
- Last benchmark run (UTC):

## Static system inventory

- Manufacturer / model:
- Windows edition / version / build:
- Architecture:
- PowerShell version:
- CPU model:
- Physical cores:
- Logical processors:
- Installed RAM:
- RAM speed / modules:
- Primary working disk:
- Disk media / bus type:
- Working-volume free space:
- GPU:
- GPU VRAM:
- Active network adapter:
- Negotiated link speed:
- Expected uptime window:
- Installed tooling:

## Measured benchmark results

Keep raw measurements and normalized 0-100 scores. Never replace raw values with scores alone.

### CPU
- Single-thread benchmark raw:
- Multi-thread benchmark raw:
- Representative repo build/test duration:
- CPU score (0-100):

### Memory
- Peak RAM used during standard workload:
- Paging observed:
- Standard workload memory pressure:
- Memory score (0-100):

### Storage
- Sequential read MB/s:
- Sequential write MB/s:
- Repository traversal / small-file benchmark:
- Storage score (0-100):

### Network
- GitHub/control-plane latency ms:
- Practical download Mbps:
- Practical upload Mbps:
- Packet loss / instability observed:
- Network score (0-100):

### Reliability
Rolling window should be stated, e.g. last 30 days or last 100 jobs.

- Jobs attempted:
- Jobs succeeded:
- Unexpected exits:
- Stale leases:
- Duplicate executions:
- Heartbeat uptime %:
- Reboot/logon recovery proven: yes/no
- Reliability score (0-100):

### Availability
- Expected available hours/day:
- Observed heartbeat availability %:
- Requires owner interaction for routine operation: yes/no
- Availability score (0-100):

## Capability gates

Mark explicit yes/no capabilities. A job may only be routed when all hard gates are satisfied.

- local deterministic scripts:
- large repository scans:
- Python builds/tests:
- Node builds/tests:
- browser automation:
- Docker/WSL:
- long-running unattended jobs:
- high-memory jobs:
- high-I/O jobs:
- large-download/artifact jobs:
- Codex CLI authorized:
- production mutation authorized:
- customer communication authorized:
- secret-management authorized:

## Dispatch classification

- Primary class: light / standard / heavy
- Secondary tags:
- Preferred job types:
- Avoid job types:
- Max recommended concurrent jobs:
- Long-job suitability: poor / fair / good / excellent
- Owner-interaction dependency: low / medium / high

## Benchmark history

Append new runs. Do not erase prior results.

### YYYY-MM-DD HH:MM UTC
- Trigger:
- Benchmark version:
- CPU:
- MEM:
- DISK:
- NET:
- REL:
- AVL:
- Material changes since prior run:
- Notes:

## Dispatcher rule

Use hard capability gates first. Among eligible workers, choose based on the workload-relevant measured KPIs plus reliability and availability. Do not choose from one overall score alone.
