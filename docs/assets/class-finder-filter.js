(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.ClassFinderFilter=api})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  function validCalendarDate(value){if(!/^\d{4}-\d{2}-\d{2}$/.test(value||''))return false;const[y,m,d]=value.split('-').map(Number),date=new Date(Date.UTC(y,m-1,d));return date.getUTCFullYear()===y&&date.getUTCMonth()===m-1&&date.getUTCDate()===d}
  function matches(record,state,ignoreKey){return['course','date','location'].every(key=>key===ignoreKey||!state[key]||record[key]===state[key])}
  function create(options={}){
    const win=options.window||(typeof window!=='undefined'?window:null),doc=options.document||(typeof document!=='undefined'?document:null),controls=options.controls||{course:doc.getElementById('class-filter-course'),date:doc.getElementById('class-filter-date'),location:doc.getElementById('class-filter-location')},cards=options.cards||Array.from(doc.querySelectorAll('.js-class-result')),count=options.count||doc.getElementById('class-filter-count'),empty=options.empty||doc.getElementById('class-filter-empty'),reset=options.reset||doc.getElementById('class-filter-reset');
    const state=()=>({course:controls.course.value,date:controls.date.value,location:controls.location.value});
    function syncUrl(mode='replaceState'){const url=new URL(win.location.href),date=controls.date.value;if(date)url.searchParams.set('date',date);else url.searchParams.delete('date');win.history[mode]({},'',url.pathname+url.search+url.hash)}
    function updateOptions(current){Object.keys(controls).forEach(key=>{const select=controls[key];Array.from(select.options).forEach(option=>{if(!option.value){option.disabled=false;option.hidden=false;return}const available=cards.some(card=>card.dataset[key]===option.value&&matches(card.dataset,current,key));option.disabled=!available;option.hidden=!available&&select.value!==option.value});if(select.value&&select.selectedOptions[0]?.disabled)select.value=''})}
    function applyFilters(){let current=state();updateOptions(current);current=state();let visible=0;cards.forEach(card=>{const show=matches(card.dataset,current);card.hidden=!show;card.style.display=show?'':'none';if(show)visible++});count.textContent=`${visible} class${visible===1?'':'es'} found`;empty.hidden=visible!==0;return visible}
    function initializeFromUrl(){const url=new URL(win.location.href),requested=url.searchParams.get('date')||'',supported=validCalendarDate(requested)&&Array.from(controls.date.options).some(option=>option.value===requested);controls.date.value=supported?requested:'';if(requested&&!supported)syncUrl('replaceState');return applyFilters()}
    Object.keys(controls).forEach(key=>controls[key].addEventListener('change',()=>{applyFilters();syncUrl('replaceState')}));reset.addEventListener('click',()=>{Object.keys(controls).forEach(key=>{controls[key].value=''});applyFilters();syncUrl('replaceState')});
    return{applyFilters,initializeFromUrl,currentState:state,syncUrl};
  }
  function init(options){const controller=create(options);controller.initializeFromUrl();return controller}
  return{validCalendarDate,matches,create,init};
});
