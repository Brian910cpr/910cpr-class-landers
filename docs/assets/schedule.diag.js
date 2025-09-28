// /assets/schedule.diag.js — DIAGNOSTIC LOADER
(() => {
  try {
    console.log("[diag] schedule.diag.js <loaded>");
    window.__sched = { probe: () => console.log("[diag] probe OK") };

    // 1) Prove DOM hookup first: write TEST CHIPs immediately.
    const ids = [
      "times-bls-ren","times-bls-init","times-bls-heart",
      "times-acls-ren","times-acls-init","times-acls-heart",
      "times-pals-ren","times-pals-init","times-pals-heart",
      "wk-aha-list","hsi-list"
    ];
    for (const id of ids) {
      const el = document.getElementById(id);
      if (el) el.innerHTML = '<a class="timechip" href="#">TEST CHIP</a>';
      else console.warn("[diag] missing chip node:", id);
    }
    console.log("[diag] wrote TEST CHIPs to all present nodes");

    // 2) Try to fetch the feed and log outcomes (no parsing yet).
    const CANDIDATES = [
      "periscope_full.json",
      "./periscope_full.json",
      "/periscope_full.json",
      "/assets/periscope_full.json"
    ];

    (async () => {
      for (const url of CANDIDATES) {
        try {
          const r = await fetch(url, { cache: "no-store" });
          console.log("[diag] fetch", url, r.status, r.ok ? "OK" : "FAIL", r.headers.get("content-type"));
          if (r.ok) {
            const txt = await r.text();
            console.log("[diag] sample payload head:", txt.slice(0, 120));
            break; // one good hit is enough
          }
        } catch (e) {
          console.warn("[diag] fetch error", url, e?.message || e);
        }
      }
      console.log("[diag] diagnostics complete");
    })();
  } catch (e) {
    console.error("[diag] fatal:", e);
  }
})();
