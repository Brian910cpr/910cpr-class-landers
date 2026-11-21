import {execFile} from 'node:child_process';
import {promisify} from 'node:util';

const run = promisify(execFile);
const repo = 'Brian910cpr/910cpr-class-landers';

// Read-only source acquisition for an EXISTING authenticated canonical intake.
// The caller must read that intake itself; this module cannot authenticate a JS
// object or bootstrap the card/issue mapping. Never interpret prose as opt-in.
export async function readGitHubSource(binding, {execute = run} = {}) {
  const review = reason => ({decision:'review', reason, can_execute:false});
  let cardId, issueId, version, sourceRef;
  try {
    ({card_id:cardId, issue_id:issueId, version, source_ref:sourceRef} = binding ?? {});
    if (typeof cardId !== 'string' || !/^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(cardId)
        || !Number.isSafeInteger(issueId) || issueId < 1
        || typeof version !== 'string' || !/^[1-9][0-9]*$/.test(version)
        || BigInt(version) > 9223372036854775807n
        || sourceRef !== `https://github.com/${repo}/issues/${issueId}`) {
      return review('unsupported_canonical_source_binding');
    }
    const {stdout} = await execute('gh', ['api', '--hostname', 'github.com',
      '--method', 'GET', `repos/${repo}/issues/${issueId}`,
      '-H', 'Accept: application/vnd.github+json', '-H', 'X-GitHub-Api-Version: 2022-11-28'],
    {timeout:5000, maxBuffer:262144, windowsHide:true, encoding:'utf8'});
    const issue = JSON.parse(stdout);
    if (issue.number !== issueId || issue.html_url !== sourceRef
        || issue.url !== `https://api.github.com/repos/${repo}/issues/${issueId}`
        || Object.hasOwn(issue, 'pull_request')
        || !Number.isSafeInteger(issue.id) || issue.id < 1
        || typeof issue.node_id !== 'string' || !issue.node_id
        || !['open','closed'].includes(issue.state)
        || typeof issue.updated_at !== 'string'
        || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(issue.updated_at)
        || !Number.isFinite(Date.parse(issue.updated_at))) {
      return review('github_source_identity_or_state_invalid');
    }
    // Input mutation during network acquisition invalidates this observation.
    if (binding.card_id !== cardId || binding.issue_id !== issueId
        || binding.version !== version || binding.source_ref !== sourceRef) {
      return review('canonical_binding_changed');
    }
    return {decision:'review', reason:issue.state === 'closed'
      ? 'github_issue_closed_requires_reconciliation' : 'underlying_source_check_required',
    can_execute:false, card_id:cardId, issue_id:issueId, expected_version:version,
    source_kind:'github_issue_lifecycle', source_ref:sourceRef,
    source_id:issue.id, source_node_id:issue.node_id, issue_state:issue.state,
    source_updated_at:issue.updated_at, checked_at:new Date().toISOString(),
    source_state:'unknown', worker_safe:false};
  } catch {
    // CLI stderr/response can contain private source content or auth details.
    return review('github_source_read_failed');
  }
}
