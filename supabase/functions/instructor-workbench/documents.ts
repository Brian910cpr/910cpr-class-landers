// Keep document lookups scoped to the class, even when callers know a document UUID.
const uuid = (value: string) => /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);

export function validId(value: string) {
  if (!uuid(value)) throw Error('not_found');
  return value;
}

export async function viewDocument(sessionId: string, documentId: string, rest: Function, env: Function) {
  const rows = await rest(`class_session_documents?class_session_id=eq.${validId(sessionId)}&id=eq.${validId(documentId)}&select=id,file_name,content_type,storage_bucket,storage_path&limit=1`);
  const doc = rows?.[0];
  if (!doc) throw Error('document_not_found');
  // Never turn an arbitrary client URL/path into a privileged storage request.
  if (doc.storage_bucket !== 'class-session-docs' || !doc.storage_path?.startsWith(`${sessionId}/`) || doc.storage_path.split('/').includes('..')) throw Error('document_unavailable');
  const key = env('SUPABASE_SERVICE_ROLE_KEY'), base = env('SUPABASE_URL');
  const path = doc.storage_path.split('/').map(encodeURIComponent).join('/');
  const response = await fetch(`${base}/storage/v1/object/sign/class-session-docs/${path}`, {
    method: 'POST',
    headers: { apikey: key, Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ expiresIn: 300 }),
  });
  if (!response.ok) throw Error('document_unavailable');
  const signed = await response.json();
  if (!signed.signedURL) throw Error('document_unavailable');
  const signedUrl = new URL(signed.signedURL, `${base}/storage/v1/`);
  // Storage currently returns /object/sign/... relative to /storage/v1.
  if (signed.signedURL.startsWith('/object/')) signedUrl.pathname = `/storage/v1${signedUrl.pathname}`;
  if (signedUrl.origin !== new URL(base).origin || !signedUrl.pathname.startsWith('/storage/v1/object/sign/class-session-docs/')) throw Error('document_unavailable');
  return { id: doc.id, file_name: doc.file_name, content_type: doc.content_type, url: signedUrl.href, expires_in: 300 };
}

export async function removeDocument(req: Request, sessionId: string, documentId: string, actorSessionHash: string, rest: Function) {
  validId(sessionId); validId(documentId);
  const body = await req.json().catch(() => null);
  if (body?.confirm !== true) throw Error('confirmation_required');
  const result = await rest('rpc/remove_instructor_document', {
    method: 'POST',
    body: JSON.stringify({ p_class_session_id: sessionId, p_document_id: documentId, p_actor_session_hash: actorSessionHash }),
  });
  if (result?.error) throw Error(result.error);
  if (!result?.ok) throw Error('document_removal_failed');
  return result;
}
