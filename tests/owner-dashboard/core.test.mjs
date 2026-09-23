import {test} from 'node:test';
import assert from 'node:assert/strict';
import {boardPrompts,reportDigest,financeWindow} from '../../supabase/functions/owner-dashboard/core.mjs';

test('only a translated owner action reaches the Brian list',()=>{
  const cards=[
    {id:'broken',lane:'decision',title:'Restore credential parity',updated_at:'2026-09-23T00:00:00Z'},
    {id:'explicit',lane:'decision',title:'Secret check',updated_at:'2026-09-23T00:00:00Z',context_manifest:{owner_action:{root_action_id:'github-secret',action:'Check whether the secret exists',where:'GitHub Actions secrets',look_for:'HOT_SYNC_ADMIN_KEY',reply_with:'YES or NO',do_not_touch:'Do not edit the secret',why:'Publisher diagnosis can resume'}}},
    {id:'duplicate',lane:'decision',context_manifest:{owner_action:{root_action_id:'github-secret',action:'Check whether the secret exists',where:'GitHub Actions secrets',look_for:'HOT_SYNC_ADMIN_KEY',reply_with:'YES or NO',do_not_touch:'Do not edit the secret',why:'Publisher diagnosis can resume'}}}
  ];
  const prompts=boardPrompts(cards);
  assert.equal(prompts.length,1);
  assert.equal(prompts[0].steps.look_for,'HOT_SYNC_ADMIN_KEY');
});

test('old green report remains stale and a missing report remains unavailable',()=>{
  const entries=reportDigest([
    {path:'debug/a.json',label:'Old',max_age_hours:24,document:{generated_at:'2026-09-01T00:00:00Z',status:'completed'}},
    {path:'debug/b.json',label:'Missing',max_age_hours:24,error:true},
    {path:'debug/c.json',label:'Failed',max_age_hours:24,document:{timestamp:'2026-09-23T00:00:00Z',status:'failed'}}
  ],Date.parse('2026-09-23T01:00:00Z'));
  assert.deepEqual(entries.map(x=>x.state),['stale','unavailable','attention']);
  assert.equal(entries[0].url,'https://github.com/Brian910cpr/910cpr-class-landers/blob/main/debug/a.json');
});

test('incomplete cash source never produces a payment instruction',()=>{
  assert.deepEqual(financeWindow(null).prompts,[]);
  assert.equal(financeWindow({observed_at:'2026-09-01T00:00:00Z',expires_at:'2026-09-02T00:00:00Z',obligations_through:'2026-09-30T00:00:00Z'}).state,'unavailable');
});
