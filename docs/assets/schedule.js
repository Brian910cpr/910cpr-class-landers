// Minimal, robust loader for periscope_full.json → fills chips
(() => {
  const FEED_PATHS = [
    "periscope_full.json",        // next to index.html (GitHub Pages docs root)
    "./periscope_full.json",
    "/periscope_full.json",
    "assets/periscope_full.json"  // fallback if you ever move it
  ];

  let feedPromise = null;
  async function getFeed() {
    if (feedPromise) return feedPromise;
    feedPromise = (async () => {
      for (const u of FEED_PATHS) {
        try {
          const r = await fetch(u, { cache: "no-store" });
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          const json = await r.json();
          if (!Array.isArray(json)) throw new Error("Feed is not an array");
          console.info("[sched] OK:", u, json.length, "items");
          return json;
        } catch (e) {
          console.warn("[sched] fail:", u, e?.message || e);
        }
      }
      throw new Error("No feed path worked");
    })();
    return feedPromise;
  }

  const U = s => (s||"").toUpperCase();
  const textOf = it => Object.values(it).filter(v => typeof v === "string").join(" ");
  const detectUrl = it => { const k = Object.keys(it).find(k => /(url|href|link)/i.test(k)); return (k && it[k]) || ""; };
  const detectCity = (it, all) => {
    const d = it.city || it.City || it.location_city || it.LocationCity;
    if (d) return d;
    const loc = it.location || it.Location || "";
    if (/WILM(INGTON)?/i.test(loc) || /WILM(INGTON)?/i.test(all)) return "Wilmington";
    if (/BURGAW/i.test(loc) || /BURGAW/i.test(all)) return "Burgaw";
    return "";
  };

  function parseDate(sIn){
    if (sIn==null) return null; let s=String(sIn).trim();
    s = s.replace(/[–—].*$/,"").replace(/\s+at\s+/i," ").replace("@"," ").replace(/\s+/g," ").trim();
    if (/^\d+(\.\d+)?$/.test(s)){ const n=+s; if(n>25569&&n<70000){ const d=new Date(Math.round((n-25569)*86400*1000)); if(!isNaN(d)) return d; } }
    let d=new Date(s); if(!isNaN(d)) return d;
    let m=s.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})(?:\s+(\d{1,2}):(\d{2})(?:\s*(AM|PM))?)?/i);
    if(m){ let[,mo,da,yr,h,mi,ap]=m; let H=h?+h:9; if(ap){ap=ap.toUpperCase(); if(ap==="PM"&&H!==12)H+=12; if(ap==="AM"&&H===12)H=0;}
      d=new Date(+yr,+mo-1,+da,H,mi?+mi:0,0); if(!isNaN(d)) return d; }
    m=s.match(/(\d{4}-\d{2}-\d{2})(?:[ T](\d{1,2}):(\d{2}))?/);
    if(m){ const iso=`${m[1]}T${m[2]?String(m[2]).padStart(2,"0"):"09"}:${m[3]||"00"}:00`; d=new Date(iso); if(!isNaN(d)) return d; }
    return null;
  }

  function normalize(it){
    const all=textOf(it), keys=Object.keys(it);
    const pref=["start","Start","start_time","startTime","StartTime","startDate","StartDate","date","Date","datetime","DateTime"];
    const k = pref.find(x=>x in it) || keys.find(x=>/start|date/i.test(x));
    let raw = k ? it[k] : (it.start || it.date || "");
    let dt = parseDate(raw);
    if(!dt){
      for(const [kk,v] of Object.entries(it)){
        if(typeof v==="string"){ const d=parseDate(v); if(d){ dt=d; raw=v; break; } }
      }
    }
    return { dt, url:detectUrl(it), city:detectCity(it, all), text:U(all) };
  }

  const has = (n,re)=>re.test(n.text);
  const family=n=>has(n,/(^|[^A-Z])BLS([^A-Z]|$)|BASIC\s+LIFE\s+SUPPORT/)? "BLS" :
                  has(n,/(^|[^A-Z])ACLS([^A-Z]|$)|ADVANCED\s+CARDIO/)?      "ACLS" :
                  has(n,/(^|[^A-Z])PALS([^A-Z]|$)|PEDIATRIC\s+ADVANCED/)?   "PALS" : null;
  const isHeart=n=>has(n,/HEART\s*CODE|HEARTCODE|ONLINE.*SKILLS|SKILLS\s*ASSESSMENT/);
  const isRenew=n=>has(n,/\bRENEW(AL)?\b|RECERT|UPDATE\b/);
  const isInPerson=n=>has(n,/IN\s*PERSON|CLASSROOM|INSTRUCTOR[-\s]?LED/) && !isHeart(n);
  const tri=f=>({ ren:n=>family(n)===f&&isRenew(n)&&!isHeart(n),
                  init:n=>family(n)===f&&!isRenew(n)&&isInPerson(n),
                  heart:n=>family(n)===f&&isHeart(n) });
  const BLS=tri("BLS"), ACLS=tri("ACLS"), PALS=tri("PALS");

  const LIM_TRI=6, LIM_WORK=12;

  function label(n){
    if(!(n&&n.dt instanceof Date&&!isNaN(n.dt))) return "";
    const d=n.dt, mo=d.toLocaleString(undefined,{month:"short"}), day=String(d.getDate()).padStart(2,"0");
    let h=d.getHours(), m=d.getMinutes(), ap=h>=12?"p":"a"; h=h%12||12;
    const hm=m?`${h}:${String(m).padStart(2,"0")}${ap}`:`${h}${ap}`;
    return `${mo} ${day}, ${hm}${n.city?` — ${n.city}`:""}`;
  }

  function setChips(id, arr){
    const el=document.getElementById(id); if(!el) return;
    const html=(arr||[]).map(n=>({l:label(n),u:n.url||"#"})).filter(x=>x.l)
      .map(x=>`<a class="timechip" href="${x.u}">${x.l}</a>`).join("");
    if (html) el.innerHTML = html;
  }

  async function go(){
    let raw;
    try { raw = await getFeed(); } catch(e){ console.error("[sched] failed:", e); return; }
    const all = raw.map(normalize)
                   .filter(n => n.dt instanceof Date && !isNaN(n.dt))
                   .filter(n => n.dt >= new Date())
                   .sort((a,b)=>a.dt-b.dt);

    const pick = (fn, lim) => all.filter(fn).slice(0, lim);

    setChips("times-bls-ren",   pick(BLS.ren,   LIM_TRI));
    setChips("times-bls-init",  pick(BLS.init,  LIM_TRI));
    setChips("times-bls-heart", pick(BLS.heart, LIM_TRI));

    setChips("times-acls-ren",   pick(ACLS.ren,   LIM_TRI));
    setChips("times-acls-init",  pick(ACLS.init,  LIM_TRI));
    setChips("times-acls-heart", pick(ACLS.heart, LIM_TRI));

    setChips("times-pals-ren",   pick(PALS.ren,   LIM_TRI));
    setChips("times-pals-init",  pick(PALS.init,  LIM_TRI));
    setChips("times-pals-heart", pick(PALS.heart, LIM_TRI));

    setChips("wk-aha-list",   all.filter(n => has(n,/HEARTSAVER|AHA/) && has(n,/FIRST\s*AID|CPR/)).slice(0, LIM_WORK));
    setChips("wk-aha-list-2", all.filter(n => has(n,/HEARTSAVER|AHA/) && has(n,/ONLINE|BLENDED/)).slice(0, LIM_WORK));
    setChips("hsi-list",      all.filter(n => has(n,/(^|[^A-Z])HSI([^A-Z]|$)/)).slice(0, LIM_WORK));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", go, { once:true });
  } else {
    go();
  }
})();
