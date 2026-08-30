-- Additive bookkeeping evidence and reconciliation layer.
-- This migration does not make QBO authoritative and does not mutate QBO.

CREATE TABLE IF NOT EXISTS financial_accounts (
  id TEXT PRIMARY KEY,
  canonical_name TEXT NOT NULL,
  account_type TEXT NOT NULL,
  business_classification TEXT NOT NULL DEFAULT 'unknown',
  qbo_account_id TEXT,
  bank_account_id TEXT,
  account_last_four TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(qbo_account_id),
  CHECK (account_last_four IS NULL OR length(account_last_four) = 4)
);

CREATE TABLE IF NOT EXISTS financial_source_records (
  id TEXT PRIMARY KEY,
  source_system TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_record_id TEXT NOT NULL,
  source_reference TEXT,
  observed_at TEXT,
  ingested_at TEXT NOT NULL,
  checksum_sha256 TEXT NOT NULL,
  raw_payload_json TEXT NOT NULL,
  UNIQUE(source_system, source_type, source_record_id)
);

CREATE TABLE IF NOT EXISTS financial_account_sources (
  account_id TEXT NOT NULL,
  source_record_id TEXT NOT NULL,
  relationship_type TEXT NOT NULL,
  match_confidence TEXT NOT NULL,
  match_basis TEXT NOT NULL,
  PRIMARY KEY(account_id, source_record_id, relationship_type),
  FOREIGN KEY(account_id) REFERENCES financial_accounts(id),
  FOREIGN KEY(source_record_id) REFERENCES financial_source_records(id)
);

CREATE TABLE IF NOT EXISTS financial_facts (
  id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  field_name TEXT NOT NULL,
  value_json TEXT,
  confidence TEXT NOT NULL,
  source_record_id TEXT,
  effective_at TEXT,
  last_verified_at TEXT,
  is_current INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  FOREIGN KEY(account_id) REFERENCES financial_accounts(id),
  FOREIGN KEY(source_record_id) REFERENCES financial_source_records(id),
  CHECK (confidence IN ('VERIFIED','HIGH','MEDIUM','LOW','UNKNOWN','CONFLICTED'))
);

CREATE INDEX IF NOT EXISTS idx_financial_facts_current
  ON financial_facts(account_id, field_name, is_current);

CREATE TABLE IF NOT EXISTS financial_transactions (
  id TEXT PRIMARY KEY,
  source_record_id TEXT NOT NULL,
  source_system TEXT NOT NULL,
  external_id TEXT NOT NULL,
  account_id TEXT,
  transaction_date TEXT,
  posted_at TEXT,
  amount_minor INTEGER,
  currency TEXT NOT NULL DEFAULT 'USD',
  transaction_type TEXT,
  payee TEXT,
  memo TEXT,
  category_name TEXT,
  category_type TEXT,
  transfer_account_id TEXT,
  raw_payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(source_system, external_id),
  FOREIGN KEY(source_record_id) REFERENCES financial_source_records(id),
  FOREIGN KEY(account_id) REFERENCES financial_accounts(id)
);

CREATE INDEX IF NOT EXISTS idx_financial_transactions_date
  ON financial_transactions(transaction_date, account_id);

CREATE TABLE IF NOT EXISTS financial_reconciliation_exceptions (
  id TEXT PRIMARY KEY,
  detector_code TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  severity TEXT NOT NULL,
  priority_rank INTEGER NOT NULL,
  financial_impact_json TEXT,
  account_id TEXT,
  transaction_id TEXT,
  source_evidence_json TEXT NOT NULL,
  suspected_cause TEXT,
  safe_proposed_correction TEXT,
  user_clarification_required INTEGER NOT NULL DEFAULT 0,
  smallest_user_question TEXT,
  first_detected_at TEXT NOT NULL,
  last_detected_at TEXT NOT NULL,
  resolved_at TEXT,
  resolution_correction_id TEXT,
  UNIQUE(detector_code, account_id, transaction_id, source_evidence_json)
);

CREATE INDEX IF NOT EXISTS idx_financial_exceptions_queue
  ON financial_reconciliation_exceptions(status, priority_rank, severity);

CREATE TABLE IF NOT EXISTS financial_user_corrections (
  id TEXT PRIMARY KEY,
  correction_type TEXT NOT NULL,
  statement TEXT NOT NULL,
  accounting_treatment_json TEXT NOT NULL,
  supplied_by TEXT NOT NULL,
  supplied_at TEXT NOT NULL,
  supersedes_correction_id TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  FOREIGN KEY(supersedes_correction_id) REFERENCES financial_user_corrections(id)
);

CREATE TABLE IF NOT EXISTS financial_correction_targets (
  correction_id TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  PRIMARY KEY(correction_id, target_type, target_id),
  FOREIGN KEY(correction_id) REFERENCES financial_user_corrections(id)
);

CREATE TABLE IF NOT EXISTS financial_bookkeeping_actions (
  id TEXT PRIMARY KEY,
  correction_id TEXT,
  status TEXT NOT NULL DEFAULT 'proposed',
  current_treatment_json TEXT NOT NULL,
  proposed_treatment_json TEXT NOT NULL,
  reason TEXT NOT NULL,
  affected_records_json TEXT NOT NULL,
  reversal_or_reclassification TEXT,
  incorrect_action_risk TEXT NOT NULL,
  execution_mode TEXT NOT NULL DEFAULT 'human_review',
  created_at TEXT NOT NULL,
  executed_at TEXT,
  FOREIGN KEY(correction_id) REFERENCES financial_user_corrections(id)
);

