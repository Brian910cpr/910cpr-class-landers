// /scripts/cards.js
(function(){
  const BASE='https://coastalcprtraining.enrollware.com';
  function absURL(u){ try{return new URL(u,BASE).toString()}catch(e){return null} }
  function sanitizeHTML(unsafe){
    const w=document.createElement('div'); w.innerHTML=unsafe||'';
    const AL=new Set(['A','P','UL','LI','EM','STRONG','IMG','BR']);
    const SA={'A':['href','title','rel','target'],'IMG':['src','alt','width','height']};
    (function walk(n){
      Array.from(n.children).forEach(el=>{
        if(!AL.has(el.tagName)){ const f=document.createDocumentFragment(); while(el.firstChild) f.appendChild(el.firstChild); el.replaceWith(f); walk(n); return; }
        Array.from(el.attributes).forEach(a=>{ const keep=(SA[el.tagName]||[]).includes(a.name.toLowerCase()); if(!keep) el.removeAttribute(a.name); });
        if(el.tagName==='A'){
          try{ const u=new URL(el.getAttribute('href')||'',BASE); el.setAttribute('href',u.toString()); el.setAttribute('rel','nofollow noopener'); el.setAttribute('target','_blank'); }
          catch(e){ el.remove(); }
        }
        if(el.tagName==='IMG'){ el.setAttribute('src', absURL(el.getAttribute('src')||'') || ''); }
        walk(el);
      });
    })(w);
    return w.innerHTML;
  }
  function parse(html){
    const t=document.createElement('div'); t.innerHTML=html;
    const out=[];
    t.querySelectorAll('a[href]').forEach(a=>{
      const href=a.getAttribute('href')||''; const abs=absURL(href);
      if(!abs || !(/(\/enroll\?id=\d+)|(\/reg\/\d+)/i.test(abs))) return;
      const label=(a.textContent||'').trim().replace(/\s+/g,' ');
      const p=a.closest('.enrpanel'); let raw='';
      if(p){
        const v=p.getAttribute('value'); if(v) raw=v;
        if(!raw){
          const b=p.querySelector('.enrpanel-body');
          if(b){
            const list=b.querySelector('.enrclass-list'); const parts=[]; let n=list?list.previousElementSibling:null;
            while(n){ if(/^(P|UL)$/i.test(n.tagName)) parts.unshift(n.outerHTML); n=n.previousElementSibling; }
            raw=parts.join('');
          }
        }
      }
      const clean=sanitizeHTML(raw);
      const tmp=document.createElement('div'); tmp.innerHTML=clean; const img=tmp.querySelector('img');
      out.push({label,url:abs,img:img?img.getAttribute('src'):null,desc:clean});
    });
    const seen=new Set();
    return out.filter(x=>{ if(seen.has(x.url)) return false; seen.add(x.url); return true; });
  }
  function courseMatches(label,c){ return (c.patterns||[]).some(p=>{ try{return new RegExp(p,'i').test(label)}catch(e){return False} }); }
  function build(items,courses,field){
    const map={};
    items.forEach(s=>{ courses.forEach(c=>{ if(!map[c.slug] && (c.patterns||[]).some(p=>{try{return new RegExp(p,'i').test(s.label)}catch(e){return false}}) && s[field]){ map[c.slug]=s[field]; } }); });
    return map;
  }
  async function load(p){ const r=await fetch(p,{cache:'no-store'}).catch(()=>null); if(!r) return null; return p.endsWith('.json')?r.json():r.text(); }
  window.CourseCards = { async renderCards({coursesJsonPath,scheduleHtmlPath,targetSelector,prefix}){
    const [courses,html] = await Promise.all([load(coursesJsonPath), load(scheduleHtmlPath)]);
    const items = parse(html||'');
    const imgMap  = build(items, courses, 'img');
    const descMap = build(items, courses, 'desc');
    const el = document.querySelector(targetSelector);
    el.innerHTML = courses.map(c=>{
      const img = imgMap[c.slug] || c.image || '';
      const desc = (descMap[c.slug]||'').split('</p>')[0] || '';
      const href = `${prefix}${c.slug}.html`;
      return `<div class="card card-course">
        ${img?`<img class="card-img" src="${img}" alt="${c.name}">`:''}
        <h3>${c.name}</h3>
        ${desc?`<div class="card-desc small">${desc}</div>`:''}
        <p><a class="btn" href="${href}">View ${c.name}</a></p>
      </div>`;
    }).join('');
  }};
})();