(function () {
  const EMPTY_FALLBACK_TITLE = "No upcoming dates are currently listed for this course.";
  const EMPTY_FALLBACK_BODY = "Please contact us and we'll help you find the right class.";
  const MONTHS = {
    jan: 0,
    january: 0,
    feb: 1,
    february: 1,
    mar: 2,
    march: 2,
    apr: 3,
    april: 3,
    may: 4,
    jun: 5,
    june: 5,
    jul: 6,
    july: 6,
    aug: 7,
    august: 7,
    sep: 8,
    sept: 8,
    september: 8,
    oct: 9,
    october: 9,
    nov: 10,
    november: 10,
    dec: 11,
    december: 11,
  };

  function getTriggersForTarget(targetSelector) {
    if (!targetSelector) return [];
    return Array.from(document.querySelectorAll(`[data-tab-target="${targetSelector}"]`));
  }

  function parseSessionStartValue(value) {
    if (!value) return null;
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  function parseTimeParts(value) {
    const text = String(value || "").trim().toUpperCase();
    const match = text.match(/(\d{1,2})(?::(\d{2}))?\s*(AM|PM)/);
    if (!match) return null;

    let hour = Number(match[1]);
    const minute = Number(match[2] || 0);
    const meridiem = match[3];

    if (meridiem === "AM" && hour === 12) hour = 0;
    if (meridiem === "PM" && hour < 12) hour += 12;

    return { hour, minute };
  }

  function parseMonthDayYear(text) {
    const source = String(text || "").trim();
    const match = source.match(/([A-Za-z]+)\s+(\d{1,2})(?:,?\s+(\d{4}))?/);
    if (!match) return null;

    const monthKey = match[1].toLowerCase();
    if (!(monthKey in MONTHS)) return null;

    return {
      monthIndex: MONTHS[monthKey],
      day: Number(match[2]),
      year: match[3] ? Number(match[3]) : null,
    };
  }

  function parseWeekday(text) {
    const match = String(text || "").trim().match(/^(Sun|Mon|Tue|Tues|Wed|Thu|Thur|Fri|Sat)/i);
    if (!match) return "";
    return match[1].slice(0, 3).toLowerCase();
  }

  function formatSessionDateKey(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function buildCandidateDate(year, monthIndex, day, timeParts) {
    if (!timeParts) return null;
    const candidate = new Date(year, monthIndex, day, timeParts.hour, timeParts.minute, 0, 0);
    if (
      Number.isNaN(candidate.getTime()) ||
      candidate.getFullYear() !== year ||
      candidate.getMonth() !== monthIndex ||
      candidate.getDate() !== day
    ) {
      return null;
    }
    return candidate;
  }

  function inferCandidateDate(monthIndex, day, weekdayHint, timeParts) {
    const now = new Date();
    const candidates = [];

    for (let year = now.getFullYear() - 1; year <= now.getFullYear() + 1; year += 1) {
      const candidate = buildCandidateDate(year, monthIndex, day, timeParts);
      if (!candidate) continue;
      if (weekdayHint) {
        const actualWeekday = candidate.toLocaleDateString("en-US", { weekday: "short" }).slice(0, 3).toLowerCase();
        if (actualWeekday !== weekdayHint) continue;
      }
      candidates.push(candidate);
    }

    if (!candidates.length) return null;

    candidates.sort((a, b) => Math.abs(a.getTime() - now.getTime()) - Math.abs(b.getTime() - now.getTime()));
    return candidates[0];
  }

  function inferSessionStart(element) {
    if (!element) return null;

    const existing = parseSessionStartValue(element.getAttribute("data-session-start"));
    if (existing) return existing;

    const timeText =
      element.getAttribute("data-session-time") ||
      (Array.from(element.querySelectorAll(".slug-pill-chip, .slug-time-meta .slug-pill-chip"))
        .find((chip) => !chip.classList.contains("slug-pill-chip-location")) || {}).textContent ||
      "";

    const timeParts = parseTimeParts(timeText);
    if (!timeParts) return null;

    const directDate =
      element.getAttribute("data-session-date-text") ||
      (element.querySelector(".upcoming-date") ? element.querySelector(".upcoming-date").textContent.trim() : "");
    if (directDate) {
      const direct = parseSessionStartValue(`${directDate} ${timeText}`);
      if (direct) {
        element.setAttribute("data-session-start", direct.toISOString());
        return direct;
      }
    }

    const dateBadge = element.querySelector(".slug-pill-date") || element.closest(".slug-day-card");
    const titleText =
      element.getAttribute("data-session-title") ||
      (element.querySelector(".slug-pill-title") ? element.querySelector(".slug-pill-title").textContent.trim() : "") ||
      (element.closest(".slug-day-card") && element.closest(".slug-day-card").querySelector(".slug-day-title")
        ? element.closest(".slug-day-card").querySelector(".slug-day-title").textContent.trim()
        : "");

    const monthText =
      element.getAttribute("data-session-month") ||
      (dateBadge && dateBadge.querySelector(".slug-pill-month") ? dateBadge.querySelector(".slug-pill-month").textContent.trim() : "");
    const dayText =
      element.getAttribute("data-session-day") ||
      (dateBadge && dateBadge.querySelector(".slug-pill-day") ? dateBadge.querySelector(".slug-pill-day").textContent.trim() : "");
    const weekdayText =
      element.getAttribute("data-session-weekday") ||
      (dateBadge && dateBadge.querySelector(".slug-pill-weekday") ? dateBadge.querySelector(".slug-pill-weekday").textContent.trim() : "") ||
      titleText;

    let monthDayYear = null;
    if (monthText && dayText) {
      monthDayYear = parseMonthDayYear(`${monthText} ${dayText}`);
    }
    if (!monthDayYear) {
      monthDayYear = parseMonthDayYear(titleText);
    }
    if (!monthDayYear) return null;

    const weekdayHint = parseWeekday(weekdayText);
    const start = monthDayYear.year
      ? buildCandidateDate(monthDayYear.year, monthDayYear.monthIndex, monthDayYear.day, timeParts)
      : inferCandidateDate(monthDayYear.monthIndex, monthDayYear.day, weekdayHint, timeParts);

    if (!start) return null;
    element.setAttribute("data-session-start", start.toISOString());
    return start;
  }

  function countVisibleSessions(panel) {
    if (!panel) return 0;
    const groupedRows = panel.querySelectorAll(".slug-time-row");
    if (groupedRows.length) return groupedRows.length;
    return panel.querySelectorAll(".slug-pill-list > .slug-pill").length;
  }

  function panelHasSessions(panel) {
    return countVisibleSessions(panel) > 0;
  }

  function ensureScopeEmptyFallback(scope) {
    let fallback = scope.querySelector(".hub-empty-state");
    if (!fallback) {
      fallback = document.createElement("div");
      fallback.className = "slug-empty hub-empty-state";
      fallback.innerHTML = `<strong>${EMPTY_FALLBACK_TITLE}</strong><p>${EMPTY_FALLBACK_BODY}</p>`;
      scope.appendChild(fallback);
    }
    return fallback;
  }

  function ensurePanelEmptyState(panel) {
    const list = panel ? panel.querySelector(".slug-pill-list") : null;
    if (!list) return;

    const existing = list.querySelector(":scope > .slug-empty");
    const hasSessions = countVisibleSessions(panel) > 0;

    if (hasSessions) {
      if (existing) existing.remove();
      return;
    }

    if (!existing) {
      list.innerHTML = (
        "<div class='slug-empty'>"
        + `<strong>${EMPTY_FALLBACK_TITLE}</strong>`
        + `<p>${EMPTY_FALLBACK_BODY}</p>`
        + "</div>"
      );
    }
  }

  function syncPanelInventory(panel) {
    const kicker = panel ? panel.querySelector(".slug-panel-kicker") : null;
    if (!kicker) return;
    const count = countVisibleSessions(panel);
    kicker.textContent = `${count} upcoming option${count === 1 ? "" : "s"}`;
  }

  function syncTriggerInventory(targetSelector, count) {
    getTriggersForTarget(targetSelector).forEach((trigger) => {
      const strong = trigger.querySelector("strong");
      if (strong) {
        strong.textContent = `${count} date${count === 1 ? "" : "s"}`;
      }
      trigger.setAttribute("data-visible-count", String(count));
    });
  }

  function syncScopeVisibility(scope) {
    if (!scope) return;

    const panels = Array.from(scope.querySelectorAll(".tab-panel"));
    const visibleTargets = [];

    panels.forEach((panel) => {
      ensurePanelEmptyState(panel);
      syncPanelInventory(panel);

      const targetSelector = `#${panel.id}`;
      const count = countVisibleSessions(panel);
      const hasSessions = panelHasSessions(panel);
      panel.hidden = !hasSessions;
      panel.classList.toggle("is-empty-panel", !hasSessions);
      syncTriggerInventory(targetSelector, count);

      getTriggersForTarget(targetSelector).forEach((trigger) => {
        trigger.hidden = !hasSessions;
        trigger.classList.toggle("is-hidden", !hasSessions);
      });

      if (hasSessions) visibleTargets.push(targetSelector);
    });

    const fallback = ensureScopeEmptyFallback(scope);
    const tabs = scope.querySelector(".hub-tabs");
    fallback.hidden = visibleTargets.length > 0;
    if (tabs) tabs.hidden = visibleTargets.length === 0;
  }

  function firstVisibleTrigger(scope) {
    if (!scope) return null;
    return Array.from(scope.querySelectorAll(".tab-btn, .slug-quick-pick")).find((trigger) => !trigger.hidden);
  }

  function extractTimeRowData(pill) {
    const start = inferSessionStart(pill);
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
      sessionStart: start ? start.toISOString() : "",
      sessionDate: start ? formatSessionDateKey(start) : "",
    };
  }

  function pruneDirectPills(scope) {
    const now = new Date();
    scope.querySelectorAll(".tab-panel .slug-pill-list > .slug-pill").forEach((pill) => {
      const start = inferSessionStart(pill);
      if (start && start < now) {
        pill.remove();
      }
    });
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
        const key = row.sessionDate || row.title || row.dateHtml;
        if (!byKey.has(key)) {
          const group = {
            key,
            title: row.title,
            dateHtml: row.dateHtml,
            sessionDate: row.sessionDate,
            rows: [],
          };
          byKey.set(key, group);
          groups.push(group);
        }
        byKey.get(key).rows.push(row);
      });

      list.innerHTML = groups.map((group) => {
        const rowsMarkup = group.rows.map((row) => `
          <div class="slug-time-row" data-session-start="${row.sessionStart}">
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
          <article class="slug-day-card" ${group.sessionDate ? `data-session-date="${group.sessionDate}"` : ""}>
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

  function pruneGroupedRows(scope) {
    const now = new Date();
    scope.querySelectorAll(".slug-time-row").forEach((row) => {
      const start = inferSessionStart(row);
      if (start && start < now) {
        row.remove();
      }
    });

    scope.querySelectorAll(".slug-day-card").forEach((card) => {
      if (!card.querySelector(".slug-time-row")) {
        card.remove();
      }
    });
  }

  function pruneExpiredSessions(root) {
    const scopes = root && root.querySelectorAll ? root.querySelectorAll("[data-tabs]") : [];
    scopes.forEach((scope) => {
      pruneDirectPills(scope);
      groupSessionsByDay(scope);
      pruneGroupedRows(scope);
      syncScopeVisibility(scope);
    });
  }

  function activateTab(scope, trigger) {
    if (!scope || !trigger || trigger.hidden) return;
    const targetSelector = trigger.getAttribute("data-tab-target");
    if (!targetSelector) return;

    const panel = scope.querySelector(targetSelector);
    if (!panel || panel.hidden) return;

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
      const active = scope.querySelector(".tab-btn.active:not([hidden]), .slug-quick-pick.active:not([hidden]), .tab-panel.active:not([hidden])");
      if (!active) {
        const fallback = firstVisibleTrigger(scope);
        if (fallback) activateTab(scope, fallback);
        return;
      }

      if (active.matches(".tab-panel")) {
        const trigger = scope.querySelector(`[data-tab-target="#${active.id}"]`);
        if (trigger && !trigger.hidden) {
          activateTab(scope, trigger);
          return;
        }
      }

      if (!active.hidden) {
        activateTab(scope, active);
        return;
      }

      const fallback = firstVisibleTrigger(scope);
      if (fallback) activateTab(scope, fallback);
    });
  }

  function boot() {
    pruneExpiredSessions(document);
    initializeScopes();
    activateProgramFromQuery();
  }

  window.pruneExpiredSessions = window.pruneExpiredSessions || pruneExpiredSessions;

  bindTriggers();
  if (document.readyState === "loading") {
    window.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
