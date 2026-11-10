// Recover an older saved receipt before requesting a new offer: its occupied
// seat may make that offer disappear. The server still authenticates the nonce.
export function legacySkillsReceipt(storage,selection){
 if(selection.course!=='509474'||!['cpr-aed','first-aid-cpr-aed','arc-blended','hsi-blended'].includes(selection.skillsContext))return '';
 const matches=new Set();
 try{
  for(let i=0;i<Math.min(storage.length,500);i++){
   const name=storage.key(i);if(!name?.startsWith('skillsReservation:skills:'))continue;
   let identity;try{identity=JSON.parse(decodeURIComponent(name.slice('skillsReservation:skills:'.length)));}catch{continue;}
   if(!Array.isArray(identity)||identity.length!==6||identity[0]!=='509474'||identity[1]!==selection.skillsContext
    ||identity[2]!==selection.date+'T'+selection.startTime||identity[3]!==selection.instructor
    ||identity[4]!==':: Wilmington; Shipyard Blvd - B'||!identity[5]||selection.location!==':: Wilmington; Shipyard Blvd')continue;
   const nonce=storage.getItem(name);if(/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i.test(nonce||''))matches.add(nonce);
  }
 }catch{return '';}
 if(matches.size>1)throw Error('ambiguous_saved_reservation');
 return [...matches][0]||'';
}

