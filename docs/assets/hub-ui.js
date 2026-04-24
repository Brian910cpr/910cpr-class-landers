(function () {
  const EMPTY_FALLBACK_MESSAGE = "No upcoming dates are currently listed for this course. Please check back soon or request help finding a class.";

  function getTriggersForTarget(targetSelector) {
    if (!targetSelector) return [];
    return Array.from(document.querySelectorAll(`[data-tab-target="${targetSelector}"]`));
  }

  function panelHasSessions(panel) {
    return Boolean(panel && (panel.querySelector(".slug-pill") || panel.querySelector(".slug-day-card")));
  }

  function ensureEmptyFallback(scope) {
    let fallback = scope.querySelector(".hub-empty-state");
    if (!fallback) {
      fallback = document.createElement("div");
      fallback.className = "slug-empty hub-empty-state";
      fallback.innerHTML = `<strong>${EMPTY_FALLBACK_MESSAGE}</strong>`;
      scope.appendChild(fallback);
    }
    return fallback;
  }

  function syncScopeVisibility(scope) {
    if (!scope) return;

    const panels = Array.from(scope.querySelectorAll(".tab-panel"));
    const visibleTargets = [];

    panels.forEach((panel) => {
      const targetSelector = `#${panel.id}`;
      const hasSessions = panelHasSessions(panel);
      panel.hidden = !hasSessions;
      panel.classList.toggle("is-empty-panel", !hasSessions);

      getTriggersForTarget(targetSelector).forEach((trigger) => {
        trigger.hidden = !hasSessions;
        trigger.classList.toggle("is-hidden", !hasSessions);
      });

      if (hasSessions) visibleTargets.push(targetSelector);
    });

    const fallback = ensureEmptyFallback(scope);
    const tabs = scope.querySelector(".hub-tabs");
    fallback.hidden = visibleTargets.length > 0;
    if (tabs) tabs.hidden = visibleTargets.length === 0;
  }

  function firstVisibleTrigger(scope) {
    if (!scope) return null;
    return Array.from(scope.querySelectorAll(".tab-btn, .slug-quick-pick")).find((trigger) => !trigger.hidden);
  }

  function extractTimeRowData(pill) {
    const dateNode = pill.querySelector(".slug-pill-date");
    const titleNode = pill.querySelector(".slug-pill-title");
    const subtitleNode = pill.querySelector(".slug-pill-subtitle");
    const locationNode = pill.querySelector(".slug-pill-chip-location");
    const timeNode = Array.from(pill.querySelectorAll(".slug-pill-chip")).find((chip) => !chip.classList.contains("slug-pill-chip-location"));
    const buttonNode = pill.querySelector(".slug-pill-actions .button");
    const hintNode = pill.querySelector(".slug-pill-hint");

    return {
      dateHtml: dateNode ? dateNode.outerHTML : "",
      title: titleNode ? titleNode.textContent.trim() : "",
      subtitle: subtitleNode ? subtitleNode.textContent.trim() : "",
      time: timeNode ? timeNode.textContent.trim() : "",
      location: locationNode ? locationNode.textContent.trim() : "",
      href: buttonNode ? buttonNode.getAttribute("href") : "",
      buttonText: buttonNode ? buttonNode.textContent.trim() : "Register",
      hint: hintNode ? hintNode.textContent.trim() : "Reserve this class time",
    };
  }

  function groupSessionsByDay(scope) {
    if (!scope) return;

    scope.querySelectorAll(".tab-panel .slug-pill-list").forEach((list) => {
      if (list.dataset.groupedByDay === "true") return;

      const pills = Array.from(list.querySelectorAll(":scope > .slug-pill"));
      if (!pills.length) {
        list.dataset.groupedByDay = "true";
        return;
      }

      const groups = [];
      const byKey = new Map();

      pills.forEach((pill) => {
        const row = extractTimeRowData(pill);
        const key = row.title || row.dateHtml;
        if (!byKey.has(key)) {
          const group = {
            key,
            title: row.title,
            dateHtml: row.dateHtml,
            rows: [],
          };
          byKey.set(key, group);
          groups.push(group);
        }
        byKey.get(key).rows.push(row);
      });

      list.innerHTML = groups.map((group) => {
        const rowsMarkup = group.rows.map((row) => `
          <div class="slug-time-row">
            <div class="slug-time-copy">
              <div class="slug-pill-meta-row slug-time-meta">
                ${row.time ? `<span class="slug-pill-chip">${row.time}</span>` : ""}
                ${row.location ? `<span class="slug-pill-chip slug-pill-chip-location">${row.location}</span>` : ""}
              </div>
              ${row.subtitle ? `<div class="slug-time-subtitle">${row.subtitle}</div>` : ""}
            </div>
            <div class="slug-time-actions">
              <div class="slug-pill-hint">${row.hint}</div>
              ${row.href ? `<a class="button small primary" href="${row.href}">${row.buttonText}</a>` : ""}
            </div>
          </div>
        `).join("");

        return `
          <article class="slug-day-card">
            ${group.dateHtml}
            <div class="slug-day-main">
              <div class="slug-day-title">${group.title}</div>
              <div class="slug-time-list">${rowsMarkup}</div>
            </div>
          </article>
        `;
      }).join("");

      list.dataset.groupedByDay = "true";
    });
  }

  function activateTab(scope, trigger) {
    if (!scope || !trigger) return;
    const targetSelector = trigger.getAttribute("data-tab-target");
    if (!targetSelector) return;

    const panel = scope.querySelector(targetSelector);
    if (!panel) return;

    scope.querySelectorAll(".tab-btn, .slug-quick-pick").forEach((element) => {
      const sameTarget = element.getAttribute("data-tab-target") === targetSelector;
      element.classList.toggle("active", sameTarget);
    });
    scope.querySelectorAll(".tab-panel").forEach((element) => {
      element.classList.toggle("active", element === panel);
    });

    const program = trigger.getAttribute("data-program");
    const inputSelector = scope.getAttribute("data-sync-program");
    if (program && inputSelector) {
      const input = document.querySelector(inputSelector);
      if (input) input.value = program;
    }

    const bannerLink = scope.parentElement && scope.parentElement.querySelector("[data-full-schedule-link]");
    const bannerRaw = panel.getAttribute("data-banner");
    if (bannerLink && bannerRaw) {
      try {
        const data = JSON.parse(bannerRaw);
        if (data.url) bannerLink.setAttribute("href", data.url);
        if (data.label) bannerLink.textContent = data.label;
      } catch (error) {
        console.error(error);
      }
    }
  }

  function scopeForTrigger(trigger) {
    const explicitScope = trigger.getAttribute("data-tab-scope");
    if (explicitScope) return document.querySelector(explicitScope);
    return trigger.closest("[data-tabs]");
  }

  function bindTriggers() {
    document.querySelectorAll("[data-tab-target]").forEach((trigger) => {
      trigger.addEventListener("click", () => {
        activateTab(scopeForTrigger(trigger), trigger);
      });
    });
  }

  function activateProgramFromQuery() {
    const requestedProgram = new URLSearchParams(window.location.search).get("program");
    if (!requestedProgram) return;

    const target = Array.from(document.querySelectorAll("[data-program]")).find((button) => {
      return !button.hidden && button.getAttribute("data-program") === requestedProgram;
    });
    if (!target) return;

    activateTab(scopeForTrigger(target), target);
  }

  function initializeScopes() {
    document.querySelectorAll("[data-tabs]").forEach((scope) => {
      groupSessionsByDay(scope);
      syncScopeVisibility(scope);

      const active = scope.querySelector(".tab-btn.active:not([hidden]), .slug-quick-pick.active:not([hidden]), .tab-panel.active:not([hidden])");
      if (!active) {
        const fallback = firstVisibleTrigger(scope);
        if (fallback) activateTab(scope, fallback);
        return;
      }

      if (active.matches(".tab-panel")) {
        const trigger = scope.querySelector(`[data-tab-target="#${active.id}"]`);
        if (trigger) activateTab(scope, trigger);
        return;
      }

      activateTab(scope, active);
    });
  }

  bindTriggers();
  initializeScopes();
  activateProgramFromQuery();
})();
