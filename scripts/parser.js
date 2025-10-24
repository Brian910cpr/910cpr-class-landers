/* /scripts/parser.js */
(function(){
  const ENROLLWARE_BASE = 'https://coastalcprtraining.enrollware.com';
  function absURL(u){ try { return new URL(u, ENROLLWARE_BASE).toString(); } catch(e){ return null; } }
  function sanitizeHTML(unsafe){
    const w = document.createElement('div'); w.innerHTML = unsafe || '';
    const ALLOW = new Set(['A','P','UL','LI','EM','STRONG','IMG','BR']);
    const SAFE_ATTR = { 'A':['href','title','rel','target'], 'IMG':['src','alt','width','height'] };
    (function walk(n){
      Array.from(n.children).forEach(el=>{
        if(!ALLOW.has(el.tagName)){
          const f=document.createDocumentFragment(); while(el.firstChild) f.appendChild(el.firstChild);
          el.replaceWith(f); walk(n); return;
        }
        Array.from(el.attributes).forEach(a=>{
          const keep=(SAFE_ATTR[el.tagName]||[]).includes(a.name.toLowerCase());
          if(!keep) el.removeAttribute(a.name);
        });
        if(el.tagName==='A'){
          try{ const u=new URL(el.getAttribute('href')||'', ENROLLWARE_BASE);
               el.setAttribute('href', u.toString());
               el.setAttribute('rel','nofollow noopener'); el.setAttribute('target','_blank'); }
          catch(e){ el.remove(); }
        }
        if(el.tagName==='IMG'){
          const src = el.getAttribute('src')||'';
          el.setAttribute('src', absURL(src)||'');
        }
        walk(el);
      });
    })(w);
    return w.innerHTML;
  }
  function findPanelMeta(a){
    const p = a.closest('.enrpanel'); let raw='';
    if(p){
      const v = p.getAttribute('value'); if(v) raw=v;
      if(!raw){
        const b = p.querySelector('.enrpanel-body');
        if(b){
          const list = b.querySelector('.enrclass-list'); const pieces=[];
          let n = list ? list.previousElementSibling : null;
          while(n){ if(/^(P|UL)$/i.test(n.tagName)) pieces.unshift(n.outerHTML); n = n.previousElementSibling; }
          raw = pieces.join('');
        }
      }
    }
    const clean = sanitizeHTML(raw);
    const t = document.createElement('div'); t.innerHTML = clean;
    const img = t.querySelector('img');
    return { descHTML: clean, image: img ? img.getAttribute('src') : null };
  }
  function detectNoDateCTAs(root){
    const map = {};
    root.querySelectorAll("a[href*='?course=']").forEach(a=>{
      const href = absURL(a.getAttribute('href')||''); const label = (a.textContent||'').trim().replace(/\s+/g,' ');
      if(href) map[href] = { url: href, label };
    });
    return Object.values(map);
  }
  function parseSessionsFromHTML(html){
    const tmp=document.createElement('div'); tmp.innerHTML = html;
    const ctas = detectNoDateCTAs(tmp);
    const out = [];
    tmp.querySelectorAll('a[href]').forEach(a=>{
      const href=a.getAttribute('href')||''; const abs=absURL(href);
      if(!abs) return;
      if(!(/(\/enroll\?id=\d+)|(\/reg\/\d+)/i.test(abs))) return;
      const label=(a.textContent||'').trim().replace(/\s+/g,' ');
      const meta = findPanelMeta(a);
      out.push({label, url: abs, img: meta.image || null, desc: meta.descHTML || '', ctaNoDate: ctas.length ? ctas[0] : null});
    });
    const seen=new Set();
    return out.filter(x=>{ if(seen.has(x.url)) return false; seen.add(x.url); return true; });
  }
  async function fetchText(p){ const r=await fetch(p,{cache:'no-store'}); return r.text(); }
  async function fetchJSON(p){ const r=await fetch(p,{cache:'no-store'}); return r.json(); }
  function courseMatches(label, c){ return (c.patterns||[]).some(p=>{ try { return new RegExp(p,'i').test(label); } catch(e){ return false; } }); }
  function renderSessions(el, list){
    el.innerHTML = list.map(s=>`<li><a class="btn" rel="nofollow noopener" target="_blank" href="${s.url}">${s.label}</a></li>`).join('')
      || `<li><em>No upcoming sessions found.</em></li>`;
  }
  window.CoursePage = { async run(){
    const main=document.querySelector('main[data-course]'); const slug=main?main.getAttribute('data-course'):null; if(!slug) return;
    const [courses, html] = await Promise.all([ fetchJSON('../courses.json'), fetchText('../shared/schedule.html') ]);
    const course = courses.find(c=>c.slug===slug); if(!course) return;
    const all = parseSessionsFromHTML(html);
    const filtered = all.filter(s=>courseMatches(s.label, course));
    const rich = filtered.find(x=>x.img || x.desc || x.ctaNoDate) || {};
    if(rich.img){ const h=document.querySelector('.hero-holder'); if(h) h.innerHTML = `<img class="hero-img" src="${rich.img}" alt="${course.name}">`; }
    if(rich.desc){ const d=document.querySelector('.course-desc'); if(d) d.innerHTML = `<div class="desc">${rich.desc}</div>`; }
    if(rich.ctaNoDate){ const c=document.querySelector('.no-date-cta'); if(c) c.innerHTML = `<a class="btn secondary" href="${rich.ctaNoDate.url}" rel="nofollow noopener" target="_blank">${rich.ctaNoDate.label}</a>`; }
    const ul=document.querySelector('#sessions'); if(ul) renderSessions(ul, filtered);
  }};
})();