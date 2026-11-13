import {escapeCheckoutText as esc} from './checkout-profile.js?v=20261111-native2';

// Compatibility projection for the existing public-order API. Prices and
// availability always come from the selected session's server catalog. New
// native profiles use the shared profile renderer instead of these legacy wires.
const legacyBindings={
 aha_bls_provider_manual_ebook:{manualChoice:'ebook'},
 aha_heartsaver_first_aid_in_person:{firstAidChoice:'in-person'},
 aha_heartsaver_first_aid_online:{firstAidChoice:'online'},
 aha_heartsaver_first_aid_manual_ebook:{firstAidManualChoice:'ebook'}
};
export function catalogChoices(session){
 const seen=new Set();
 return (Array.isArray(session.addons)?session.addons:[]).filter(a=>{
  if(!a||typeof a.key!=='string'||! /^[A-Za-z][A-Za-z0-9_-]{0,99}$/.test(a.key)||seen.has(a.key)||!Number.isSafeInteger(a.unit_amount)||a.unit_amount<=0)return false;
  seen.add(a.key);return true;
 }).map(a=>({key:a.key,label:String(a.display_name||a.key),description:String(a.description||''),amountCents:a.unit_amount,available:a.active!==false}));
}
export function catalogOptionsMarkup(index,session,money){
 const choices=catalogChoices(session);if(!choices.length)return '';
 return `<fieldset class="product-group"><legend>Course options</legend>${choices.map(c=>`<label class="product-choice"><input type="checkbox" data-catalog-choice value="${esc(c.key)}" data-price="${c.amountCents/100}" ${c.available?'':'disabled'}><span><strong>${esc(c.label)} — ${esc(money(c.amountCents/100))}${c.available?'':' (unavailable)'}</strong><small>${esc(c.description)}</small></span></label>`).join('')}</fieldset>`;
}
export function catalogOptionSelections(session,keys){
 const available=new Set(catalogChoices(session).filter(c=>c.available).map(c=>c.key));
 if(!Array.isArray(keys)||new Set(keys).size!==keys.length||keys.some(k=>!available.has(k)))throw Error('invalid_addon');
 const result={addons:keys.map(key=>({key,quantity:1}))},bound=new Set();
 if(['209806','359474','210549'].includes(String(session.courseId)))Object.assign(result,{manualChoice:'own-copy',firstAidChoice:'none',firstAidManualChoice:'own-copy'});
 for(const key of keys)for(const [wire,value] of Object.entries(legacyBindings[key]||{})){
  if(bound.has(wire))throw Error('invalid_course_option');bound.add(wire);result[wire]=value;
 }
 if(result.firstAidManualChoice==='ebook'&&result.firstAidChoice!=='in-person')throw Error('invalid_course_option');
 return result;
}
