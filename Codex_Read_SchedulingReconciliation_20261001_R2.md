# Scheduling reconciliation — October 12 release gate

Timestamp: 2026-10-01T04:06:51.951200+00:00
Branch: `codex/scheduling-reconciliation-20261001`
Implementation commit: `46a83950e10df6077a80859170830734e637863d`
Work-item state: PR_OPEN — https://github.com/Brian910cpr/910cpr-class-landers/pull/322

Owner added October 12 to mandatory post-deploy browser verification. Reported source facts: 09:00 BLS Renewal with one registration; 17:00 BLS Initial session. The Initial registration count was not given and remains unspecified. Reported bad public Initial offers: 00:00 through 04:30 at half-hour intervals, plus 12:45.

Changed files:
- `tests/test_scheduling_reconciliation.py`
- `data/audit/scheduling_reconciliation_20261001.md`
- `Codex_Reply_SchedulingReconciliation_20261001_R2.md`

Added a focused regression requiring the Initial selector to honor the Renewal anchor even when Renewal is absent from its displayed offers. Both known-zero and unknown Initial demand retain only the 17:00 real offer and remove all eleven named orphan starts. Flat offers and nested calendar decisions must agree. No scheduling policy or live records changed in this addition.

Validation:
```text
python -B -m unittest tests.test_scheduling_reconciliation
Ran 13 tests in 0.006s
OK
Python AST syntax validation passed
git diff --check: clean
```

Post-deploy acceptance: verify live BLS Initial with October 12 selected, including calendar and Start Times. Capture the rendered starts, registration target, build/asset/feed versions and screenshot. Inspect Renewal and Landscape for the 09:00/17:00 real occurrences and honest roster freshness. If any named unrelated synthetic offer remains, STOP the release-verification procedure and do not call the release verified; investigate the deployed occupied-date/barnacle rule before continuing completion.

Release status: PR #322 was still open when checked at 2026-10-01T04:05 UTC. Earlier backend components are deployed; public frontend release and live verification remain pending the previously requested production-refresh approval. The roster collector gap and October 7 source conflict remain as documented in the primary audit. Local prior source snapshots are historical evidence and must not be relabeled current.

Persistent-system evidence: this addition is BUILT and locally validated. It establishes a required release check, not a successful production proof. Next action: after the approved merge/refresh, run October 2, 3, 7 and 12 browser checks; enforce the owner's October 12 stop condition. Unrelated Earl/Jackson checkout collisions, Python caches and `supabase/.temp/` remain uncommitted.
