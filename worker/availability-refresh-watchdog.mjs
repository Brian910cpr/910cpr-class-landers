// Refresh the existing publisher before its public BLS publication expires.
// This timer never generates inventory or changes scheduling/roster policy.
export const FEED = 'https://www.910cpr.com/data/block-selector-availability/bls.json';
export const WORKFLOW = 'https://api.github.com/repos/Brian910cpr/910cpr-class-landers/actions/workflows/refresh-admin-availability.yml';
const MINUTE = 60_000;
const STATE_KEY = 'publication-watchdog';

async function jsonResponse(response, maxBytes) {
  if (!response.ok) throw new Error(`http_${response.status}`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let text = '', bytes = 0;
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > maxBytes) throw new Error('response_too_large');
      text += decoder.decode(value, { stream: true });
    }
    return JSON.parse(text + decoder.decode());
  } finally { await reader.cancel(); }
}

export function publicationState(feed, now) {
  const expires = Date.parse(feed.validUntil);
  if (!Number.isFinite(expires) || !Array.isArray(feed.dates)) throw new Error('invalid_publication');
  let offers = 0;
  for (const day of feed.dates) {
    if (!Array.isArray(day.startTimes)) throw new Error('invalid_publication');
    for (const slot of day.startTimes) {
      if (!Array.isArray(slot.courses)) throw new Error('invalid_publication');
      offers += slot.courses.length;
    }
  }
  return {
    validUntil: feed.validUntil, generatedAt: feed.generatedAt,
    dates: feed.dates.length, offers,
    expired: expires <= now,
    refreshDue: expires - now <= 60 * MINUTE,
  };
}

export async function checkAndRefresh(env, { now = Date.now(), request = fetch } = {}) {
  const previous = await env.STATE.get(STATE_KEY, 'json') || {};
  const state = { checkedAt: new Date(now).toISOString(), lastDispatchAt: previous.lastDispatchAt || null };
  const options = { signal: AbortSignal.timeout(20_000), redirect: 'error' };
  try {
    try {
      const response = await request(`${FEED}?watchdog=${now}`, { ...options, cache: 'no-store' });
      state.publication = publicationState(await jsonResponse(response, 8 * 1024 * 1024), now);
    } catch {
      // A broken public feed warrants the same bounded recovery as a stale one.
      state.publicationError = 'public_feed_unavailable_or_invalid';
    }
    if (state.publication && !state.publication.refreshDue) {
      state.action = 'fresh';
    } else if (now - Date.parse(previous.lastDispatchAt) < 10 * MINUTE) {
      state.action = 'dispatch_cooldown';
    } else {
      if (!env.GITHUB_ACTIONS_TOKEN) throw new Error('github_token_missing');
      const headers = {
        Authorization: `Bearer ${env.GITHUB_ACTIONS_TOKEN}`,
        Accept: 'application/vnd.github+json',
        'User-Agent': '910cpr-availability-watchdog',
        'X-GitHub-Api-Version': '2022-11-28',
      };
      const response = await request(`${WORKFLOW}/runs?branch=main&per_page=10`, { ...options, headers });
      const runs = await jsonResponse(response, 1024 * 1024);
      if (!Array.isArray(runs.workflow_runs)) throw new Error('invalid_workflow_runs');
      const active = runs.workflow_runs.find(run => run.status !== 'completed');
      if (active) {
        state.action = 'refresh_running';
        state.runId = active.id;
        if (now - Date.parse(active.created_at) > 30 * MINUTE) state.error = 'refresh_stalled';
      } else {
        const dispatched = await request(`${WORKFLOW}/dispatches`, {
          ...options, method: 'POST', headers: { ...headers, 'Content-Type': 'application/json' },
          body: JSON.stringify({ ref: 'main' }),
        });
        if (dispatched.status !== 204) throw new Error(`dispatch_http_${dispatched.status}`);
        state.action = 'refresh_dispatched';
        state.lastDispatchAt = state.checkedAt;
      }
    }
  } catch (error) {
    // Never log upstream response bodies, credentials or arbitrary exception text.
    const allowed = /^(github_token_missing|invalid_workflow_runs|response_too_large|http_\d+|dispatch_http_\d+)$/;
    state.error = allowed.test(error.message) ? error.message : 'refresh_check_failed';
  }
  await env.STATE.put(STATE_KEY, JSON.stringify(state));
  console.log(JSON.stringify({ event: 'availability_refresh_watchdog', ...state }));
  return state;
}

export function health(state, now = Date.now()) {
  const checked = Date.parse(state?.checkedAt);
  const heartbeatStale = !Number.isFinite(checked) || now - checked > 12 * MINUTE;
  const expired = !state?.publication || Date.parse(state.publication.validUntil) <= now;
  return { ok: !heartbeatStale && !expired && !state?.error, heartbeatStale, publicationExpired: expired, ...state };
}

export default {
  async scheduled(_event, env) { await checkAndRefresh(env); },
  async fetch(request, env) {
    if (request.method !== 'GET' || new URL(request.url).pathname !== '/health') return new Response('Not found', { status: 404 });
    try {
      const result = health(await env.STATE.get(STATE_KEY, 'json'));
      return Response.json(result, { status: result.ok ? 200 : 503, headers: { 'Cache-Control': 'no-store' } });
    } catch { return Response.json({ ok: false, error: 'health_state_unavailable' }, { status: 503 }); }
  },
};
