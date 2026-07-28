CREATE TABLE IF NOT EXISTS financial_payment_receipts (
  id TEXT PRIMARY KEY,
  invoice_id TEXT NOT NULL,
  invoice_number TEXT,
  customer_name TEXT,
  amount INTEGER NOT NULL,
  currency TEXT NOT NULL DEFAULT 'usd',
  payment_method TEXT NOT NULL,
  reference TEXT,
  received_date TEXT NOT NULL,
  comment TEXT,
  recorded_at TEXT NOT NULL,
  recorded_by TEXT NOT NULL,
  stripe_status TEXT NOT NULL DEFAULT 'paid'
);

CREATE INDEX IF NOT EXISTS idx_financial_receipts_invoice
  ON financial_payment_receipts(invoice_id, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_financial_receipts_received
  ON financial_payment_receipts(received_date DESC);
