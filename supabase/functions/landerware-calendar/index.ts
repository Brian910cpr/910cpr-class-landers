import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const EXCLUDED = new Set(["cancelled","canceled","removed","superseded","replacing","deleted","proposed","draft","tentative","pending_proposal"]);
const env = (name:string) => Deno.env.get(name) || "";

function esc(value: unknown) {
  return String(value ?? "")
    .replace(/\\/g, "\\\\")
    .replace(/\r?\n/g, "\\n")
    .replace(/,/g, "\\,")
    .replace(/;/g, "\\;");
}

function dt(value:string) {
  return new Date(value).toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

function safeEq(a:string,b:string) {
  const x = new TextEncoder().encode(a), y = new TextEncoder().encode(b);
  if (x.length !== y.length) return false;
  let diff = 0;
  for (let i=0;i<x.length;i++) diff |= x[i]^y[i];
  return diff === 0;
}

function adminKey() {
  const legacy = env("SUPABASE_SERVICE_ROLE_KEY");
  if (legacy) return legacy;
  try {
    const keys = JSON.parse(env("SUPABASE_SECRET_KEYS") || "{}");
    return keys.default || "";
  } catch {
    return "";
  }
}

async function rest(path:string) {
  const key = adminKey(), url = env("SUPABASE_URL");
  if (!key || !url) throw new Error("supabase_admin_key_unavailable");
  const r = await fetch(`${url}/rest/v1/${path}`, {
    headers: { apikey:key, Authorization:`Bearer ${key}` }
  });
  if (!r.ok) throw new Error(`database_${r.status}`);
  return await r.json();
}

Deno.serve(async (req:Request) => {
  try {
    if (req.method !== "GET") return new Response("Method Not Allowed", { status:405, headers:{ Allow:"GET" } });

    const url = new URL(req.url);
    const supplied = url.searchParams.get("token") || "";
    const expected = env("LANDERWARE_ICAL_TOKEN");

    if (!expected || !supplied || !safeEq(supplied, expected)) {
      return new Response("Not found", { status:404, headers:{ "Cache-Control":"no-store" } });
    }

    const since = new Date();
    since.setUTCDate(since.getUTCDate() - 90);

    const select = "id,external_session_id,course_id,course_name,starts_at,ends_at,location_name,instructor_name,lifecycle_state,provenance,updated_at";
    const sessions = await rest(`landerware_sessions?starts_at=gte.${encodeURIComponent(since.toISOString())}&select=${select}&order=starts_at.asc&limit=2000`);
    const real = (Array.isArray(sessions) ? sessions : []).filter((s:any) =>
      s.starts_at && !EXCLUDED.has(String(s.lifecycle_state || "").toLowerCase())
    );

    const counts = new Map<string,number>();
    for (let i=0;i<real.length;i+=100) {
      const ids = real.slice(i,i+100).map((s:any)=>s.id).filter(Boolean);
      if (!ids.length) continue;
      const rows = await rest(`landerware_registrations?session_id=in.(${ids.join(",")})&select=session_id,status&limit=5000`);
      for (const r of (Array.isArray(rows) ? rows : [])) {
        if (EXCLUDED.has(String(r.status || "").toLowerCase())) continue;
        counts.set(r.session_id, (counts.get(r.session_id) || 0) + 1);
      }
    }

    const lines:string[] = [
      "BEGIN:VCALENDAR",
      "VERSION:2.0",
      "PRODID:-//910CPR//LanderWare Operations//EN",
      "CALSCALE:GREGORIAN",
      "METHOD:PUBLISH",
      "X-WR-CALNAME:910CPR LanderWare"
    ];

    for (const s of real) {
      const start = dt(s.starts_at);
      const endSource = s.ends_at && new Date(s.ends_at) > new Date(s.starts_at)
        ? s.ends_at
        : new Date(new Date(s.starts_at).getTime() + 60*60*1000).toISOString();
      const end = dt(endSource);
      const sid = s.external_session_id || s.id;
      const count = counts.get(s.id) || 0;
      const date = new Date(s.starts_at).toLocaleDateString("en-CA", { timeZone:"America/New_York" });
      const workspace = `https://910cpr.com/admin/session-bundles/${date}`;
      const desc = [
        `Instructor: ${s.instructor_name || "Unassigned"}`,
        `Students: ${count}`,
        `Status: ${s.lifecycle_state || "unknown"}`,
        `Session ID: ${sid}`,
        `Source: ${s.provenance || "LanderWare"}`,
        `Workspace: ${workspace}`
      ].join("\n");

      lines.push(
        "BEGIN:VEVENT",
        `UID:landerware-${esc(s.id)}@910cpr.com`,
        `DTSTAMP:${dt(s.updated_at || new Date().toISOString())}`,
        `DTSTART:${start}`,
        `DTEND:${end}`,
        `SUMMARY:${esc(s.course_name || s.course_id || "910CPR Session")}`,
        `LOCATION:${esc(s.location_name || "")}`,
        `DESCRIPTION:${esc(desc)}`,
        `URL:${workspace}`,
        `X-LANDERWARE-SESSION-ID:${esc(sid)}`,
        `X-LANDERWARE-STATUS:${esc(s.lifecycle_state || "unknown")}`,
        "END:VEVENT"
      );
    }

    lines.push("END:VCALENDAR");

    return new Response(lines.join("\r\n") + "\r\n", {
      status:200,
      headers:{
        "Content-Type":"text/calendar; charset=utf-8",
        "Content-Disposition":"inline; filename=\"landerware.ics\"",
        "Cache-Control":"private, max-age=300"
      }
    });
  } catch {
    return new Response("Calendar unavailable", { status:500, headers:{ "Cache-Control":"no-store" } });
  }
});
