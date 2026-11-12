-- Disposable LOCAL fixture only; never production inventory or access codes.
create table public.products(id uuid primary key default gen_random_uuid(),product_key text unique,
 active boolean,product_type text,customer_price numeric,fulfillment_mode text);
create table public.product_inventory_units(id uuid primary key default gen_random_uuid(),product_id uuid,
 secret_value text,status text,reserved_for_registration_id uuid,reserved_at timestamptz,
 exposed_at timestamptz,fulfilled_at timestamptz,updated_at timestamptz);
