import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {readGitHubSource} from './read-github-source.mjs';

const run = promisify(execFile);
const uuid = /^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i;
const review = reason => ({decision:'review', reason, can_execute:false});

// Explicit libpq service configuration supplies the separately authenticated
// collector connection. Never fall back to an administrative/default database.
// This read-only bridge does NOT publish lifecycle metadata as operational proof.
export async function readCanonicalGitHubSource(cardId, service, {execute = run} = {}) {
  if (typeof cardId !== 'string' || !uuid.test(cardId)
      || typeof service !== 'string' || !/^[a-zA-Z0-9_-]{1,64}$/.test(service)) {
    return review('invalid_collector_connection_or_card');
  }
  const read = async () => {
    const sql = `begin read only; set local role production_board_collector; select production_board_private.production_board_read_source_binding('${cardId}'::uuid); commit;`;
    const {stdout} = await execute('psql', ['--dbname', `service=${service}`, '-X', '--no-password',
      '--quiet', '--tuples-only', '--no-align', '--set', 'ON_ERROR_STOP=1', '--command', sql],
    {timeout:5000, maxBuffer:16384, windowsHide:true, encoding:'utf8'});
    return JSON.parse(stdout.trim());
  };
  try {
    const binding = await read();
    if (binding?.can_execute !== false) return review('invalid_canonical_binding_response');
    if (binding.decision === 'skip' && binding.reason === 'card_resolved') {
      return {decision:'skip', reason:'card_resolved', can_execute:false};
    }
    if (binding.decision !== 'review' || binding.reason !== 'underlying_source_check_required'
        || binding.card_id?.toLowerCase() !== cardId.toLowerCase()) {
      return review('canonical_binding_unavailable');
    }
    const observation = await readGitHubSource(binding, {execute});
    if (observation.source_kind !== 'github_issue_lifecycle') return observation;
    const latest = await read();
    if (latest?.decision === 'skip' && latest.reason === 'card_resolved' && latest.can_execute === false) {
      return {decision:'skip', reason:'card_resolved', can_execute:false};
    }
    if (latest?.decision !== binding.decision || latest.reason !== binding.reason
        || latest.can_execute !== false || ['card_id','issue_id','version','source_ref'].some(k => latest[k] !== binding[k])) {
      return review('canonical_binding_changed');
    }
    return observation;
  } catch {
    // Neither libpq diagnostics nor private database/source payloads escape.
    return review('canonical_source_acquisition_failed');
  }
}
