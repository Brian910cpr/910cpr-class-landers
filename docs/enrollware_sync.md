# Enrollware Sync

This workflow treats the master schedule spreadsheet as the source of truth and Enrollware as the publishing and payment surface.

## Phases

### Phase 1: Dry Run

Build desired sessions, validate them, and compare them against an Enrollware export without touching Enrollware.

Example:

```powershell
C:\Users\ten77\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m scripts.enrollware_sync dry-run `
  --repo-root E:\GitHub\910cpr-class-landers `
  --master data\Class Report.xlsx `
  --enrollware-export data\enrollware_export.xlsx `
  --rules data\config\enrollware_sync_rules.example.json
```

Outputs go to `data/runtime/enrollware_sync/<timestamp>/`:

- `desired_sessions.json`
- `sync_report.json`
- `sync_report.md`

The dry run validates:

- duplicate desired slots
- closed days
- instructor overlaps
- location overlaps
- impossible or missing time windows
- expected course duration ranges
- configured instructor or location blackout windows

The sync report separates:

- would create
- would update
- would skip
- duplicate risk
- missing in Enrollware
- extra in Enrollware
- manual review needed

Extra classes in Enrollware are flagged only. The tool does not delete live classes automatically.

### Phase 2: Playwright Scaffold

The scaffold opens Enrollware pages and fills fields like a human user. It stops before clicking Save unless `--apply` is explicitly passed.

Example:

```powershell
C:\Users\ten77\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m scripts.enrollware_sync playwright-scaffold `
  --repo-root E:\GitHub\910cpr-class-landers `
  --dry-run-report E:\GitHub\910cpr-class-landers\data\runtime\enrollware_sync\20260427-120000\sync_report.json `
  --master data\Class Report.xlsx `
  --rules data\config\enrollware_sync_rules.example.json `
  --headed
```

If Playwright, selectors, or authorized session details are missing, the scaffold writes a blocker report instead of guessing.

### Phase 3: Controlled Writes

Live writes are allowed only when all of these are true:

- `--apply` is passed
- `--limit` is passed
- a dry-run report exists
- the dry-run report matches the current master schedule file hash
- a timestamped Enrollware export snapshot is supplied

The script never enables live writes by accident.

### Phase 4: Reconciliation

After any write, compare the desired sessions against a fresh Enrollware export and save the resolved Enrollware IDs and registration URLs back into reconciliation output.

Example:

```powershell
C:\Users\ten77\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m scripts.enrollware_sync reconcile `
  --repo-root E:\GitHub\910cpr-class-landers `
  --desired-sessions E:\GitHub\910cpr-class-landers\data\runtime\enrollware_sync\20260427-120000\desired_sessions.json `
  --enrollware-export E:\GitHub\910cpr-class-landers\data\enrollware_export.xlsx
```

## Notes

- The current script assumes spreadsheet headers shaped like the existing class report and Enrollware export.
- `data/config/enrollware_sync_rules.example.json` is a starter config and should be copied to a real local rules file before live use.
- The Playwright selectors in the example config are placeholders until they are confirmed against the actual Enrollware admin UI.
