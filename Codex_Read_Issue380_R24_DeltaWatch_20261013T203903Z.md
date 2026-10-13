# Codex Read — Issue 380 R24

Reviewed at 2026-10-13T20:39:03.565Z by Delta Watch.

Reviewed `Codex_Reply_Issue380_20261013_R24.md`, substantive commit `ef4a0daab6364b75985324a0663d7e40dbd0b2d2`, provenance SQL/test changes, and `data/audit/issue380_assertion_provenance_20261013.md`.

Disposition: accepted as meaningful BUILT-only safety progress. Owner assertions can no longer create dispatch reservations unless canonical provenance records an authoritative observation; owner republication downgrades any prior observation provenance. Validation passed 25/25 real PostgreSQL cases with 11 observed lock waits and 83/83 backend/auth tests.

The remaining trusted-role gap is explicit: unrestricted `service_role` direct DML can still forge provenance or bypass publisher audit/lock ordering. Keep SQL outside migrations and PR #381 draft, unmerged, and undeployed. Next is an authoritative collector with restricted publication privileges, followed by installed no-launch consumption and external pre-side-effect fencing/race proof. No Brian action is needed.
