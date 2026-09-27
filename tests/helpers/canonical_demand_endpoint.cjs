const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {stripTypeScriptTypes} = require('node:module');

function loadEndpoint(fetch) {
  const filename = path.resolve(__dirname, '../../supabase/functions/canonical-scheduling-demand/index.ts');
  const shared = fs.readFileSync(path.resolve(__dirname, '../../supabase/functions/_shared/external-roster-proof.ts'), 'utf8');
  const clock = fs.readFileSync(path.resolve(__dirname, '../../supabase/functions/_shared/scheduling-clock.ts'), 'utf8');
  const source = (clock + '\n' + shared + '\n' + fs.readFileSync(filename, 'utf8').replace(/^(?:import|export \{).*;\r?\n/gm, '')).replace(/export /g, '');
  const context = vm.createContext({
    Date, Intl, URL, URLSearchParams, Request, Response, AbortSignal, console, fetch,
    Deno: {serve() {}, env: {get: name => ({SUPABASE_URL:'https://database.test', SUPABASE_SERVICE_ROLE_KEY:'fixture-only'})[name]}},
  });
  vm.runInContext(stripTypeScriptTypes(source) + '\nthis.api = {localDate, localMidnight, demandRange, projectDemand, loadDemand, handleRequest};', context, {filename});
  return context.api;
}

module.exports = {loadEndpoint};

if (require.main === module) {
  const input = JSON.parse(fs.readFileSync(0, 'utf8'));
  const rows = Array.isArray(input) ? input : input.sessions;
  const health = Array.isArray(input) ? {sessions:[]} : input.health;
  const api = loadEndpoint(async url => new Response(JSON.stringify(String(url).includes('/admin/hot-sync') ? {} : String(url).includes('/rpc/') ? health : rows)));
  api.handleRequest(new Request('https://endpoint.test/?from=2030-09-01&to=2030-10-01', {headers:{'x-hot-sync-admin-key':'fixture-only'}}))
    .then(response => response.text()).then(body => process.stdout.write(body));
}
