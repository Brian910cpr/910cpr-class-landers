// Every owner endpoint delegates to the deployed HOT_SYNC authority.
// Corporate access codes and corporate sessions never authorize owner APIs.
export async function authorizedOwner(req: Request): Promise<boolean> {
  const origin = req.headers.get('origin');
  if (origin && !['https://www.910cpr.com','https://910cpr.com'].includes(origin)) {
    throw Object.assign(new Error('Origin not allowed'), {status:403});
  }
  const key = req.headers.get('x-hot-sync-admin-key');
  if (!key) return false;
  let response;
  try {
    response = await fetch('https://schedule.910cpr.com/admin/hot-sync', {
      headers:{'x-hot-sync-admin-key':key}, signal:AbortSignal.timeout(10000), redirect:'error'
    });
  } catch { throw Object.assign(new Error('Admin access check is unavailable. Try again shortly.'), {status:503}); }
  if (response.status === 401 || response.status === 403) return false;
  if (!response.ok) throw Object.assign(new Error('Admin access check is unavailable. Try again shortly.'), {status:503});
  return true;
}
