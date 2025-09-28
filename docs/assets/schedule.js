// /assets/schedule.js
(() => {
  if (window.__910cprScheduleLoaded) return;
  window.__910cprScheduleLoaded = true;

  const FEED_PATHS = [
    "periscope_full.json",
    "./periscope_full.json",
    "/periscope_full.json",
    "/assets/periscope_full.json" // keep or remove; works as a fallback if you ever move it
  ];

  let FEED_PROMISE = null;
  async function getFeed() {
    if (FEED_PROMISE) return FEED_PROMISE;
    FEED_PROMISE = (async () => {
      for (const u of FEED_PATHS) {
        try {
          const r = await fetch(u, { cache: "no-store" });
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          const json = await r.json();
          console.info("[sched] feed ok:", u, json.length, "items");
          return json;
        } catch (e) {
          console.warn("[sched] feed fail:", u, e?.message || e);
        }
      }
      throw new Error("All feed paths failed");
    })();
    return FEED_PROMISE;
  }

  const U = s => (s||"").toUpperCase();
  const txt = it => Object.values(it).filter(v => typeof v === "string").join(" ");
  const detectUrl  = it => { const k = Object.keys(it).find(k => /(url|href|link)/i.test(k)); return (k && it[k]) || ""; };
  function detectCity(it, all) {
    const d = it.city || it.City || it.location_city || it.LocationCity; if (d) return d;
    const loc = it.location || it.Location || "";
    if (/WILM(INGTON)?/i.test(loc) || /WILM(INGTON)?/i.test(all)) return "Wilmington";
    if (/BURGAW/i.test(loc) || /BURGAW/i.test(all)) return "Burgaw";
    return "";
  }

  function parseFlexDate(sIn) {
    if (sIn == null) return null; let s = String(sIn).trim();
    s = s.replace(/[–—].*$/,"").replace(/\s+at\s+/i," ").replace("@"," ").replace(/\s+/g," ").trim();
    if (/^\d+(\.\d+)?$/.test(s)) { const n = +s;
      if (n > 25569 && n < 70000) { const d = new Date(Math.round((n-25569)*86400*1000)); if (!isNaN(d)) return d; } }
    let d = new Date(s); if (!isNaN(d)) return d;
    let m = s.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM)?\s*([A-Z]{1,4})?$/i);
    if (m) { let [,Y,M,D,h,mi,ss,ap,tz] = m; let H = +h;
      if (ap) { ap = ap.toUpperCase(); if (ap === "PM" && H !== 12) H += 12; if (ap === "AM" && H === 12) H = 0; }
      const tzMap = { EDT:"-04:00", EST:"-05:00", ET:"-05:00", CDT:"-05:00", CST:"-06:00", PDT:"-07:00", PST:"-08:00" };
      const off = tz && tzMap[tz.toUpperCase()] ? tzMap[tz.toUpperCase()] : "";
      d = new Date(`${Y}-${M}-${D}T${String(H).padStart(2,"0")}:${mi}:${ss||"00"}${off}`); if (!isNaN(d)) return d;
      d = new Date(`${Y}-${M}-${D}T${String(H).padStart(2,"0")}:${mi}:${ss||"00"}`);     if (!isNaN(d)) return d;
    }
    m = s.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})(?:\s+(\d{1,2}):(\d{2})(?:\s*(AM|PM))?)?/i);
    if (m) { let [,mo,da,yr,h,mi,ap] = m; let H = h ? +h : 9;
      if (ap) { ap = ap.toUpperCase(); if (ap === "PM" && H !== 12) H += 12; if (ap === "AM" && H === 12) H = 0; }
      d = new Date(+yr, +mo-1, +da, H, mi ? +mi : 0, 0); if (!isNaN(d)) return d;
    }
    m = s.match(/(\d{4}-\d{2}-\d{2})(?:[ T](\d{1,2}):(\d{2}))?/);
    if (m) { const iso = `${m[1]}T${m[2] ? String(m[2]).padStart(2,"0") : "09"}:${m[3] || "00"}:00`;
      d = new Date(iso); if (!isNaN(d)) return d; }
    return null;
  }

  function findAnyDate(it){
    for (const [k,v] of Object.entries(it)) if (typeof v === "string") { const d = parseFlexDate(v); if (d) return {dt:d, key:k, raw:v}; }
    return { dt:null, key:"", raw:"" };
  }

  function normalize(it){
    const all = txt(it), keys = Object.keys(it);
    const pref = ["start","Start","start_time","startTime","StartTime","startDate","StartDate","startDateTime","StartDateTime","start_at","Start Date / Time","Start Date","Date","date","datetime"];
    const key = pref.find(k=>k in it) || keys.find(k=>/start|date/i.test(k));
    let startRaw = key ? it[key] : (it.start || it.date || "");
    let dt = parseFlexDate(startRaw); let usedKey = key || (startRaw ? "guessed" : "");
    if (!dt) { const f = findAnyDate(it); dt = f.dt; startRaw = f.raw || startRaw; usedKey = f.key || usedKey; }
    return { dt, startRaw, url: detectUrl(it), city: detectCity(it, all), text: U(all) };
  }

  function chipLabel(n){
    if (!(n && n.dt instanceof Date && !isNaN(n.dt))) return "";
    const d=n.dt, mo=d.toLocaleString(undefined,{month:"short"}), day=String(d.getDate()).padStart(2,"0");
    let h=d.getHours(), m=d.getMinutes(), ap=h>=12?"p":"a"; h=h%12||12;
    const hm = m ? `${h}:${String(m).padStart(2,"0")}${ap}` : `${h}${ap}`;
    return `${mo} ${day}, ${hm}${n.city ? ` — ${n.city}` : ""}`;
  }

  function setChips(id, items){
    const el = document.getElementById(id); if (!el) return;
    const html = (items||[]).map(n => ({ label: chipLabel(n), url: n.url || "#" }))
      .filter(x => x.label).map(x => `<a class="timechip" href="${x.url}">${x.label}</a>`).join("");
    el.innerHTML = html || '<span class="micro">New dates posting—check back soon.</span>';
  }

  const has = (n,re) => re.test(n.text);
  const family = n => has(n,/(^|[^A-Z])BLS([^A-Z]|$)|BASIC\s+LIFE\s+SUPPORT/)? "BLS" :
                       has(n,/(^|[^A-Z])ACLS([^A-Z]|$)|ADVANCED\s+CARDIO/)?      "ACLS" :
                       has(n,/(^|[^A-Z])PALS([^A-Z]|$)|PEDIATRIC\s+ADVANCED/)?   "PALS" : null;
  const isHeart = n => has(n,/HEART\s*CODE|HEARTCODE|ONLINE.*SKILLS|SKILLS\s*ASSESSMENT/);
  const isRenew = n => has(n,/\bRENEW(AL)?\b|RECERT|UPDATE\b/);
  const isInPerson = n => has(n,/IN\s*PERSON|CLASSROOM|INSTRUCTOR[-\s]?LED/) && !isHeart(n);
  const tri = f => ({ ren:n=>family(n)===f && isRenew(n) && !isHeart(n),
                      init:n=>family(n)===f && !isRenew(n) && isInPerson(n),
                      heart:n=>family(n)===f && isHeart(n) });
  const BLS=tri("BLS"), ACLS=tri("ACLS"), PALS=tri("PALS");
  const LIM_TRI=6, LIM_WORK=12;

  async function upcoming(filter, limit){
    const raw = await getFeed(); const norm = raw.map(normalize);
    const now = new Date(); const ok = norm.filter(n => n.dt instanceof Date && !isNaN(n.dt));
    return ok.filter(n => n.dt >= now).filter(filter).sort((a,b)=>a.dt-b.dt).slice(0, limit);
  }

  Promise.all([
    upcoming(BLS.ren,  LIM_TRI).then(v => setChips("times-bls-ren",   v)),
    upcoming(BLS.init, LIM_TRI).then(v => setChips("times-bls-init",  v)),
    upcoming(BLS.heart,LIM_TRI).then(v => setChips("times-bls-heart", v)),
    upcoming(ACLS.ren, LIM_TRI).then(v => setChips("times-acls-ren",  v)),
    upcoming(ACLS.init,LIM_TRI).then(v => setChips("times-acls-init", v)),
    upcoming(ACLS.heart,LIM_TRI).then(v => setChips("times-acls-heart",v)),
    upcoming(PALS.ren, LIM_TRI).then(v => setChips("times-pals-ren",  v)),
    upcoming(PALS.init,LIM_TRI).then(v => setChips("times-pals-init", v)),
    upcoming(PALS.heart,LIM_TRI).then(v => setChips("times-pals-heart",v)),
    upcoming(n => has(n,/FIRST\s*AID|HEARTSAVER|WORKPLACE|CPR\s*\/?\s*AED/)&&has(n,/(^|[^A-Z])AHA([^A-Z]|$)|HEARTSAVER/),LIM_WORK).then(v=>setChips("wk-aha-list",v)),
    upcoming(n => has(n,/FIRST\s*AID|WORKPLACE|CPR\s*\/?\s*AED/)&&has(n,/(^|[^A-Z])HSI([^A-Z]|$)|HEALTH\s*&\s*SAFETY\s*INSTITUTE/),LIM_WORK).then(v=>setChips("hsi-list",v))
  ]).catch(err=>{
    console.error("[sched] init fail:", err);
    ["times-bls-ren","times-bls-init","times-bls-heart","times-acls-ren","times-acls-init","times-acls-heart","times-pals-ren","times-pals-init","times-pals-heart","wk-aha-list","hsi-list"]
      .forEach(id => { const el = document.getElementById(id); if (el) el.innerHTML = '<span class="micro">Schedule temporarily unavailable.</span>'; });
  });

  // Dev helper
  window.__sched = {
    probe: async () => {
      try { const r = await getFeed(); console.log("[probe] items:", r.length); return r.slice(0, 6); }
      catch(e){ console.error("[probe] err:", e); return null; }
    }
  };
})();
