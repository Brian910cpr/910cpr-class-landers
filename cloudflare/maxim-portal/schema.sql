PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS people (
  person_id TEXT PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS corporate_profiles (
  person_id TEXT NOT NULL,
  corporate_customer TEXT NOT NULL,
  billing_account TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (person_id, corporate_customer),
  FOREIGN KEY (person_id) REFERENCES people(person_id)
);

CREATE TABLE IF NOT EXISTS renewal_cycles (
  renewal_id TEXT PRIMARY KEY,
  person_id TEXT NOT NULL,
  corporate_customer TEXT NOT NULL,
  billing_account TEXT,
  credential_key TEXT NOT NULL,
  source_course_date TEXT,
  expiration_date TEXT,
  status TEXT NOT NULL DEFAULT 'coming_due',
  skipped_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (person_id) REFERENCES people(person_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_renewal
ON renewal_cycles(person_id, corporate_customer, credential_key)
WHERE status IN ('coming_due','link_sent','registered');

CREATE TABLE IF NOT EXISTS registrations (
  registration_id TEXT PRIMARY KEY,
  person_id TEXT NOT NULL,
  renewal_id TEXT,
  source_renewal_ref TEXT,
  source_person_ref TEXT,
  corporate_customer TEXT NOT NULL,
  billing_account TEXT,
  course_id TEXT NOT NULL,
  credential_key TEXT NOT NULL,
  class_id TEXT,
  registration_url TEXT,
  starts_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'registered',
  superseded_by TEXT,
  ecard_number TEXT,
  ecard_url TEXT,
  billing_batch_id TEXT,
  stripe_invoice_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (person_id) REFERENCES people(person_id),
  FOREIGN KEY (renewal_id) REFERENCES renewal_cycles(renewal_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_registration
ON registrations(person_id, corporate_customer, credential_key)
WHERE status='registered' AND superseded_by IS NULL;

CREATE TABLE IF NOT EXISTS go_tokens (
  token TEXT PRIMARY KEY,
  intent_type TEXT NOT NULL,
  person_id TEXT,
  renewal_id TEXT,
  corporate_customer TEXT,
  billing_account TEXT,
  credential_key TEXT,
  state TEXT NOT NULL DEFAULT 'active',
  expires_at TEXT,
  consumed_at TEXT,
  revoked_at TEXT,
  superseded_by_token TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (person_id) REFERENCES people(person_id),
  FOREIGN KEY (renewal_id) REFERENCES renewal_cycles(renewal_id)
);

CREATE INDEX IF NOT EXISTS idx_go_tokens_renewal ON go_tokens(renewal_id, state);

CREATE TABLE IF NOT EXISTS portal_events (
  event_id TEXT PRIMARY KEY,
  person_id TEXT,
  renewal_id TEXT,
  registration_id TEXT,
  event_type TEXT NOT NULL,
  actor_type TEXT,
  actor_ref TEXT,
  payload_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
