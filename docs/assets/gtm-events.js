(() => {
  try {
    const dl = (window.dataLayer = window.dataLayer || []);
    const push = (event, payload={}) => { try { dl.push({ event, ...payload }); } catch {} };

    document.addEventListener("click", (e) => {
      const c = (sel) => e.target.closest && e.target.closest(sel);

      const aSess = c("a[href^='/sessions/'],a[href^=\"/sessions/\"]");
      if (aSess) { push("click_session_link", { link_url:aSess.href, link_text:(aSess.textContent||"").trim() }); return; }

      const aTel = c("a[href^='tel:'],a[href^=\"tel:\"]");
      if (aTel) { push("click_phone", { phone:(aTel.getAttribute("href")||"").replace(/^tel:/i,"") }); return; }

      const aMail = c("a[href^='mailto:'],a[href^=\"mailto:\"]");
      if (aMail) { push("click_email", { email:(aMail.getAttribute("href")||"").replace(/^mailto:/i,"") }); return; }

      const aOut = c("a[href]");
      if (aOut && /^https?:/i.test(aOut.href) && new URL(aOut.href).origin !== location.origin) {
        push("click_outbound", { link_url:aOut.href, link_text:(aOut.textContent||"").trim() }); return;
      }
    }, { passive:true, capture:true });

    push("custom_page_loaded", { path: location.pathname + location.search });
    console.info("[gtm-events] initialized");
  } catch (e) { try { console.warn("[gtm-events] init error:", e?.message||e); } catch {} }
})();
