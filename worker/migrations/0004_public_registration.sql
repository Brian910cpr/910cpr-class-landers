-- LanderWare public registration lifecycle.
ALTER TABLE hot_sync_sessions ADD COLUMN registration_open INTEGER NOT NULL DEFAULT 0;
ALTER TABLE hot_sync_sessions ADD COLUMN public_slug TEXT NOT NULL DEFAULT '';
ALTER TABLE hot_sync_sessions ADD COLUMN base_price_cents INTEGER NOT NULL DEFAULT 0;
ALTER TABLE hot_sync_sessions ADD COLUMN card_price_cents INTEGER NOT NULL DEFAULT 0;
ALTER TABLE hot_sync_sessions ADD COLUMN ebook_enabled INTEGER NOT NULL DEFAULT 0;
ALTER TABLE hot_sync_sessions ADD COLUMN ebook_title TEXT NOT NULL DEFAULT '';
ALTER TABLE hot_sync_sessions ADD COLUMN ebook_price_cents INTEGER NOT NULL DEFAULT 0;

CREATE UNIQUE INDEX IF NOT EXISTS idx_hot_sync_public_slug
  ON hot_sync_sessions(public_slug) WHERE public_slug <> '';

ALTER TABLE class_students ADD COLUMN registration_status TEXT NOT NULL DEFAULT 'active';
ALTER TABLE class_students ADD COLUMN manage_token_hash TEXT NOT NULL DEFAULT '';
ALTER TABLE class_students ADD COLUMN base_price_cents INTEGER NOT NULL DEFAULT 0;
ALTER TABLE class_students ADD COLUMN card_price_cents INTEGER NOT NULL DEFAULT 0;
ALTER TABLE class_students ADD COLUMN ebook_selected INTEGER NOT NULL DEFAULT 0;
ALTER TABLE class_students ADD COLUMN ebook_title TEXT NOT NULL DEFAULT '';
ALTER TABLE class_students ADD COLUMN ebook_price_cents INTEGER NOT NULL DEFAULT 0;
ALTER TABLE class_students ADD COLUMN total_price_cents INTEGER NOT NULL DEFAULT 0;
ALTER TABLE class_students ADD COLUMN confirmation_sent_at TEXT;
ALTER TABLE class_students ADD COLUMN reminder_sent_at TEXT;
ALTER TABLE class_students ADD COLUMN cancelled_at TEXT;
ALTER TABLE class_students ADD COLUMN registration_source TEXT NOT NULL DEFAULT 'admin';

CREATE UNIQUE INDEX IF NOT EXISTS idx_class_students_manage_token_hash
  ON class_students(manage_token_hash) WHERE manage_token_hash <> '';
CREATE INDEX IF NOT EXISTS idx_class_students_reminders
  ON class_students(registration_status, reminder_sent_at, class_id);
