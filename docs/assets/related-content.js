(function () {
  "use strict";

  const DATA_URL = "/data/related-content.json";
  const DECISION_PARAMS = ["course", "course_id", "class", "class_id", "session", "session_id", "date", "time", "start", "register", "registration"];
  const DECISION_CLICK_SELECTOR = [
    "#course-option-list button",
    "#course-option-list [role='button']",
    ".course-card",
    "[data-course-id]",
    ".day-button",
    "#start-list button",
    ".register-link",
    "[data-session-id] a.button",
    "[data-session-id] button"
  ].join(",");

  function normalize(value) {
    return String(value || "").trim().toLowerCase();
  }

  function contextTags() {
    const raw = document.body.getAttribute("data-content-tags") || "";
    return new Set(raw.split(/[\s,]+/).map(normalize).filter(Boolean));
  }

  function hasDecisionQuery() {
    const params = new URLSearchParams(window.location.search);
    return DECISION_PARAMS.some((key) => params.has(key) && normalize(params.get(key)));
  }

  function hasSelectedCourse() {
    const scope = document.querySelector(".selector-shell");
    if (!scope) return false;
    return Boolean(
      scope.querySelector("#course-option-list [aria-pressed='true']") ||
      scope.querySelector("#course-option-list .is-selected") ||
      scope.querySelector("#course-option-list .selected") ||
      scope.querySelector("[data-course-id][aria-pressed='true']")
    );
  }

  function decisionHasStarted() {
    return document.body.dataset.decisionMode === "true" || hasDecisionQuery() || hasSelectedCourse();
  }

  function suppressEditorial() {
    document.body.dataset.decisionMode = "true";
    document.querySelectorAll("[data-related-content-host]").forEach((host) => {
      host.hidden = true;
      host.setAttribute("aria-hidden", "true");
      host.innerHTML = "";
    });
  }

  function scoreItem(item, tags, path) {
    if (!item || item.status !== "published") return -1;
    const itemTags = Array.isArray(item.tags) ? item.tags.map(normalize) : [];
    let matches = 0;
    itemTags.forEach((tag) => { if (tags.has(tag)) matches += 1; });
    const preferred = Array.isArray(item.paths) && item.paths.some((candidate) => path === candidate);
    const minimum = Number(item.min_tag_matches || 2);
    if (!preferred && matches < minimum) return -1;
    return Number(item.priority || 0) + (matches * 10) + (preferred ? 50 : 0);
  }

  function render(items) {
    if (decisionHasStarted()) {
      suppressEditorial();
      return;
    }

    const host = document.querySelector("[data-related-content-host]");
    if (!host) return;

    const tags = contextTags();
    const path = window.location.pathname.toLowerCase();
    const ranked = (items || [])
      .map((item) => ({ item, score: scoreItem(item, tags, path) }))
      .filter((entry) => entry.score >= 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 2);

    if (!ranked.length) {
      host.hidden = true;
      return;
    }

    host.innerHTML = `
      <div class="related-materials-heading">
        <span>Helpful while you're deciding</span>
        <strong>Related reading</strong>
      </div>
      <div class="related-materials-list">
        ${ranked.map(({ item }) => `
          <article class="related-material-card">
            <div class="related-material-eyebrow">${escapeHtml(item.eyebrow || "FROM 910CPR")}</div>
            <h2><a href="${escapeAttr(item.url)}">${escapeHtml(item.title)}</a></h2>
            <p>${escapeHtml(item.description || "")}</p>
            <a class="related-material-link" href="${escapeAttr(item.url)}">${escapeHtml(item.cta || "Read more")} →</a>
          </article>
        `).join("")}
      </div>
    `;
    host.hidden = false;
    host.removeAttribute("aria-hidden");
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function escapeAttr(value) {
    return escapeHtml(value).replace(/`/g, "&#96;");
  }

  function bindDecisionSuppression() {
    const scope = document.querySelector(".selector-shell");
    if (!scope) return;

    scope.addEventListener("click", (event) => {
      const target = event.target.closest(DECISION_CLICK_SELECTOR);
      if (target) suppressEditorial();
    }, true);

    scope.addEventListener("change", (event) => {
      const target = event.target;
      if (!target) return;
      if (target.matches("[name*='course'], [name*='date'], [name*='time'], select[data-course], select[data-date], select[data-time]")) {
        suppressEditorial();
      }
    }, true);

    const observer = new MutationObserver(() => {
      if (hasSelectedCourse()) {
        suppressEditorial();
        observer.disconnect();
      }
    });
    observer.observe(scope, { subtree: true, attributes: true, attributeFilter: ["aria-pressed", "class"] });
  }

  function init() {
    bindDecisionSuppression();
    if (decisionHasStarted()) {
      suppressEditorial();
      return;
    }
    fetch(DATA_URL, { cache: "no-store" })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("related content unavailable")))
      .then((payload) => render(payload.items || []))
      .catch(() => {});
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();