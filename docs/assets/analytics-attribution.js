(function () {
  "use strict";

  const STORAGE_KEY = "lw_session_acquisition_v1";
  const EXCLUSION_COOKIES = ["analytics_excluded", "lw_analytics_excluded"];
  const ENROLLWARE_SUFFIX = ".enrollware.com";
  const DEFAULT_CAMPAIGN = "910cpr_registration";

  function isExcluded() {
    return EXCLUSION_COOKIES.some(function (name) {
      return new RegExp("(?:^|;\\s*)" + name + "=1(?:;|$)").test(document.cookie);
    }) || /^\/(admin|control-center|internal|drafts|analytics-preferences)(\/|$)/.test(location.pathname);
  }

  function clean(value, fallback) {
    const normalized = String(value || "").trim().slice(0, 100);
    return normalized || fallback;
  }

  function classifyHost(hostname) {
    const host = hostname.toLowerCase().replace(/^www\./, "");
    if (/^(google\.|googleusercontent\.)/.test(host)) return { source: "google", medium: "organic" };
    if (host === "bing.com" || host.endsWith(".bing.com")) return { source: "bing", medium: "organic" };
    if (host === "yahoo.com" || host.endsWith(".yahoo.com")) return { source: "yahoo", medium: "organic" };
    if (host === "chatgpt.com" || host.endsWith(".chatgpt.com") || host === "openai.com" || host.endsWith(".openai.com")) {
      return { source: "chatgpt.com", medium: "ai-assistant" };
    }
    if (host === "facebook.com" || host.endsWith(".facebook.com")) return { source: "facebook.com", medium: "social" };
    return { source: host, medium: "referral" };
  }

  function isFirstPartyHost(hostname) {
    const host = String(hostname || "").toLowerCase();
    return host === "910cpr.com" || host.endsWith(".910cpr.com");
  }

  function readStored() {
    try {
      const value = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "null");
      if (value && value.source && value.medium) return value;
    } catch (_) { /* Ignore unavailable or malformed browser storage. */ }
    return null;
  }

  function resolveAcquisition() {
    const params = new URLSearchParams(location.search);
    if (params.get("utm_source")) {
      return {
        source: clean(params.get("utm_source"), "direct"),
        medium: clean(params.get("utm_medium"), "campaign"),
        campaign: clean(params.get("utm_campaign"), DEFAULT_CAMPAIGN)
      };
    }
    if (params.get("gclid")) return { source: "google", medium: "cpc", campaign: DEFAULT_CAMPAIGN };
    if (params.get("msclkid")) return { source: "bing", medium: "cpc", campaign: DEFAULT_CAMPAIGN };

    if (document.referrer) {
      try {
        const referrer = new URL(document.referrer);
        if (!isFirstPartyHost(referrer.hostname)) {
          return Object.assign(classifyHost(referrer.hostname), { campaign: DEFAULT_CAMPAIGN });
        }
      } catch (_) { /* Fall back to the current tab's stored acquisition. */ }
    }

    return readStored() || { source: "direct", medium: "none", campaign: DEFAULT_CAMPAIGN };
  }

  function store(acquisition) {
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(acquisition)); } catch (_) { /* Optional enhancement only. */ }
  }

  function isEnrollware(url) {
    return url.hostname === "enrollware.com" || url.hostname.endsWith(ENROLLWARE_SUFFIX);
  }

  function contentLabel(url) {
    const page = location.pathname.replace(/^\/+|\/+$/g, "").replace(/[^a-z0-9]+/gi, "-").slice(0, 60) || "home";
    const id = url.searchParams.get("id") || url.searchParams.get("courseId") || url.searchParams.get("appointmentDayId");
    return id ? page + "_id-" + clean(id, "unknown") : page;
  }

  function decorate(raw, acquisition) {
    if (!raw) return raw;
    let url;
    try { url = new URL(raw, location.href); } catch (_) { return raw; }
    if (!isEnrollware(url)) return raw;
    if (!url.searchParams.has("utm_source")) url.searchParams.set("utm_source", acquisition.source);
    if (!url.searchParams.has("utm_medium")) url.searchParams.set("utm_medium", acquisition.medium);
    if (!url.searchParams.has("utm_campaign")) url.searchParams.set("utm_campaign", acquisition.campaign || DEFAULT_CAMPAIGN);
    if (!url.searchParams.has("utm_content")) url.searchParams.set("utm_content", contentLabel(url));
    return url.toString();
  }

  function decorateLink(link, acquisition) {
    ["href", "data-original-href"].forEach(function (attribute) {
      const raw = link.getAttribute(attribute);
      const decorated = decorate(raw, acquisition);
      if (decorated && decorated !== raw) link.setAttribute(attribute, decorated);
    });
  }

  function decorateAll(root, acquisition) {
    if (root.matches && root.matches("a[href],a[data-original-href]")) decorateLink(root, acquisition);
    if (root.querySelectorAll) root.querySelectorAll("a[href],a[data-original-href]").forEach(function (link) {
      decorateLink(link, acquisition);
    });
  }

  if (isExcluded()) return;

  const acquisition = resolveAcquisition();
  store(acquisition);
  decorateAll(document, acquisition);

  document.addEventListener("click", function (event) {
    const link = event.target.closest && event.target.closest("a[href],a[data-original-href]");
    if (!link) return;
    decorateLink(link, acquisition);
    let destination;
    try { destination = new URL(link.href, location.href); } catch (_) { return; }
    if (!isEnrollware(destination)) return;
    link.dataset.attributionBeginRegistration = "1";
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({
      event: "begin_registration",
      registration_type: destination.searchParams.has("appointmentDayId") ? "appointment" : "seated_class",
      destination_host: destination.hostname,
      session_id: destination.searchParams.get("id") || "",
      course_id: destination.searchParams.get("courseId") || "",
      acquisition_source: acquisition.source,
      acquisition_medium: acquisition.medium,
      source_path: location.pathname
    });
  }, true);

  if (window.MutationObserver) {
    new MutationObserver(function (records) {
      records.forEach(function (record) {
        record.addedNodes.forEach(function (node) {
          if (node.nodeType === 1) decorateAll(node, acquisition);
        });
      });
    }).observe(document.documentElement, { childList: true, subtree: true });
  }

  window.LanderWareAnalytics = { decorate: decorate, acquisition: acquisition, isExcluded: isExcluded };
})();
