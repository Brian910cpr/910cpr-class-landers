// Executes the actual shared form module in a minimal DOM, with no network/browser.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {conditionApplies,checkoutSelection,escapeCheckoutText} from '../supabase/functions/_shared/checkout-profile.mjs';
const source=readFileSync(new URL('../docs/assets/generic-checkout.js',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'').replace('init();','globalThis.initialized=init();');
const key='11111111-1111-4111-8111-111111111111';
async function harness({online=false,uploads=false,file=null,failUpload=false,saved=false,paid=false,processing=false,refunded=false,legacy=null}={}){
 const calls=[],nodes=new Map(),store=new Map(),cards=[];let redirected,receipt;
 const profile={profileKey:'generic',profileVersion:1,title:'Fixture course',description:'Fixture description',fields:[],baseCents:5500,maxStudents:2,backUrl:'/classes/',driverRules:[{driver:'native_order'}],defaultChoices:[online?'online':'skills'],optionGroups:[{key:'path',label:'Course option',type:'radio',required:true,choices:[{key:'skills',label:'Skills only',available:true,amountCents:0,catalog_keys:[]},{key:'online',label:'Online access + skills',available:true,amountCents:4000,catalog_keys:['code']}]}],uploads:uploads?[{key:'completion',label:'Certificate',mode:'optional',required:false,maxBytes:2097152,mimeTypes:['application/pdf']}]:[]};
 function element(){return {hidden:false,disabled:false,required:false,textContent:'',value:'',files:[],dataset:{},addEventListener(){},append(c){this.children=(this.children||[]).concat(c);},querySelectorAll(){return [];}};}
 for(const id of ['app','status','total','students','add-student','pay','check-status','checkout-form','result'])nodes.set(id,element());
 nodes.get('students').append=card=>cards.push(card);
 function card(){const c=element(),remove=element();c.choices=profile.optionGroups[0].choices.map(x=>({...element(),value:x.key,checked:profile.defaultChoices.includes(x.key)}));c.upload=Object.assign(element(),{dataset:{upload:'completion'},files:file?[file]:[]});
  c.wrapper=Object.assign(element(),{dataset:{uploadWrapper:'completion'},querySelector:()=>c.upload});
  c.querySelector=s=>s==='.remove'?remove:null;
  c.querySelectorAll=s=>s==='[data-choice]:checked'?c.choices.filter(x=>x.checked):s==='[data-choice]'?c.choices:s==='[data-choice],.remove'?[...c.choices,remove]:s==='[data-upload]'?uploads?[c.upload]:[]:s==='[data-upload-wrapper]'?uploads?[c.wrapper]:[]:[];
  c.remove=()=>cards.splice(cards.indexOf(c),1);return c;}
 const query=new URLSearchParams({session:'123456',paid:'1'}),selectionKey='native-checkout:'+JSON.stringify([['session','123456']]);
 if(saved){store.set(selectionKey,key);receipt={status:paid?'paid':refunded?'refunded':processing?'processing':'held',orderId:'order',amountCents:online?9500:5500,students:[{selectedChoices:[online?'online':'skills'],uploads:{}}]};}
 const model=()=>legacy?{ok:true,nativeReady:false,sessionId:'123456',fallbackRegistrationUrl:legacy}:({ok:true,profile,selection:{session:'123456'},session:{startsAt:'2031-01-01T14:00:00Z',location:'Fixture location'},...(receipt?{receipt}:{} )});
 const context=vm.createContext({AbortSignal,URL,URLSearchParams,Intl,Date,Uint8Array,TextEncoder,Error,Object,JSON,Number,String,console,conditionApplies,checkoutSelection,esc:escapeCheckoutText,btoa,
  location:{search:'?'+query,origin:'https://fixture.invalid',assign:url=>redirected=url},window:{},parent:{postMessage(){}},crypto:{randomUUID:()=>key},
  sessionStorage:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)},ResizeObserver:class{observe(){}},
  document:{getElementById:id=>nodes.get(id),querySelectorAll:s=>s==='.student'?cards:[],documentElement:{scrollHeight:900,classList:{add(){}}},createElement:tag=>tag==='fieldset'?card():element()},
  fetch:async(url,init)=>{const action=new URL(url).pathname.split('/').at(-1);calls.push(action);const body=init.body?JSON.parse(init.body):null;
   if(action==='form')return Response.json(model());
   if(action==='reserve'){assert.equal(body.profileKey,profile.profileKey);assert.equal(body.profileVersion,profile.profileVersion);assert.equal(store.get(selectionKey),key);receipt={status:'held',orderId:'order',amountCents:online?9500:5500,students:body.students.map(s=>({selectedChoices:s.selectedChoices,uploads:{}}))};return Response.json({ok:true,receipt});}
   if(action==='status')return Response.json({ok:true,receipt});
   if(action==='upload'&&failUpload)return Response.json({error:'document_storage_pending'},{status:503});
   if(action==='upload')return Response.json({ok:true,evidenceStatus:'received',approved:false});
   if(action==='checkout')return Response.json({ok:true,checkoutUrl:'https://checkout.stripe.com/c/pay/fixture'});
   throw Error('unexpected_action');}});
 vm.runInContext(source,context);await context.initialized;
 return {calls,nodes,store,cards,submit:()=>context.submit({preventDefault(){}}),clearFile:()=>{file=null;for(const c of cards)c.upload.files=[];},redirected:()=>redirected};
}

test('shared form selects $55 skills or $95 online-inclusive options and proceeds with no certificate',async()=>{
 for(const online of [false,true]){const h=await harness({online,uploads:true});assert.match(h.nodes.get('total').textContent,online?/95/:/55/);await h.submit();assert.deepEqual(h.calls,['form','reserve','status','checkout']);assert.match(h.redirected(),/^https:\/\/checkout.stripe.com\//);}
});
test('optional upload failure allows removing the file and retrying the saved hold without a duplicate reservation',async()=>{
 const file={type:'application/pdf',size:10,arrayBuffer:async()=>new TextEncoder().encode('%PDF-test').buffer};
 const h=await harness({uploads:true,file,failUpload:true});await h.submit();assert.equal(h.redirected(),undefined);assert.match(h.nodes.get('status').textContent,/not received/);assert.equal(h.nodes.get('pay').disabled,false);
 h.clearFile();await h.submit();assert.equal(h.calls.filter(x=>x==='reserve').length,1);assert.match(h.redirected(),/^https:\/\/checkout.stripe.com\//);
});
test('paid query alone does not confirm; a saved return uses server status and never reserves again',async()=>{
 const pending=await harness({saved:true});assert.equal(pending.nodes.get('checkout-form').hidden,false);await pending.submit();assert.equal(pending.calls.includes('reserve'),false);assert.match(pending.redirected(),/^https:\/\/checkout.stripe.com\//);
 const paid=await harness({saved:true,paid:true});assert.equal(paid.nodes.get('checkout-form').hidden,true);assert.match(paid.nodes.get('result').textContent,/Payment received/);assert.equal(paid.calls.includes('checkout'),false);
});
test('disabled upload configuration renders no upload control and all legacy skills URLs use the same form',async()=>{
 const h=await harness();assert.equal(h.cards[0].querySelectorAll('[data-upload]').length,0);
 const alias=readFileSync(new URL('../docs/register/skills-session/index.html',import.meta.url),'utf8');assert.match(alias,/location.replace\(destination\)/);assert.equal(alias.includes('<form'),false);
 const mirror=readFileSync(new URL('../docs/assets/checkout-profile.js',import.meta.url),'utf8'),server=readFileSync(new URL('../supabase/functions/_shared/checkout-profile.mjs',import.meta.url),'utf8');assert.equal(mirror,server);
});
test('saved observed payment hides the payment action and offers status recovery without confirming registration or charging again',async()=>{
 const h=await harness({saved:true,processing:true});assert.equal(h.nodes.get('pay').hidden,true);assert.match(h.nodes.get('status').textContent,/Payment received; registration confirmation is pending/);assert.doesNotMatch(h.nodes.get('result').textContent,/registration is confirmed/);
 await h.submit();assert.equal(h.calls.includes('reserve'),false);assert.equal(h.calls.includes('checkout'),false);assert.equal(h.redirected(),undefined);
});
test('saved refunded order shows its terminal state and cannot offer another payment or a confirmed registration',async()=>{
 const h=await harness({saved:true,refunded:true});assert.equal(h.nodes.get('pay').hidden,true);assert.match(h.nodes.get('status').textContent,/order was refunded/);assert.equal(h.nodes.get('result').textContent,'');
 await h.submit();assert.equal(h.calls.includes('checkout'),false);assert.equal(h.calls.includes('reserve'),false);
});
test('unconverted concrete classes expose the verified original route rather than a dead-end native form',async()=>{
 const url='https://coastalcprtraining.enrollware.com/enroll?id=123456',h=await harness({legacy:url});
 assert.deepEqual(h.calls,['form']);assert.equal(h.cards.length,0);assert.equal(h.nodes.get('app').children[0].href,url);assert.equal(h.nodes.get('app').children[0].target,'_top');
 const rejected=await harness({legacy:'https://unapproved.invalid/enroll?id=123456'});assert.equal(rejected.nodes.get('app').children[0].href,'/classes/');
});
