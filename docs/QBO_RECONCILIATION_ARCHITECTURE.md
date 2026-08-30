# QBO Reconciliation Foundation

## Boundary

This layer makes financial evidence disagreements visible before any value reaches CFO reasoning. It is not a forecasting engine and does not make QuickBooks Online authoritative merely because a record exists there.

The three layers are deliberately separate:

1. **Source evidence** is immutable-at-ingest provenance from QBO exports, bank exports, statements, Drive documents, notices, and user statements.
2. **Bookkeeping truth** is the current evidence-backed account, fact, transaction treatment, exception, and approved correction state.
3. **CFO inference** is downstream analysis. It may consume `VERIFIED`, `HIGH`, and contextually reviewed `MEDIUM` facts. It must label or exclude `LOW`, `UNKNOWN`, and `CONFLICTED` facts.

A missing value is never converted to zero.

## Phase 1 status

Phase 1 is additive and read-only with respect to QBO. The migration creates tables but is not deployed by this branch. The local audit script reads exported JSON into a local SQLite database using the same D1-compatible schema. Existing Stripe receipt and scheduling paths are unchanged.

## Data model

| Structure | Purpose |
|---|---|
| `financial_accounts` | Canonical financial account or obligation identity |
| `financial_source_records` | Original source identity, payload, checksum, and reference |
| `financial_account_sources` | Explicit evidence-to-account relationship and match basis |
| `financial_facts` | Field-level value, confidence, source, and verification date |
| `financial_transactions` | Imported QBO/bank transaction evidence |
| `financial_reconciliation_exceptions` | First-class coverage gap and cleanup queue item |
| `financial_user_corrections` | Durable user-confirmed statement and treatment |
| `financial_correction_targets` | Accounts/transactions affected by a correction |
| `financial_bookkeeping_actions` | Reviewable proposed reclassification or reversal |

Monetary transaction values use integer minor units. Fact values are JSON so unknown stays `null`, not `0`, and non-monetary values retain their type. Only masked last-four account digits may be stored.

## Confidence model

- `VERIFIED`: current primary evidence directly establishes the fact.
- `HIGH`: strong official or posted evidence with no known conflict.
- `MEDIUM`: credible evidence with a material limitation.
- `LOW`: weak or stale evidence; never an established forecasting input.
- `UNKNOWN`: no evidence-backed value. This is not zero.
- `CONFLICTED`: credible sources disagree; a reconciliation exception is required.

## Ingestion and matching

```text
source export/document metadata
  -> parse without mutation
  -> store source record + checksum
  -> resolve explicit source/account identity
  -> attach field-level facts with confidence
  -> import transactions
  -> run deterministic detectors
  -> rank cleanup queue
  -> request the smallest useful user clarification
```

Matching priority is explicit source ID, explicit QBO/bank ID, masked suffix plus canonical name and type, then a review candidate. Amount-only matches are prohibited. The initial importer intentionally does not fuzzy-match accounts.

Expected adapter inputs are JSON arrays or an object containing `accounts`/`transactions`. QBO API response adapters can be added later without changing canonical tables. Raw statements and secrets must not be committed.

## Read-only audit detectors

The first implementation detects:

- duplicate account candidates by normalized active name and type;
- transactions whose source account is unmatched;
- likely credit-card payments categorized to profit and loss;
- transfer-like activity categorized as income or expense;
- missing current balances, due dates, minimums, and APRs on material liabilities.

These are review findings, not automatic reclassifications. Implausible balances, stale A/P, orphan documents, source conflicts, duplicate bills, and paired-bank-transfer matching require richer adapters and evidence and remain planned.

## Prioritization

`priority_rank=1` affects current cash, debt, or material profit reporting. Rank 2 affects debt completeness or accounting/tax review. Lower ranks are reserved for cosmetic cleanup. Severity and exact evidence remain separate fields so ranking is explainable.

## Durable correction loop

A correction JSON stores the user's exact statement, structured accounting treatment, targets, current and proposed treatment, reason, reclassification steps, and the risk of acting incorrectly. It creates a `proposed` bookkeeping action in `human_review` mode. Nothing in Phase 1 executes against QBO.

## Usage

```powershell
python scripts/qbo_reconciliation.py --database data/private/qbo_audit.sqlite init
python scripts/qbo_reconciliation.py --database data/private/qbo_audit.sqlite import-accounts path/to/qbo_accounts.json --system qbo
python scripts/qbo_reconciliation.py --database data/private/qbo_audit.sqlite import-transactions path/to/qbo_transactions.json --system qbo
python scripts/qbo_reconciliation.py --database data/private/qbo_audit.sqlite audit --json-output data/audit/qbo_reconciliation.json --markdown-output data/audit/qbo_reconciliation.md
python scripts/qbo_reconciliation.py --database data/private/qbo_audit.sqlite record-correction path/to/correction.json
```

`data/private/` and real exports must remain untracked. Reports must be reviewed for sensitive content before commit or sharing.

## Next safe increments

1. Export the QBO chart of accounts and a bounded transaction period; run the audit locally.
2. Add Novo/bank transaction adapter and explicit paired-transfer matching.
3. Add statement/document metadata ingestion and conflict detection.
4. Review the cleanup queue with Brian and persist corrections.
5. Only then design narrowly scoped QBO write actions with approval and reversal plans.
