const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {JSDOM}=require('jsdom');
const source=fs.readFileSync('docs/assets/instructor-workbench.js','utf8');
const html=fs.readFileSync('docs/admin/instructor-workbench.html','utf8');
const sessionId='10000000-0000-4000-8000-000000000001',docId='20000000-0000-4000-8000-000000000001';
const tick=()=>new Promise(resolve=>setImmediate(resolve));
async function setup({deleteError=false,viewError=false}={}){
 const dom=new JSDOM(html,{url:'https://www.910cpr.com/admin/instructor-workbench.html',runScripts:'outside-only'});
 const w=dom.window,el=id=>w.document.getElementById(id);let docs=[{id:docId,file_name:'Roster <img src=x>.pdf',document_type:'roster',created_at:'2026-09-13T17:28:00Z'}],calls=[];
 w.Headers=Headers;w.sessionStorage.setItem('maximPortalSession','fixture');
 w.HTMLDialogElement.prototype.showModal=function(){this.open=true};
 w.HTMLDialogElement.prototype.close=function(){this.open=false;this.dispatchEvent(new w.Event('close'))};
 const session=()=>({id:sessionId,course_name:'AHA BLS Provider (Renewal)',start_at:'2026-08-28T22:00:00Z',instructor_name:'B. Bailey',participant_count:1,credential_count:0,score_count:0,requirements_total:0,requirements_satisfied:0,health:{percent:docs.length?50:25,missing:[],keys:docs.length?[]:['paperwork']}});
 w.fetch=async(url,options)=>{
  calls.push({url,options});
  if(options.method==='DELETE'){
   if(deleteError)return Response.json({error:'document_in_use'},{status:409});
   docs=[];return Response.json({ok:true,removed_id:docId});
  }
  if(url.includes('/documents/'))return viewError?Response.json({error:'document_unavailable'},{status:503}):Response.json({ok:true,document:{content_type:'application/pdf',url:'https://wktwgcnwdvbebcobgyey.supabase.co/storage/v1/object/sign/class-session-docs/example.pdf?token=test'}});
  if(url.endsWith('/sessions?limit=400'))return Response.json({sessions:[session()]});
  return Response.json({session:session(),documents:docs,registrations:[],customers:[]});
 };
 w.eval(source);await tick();el('session-list').querySelector('button.open').click();await tick();
 return {dom,w,el,calls,docs:()=>docs};
}
test('filenames are escaped and View loads a document without leaving the class',async()=>{
 const r=await setup();assert.equal(r.el('detail-body').querySelectorAll('img').length,0);
 r.el('detail-body').querySelector('.document-view').click();await tick();
 assert.equal(r.el('document-dialog').open,true);assert.equal(r.el('session-dialog').open,true);
 assert.equal(r.el('document-title').textContent,'Roster <img src=x>.pdf');assert.equal(r.el('document-preview').querySelector('iframe').title,'Roster <img src=x>.pdf');
 assert.equal(r.el('document-open-tab').rel,'noopener noreferrer');r.el('close-document').click();assert.equal(r.el('document-preview').children.length,0);r.dom.window.close();
});
test('Cancel does not send a deletion and keeps the upload',async()=>{
 const r=await setup();r.el('detail-body').querySelector('.document-remove').click();
 assert.match(r.el('remove-class-name').textContent,/Aug 28, 2026/);assert.match(r.el('remove-class-name').textContent,/B\. Bailey/);
 r.el('cancel-remove').click();await tick();assert.equal(r.docs().length,1);assert.equal(r.calls.filter(c=>c.options.method==='DELETE').length,0);r.dom.window.close();
});
test('confirmed removal updates the class document list, counts and health',async()=>{
 const r=await setup();r.el('instructor').value='B. Bailey';r.el('detail-body').querySelector('.document-remove').click();r.el('confirm-remove').click();await tick();await tick();
 assert.equal(r.docs().length,0);assert.equal(r.el('remove-document-dialog').open,false);assert.equal(r.el('instructor').value,'B. Bailey');assert.match(r.el('detail-body').textContent,/No paperwork attached yet/);assert.match(r.el('detail-body').textContent,/Documents0/);assert.equal(r.el('metric-paperwork').textContent,'1');assert.equal(r.el('document-status').textContent,'Upload removed from this class.');r.dom.window.close();
});
test('a rejected removal keeps the file and explains what needs replacing',async()=>{
 const r=await setup({deleteError:true});r.el('detail-body').querySelector('.document-remove').click();r.el('confirm-remove').click();await tick();
 assert.equal(r.docs().length,1);assert.equal(r.el('remove-document-dialog').open,true);assert.match(r.el('remove-status').textContent,/Replace that evidence/);assert.equal(r.el('confirm-remove').disabled,false);assert.equal(r.el('cancel-remove').disabled,false);r.dom.window.close();
});
test('failed document view leaves the class open with a retry message',async()=>{
 const r=await setup({viewError:true});r.el('detail-body').querySelector('.document-view').click();await tick();assert.match(r.el('document-preview-status').textContent,/could not be opened/);assert.equal(r.el('document-open-tab').hidden,true);assert.equal(r.el('session-dialog').open,true);r.dom.window.close();
});
