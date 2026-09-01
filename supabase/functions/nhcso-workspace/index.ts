import { createClient } from "https://esm.sh/@supabase/supabase-js@2.56.0";

const cors = {
  "Access-Control-Allow-Origin": "https://www.910cpr.com",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const admin = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
  { auth: { persistSession: false } },
);
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { ...cors, "Content-Type": "application/json", "Cache-Control": "no-store" },
});
const clean = (value: unknown) => String(value ?? "").trim();

async function studentKey(name: string, email: string) {
  const bytes = new TextEncoder().encode((email || name).trim().toLowerCase());
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest)).map((byte) => byte.toString(16).padStart(2, "0")).join("").slice(0, 24);
}

async function dispatchNotifications(classSessionId: string) {
  const workerUrl = Deno.env.get("TRANSACTIONAL_EMAIL_WORKER_URL") || "";
  const workerSecret = Deno.env.get("TRANSACTIONAL_EMAIL_WORKER_SECRET") || "";
  const { data: pending, error } = await admin.from("transactional_email_outbox").select("*")
    .eq("class_session_id", classSessionId).in("status", ["pending", "failed"]).order("created_at");
  if (error) throw error;
  const results = [];
  for (const item of pending || []) {
    if (!workerUrl || !workerSecret) {
      const message = "Transactional email delivery is not configured";
      await admin.from("transactional_email_outbox").update({
        status: "failed", attempt_count: item.attempt_count + 1, last_error: message, updated_at: new Date().toISOString(),
      }).eq("id", item.id);
      console.error("notification delivery", { id: item.id, error: message });
      results.push({ id: item.id, ok: false, error: message });
      continue;
    }
    try {
      await admin.from("transactional_email_outbox").update({ status: "sending", updated_at: new Date().toISOString() }).eq("id", item.id);
      const mailResponse = await fetch(workerUrl, {
        method: "POST",
        headers: { authorization: `Bearer ${workerSecret}`, "content-type": "application/json" },
        body: JSON.stringify({
          to: item.recipient_email,
          notificationType: item.notification_type,
          subject: item.notification_type === "submitter_confirmation" ? "910CPR received your NHCSO class" : "NHCSO class ready for card review",
          ...item.payload,
        }),
      });
      const mailResult = await mailResponse.json().catch(() => ({}));
      if (!mailResponse.ok) throw new Error(mailResult.error || `Email worker returned ${mailResponse.status}`);
      await admin.from("transactional_email_outbox").update({ status: "sent", attempt_count: item.attempt_count + 1, last_error: null, message_id: mailResult.messageId || null, sent_at: new Date().toISOString(), updated_at: new Date().toISOString() }).eq("id", item.id);
      results.push({ id: item.id, ok: true, message_id: mailResult.messageId || null });
    } catch (dispatchError) {
      const message = dispatchError instanceof Error ? dispatchError.message : String(dispatchError);
      await admin.from("transactional_email_outbox").update({ status: "failed", attempt_count: item.attempt_count + 1, last_error: message, updated_at: new Date().toISOString() }).eq("id", item.id);
      console.error("notification delivery", { id: item.id, error: message });
      results.push({ id: item.id, ok: false, error: message });
    }
  }
  return results;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "POST required" }, 405);
  try {
    const contentType = req.headers.get("content-type") || "";
    if (contentType.includes("multipart/form-data")) {
      const form = await req.formData();
      if (clean(form.get("action")) !== "upload_document") return json({ error: "Unsupported multipart action" }, 400);
      const classNumber = clean(form.get("class_number"));
      const documentType = clean(form.get("document_type")) || "course_completion";
      const file = form.get("file");
      if (!classNumber || !(file instanceof File) || !file.size) return json({ error: "class_number and file are required" }, 400);
      if (file.size > 15 * 1024 * 1024) return json({ error: "File exceeds 15 MB limit" }, 400);
      const { data: exists } = await admin.from("nhcso_classes").select("class_number").eq("class_number", classNumber).maybeSingle();
      if (!exists) return json({ error: "Save the class before uploading paperwork" }, 400);
      const safe = file.name.replace(/[^a-zA-Z0-9._-]+/g, "_");
      const path = `${classNumber}/${documentType}/${Date.now()}-${safe}`;
      const { error: uploadError } = await admin.storage.from("nhcso-class-docs").upload(path, file, {
        contentType: file.type || "application/octet-stream",
        upsert: false,
      });
      if (uploadError) throw uploadError;
      const { data, error } = await admin.from("nhcso_documents").insert({
        class_number: classNumber,
        document_type: documentType,
        file_name: file.name,
        storage_path: path,
        content_type: file.type || null,
        file_size: file.size,
      }).select().single();
      if (error) throw error;
      return json({ ok: true, document: data });
    }

    const body = await req.json();
    const action = clean(body.action);
    if (action === "save_class") {
      const c = body.class || {};
      const course = clean(c.course);
      const classDate = clean(c.class_date || c.date);
      const startTime = clean(c.start_time || c.time);
      const client = clean(body.client || c.client) || "NHCSO";
      if (!course || !classDate || !startTime) return json({ error: "course, class_date, and start_time are required" }, 400);
      let classNumber = clean(c.class_number);
      if (!classNumber) classNumber = `NHSO-${classDate.replaceAll("-", "")}-${startTime.replace(":", "")}-${crypto.randomUUID().slice(0, 6).toUpperCase()}`;
      const classRow = {
        class_number: classNumber,
        course,
        class_date: classDate,
        start_time: startTime,
        location: clean(c.location) || null,
        lead_instructor: clean(c.lead_instructor || c.lead) || null,
        assistant_instructors: clean(c.assistant_instructors || c.assistants) || null,
        notes: clean(c.notes) || null,
        status: clean(c.status) || "scheduled",
        updated_at: new Date().toISOString(),
      };
      const { error: classError } = await admin.from("nhcso_classes").upsert(classRow, { onConflict: "class_number" });
      if (classError) throw classError;
      const rows = [];
      for (const raw of Array.isArray(body.students) ? body.students : []) {
        const name = clean(raw.name);
        const email = clean(raw.email).toLowerCase();
        if (!name && !email) continue;
        rows.push({
          class_number: classNumber,
          student_key: clean(raw.student_key) || await studentKey(name, email),
          client: clean(raw.client) || client,
          name: name || email,
          email: email || null,
          status: clean(raw.status) || "Active",
          ecard_number: clean(raw.ecard_number || raw.card) || null,
          updated_at: new Date().toISOString(),
        });
      }
      if (rows.length) {
        const { error } = await admin.from("nhcso_students").upsert(rows, { onConflict: "class_number,student_key" });
        if (error) throw error;
      }
      const { data: savedStudents, error } = await admin.from("nhcso_students").select("*").eq("class_number", classNumber).order("created_at");
      if (error) throw error;
      return json({ ok: true, class_number: classNumber, student_records: savedStudents || [] });
    }
    if (action === "get_class") {
      const classNumber = clean(body.class_number);
      const [{ data: classRow, error: classError }, { data: students, error: studentError }, { data: documents, error: docError }] = await Promise.all([
        admin.from("nhcso_classes").select("*").eq("class_number", classNumber).single(),
        admin.from("nhcso_students").select("*").eq("class_number", classNumber).order("created_at"),
        admin.from("nhcso_documents").select("id,class_number,document_type,file_name,content_type,file_size,created_at").eq("class_number", classNumber).order("created_at", { ascending: false }),
      ]);
      if (classError) throw classError;
      if (studentError) throw studentError;
      if (docError) throw docError;
      let durable = null;
      if (classRow.class_session_id) {
        const [{ data: session }, { data: instructors }, { data: requirements }, { data: cardProcessing }] = await Promise.all([
          admin.from("class_sessions").select("id,status,external_class_id,start_at,end_at,registration_status,public_notes").eq("id", classRow.class_session_id).single(),
          admin.from("class_session_instructors").select("role,source,instructor:people(id,person_key,display_name,email)").eq("class_session_id", classRow.class_session_id),
          admin.from("class_session_requirements").select("requirement_key,status,evidence_document_id,verified_at,notes").eq("class_session_id", classRow.class_session_id).order("requirement_key"),
          admin.from("session_card_processing").select("status,cards_required,cards_issued,missing_requirements,reviewed_at").eq("class_session_id", classRow.class_session_id).maybeSingle(),
        ]);
        durable = { session, instructors: instructors || [], requirements: requirements || [], card_processing: cardProcessing };
      }
      return json({ ok: true, class: classRow, students: students || [], documents: documents || [], durable });
    }
    if (action === "list_instructors") {
      const { data, error } = await admin.from("instructor_qualifications")
        .select("status,instructor:people(id,person_key,display_name,email,active)")
        .eq("qualification_key", "NHCSO_CADRE").eq("status", "active");
      if (error) throw error;
      const instructors = (data || []).map((row: any) => row.instructor as any).filter((person: any) => person?.active)
        .sort((a: any, b: any) => a.display_name.localeCompare(b.display_name));
      return json({ ok: true, instructors });
    }
    if (action === "dispatch_notifications") {
      const classSessionId = clean(body.class_session_id);
      if (!classSessionId) return json({ error: "class_session_id is required" }, 400);
      const results = await dispatchNotifications(classSessionId);
      return json({ ok: true, committed_class_preserved: true, results });
    }
    if (action === "get_document_link") {
      const documentId = clean(body.document_id);
      const classNumber = clean(body.class_number);
      const { data: document, error } = await admin.from("nhcso_documents").select("id,class_number,file_name,storage_path").eq("id", documentId).eq("class_number", classNumber).single();
      if (error || !document) return json({ error: "Document not found" }, 404);
      const { data: signed, error: signedError } = await admin.storage.from("nhcso-class-docs").createSignedUrl(document.storage_path, 300, { download: document.file_name });
      if (signedError) throw signedError;
      return json({ ok: true, document_id: document.id, file_name: document.file_name, signed_url: signed.signedUrl, expires_in: 300 });
    }
    if (action === "list_classes") {
      const { data, error } = await admin.from("nhcso_classes").select("class_number,course,class_date,start_time,location,lead_instructor,status,updated_at").order("class_date", { ascending: false }).order("start_time", { ascending: false }).limit(250);
      if (error) throw error;
      return json({ ok: true, classes: data || [] });
    }
    if (action === "delete_class") {
      const classNumber = clean(body.class_number);
      const { count, error: countError } = await admin.from("nhcso_students").select("*", { count: "exact", head: true }).eq("class_number", classNumber).eq("status", "Active");
      if (countError) throw countError;
      if ((count || 0) > 0) return json({ error: "Clear all active participants before deleting the class" }, 409);
      const { error } = await admin.from("nhcso_classes").delete().eq("class_number", classNumber);
      if (error) throw error;
      return json({ ok: true });
    }
    return json({ error: "Unsupported action" }, 400);
  } catch (error) {
    console.error(error);
    return json({ error: error instanceof Error ? error.message : String(error) }, 500);
  }
});
