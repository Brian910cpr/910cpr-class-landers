const ALLOWED_ORIGINS = new Set(["https://www.910cpr.com", "https://910cpr.com"]);
const ALLOWED_STATUSES = new Set(["committed", "tentative", "completed", "cancelled"]);
const ALLOWED_VISIBILITY = new Set(["hidden", "public"]);
const ALLOWED_EXTENSIONS = new Set(["pdf", "xlsx", "xls", "csv", "docx", "png", "jpg", "jpeg"]);
const MAX_UPLOAD_BYTES = 15 * 1024 * 1024;

export async function handleAdminApi(request, env, url) {
  if (!url.pathname.startsWith("/admin/")) return null;
  const origin = request.headers.get("Origin") || "";
  if (origin && !ALLOWED_ORIGINS.has(origin)) return json({ error: "Origin is not allowed.", code: "origin_rejected" }, 403, origin);
  if (request.method === "OPTIONS") return corsPreflight(origin);
  if (!env.HOT_SYNC_ADMIN_KEY) return json({ error: "Admin service is not configured.", code: "service_unavailable" }, 503, origin);
  if (!(await authorized(request, env.HOT_SYNC_ADMIN_KEY))) return json({ error: "Authentication failed.", code: "authentication_failed" }, 401, origin);

  if (url.pathname === "/admin/hot-sync" && request.method === "GET") return listHotSync(env, origin);
  if (url.pathname === "/admin/hot-sync" && request.method === "POST") return createHotSync(request, env, origin);
  const hotSyncMatch = url.pathname.match(/^\/admin\/hot-sync\/([A-Za-z0-9_-]{6,100})$/);
  if (hotSyncMatch && request.method === "GET") return readHotSync(hotSyncMatch[1], env, origin);
  if (hotSyncMatch && request.method === "PUT") return updateHotSync(hotSyncMatch[1], request, env, origin);
  if (hotSyncMatch && request.method === "DELETE") return cancelHotSync(hotSyncMatch[1], env, origin);

  if (url.pathname === "/admin/inbox" && request.method === "GET") return listInbox(env, origin);
  if (url.pathname === "/admin/inbox" && request.method === "POST") return uploadInbox(request, env, origin);
  const inboxMatch = url.pathname.match(/^\/admin\/inbox\/([A-Za-z0-9_-]{6,100})$/);
  const contentMatch = url.pathname.match(/^\/admin\/inbox\/([A-Za-z0-9_-]{6,100})\/content$/);
  if (contentMatch && request.method === "GET") return downloadInbox(contentMatch[1], env, origin);
  if (inboxMatch && request.method === "PATCH") return updateInbox(inboxMatch[1], request, env, origin);
  if (inboxMatch && request.method === "DELETE") return deleteInbox(inboxMatch[1], env, origin);
  return json({ error: "Admin endpoint not found.", code: "not_found" }, 404, origin);
}

async function authorized(request, expected) {
  const supplied = request.headers.get("X-Hot-Sync-Admin-Key") || "";
  const encoder = new TextEncoder();
  const expectedDigest = await crypto.subtle.digest("SHA-256", encoder.encode(expected));
  const suppliedDigest = await crypto.subtle.digest("SHA-256", encoder.encode(supplied));
  const left = new Uint8Array(expectedDigest);
  const right = new Uint8Array(suppliedDigest);
  let mismatch = left.length ^ right.length;
  for (let index = 0; index < left.length; index += 1) mismatch |= left[index] ^ (right[index] || 0);
  return supplied.length > 0 && mismatch === 0;
}

function requireDatabase(env, origin) {
  if (!env.HOT_SYNC_D1) return json({ error: "HOT_SYNC persistence is not connected.", code: "storage_unavailable" }, 503, origin);
  return null;
}

function cleanText(value, maxLength, required = false) {
  const text = String(value ?? "").replace(/[\u0000-\u001f\u007f]/g, " ").trim();
  if (required && !text) throw new ValidationError("A required field is missing.");
  if (text.length > maxLength) throw new ValidationError(`A field exceeds ${maxLength} characters.`);
  return text;
}

function normalizeClass(input, id) {
  const start = cleanText(input.start || input.start_time, 40, true);
  const end = cleanText(input.end || input.end_time, 40, true);
  const startDate = new Date(start);
  const endDate = new Date(end);
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime()) || endDate <= startDate) {
    throw new ValidationError("Start and end must be valid, and end must be after start.");
  }
  const status = cleanText(input.status || "committed", 20);
  const visibility = cleanText(input.visibility || "hidden", 20);
  if (!ALLOWED_STATUSES.has(status)) throw new ValidationError("Status is not allowed.");
  if (!ALLOWED_VISIBILITY.has(visibility)) throw new ValidationError("Visibility is not allowed.");
  const capacity = input.capacity === null || input.capacity === "" || input.capacity === undefined ? null : Number(input.capacity);
  if (capacity !== null && (!Number.isInteger(capacity) || capacity < 1 || capacity > 1000)) throw new ValidationError("Capacity must be a whole number from 1 to 1000.");
  return {
    id,
    source: "hot_sync_manual",
    status,
    visibility,
    course_key: cleanText(input.course_key, 120),
    course_display_name: cleanText(input.course_display_name, 240, true),
    start: startDate.toISOString(),
    end: endDate.toISOString(),
    capacity,
    client_name: cleanText(input.client_name, 240, true),
    location_name: cleanText(input.location_name, 500, true),
    instructor: cleanText(input.instructor || "Brian", 120, true),
    notes: cleanText(input.notes, 4000),
    needs_class_report_absorption: true,
  };
}

async function requestJson(request) {
  const type = request.headers.get("Content-Type") || "";
  if (!type.toLowerCase().startsWith("application/json")) throw new ValidationError("Content-Type must be application/json.");
  try { return await request.json(); }
  catch (_) { throw new ValidationError("Request body is not valid JSON."); }
}

function actor(env) {
  return cleanText(env.HOT_SYNC_ADMIN_ACTOR || "dashboard_admin", 120);
}

async function createHotSync(request, env, origin) {
  const unavailable = requireDatabase(env, origin);
  if (unavailable) return unavailable;
  try {
    const input = await requestJson(request);
    const id = input.id ? cleanId(input.id) : `hs_${crypto.randomUUID().replace(/-/g, "")}`;
    const record = normalizeClass(input, id);
    const now = new Date().toISOString();
    const who = actor(env);
    await env.HOT_SYNC_D1.batch([
      env.HOT_SYNC_D1.prepare(`INSERT INTO hot_sync_sessions
        (id,source,status,visibility,course_key,course_display_name,start_time,end_time,capacity,client_name,location_name,instructor,notes,created_at,updated_at,created_by,needs_class_report_absorption)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`).bind(record.id, record.source, record.status, record.visibility, record.course_key, record.course_display_name, record.start, record.end, record.capacity, record.client_name, record.location_name, record.instructor, record.notes, now, now, who, 1),
      auditStatement(env, "create", record.id, who, now, record),
    ]);
    return json({ record: { ...record, created_at: now, updated_at: now, created_by: who }, blocking: blocksAvailability(record) }, 201, origin);
  } catch (error) {
    if (String(error.message || "").includes("UNIQUE")) return json({ error: "A record with that ID already exists.", code: "duplicate_id" }, 409, origin);
    return safeError(error, origin);
  }
}

async function updateHotSync(id, request, env, origin) {
  const unavailable = requireDatabase(env, origin);
  if (unavailable) return unavailable;
  try {
    id = cleanId(id);
    const existing = await env.HOT_SYNC_D1.prepare("SELECT * FROM hot_sync_sessions WHERE id = ?").bind(id).first();
    if (!existing) return json({ error: "HOT_SYNC record not found.", code: "not_found" }, 404, origin);
    const record = normalizeClass(await requestJson(request), id);
    const now = new Date().toISOString();
    const who = actor(env);
    await env.HOT_SYNC_D1.batch([
      env.HOT_SYNC_D1.prepare(`UPDATE hot_sync_sessions SET source=?,status=?,visibility=?,course_key=?,course_display_name=?,start_time=?,end_time=?,capacity=?,client_name=?,location_name=?,instructor=?,notes=?,updated_at=?,needs_class_report_absorption=1 WHERE id=?`)
        .bind(record.source, record.status, record.visibility, record.course_key, record.course_display_name, record.start, record.end, record.capacity, record.client_name, record.location_name, record.instructor, record.notes, now, id),
      auditStatement(env, "update", id, who, now, { before: existing, after: record }),
    ]);
    return json({ record: { ...record, created_at: existing.created_at, updated_at: now, created_by: existing.created_by }, blocking: blocksAvailability(record) }, 200, origin);
  } catch (error) { return safeError(error, origin); }
}

async function cancelHotSync(id, env, origin) {
  const unavailable = requireDatabase(env, origin);
  if (unavailable) return unavailable;
  try {
    id = cleanId(id);
    const existing = await env.HOT_SYNC_D1.prepare("SELECT * FROM hot_sync_sessions WHERE id = ?").bind(id).first();
    if (!existing) return json({ error: "HOT_SYNC record not found.", code: "not_found" }, 404, origin);
    const now = new Date().toISOString();
    const who = actor(env);
    await env.HOT_SYNC_D1.batch([
      env.HOT_SYNC_D1.prepare("UPDATE hot_sync_sessions SET status='cancelled', updated_at=? WHERE id=?").bind(now, id),
      auditStatement(env, "cancel", id, who, now, existing),
    ]);
    return json({ id, status: "cancelled", blocking: false }, 200, origin);
  } catch (error) { return safeError(error, origin); }
}

async function listHotSync(env, origin) {
  const unavailable = requireDatabase(env, origin);
  if (unavailable) return unavailable;
  const result = await env.HOT_SYNC_D1.prepare("SELECT * FROM hot_sync_sessions ORDER BY start_time DESC LIMIT 250").all();
  return json({ records: (result.results || []).map(classFromRow) }, 200, origin);
}

async function readHotSync(id, env, origin) {
  const unavailable = requireDatabase(env, origin);
  if (unavailable) return unavailable;
  try {
    const row = await env.HOT_SYNC_D1.prepare("SELECT * FROM hot_sync_sessions WHERE id = ?").bind(cleanId(id)).first();
    return row ? json({ record: classFromRow(row), blocking: blocksAvailability(classFromRow(row)) }, 200, origin) : json({ error: "HOT_SYNC record not found.", code: "not_found" }, 404, origin);
  } catch (error) { return safeError(error, origin); }
}

function classFromRow(row) {
  return {
    id: row.id, source: row.source, status: row.status, visibility: row.visibility,
    course_key: row.course_key, course_display_name: row.course_display_name,
    start: row.start_time, end: row.end_time, capacity: row.capacity,
    client_name: row.client_name, location_name: row.location_name, instructor: row.instructor,
    notes: row.notes, created_at: row.created_at, updated_at: row.updated_at,
    created_by: row.created_by, needs_class_report_absorption: Boolean(row.needs_class_report_absorption),
  };
}

function blocksAvailability(record) {
  return record.status === "committed" && record.needs_class_report_absorption;
}

function auditStatement(env, action, recordId, who, now, payload) {
  return env.HOT_SYNC_D1.prepare("INSERT INTO admin_audit_log (id,logged_at,actor,action,record_type,record_id,payload_json) VALUES (?,?,?,?,?,?,?)")
    .bind(crypto.randomUUID(), now, who, action, "hot_sync", recordId, JSON.stringify(payload));
}

async function uploadInbox(request, env, origin) {
  const unavailable = requireDatabase(env, origin);
  if (unavailable) return unavailable;
  if (!env.LANDERWARE_INBOX) return json({ error: "LanderWare Inbox is not connected.", code: "storage_unavailable" }, 503, origin);
  const declaredLength = Number(request.headers.get("Content-Length") || 0);
  if (declaredLength > MAX_UPLOAD_BYTES + 1_000_000) return json({ error: "File exceeds the 15 MB limit.", code: "file_too_large" }, 413, origin);
  try {
    const form = await request.formData();
    const file = form.get("file");
    if (!file || typeof file.arrayBuffer !== "function") throw new ValidationError("A file is required.");
    const original = cleanText(file.name, 255, true);
    const extension = original.includes(".") ? original.split(".").pop().toLowerCase() : "";
    if (!ALLOWED_EXTENSIONS.has(extension)) throw new ValidationError("Unsupported file type.");
    if (file.size <= 0 || file.size > MAX_UPLOAD_BYTES) return json({ error: "File exceeds the 15 MB limit or is empty.", code: "file_too_large" }, 413, origin);
    const bytes = await file.arrayBuffer();
    const checksum = hex(await crypto.subtle.digest("SHA-256", bytes));
    const id = `inbox_${crypto.randomUUID().replace(/-/g, "")}`;
    const storageKey = `private/${new Date().toISOString().slice(0, 10)}/${id}.${extension}`;
    const now = new Date().toISOString();
    const who = actor(env);
    const metadata = {
      id, original_filename: original, storage_key: storageKey,
      mime_type: cleanText(file.type || "application/octet-stream", 150),
      file_size: file.size, uploaded_at: now, uploaded_by: who,
      category: cleanText(form.get("category") || "Other", 80),
      class_association: cleanText(form.get("association"), 160),
      processing_status: "stored", notes: cleanText(form.get("notes"), 2000), checksum_sha256: checksum,
    };
    await env.LANDERWARE_INBOX.put(storageKey, bytes, { httpMetadata: { contentType: metadata.mime_type }, customMetadata: { id, checksum_sha256: checksum } });
    try {
      await env.HOT_SYNC_D1.batch([
        env.HOT_SYNC_D1.prepare(`INSERT INTO inbox_files (id,original_filename,storage_key,mime_type,file_size,uploaded_at,uploaded_by,category,class_association,processing_status,notes,checksum_sha256)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`).bind(id, original, storageKey, metadata.mime_type, file.size, now, who, metadata.category, metadata.class_association, metadata.processing_status, metadata.notes, checksum),
        env.HOT_SYNC_D1.prepare("INSERT INTO admin_audit_log (id,logged_at,actor,action,record_type,record_id,payload_json) VALUES (?,?,?,?,?,?,?)")
          .bind(crypto.randomUUID(), now, who, "upload", "inbox", id, JSON.stringify(metadata)),
      ]);
    } catch (error) {
      await env.LANDERWARE_INBOX.delete(storageKey);
      throw error;
    }
    return json({ file: metadata }, 201, origin);
  } catch (error) { return safeError(error, origin); }
}

async function listInbox(env, origin) {
  const unavailable = requireDatabase(env, origin);
  if (unavailable) return unavailable;
  if (!env.LANDERWARE_INBOX) return json({ error: "LanderWare Inbox is not connected.", code: "storage_unavailable" }, 503, origin);
  const result = await env.HOT_SYNC_D1.prepare("SELECT * FROM inbox_files ORDER BY uploaded_at DESC LIMIT 100").all();
  return json({ files: result.results || [] }, 200, origin);
}

async function downloadInbox(id, env, origin) {
  const unavailable = requireDatabase(env, origin);
  if (unavailable) return unavailable;
  if (!env.LANDERWARE_INBOX) return json({ error: "LanderWare Inbox is not connected.", code: "storage_unavailable" }, 503, origin);
  try {
    const row = await env.HOT_SYNC_D1.prepare("SELECT * FROM inbox_files WHERE id = ?").bind(cleanId(id)).first();
    if (!row) return json({ error: "File not found.", code: "not_found" }, 404, origin);
    const object = await env.LANDERWARE_INBOX.get(row.storage_key);
    if (!object) return json({ error: "Stored file is unavailable.", code: "not_found" }, 404, origin);
    return new Response(object.body, { headers: corsHeaders(origin, {
      "Content-Type": row.mime_type || "application/octet-stream",
      "Content-Disposition": `attachment; filename*=UTF-8''${encodeURIComponent(row.original_filename)}`,
      "Cache-Control": "private, no-store",
    }) });
  } catch (error) { return safeError(error, origin); }
}

async function updateInbox(id, request, env, origin) {
  const unavailable = requireDatabase(env, origin);
  if (unavailable) return unavailable;
  try {
    id = cleanId(id);
    const input = await requestJson(request);
    const category = cleanText(input.category || "Other", 80);
    const notes = cleanText(input.notes, 2000);
    const association = cleanText(input.class_association, 160);
    const result = await env.HOT_SYNC_D1.prepare("UPDATE inbox_files SET category=?,notes=?,class_association=? WHERE id=?").bind(category, notes, association, id).run();
    if (!result.meta || result.meta.changes === 0) return json({ error: "File not found.", code: "not_found" }, 404, origin);
    return json({ id, category, notes, class_association: association }, 200, origin);
  } catch (error) { return safeError(error, origin); }
}

async function deleteInbox(id, env, origin) {
  const unavailable = requireDatabase(env, origin);
  if (unavailable) return unavailable;
  if (!env.LANDERWARE_INBOX) return json({ error: "LanderWare Inbox is not connected.", code: "storage_unavailable" }, 503, origin);
  try {
    id = cleanId(id);
    const row = await env.HOT_SYNC_D1.prepare("SELECT * FROM inbox_files WHERE id = ?").bind(id).first();
    if (!row) return json({ error: "File not found.", code: "not_found" }, 404, origin);
    await env.LANDERWARE_INBOX.delete(row.storage_key);
    const now = new Date().toISOString();
    const who = actor(env);
    await env.HOT_SYNC_D1.batch([
      env.HOT_SYNC_D1.prepare("DELETE FROM inbox_files WHERE id = ?").bind(id),
      env.HOT_SYNC_D1.prepare("INSERT INTO admin_audit_log (id,logged_at,actor,action,record_type,record_id,payload_json) VALUES (?,?,?,?,?,?,?)")
        .bind(crypto.randomUUID(), now, who, "delete", "inbox", id, JSON.stringify({ ...row, storage_key: "[deleted]" })),
    ]);
    return json({ id, deleted: true }, 200, origin);
  } catch (error) { return safeError(error, origin); }
}

function cleanId(value) {
  const id = String(value || "");
  if (!/^[A-Za-z0-9_-]{6,100}$/.test(id)) throw new ValidationError("Record ID is invalid.");
  return id;
}

function hex(buffer) {
  return Array.from(new Uint8Array(buffer), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function corsPreflight(origin) {
  if (!origin || !ALLOWED_ORIGINS.has(origin)) return json({ error: "Origin is not allowed.", code: "origin_rejected" }, 403, origin);
  return new Response(null, { status: 204, headers: corsHeaders(origin) });
}

function corsHeaders(origin, additional = {}) {
  const headers = {
    "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,X-Hot-Sync-Admin-Key",
    "Access-Control-Max-Age": "600",
    "Vary": "Origin",
    ...additional,
  };
  if (ALLOWED_ORIGINS.has(origin)) headers["Access-Control-Allow-Origin"] = origin;
  return headers;
}

function json(payload, status, origin) {
  return new Response(JSON.stringify(payload), { status, headers: corsHeaders(origin, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "private, no-store" }) });
}

function safeError(error, origin) {
  if (error instanceof ValidationError) return json({ error: error.message, code: "validation_error" }, 400, origin);
  console.error(JSON.stringify({ event: "admin_api_error", message: String(error && error.message || "unknown") }));
  return json({ error: "The admin operation failed safely.", code: "operation_failed" }, 500, origin);
}

class ValidationError extends Error {}

export const adminApiInternals = { normalizeClass, blocksAvailability, cleanId, MAX_UPLOAD_BYTES, ALLOWED_EXTENSIONS };
