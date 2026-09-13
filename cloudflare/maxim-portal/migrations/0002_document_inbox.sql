PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS documents (
  document_id TEXT PRIMARY KEY,
  storage_key TEXT NOT NULL UNIQUE,
  original_name TEXT NOT NULL,
  content_type TEXT,
  size_bytes INTEGER NOT NULL DEFAULT 0,
  sha256 TEXT,
  document_type TEXT NOT NULL DEFAULT 'unknown',
  state TEXT NOT NULL DEFAULT 'unfiled',
  corporate_customer TEXT NOT NULL DEFAULT 'MAXIM',
  person_id TEXT,
  registration_id TEXT,
  class_id TEXT,
  notes TEXT,
  uploaded_by TEXT,
  uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  assigned_at TEXT,
  processed_at TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (person_id) REFERENCES people(person_id),
  FOREIGN KEY (registration_id) REFERENCES registrations(registration_id)
);

CREATE INDEX IF NOT EXISTS idx_documents_state_uploaded
ON documents(state, uploaded_at DESC);

CREATE INDEX IF NOT EXISTS idx_documents_registration
ON documents(registration_id, uploaded_at DESC);

CREATE INDEX IF NOT EXISTS idx_documents_person
ON documents(person_id, uploaded_at DESC);
