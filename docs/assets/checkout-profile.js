// Shared, declarative course-profile model. No course IDs or executable profile
// expressions. The server resolves catalog prices; browser totals are previews.
const MIME=new Set(['application/pdf','image/jpeg','image/png','image/webp']);
const TYPES=new Set(['text','email','tel','date','checkbox','textarea']);
const DRIVERS=new Set(['native_order','public_session','skills_reservation','skills_bundle']);
const KEY=/^[A-Za-z][A-Za-z0-9_-]{0,79}$/;
const fail=()=>{throw Error('invalid_checkout_profile');};
const array=v=>Array.isArray(v)?v:[];
export function conditionApplies(rule,selected){
  return (!rule.when_choice||selected.includes(rule.when_choice))&&(!rule.unless_choice||!selected.includes(rule.unless_choice));
}
export function uploadPolicies(profile){
  if(array(profile.requirements).some(r=>r.required_before_registration===true&&(r.upload_now!==true||r.upload?.enabled===false)))fail();
  return array(profile.requirements).filter(r=>r.upload_now===true&&r.upload?.enabled!==false).map(r=>{
    if(!KEY.test(r.key)||!r.type)fail();
    const types=array(r.upload?.mime_types);const max=Number(r.upload?.max_bytes??2097152);
    if(!types.length||types.some(t=>!MIME.has(t))||!Number.isSafeInteger(max)||max<1||max>10485760)fail();
    return {key:r.key,documentType:r.type,label:String(r.display_name||'Supporting document'),mode:r.required_before_registration===true?'required':'optional',
      required:r.required_before_registration===true,maxBytes:max,mimeTypes:types,
      when_choice:r.when_choice||null,unless_choice:r.unless_choice||null,
      receivedMeansApproved:false};
  });
}
export function normalizeCheckoutProfile(profile,catalog,{context='',publicCourse=''}={}){
  const schema=profile.form_schema;
  if(!profile.active||!KEY.test(profile.profile_key)||!Number.isInteger(profile.version)||profile.version<1||schema?.schemaVersion!=='native-checkout.form.v1')fail();
  if(!Number.isSafeInteger(catalog.unit_amount)||catalog.unit_amount<=0||catalog.currency!=='usd')throw Error('price_catalog_missing');
  if(array(schema.allowed_contexts).length&&!schema.allowed_contexts.includes(context))throw Error('invalid_context');
  const fields=array(schema.fields).map(f=>{
    if(!KEY.test(f.key)||!TYPES.has(f.type)||f.max_length!==undefined&&(!Number.isInteger(f.max_length)||f.max_length<1||f.max_length>2000))fail();
    return {...f,label:String(f.label||f.key),required:f.required===true,max_length:f.max_length??(f.type==='email'?254:100)};
  });
  if(new Set(fields.map(f=>f.key)).size!==fields.length)fail();
  const configuredIds=array(schema.option_groups).flatMap(g=>array(g.choices).map(c=>c.key));
  if(configuredIds.some(id=>!KEY.test(id))||new Set(configuredIds).size!==configuredIds.length)fail();
  const uploads=uploadPolicies(profile);
  if(new Set(uploads.map(p=>p.key)).size!==uploads.length)fail();
  if([...fields,...uploads].some(r=>['when_choice','unless_choice','required_when_choice'].some(k=>r[k]&&!configuredIds.includes(r[k]))))fail();
  const ids=new Set();
  const optionGroups=array(schema.option_groups).map(g=>{
    if(!KEY.test(g.key)||!['radio','checkbox'].includes(g.type))fail();
    const choices=array(g.choices).filter(c=>!array(c.contexts).length||c.contexts.includes(context)).map(c=>{
      if(!KEY.test(c.key)||ids.has(c.key))fail();ids.add(c.key);
      const addons=array(c.catalog_keys).map(key=>array(catalog.addons).find(a=>a.key===key));
      let amount=0,available=c.enabled!==false;
      for(const a of addons){if(!a||!Number.isSafeInteger(a.unit_amount)||a.unit_amount<=0){available=false;continue;}amount+=a.unit_amount;if(a.active===false)available=false;}
      if(!Number.isSafeInteger(amount)||amount>10000000)fail();
      return {...c,label:String(c.label||c.key),catalog_keys:array(c.catalog_keys),amountCents:amount,available};
    });
    return {key:g.key,label:String(g.label||g.key),type:g.type,required:g.required===true,priceMode:g.price_mode||'addition',choices};
  }).filter(g=>g.choices.length);
  const driverRules=array(schema.driver_rules);
  if(!driverRules.length||driverRules.some(r=>!DRIVERS.has(r.driver)||r.when_choice&&!configuredIds.includes(r.when_choice)))fail();
  let defaults=array(schema.default_choices);
  const alias=array(schema.public_aliases).find(a=>a.public_course_id===publicCourse&&(!a.context||a.context===context));
  if(alias)defaults=array(alias.default_choices);
  if(defaults.some(id=>!ids.has(id)))fail();
  const maxStudents=Number(schema.max_students??1);if(!Number.isInteger(maxStudents)||maxStudents<1||maxStudents>10)fail();
  const backUrl=schema.back_urls?.[context]||schema.back_url||'/classes/';
  if(typeof backUrl!=='string'||!backUrl.startsWith('/')||backUrl.startsWith('//')||/[\r\n]/.test(backUrl))fail();
  return {schemaVersion:'native-checkout.form.v1',profileKey:profile.profile_key,profileVersion:profile.version,
    courseKey:profile.course_id,title:alias?.title||profile.display_name,description:String(schema.description||''),
    currency:catalog.currency,baseCents:catalog.unit_amount,fields,optionGroups,uploads,
    defaultChoices:defaults,driverRules,maxStudents,backUrl};
}
export function checkoutSelection(view,fields,selected){
  if(!Array.isArray(selected)||new Set(selected).size!==selected.length)throw Error('invalid_course_option');
  const choices=view.optionGroups.flatMap(g=>g.choices),known=new Map(choices.map(c=>[c.key,c]));
  if(selected.some(id=>!known.get(id)?.available))throw Error('option_unavailable');
  for(const group of view.optionGroups){const n=group.choices.filter(c=>selected.includes(c.key)).length;if(group.required&&n<1||group.type==='radio'&&n>1)throw Error('invalid_course_option');}
  const values={};
  for(const f of view.fields){
    if(!conditionApplies(f,selected))continue;
    const v=f.type==='checkbox'?fields[f.key]===true:String(fields[f.key]??'').trim();
    const required=f.required||f.required_when_choice&&selected.includes(f.required_when_choice);
    if(required&&(v===false||v===''))throw Error('required_registration_field_missing');
    if(typeof v==='string'&&(v.length>f.max_length||v&&f.type==='email'&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)||v&&f.type==='date'&&!/^\d{4}-\d{2}-\d{2}$/.test(v)))throw Error('invalid_registration_field');
    values[f.key]=v;
  }
  let amountCents=view.baseCents;const addons=[],bindings={};
  for(const id of selected){const c=known.get(id);amountCents+=c.amountCents;Object.assign(bindings,c.bindings||{});for(const key of c.catalog_keys)addons.push({key,quantity:1});}
  if(new Set(addons.map(a=>a.key)).size!==addons.length||!Number.isSafeInteger(amountCents)||amountCents>10000000)throw Error('invalid_course_option');
  const driver=view.driverRules.find(r=>!r.when_choice||selected.includes(r.when_choice))?.driver;
  if(!driver)throw Error('invalid_checkout_profile');
  return {fields:values,selectedChoices:[...selected],amountCents,addons,bindings,driver};
}
export function requiredUploadKeys(view,selected){return view.uploads.filter(p=>p.required&&conditionApplies(p,selected)).map(p=>p.key);}
export function escapeCheckoutText(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
