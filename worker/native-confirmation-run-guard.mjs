export const RUNS_URL = 'https://api.github.com/repos/Brian910cpr/910cpr-class-landers/actions/workflows/native-confirmation-retry.yml/runs?branch=main&per_page=20';
const STATUSES = new Set(['completed', 'in_progress', 'queued', 'requested', 'waiting', 'pending']);
const CONCLUSIONS = new Set([null, 'success', 'failure', 'neutral', 'cancelled', 'skipped', 'timed_out', 'action_required', 'stale', 'startup_failure']);
const positiveId = value => Number.isSafeInteger(value) && value > 0;
function validRuns(runs) {
  const seen = new Set();
  for (const run of runs) {
    if (!run || typeof run !== 'object' || Array.isArray(run) || !positiveId(run.id) || seen.has(run.id) ||
        typeof run.head_branch !== 'string' || !run.head_branch || /[\x00-\x20\x7f]/.test(run.head_branch) ||
        !STATUSES.has(run.status) || !CONCLUSIONS.has(run.conclusion)) return false;
    seen.add(run.id);
  }
  return true;
}

// Persist uncertainty across ephemeral runners by refusing to run after an
// unresolved prior job. This reads existing Actions evidence; it never dispatches
// a job, changes a setting, or stores a new credential.
export async function priorRetryRunGuard({currentRunId, currentAttempt = 1, runs, totalCount, reviewedPreviousFailure = false, manual = false} = {}) {
  if (!positiveId(currentRunId) || !Array.isArray(runs) || !Number.isSafeInteger(totalCount) || totalCount < 0 ||
      totalCount < runs.length || !validRuns(runs)) return {allowed: false, reason: 'run_history_invalid'};
  if (currentAttempt !== 1) return {allowed: false, reason: 'rerun_requires_new_reviewed_dispatch'};
  // Validate every row before excluding legitimate other-branch, current or
  // future runs. Malformed rows may hide an earlier unknown retry, not prove
  // that this is a first run. Duplicate IDs are equally ambiguous.
  const previous = runs.filter(r => r.id < currentRunId && r.head_branch === 'main').sort((a, b) => b.id - a.id)[0];
  if (!previous && totalCount > runs.length) return {allowed: false, reason: 'run_history_incomplete'};
  if (!previous) return {allowed: true, reason: 'first_run'};
  if (previous.status !== 'completed') return {allowed: false, reason: 'previous_run_unresolved', previousRunId: previous.id};
  if (previous.conclusion === 'success') return {allowed: true, reason: 'previous_run_succeeded', previousRunId: previous.id};
  if (manual === true && reviewedPreviousFailure === true) return {allowed: true, reason: 'previous_failure_reviewed', previousRunId: previous.id};
  return {allowed: false, reason: 'previous_failure_requires_review', previousRunId: previous.id};
}

export async function fetchPriorRetryGuard({token, currentRunId, currentAttempt = 1, request, reviewedPreviousFailure = false, manual = false} = {}) {
  if (!positiveId(currentRunId)) return {allowed: false, reason: 'run_history_invalid'};
  if (currentAttempt !== 1) return {allowed: false, reason: 'rerun_requires_new_reviewed_dispatch'};
  if (typeof token !== 'string' || !token || /[\x00-\x20\x7f]/.test(token) || typeof request !== 'function') return {allowed: false, reason: 'run_history_unconfigured'};
  try {
    const response = await request(RUNS_URL, {method: 'GET', redirect: 'error', signal: AbortSignal.timeout(20_000),
      headers: {authorization: `Bearer ${token}`, accept: 'application/vnd.github+json', 'x-github-api-version': '2022-11-28', 'user-agent': 'native-confirmation-run-guard'}});
    if (response.status !== 200) return {allowed: false, reason: 'run_history_unavailable'};
    const length = Number(response.headers.get('content-length'));
    if (Number.isFinite(length) && length > 1024 * 1024) return {allowed: false, reason: 'run_history_invalid'};
    const reader = response.body.getReader(), decoder = new TextDecoder('utf-8', {fatal: true});
    let bytes = 0, text = '';
    try { for (;;) {const part = await reader.read(); if (part.done) break; bytes += part.value.byteLength; if (bytes > 1024 * 1024) throw Error('too_large'); text += decoder.decode(part.value, {stream: true});} text += decoder.decode(); }
    finally { try { await reader.cancel(); } catch {} }
    const data = JSON.parse(text);
    if (!data || typeof data !== 'object' || Array.isArray(data)) return {allowed: false, reason: 'run_history_invalid'};
    return priorRetryRunGuard({currentRunId, currentAttempt, runs: data.workflow_runs, totalCount: data.total_count, reviewedPreviousFailure, manual});
  } catch { return {allowed: false, reason: 'run_history_unavailable'}; }
}
