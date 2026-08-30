# Codex → ChatGPT Handoff: QBO Reconciliation Foundation

Created: 2026-08-30

## Outcome

Phase 1 of the QBO reconciliation foundation is implemented on `codex/qbo-reconciliation-foundation`, based on `dc2a2d1b59ed0aa65b17176a117ddfdb8b2d9787` (`origin/main` at worktree creation).

This is locally persisted and validated. It is not deployed, does not access live QBO, and does not change production financial or scheduling data.

## Primary architecture/report text

Review the full document at `docs/QBO_RECONCILIATION_ARCHITECTURE.md`. It defines the source-evidence → bookkeeping-truth → CFO-inference boundary, schema, confidence rules, matching restrictions, detectors, CLI workflow, and next increments.

## Important schema paths

- `worker/migrations/0004_financial_reconciliation.sql`
- `finance_reconciliation/audit.py`
- `scripts/qbo_reconciliation.py`

Tables added by the undeployed migration:

- `financial_accounts`
- `financial_source_records`
- `financial_account_sources`
- `financial_facts`
- `financial_transactions`
- `financial_reconciliation_exceptions`
- `financial_user_corrections`
- `financial_correction_targets`
- `financial_bookkeeping_actions`

## Exact validation output

```text
python -m py_compile finance_reconciliation\audit.py scripts\qbo_reconciliation.py tests\test_qbo_reconciliation.py
python -m unittest tests.test_qbo_reconciliation -v

Ran 6 tests in 0.041s
OK
```

The end-to-end synthetic CLI run imported 3 accounts and 3 transactions, retained 6 source records, produced 12 open exceptions, and persisted one proposed user correction/bookkeeping action. Detector counts:

```json
{
  "CREDIT_CARD_PAYMENT_AS_EXPENSE": 1,
  "DUPLICATE_ACCOUNT_CANDIDATE": 1,
  "MISSING_MATERIAL_FACT": 8,
  "TRANSACTION_ACCOUNT_UNMATCHED": 1,
  "TRANSFER_LIKE_P_AND_L": 1
}
```

All data in that smoke run was synthetic and remained outside the repository.

## Changed files

- `.gitignore`
- `data/audit/chatgpt_handoff_qbo_reconciliation.md`
- `docs/QBO_RECONCILIATION_ARCHITECTURE.md`
- `finance_reconciliation/__init__.py`
- `finance_reconciliation/audit.py`
- `finance_reconciliation/schema.sql`
- `ops/WORKSTREAMS.yaml`
- `scripts/qbo_reconciliation.py`
- `tests/fixtures/qbo_reconciliation/accounts.json`
- `tests/fixtures/qbo_reconciliation/correction.json`
- `tests/fixtures/qbo_reconciliation/transactions.json`
- `tests/test_qbo_reconciliation.py`
- `worker/migrations/0004_financial_reconciliation.sql`
- `workstreams/qbo-reconciliation/README.md`
- `workstreams/qbo-reconciliation/STATE.yaml`
- `workstreams/qbo-reconciliation/NOTES.md`

## Review focus

1. Confirm D1/SQLite schema names and field-level confidence model.
2. Review false-positive risk in the keyword-based card-payment and transfer detectors.
3. Confirm priority ranks before real cash-decision use.
4. Confirm real QBO export shapes before extending adapters.
5. Do not approve QBO writes or D1 deployment based on synthetic validation alone.

## Open questions and blockers

- No real QBO account or transaction export has been ingested.
- No Novo, statement, Drive, or email adapter exists yet.
- Stale A/P, duplicate vendor bills, loan principal/interest splits, orphan documents, and source conflicts require richer evidence.
- The newly created coordination state begins on 2026-08-30 and contains no invented history.
