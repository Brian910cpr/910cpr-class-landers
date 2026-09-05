alter table public.historical_registration_import_rows
  add column if not exists last_error text;
