import {lookupOwnerSession} from '../_shared/owner-session.ts';
import {createGithubSource} from './core.mjs';
import {createArchiveStatusHandler} from './handler.mjs';

// Deploy with verify_jwt=false: this endpoint verifies the existing opaque owner
// session against live revocation/expiry records, not a Supabase browser JWT.
const readStatus=createGithubSource({token:Deno.env.get('GITHUB_TOKEN'),sourceRef:Deno.env.get('ARCHIVE_STATUS_REF')||'main'});
Deno.serve(createArchiveStatusHandler({lookupSession:lookupOwnerSession,readStatus}));
