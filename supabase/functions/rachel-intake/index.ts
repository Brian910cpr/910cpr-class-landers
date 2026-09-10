import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { intakeDetails, normalizeRachelPayload, normalizePhone } from "./normalize.mjs";

const headers = {"content-type":"application/json; charset=utf-8","cache-control":"no-store"};
const reply = (data: unknown, status = 200) => new Response(JSON.stringify(data), {status, headers});
const sha256 = async (value: string) => Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)))).map(b => b.toString(16).padStart(2,"0")).join("");
const safeEqual = (a: string, b: string) => a.length === b.length && a.split('').reduce((n, c, i) => n | (c.charCodeAt(0) ^ b.charCodeAt(i)), 0) === 0;

function config() {
  const url = Deno.env.get("SUPABASE_URL")!;
  const keys = Deno.env.get("SUPABASE_SECRET_KEYS");
  const key = keys ? JSON.parse(keys).default : Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const intakeSecret = Deno.env.get("RACHEL_INTAKE_SECRET") || "";
  return {url, key, intakeSecret};
}

async function rest(path: string, init: RequestInit = {}) {
  const {url, key} = config();
  const response = await fetch(`${url}/rest/v1/${path}`, { ...init, headers: {apikey:key, authorization:`Bearer ${key}`, "content-type":"application/json", prefer:"return=representation", ...(init.headers || {})} });
  const body = await response.text();
  const data = body ? JSON.parse(body) : null;
  if (!response.ok) throw new Error(data?.message || `Database request failed (${response.status})`);
  return data;
}

async function authorized(req: Request) {
  const expected = config().intakeSecret;
  const supplied = req.headers.get("x-rachel-intake-secret") || "";
  if (!expected || !supplied) return false;
  return safeEqual(await sha256(expected), await sha256(supplied));
}

async function matchCustomer(phone: string | null) {
  if (!phone) return null;
  const rows = await rest("customers?select=id,phone&phone=not.is.null&limit=1000");
  const matches = rows.filter((row: any) => normalizePhone(row.phone) === phone);
  return matches.length === 1 ? matches[0].id : null;
}

Deno.serve(async req => {
  if (req.method !== "POST") return reply({error:"Method not allowed"}, 405);
  if (!(await authorized(req))) return reply({error:"Unauthorized"}, 401);
  try {
    const event = normalizeRachelPayload(await req.json());
    const customerId = await matchCustomer(event.caller_phone);
    const [{intake, ...storedEvent}] = [{...event, matched_customer_id:customerId}];
    const result = await rest("rpc/create_phone_intake_event", {method:"POST", body:JSON.stringify({p_event:storedEvent, p_intake:{...intake, rendered_details:intakeDetails(event)}})});
    return reply(result, result.status === "created" ? 201 : result.status === "retained_test" ? 202 : 200);
  } catch (error) {
    return reply({error:error instanceof Error ? error.message : "Unexpected error"}, 400);
  }
});
