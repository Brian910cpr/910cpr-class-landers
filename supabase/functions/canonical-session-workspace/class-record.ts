const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const ECARD = /^[A-Za-z0-9-]{8,24}$/;
const TYPES = new Set([
  "text/plain", "text/csv", "application/csv",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/pdf", "image/jpeg", "image/png", "image/webp",
]);

export function validId(value: string) {
  if (!UUID.test(value)) throw Error("not_found");
  return value;
}

const clean = (value: unknown, max = 300) => String(value ?? "").trim().slice(0, max);
const normalized = (value: unknown) => clean(value).toLowerCase().replace(/[^a-z0-9@.]+/g, "");
const safeName = (value: string) => value.replace(/[^a-zA-Z0-9._-]+/g, "_").slice(-140) || "class-intake.txt";

function splitDelimited(text: string) {
  const lines = text.replace(/^\uFEFF/, "").split(/\r?\n/).filter(line => line.trim());
  if (!lines.length) return [];
  const delimiter = lines[0].includes("\t") ? "\t" : ",";
  const parseLine = (line: string) => {
    const values: string[] = []; let value = "", quoted = false;
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"' && quoted && line[i + 1] === '"') { value += '"'; i++; }
      else if (char === '"') quoted = !quoted;
      else if (char === delimiter && !quoted) { values.push(value.trim()); value = ""; }
      else value += char;
    }
    values.push(value.trim()); return values;
  };
  return lines.map(parseLine);
}

const alias = (header: unknown) => {
  const key = normalized(header);
  if (/^(ecard|ecardcode|ecardnumber|credential|credentialnumber|cardnumber)$/.test(key)) return "ecard";
  if (/^(email|emailaddress)$/.test(key)) return "email";
  if (/^(firstname|first)$/.test(key)) return "first_name";
  if (/^(lastname|last|surname)$/.test(key)) return "last_name";
  if (/^(name|participant|student|studentname)$/.test(key)) return "name";
  if (/^(phone|telephone|mobile|phonenumber)$/.test(key)) return "phone";
  return key;
};

function objectsFromRows(rows: unknown[][]) {
  if (!rows.length) return [];
  const headers = rows[0].map(alias);
  const hasHeader = headers.some(value => ["ecard", "email", "first_name", "last_name", "name", "phone"].includes(value));
  if (!hasHeader) return rows.map((row, index) => ({ row: index + 1, raw: row.map(value => clean(value)).filter(Boolean) }));
  return rows.slice(1).map((row, index) => Object.fromEntries([["row", index + 2], ...headers.map((header, column) => [header, clean(row[column])])]))
    .filter(row => Object.values(row).some(Boolean));
}

const xmlText = (value: string) => value.replace(/<[^>]*>/g, "").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, "&");
const columnIndex = (reference: string) => {
  let value = 0;
  for (const char of (reference.match(/^[A-Z]+/i)?.[0] || "A").toUpperCase()) value = value * 26 + char.charCodeAt(0) - 64;
  return value - 1;
};

async function unzipXml(bytes: Uint8Array) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  let end = bytes.length - 22;
  while (end >= 0 && view.getUint32(end, true) !== 0x06054b50) end--;
  if (end < 0) throw Error("invalid_xlsx");
  const count = view.getUint16(end + 10, true), centralOffset = view.getUint32(end + 16, true), files = new Map<string, string>();
  let cursor = centralOffset;
  for (let index = 0; index < count; index++) {
    if (view.getUint32(cursor, true) !== 0x02014b50) throw Error("invalid_xlsx");
    const method = view.getUint16(cursor + 10, true), compressedSize = view.getUint32(cursor + 20, true), nameLength = view.getUint16(cursor + 28, true), extraLength = view.getUint16(cursor + 30, true), commentLength = view.getUint16(cursor + 32, true), localOffset = view.getUint32(cursor + 42, true);
    const name = new TextDecoder().decode(bytes.slice(cursor + 46, cursor + 46 + nameLength));
    if (name === "xl/sharedStrings.xml" || /^xl\/worksheets\/[^/]+\.xml$/.test(name)) {
      const localNameLength = view.getUint16(localOffset + 26, true), localExtraLength = view.getUint16(localOffset + 28, true), start = localOffset + 30 + localNameLength + localExtraLength;
      let content = bytes.slice(start, start + compressedSize);
      if (method === 8) content = new Uint8Array(await new Response(new Blob([content]).stream().pipeThrough(new DecompressionStream("deflate-raw"))).arrayBuffer());
      else if (method !== 0) throw Error("unsupported_xlsx_compression");
      files.set(name, new TextDecoder().decode(content));
    }
    cursor += 46 + nameLength + extraLength + commentLength;
  }
  return files;
}

async function xlsxRows(file: File) {
  const files = await unzipXml(new Uint8Array(await file.arrayBuffer())), sheet = [...files.entries()].find(([name]) => name.startsWith("xl/worksheets/"))?.[1];
  if (!sheet) throw Error("invalid_xlsx");
  const shared = [...(files.get("xl/sharedStrings.xml") || "").matchAll(/<(?:\w+:)?si\b[^>]*>([\s\S]*?)<\/(?:\w+:)?si>/g)].map(match => xmlText(match[1]));
  return [...sheet.matchAll(/<(?:\w+:)?row\b[^>]*>([\s\S]*?)<\/(?:\w+:)?row>/g)].map(rowMatch => {
    const row: string[] = [];
    for (const cell of rowMatch[1].matchAll(/<(?:\w+:)?c\b([^>]*)>([\s\S]*?)<\/(?:\w+:)?c>/g)) {
      const reference = /\br="([^"]+)"/.exec(cell[1])?.[1] || "A", type = /\bt="([^"]+)"/.exec(cell[1])?.[1] || "";
      const raw = /<(?:\w+:)?v>([\s\S]*?)<\/(?:\w+:)?v>/.exec(cell[2])?.[1] ?? /<(?:\w+:)?t[^>]*>([\s\S]*?)<\/(?:\w+:)?t>/.exec(cell[2])?.[1] ?? "";
      row[columnIndex(reference)] = type === "s" ? (shared[Number(raw)] || "") : xmlText(raw);
    }
    return row;
  }).filter(row => row.some(Boolean));
}

function matchRows(rows: any[], participants: any[]) {
  return rows.map(row => {
    const email = normalized(row.email);
    const rowName = normalized(row.name || `${row.first_name || ""}${row.last_name || ""}`);
    const matches = participants.filter(person => (email && normalized(person.email) === email) || (rowName && normalized(person.display_name) === rowName));
    const ecard = clean(row.ecard);
    return {
      ...row,
      ecard: ECARD.test(ecard) ? ecard : ecard || null,
      match_status: matches.length === 1 ? "matched" : matches.length ? "ambiguous" : "unmatched",
      matched_customer_id: matches.length === 1 ? matches[0].customer_id : null,
      matched_registration_id: matches.length === 1 ? matches[0].registration_id : null,
      warning: ecard && !ECARD.test(ecard) ? "Credential number needs review" : null,
    };
  });
}

async function extractedRows(file: File) {
  if (file.type === "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" || /\.xlsx$/i.test(file.name)) {
    return objectsFromRows(await xlsxRows(file));
  }
  if (/^(text\/plain|text\/csv|application\/csv)$/.test(file.type) || /\.(txt|csv|tsv)$/i.test(file.name)) {
    return objectsFromRows(splitDelimited(await file.text()));
  }
  return [];
}

export async function parseIntakeFile(file: File, participants: any[]) {
  return matchRows((await extractedRows(file)).slice(0, 1000), participants);
}

export async function storeIntake(req: Request, sessionId: string, participants: any[], rest: Function, env: Function) {
  validId(sessionId);
  const form = await req.formData();
  let file = form.get("file");
  const pasted = clean(form.get("pasted_text"), 250000);
  if (!(file instanceof File) && pasted) file = new File([pasted], `pasted-data-${new Date().toISOString().replace(/[:.]/g, "-")}.txt`, {type: "text/plain"});
  if (!(file instanceof File)) throw Error("file_required");
  if (!TYPES.has(file.type) && !/\.(txt|csv|tsv|xlsx|pdf|jpe?g|png|webp)$/i.test(file.name)) throw Error("unsupported_file_type");
  if (file.size <= 0 || file.size > 25 * 1024 * 1024) throw Error("file_size_limit");

  const proposals = await parseIntakeFile(file, participants);
  const rows = proposals;
  const id = crypto.randomUUID(), bytes = new Uint8Array(await file.arrayBuffer());
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  const sha256 = [...new Uint8Array(digest)].map(value => value.toString(16).padStart(2, "0")).join("");
  const path = `${sessionId}/${new Date().toISOString().slice(0, 10)}/${id}-${safeName(file.name)}`;
  const base = env("SUPABASE_URL"), key = env("SUPABASE_SERVICE_ROLE_KEY");
  const upload = await fetch(`${base}/storage/v1/object/class-session-docs/${path}`, {method: "POST", headers: {apikey: key, Authorization: `Bearer ${key}`, "Content-Type": file.type || "application/octet-stream", "x-upsert": "false"}, body: bytes});
  if (!upload.ok) throw Error(`storage_${upload.status}`);
  try {
    await rest("class_session_documents", {method: "POST", body: JSON.stringify({id, class_session_id: sessionId, document_type: "unstructured_intake", file_name: file.name, storage_bucket: "class-session-docs", storage_path: path, content_type: file.type || "application/octet-stream", file_size: file.size, sha256, source: "all_classes_junk_drawer"})});
    const eventId = crypto.randomUUID();
    await rest("class_session_audit", {method: "POST", body: JSON.stringify({class_session_id: sessionId, event_key: `class_intake:${eventId}`, event_type: "class_intake_parsed", actor_label: "Authenticated LanderWare owner", occurred_at: new Date().toISOString(), details: {document_id: id, file_name: file.name, parser: rows.length ? "structured-v1" : "manual-review", row_count: rows.length, matched_count: proposals.filter(row => row.match_status === "matched").length, proposals}})});
    return {document_id: id, file_name: file.name, row_count: rows.length, parser_status: rows.length ? "parsed" : "needs_extraction", proposals};
  } catch (error) {
    await fetch(`${base}/storage/v1/object/class-session-docs/${path}`, {method: "DELETE", headers: {apikey: key, Authorization: `Bearer ${key}`}});
    throw error;
  }
}

export async function viewDocument(sessionId: string, documentId: string, rest: Function, env: Function) {
  const rows = await rest(`class_session_documents?class_session_id=eq.${validId(sessionId)}&id=eq.${validId(documentId)}&select=id,file_name,content_type,storage_bucket,storage_path&limit=1`);
  const doc = rows?.[0];
  if (!doc) throw Error("document_not_found");
  if (doc.storage_bucket !== "class-session-docs" || !doc.storage_path?.startsWith(`${sessionId}/`) || doc.storage_path.split("/").includes("..")) throw Error("document_unavailable");
  const base = env("SUPABASE_URL"), key = env("SUPABASE_SERVICE_ROLE_KEY");
  const path = doc.storage_path.split("/").map(encodeURIComponent).join("/");
  const response = await fetch(`${base}/storage/v1/object/sign/class-session-docs/${path}`, {method: "POST", headers: {apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json"}, body: JSON.stringify({expiresIn: 300})});
  if (!response.ok) throw Error("document_unavailable");
  const signed = await response.json();
  const url = new URL(signed.signedURL, `${base}/storage/v1/`);
  if (signed.signedURL?.startsWith("/object/")) url.pathname = `/storage/v1${url.pathname}`;
  if (url.origin !== new URL(base).origin || !url.pathname.startsWith("/storage/v1/object/sign/class-session-docs/")) throw Error("document_unavailable");
  return {id: doc.id, file_name: doc.file_name, content_type: doc.content_type, url: url.href, expires_in: 300};
}
