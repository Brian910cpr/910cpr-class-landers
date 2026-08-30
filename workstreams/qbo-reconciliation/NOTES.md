# QBO Reconciliation Notes

## 2026-08-30 — Phase 1 foundation

### Findings

- The canonical base had Stripe invoice receipt recording in D1 but no QBO connector, QBO schema, reconciliation exception model, or correction memory.
- Existing production scheduling JSON is unrelated and remains untouched.
- The QBO audit can operate locally without credentials when given exported JSON.

### Decisions and assumptions

- QBO is evidence, not bookkeeping truth.
- Phase 1 is read-only with respect to QBO and undeployed with respect to D1.
- Transaction amounts use integer minor units.
- Missing material liability facts become exceptions and are never coerced to zero.
- User corrections always create a human-review bookkeeping action; they do not execute automatically.
- Exact source identity is used before any matching heuristic. Amount-only and fuzzy account matching are excluded.

### Evidence conflicts

- None from real data: no QBO, bank, statement, Drive, or inbox evidence was supplied.
- Synthetic fixtures intentionally exercise duplicate accounts, a card payment booked as expense, a transfer booked as income, and an unmatched account.

### Needs Brian

- Provide bounded QBO account and transaction exports.
- Choose the first bank export adapter (Novo CSV/JSON format).
- Review whether detector priority ranks match current cash-decision urgency.

### Opportunities discovered

- Add paired transfer detection after both bank-account legs are available.
- Add statement metadata and conflict detection without storing sensitive documents in Git.
- Feed only confidence-qualified facts and explicit coverage gaps into a future Daily CFO report.
