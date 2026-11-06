(() => {
  "use strict";

  const page = document.querySelector('meta[name="community-share-page"]')?.content;
  const descriptions = {
    pool: "FREE Family & Friends CPR, Feb 15 2027, 11 AM–2 PM at Earl Jackson Pool, Wilmington.",
    poolbls: "AHA BLS Provider, Feb 15 2027, 11 AM–2 PM at Earl Jackson Pool, Wilmington. $25."
  };
  if (!Object.prototype.hasOwnProperty.call(descriptions, page)) return;
  const url = "https://www.910cpr.com/" + page;
  const text = descriptions[page] + " " + url;
  const configuredEvent = document.querySelector('meta[name="community-facebook-event-url"]')?.content || "";
  const eventUrl = /^https:\/\/www\.facebook\.com\/events\/\d+\/?$/.test(configuredEvent) ? configuredEvent : "";

  // Reuse the existing GTM queue. No destination, identifiers or storage are added.
  function track(event, channel, placement, target, method = "none", outcome = "none") {
    try {
      const excluded = /(?:^|;\s*)(?:lw_analytics_excluded|analytics_excluded)=1(?:;|$)/.test(document.cookie)
        || /^\/(admin|control-center|internal|drafts|analytics-preferences)(\/|$)/.test(location.pathname);
      if (excluded || window.LanderWareAnalytics?.isExcluded?.()) return;
      if (typeof window.dataLayer?.push !== "function") return;
      window.dataLayer.push({
        event, page_id: page, share_channel: channel, share_placement: placement,
        share_target: target, share_method: method, share_outcome: outcome
      });
    } catch (_) { /* Analytics must never interrupt sharing, including blocked cookie access. */ }
  }

  async function copy(value, status, report = () => {}) {
    try {
      await navigator.clipboard.writeText(value);
      status.textContent = "Copied!";
      report("clipboard", "succeeded");
    } catch (_) {
      report("clipboard", "failed");
      try {
        const response = window.prompt("Copy this link", value);
        status.textContent = response === null ? "Copy canceled." : "Select and copy the link from the prompt.";
        // A prompt cannot prove that the visitor copied anything.
        report("manual", response === null ? "cancelled" : "prompted");
      } catch (_) {
        status.textContent = "Copy unavailable. Use the class link at the bottom of this page.";
        report("manual", "failed");
      }
    }
  }

  document.querySelectorAll("[data-share-placement]").forEach(section => {
    const placement = section.dataset.sharePlacement;
    if (!["top", "bottom"].includes(placement)) return;
    const status = section.querySelector(".share-status");
    section.querySelectorAll("[data-share]").forEach(control => {
      const channel = control.dataset.share === "sms" ? "text" : control.dataset.share;
      if (!["native", "facebook", "text", "email", "copy"].includes(channel)) return;
      const target = channel === "facebook" && eventUrl ? "facebook_event" : "class_page";
      if (target === "facebook_event") control.href = eventUrl;
      // One click listener handles mouse, nested SVG and native keyboard activation.
      // Links retain default navigation; asynchronous fallbacks never count another click.
      control.addEventListener("click", async () => {
        track(page + "_share_click", channel, placement, target);
        status.textContent = "";
        const report = (method, outcome) => track(page + "_share_result", channel, placement, target, method, outcome);
        if (channel === "copy") return copy(url, status, report);
        if (channel !== "native") return;
        if (typeof navigator.share !== "function") return copy(url, status, report);
        try {
          await navigator.share({title: document.title, text, url});
          report("native", "resolved"); // API handoff only, not proof of a completed share.
        } catch (error) {
          if (error?.name === "AbortError") {
            report("native", "cancelled");
            return;
          }
          report("native", "failed");
          await copy(url, status, report);
        }
      });
    });
  });

})();
