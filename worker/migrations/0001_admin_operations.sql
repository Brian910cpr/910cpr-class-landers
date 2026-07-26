CREATE TABLE IF NOT EXISTS hot_sync_sessions (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('committed','tentative','completed','cancelled','created_pending_enrollment')),
  visibility TEXT NOT NULL CHECK (visibility IN ('hidden','public')),
  course_key TEXT NOT NULL DEFAULT '',
  course_display_name TEXT NOT NULL,
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL,
  capacity INTEGER,
  client_name TEXT NOT NULL,
  location_name TEXT NOT NULL,
  instructor TEXT NOT NULL,
  notes TEXT NOT NULL DEFAULT '',
  enrollware_class_id TEXT,
  enrollware_enroll_url TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  created_by TEXT NOT NULL,
  needs_class_report_absorption INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_hot_sync_sessions_start_status
  ON hot_sync_sessions(start_time, status);

CREATE TABLE IF NOT EXISTS inbox_files (
  id TEXT PRIMARY KEY,
  original_filename TEXT NOT NULL,
  storage_key TEXT NOT NULL UNIQUE,
  mime_type TEXT NOT NULL,
  file_size INTEGER NOT NULL,
  uploaded_at TEXT NOT NULL,
  uploaded_by TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT 'Other',
  class_association TEXT NOT NULL DEFAULT '',
  processing_status TEXT NOT NULL DEFAULT 'stored',
  notes TEXT NOT NULL DEFAULT '',
  checksum_sha256 TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_inbox_files_uploaded_at
  ON inbox_files(uploaded_at DESC);

CREATE TABLE IF NOT EXISTS admin_audit_log (
  id TEXT PRIMARY KEY,
  logged_at TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  record_type TEXT NOT NULL,
  record_id TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_record
  ON admin_audit_log(record_type, record_id, logged_at);

CREATE TABLE IF NOT EXISTS offer_worker_audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  logged_at TEXT NOT NULL,
  action TEXT NOT NULL,
  source TEXT NOT NULL,
  course_key TEXT NOT NULL,
  start_time TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
