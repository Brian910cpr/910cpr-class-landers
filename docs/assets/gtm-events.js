/* /assets/gtm-events.js
   Safe GTM helpers with event delegation (no brittle querySelectorAll quoting).
   - Tracks: session link clicks, tel/mailto, outbound links, generic CTAs.
   - Pushes to dataLayer only (no hard dependency on gtag).
   - Zero-throw: wrapped in try/catch + guards.
*/
(() => {
  try {
    const dl = (window.dataLayer = window.dataLayer || []);
    const ORIGIN = location.origin;

    const push = (event, payload = {}) => {
      try {
        dl.push({ event, ...payload });
      } catch (e) {
        // swallow
      }
    };

    // Tiny helpers
    const closest = (el, sel) => (el?.closest ? el.closest(sel) : null);
    const isSameOrigin = (href) => {
      try {
        const u = new URL(href, ORIGIN);
        return u.origin === ORIGIN;
      } catch {
        return true;
      }
    };

    // Event delegation (one listener)
    document.addEventListener(
      "click",
      (ev) => {
        const t = ev.target;

        // 1) Session links: /sessions/…
        const aSession = closest(t, "a[href^='/sessions/'], a[href^=\"/sessions/\"]");
        if (aSession) {
          const href = aSession.getAttribute("href") || "";
          push("click_session_link", {
            link_url: href,
            link_text: (aSession.textContent || "").trim(),
            link_id: aSession.id || "",
            link_classes: aSession.className || "",
          });
          return;
        }

        // 2) tel:
        const aTel = closest(t, "a[href^='tel:'], a[href^=\"tel:\"]");
        if (aTel) {
          push("click_phone", {
            phone: (aTel.getAttribute("href") || "").replace(/^tel:/i, ""),
            link_id: aTel.id || "",
            placement: aTel.dataset?.placement || "",
          });
          return;
        }

        // 3) mailto:
        const aMail = closest(t, "a[href^='mailto:'], a[href^=\"mailto:\"]");
        if (aMail) {
          push("click_email", {
            email: (aMail.getAttribute("href") || "").replace(/^mailto:/i, ""),
            link_text: (aMail.textContent || "").trim(),
          });
          return;
        }

        // 4) Outbound links (same tab or new tab), only http(s) and different origin
        const aAny = closest(t, "a[href]");
        if (aAny) {
          const href = aAny.getAttribute("href") || "";
          if (/^https?:/i.test(href) && !isSameOrigin(href)) {
            push("click_outbound", {
              link_url: href,
              link_text: (aAny.textContent || "").trim(),
              target: aAny.getAttribute("target") || "",
            });
            return;
          }
        }

        // 5) Generic CTA buttons
        const cta = closest(
          t,
          "[data-cta], .cta, .pill, .chip, button[aria-pressed], button[data-action]"
        );
        if (cta) {
          push("click_cta", {
            cta_text: (cta.textContent || "").trim(),
            cta_id: cta.id || "",
            cta_classes: cta.className || "",
            cta_action: cta.getAttribute("data-action") || "",
          });
          return;
        }
      },
      { passive: true, capture: true }
    );

    // Optional: fire a pageview-ish event (GTM can listen for this)
    push("custom_page_loaded", {
      path: location.pathname + location.search,
      title: document.title,
    });

    // Dev breadcrumb (non-fatal)
    try {
      console.info("[gtm-events] initialized");
    } catch {}
  } catch (e) {
    // never throw
    try { console.warn("[gtm-events] init error:", e?.message || e); } catch {}
  }
})();
