// Browser sessions are validated by the existing revocable owner authority.
// Automation keys remain independent; corporate credentials never enter this lane.
const AUTHORITY = "https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/owner-access/session";
const HEADER = "X-LanderWare-Owner-Session";

export async function ownerAuthorization(request, env, send = fetch) {
  // A presented session must stand on its own: never fall back after revocation.
  if (request.headers.has(HEADER)) {
    const token = request.headers.get(HEADER) || "";
    if (!/^lw_s_[0-9a-f]{64}$/.test(token)) return 401;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 5000);
    try {
      const response = await send(AUTHORITY, {
        method: "GET", headers: { [HEADER]: token },
        redirect: "error", cache: "no-store", signal: controller.signal,
      });
      // The authority's /session route returns 200 only after checking session
      // and grant expiry/revocation. Never return its private owner profile.
      const status = response.status === 200 ? 200 :
        [401, 403].includes(response.status) ? 401 : 503;
      await response.body?.cancel();
      return status;
    } catch (_) {
      return 503;
    } finally {
      clearTimeout(timer);
    }
  }
  if (!env.HOT_SYNC_ADMIN_KEY) return 503;
  const supplied = request.headers.get("X-Hot-Sync-Admin-Key") || "";
  if (!supplied) return 401;
  const encoder = new TextEncoder();
  const digest = value => crypto.subtle.digest("SHA-256", encoder.encode(value));
  const left = new Uint8Array(await digest(env.HOT_SYNC_ADMIN_KEY));
  const right = new Uint8Array(await digest(supplied));
  let mismatch = left.length ^ right.length;
  for (let index = 0; index < left.length; index++) mismatch |= left[index] ^ (right[index] || 0);
  return mismatch === 0 ? 200 : 401;
}
