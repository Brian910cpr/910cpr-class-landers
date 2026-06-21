# First Brian + Shipyard BLS Filter Trace

Status: read-only trace. No public pages, Enrollware calls, appointments, appointment URL changes, Worker routes, deploys, or commits were performed.

## Summary

- Selected offer ID: `None`
- Candidate count: 0
- First failing condition: `select_offer`
- Reason code: `no_matching_offer`
- Smallest safe fix: No Brian + Shipyard BLS dynamic offer exists in current dynamic_offers_preview.json; create/fix a valid timed Brian Shipyard availability window that can fit BLS first.

## Trace

| Check | Passed | Reason if failed | Expression |
|---|---:|---|---|

No matching Brian + Shipyard BLS offer exists in `data/audit/dynamic_offers_preview.json`.
