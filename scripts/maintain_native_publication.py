"""Explicit owner-auth native maintenance. Never runs during preview or GET."""
import json
import os
from pathlib import Path
import urllib.request
from scripts.fetch_canonical_scheduling_demand import DEFAULT_URL, validate_admin_key
from scripts.run_native_publication import policy_enabled
ROOT = Path(__file__).resolve().parents[1]
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise ValueError('Native maintenance redirect refused')

def run():
    if os.environ.get('GITHUB_REF') != 'refs/heads/main' or not policy_enabled(json.loads((ROOT/'data/config/native_publication_scope.json').read_text())):
        raise ValueError('Enabled main publication required')
    req = urllib.request.Request(DEFAULT_URL, method='POST',
        data=b'{"action":"release_expired_native_holds"}',
        headers={'content-type':'application/json','x-hot-sync-admin-key':validate_admin_key(os.environ.get('HOT_SYNC_ADMIN_KEY',''))})
    with urllib.request.build_opener(NoRedirect).open(req,timeout=30) as response:
        body=json.load(response)
    if body.get('schemaVersion') != 'native-publication-maintenance.v1' or any(type(body.get(k)) is not int or not 0 <= body[k] <= 32 for k in ['released','examined']):
        raise ValueError('Invalid native maintenance result')
    body={k:body[k] for k in ['schemaVersion','released','examined','batchLimit','observedAt']}
    # Count-only operational proof; no student, order or session details.
    target=ROOT/'debug/status/native_publication_maintenance.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(body)+'\n')
    return body

if __name__=='__main__':run()
