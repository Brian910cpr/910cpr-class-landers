import { createClient } from "https://esm.sh/@supabase/supabase-js@2.56.0";
import { createHandler } from "./handler.ts";

Deno.serve(createHandler({
  db: () => createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } }),
  stripeKey: () => Deno.env.get("STRIPE_SECRET_KEY"),
  fetch: globalThis.fetch,
  now: () => Date.now(),
}));
