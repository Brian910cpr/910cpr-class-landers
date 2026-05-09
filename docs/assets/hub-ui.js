(function () {
  const EMERGENCY_SETTINGS_URL = "/data/site-emergency-settings.json";
  const DEFAULT_EMERGENCY_SETTINGS = Object.freeze({
    version: 1,
    updated_at: "",
    updated_by: "",
    note: "",
    emergency: {
      enabled: false,
      approved_page_groups: {
        hubs: true,
        home: false,
        course_landers: false,
        legacy_pages: false,
      },
      outage_banner: {
        enabled: false,
        title: "Our schedule platform is experiencing technical difficulties",
        lines: [
          "Classes listed on this page will still be held.",
          "If registration does not load, email us and we will help manually.",
        ],
      },
      hub_email_fallback: {
        enabled: false,
        email: "info@910cpr.com",
        button_label: "Email Us To Register",
      },
    },
  });
  const EMPTY_FALLBACK_TITLE = "No selected times showing here, but you still have options.";
  const EMPTY_FALLBACK_BODY = "View the full schedule for additional dates, request a class time, or ask about on-site training for your team.";
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

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function encodeMailto(value) {
    return encodeURIComponent(String(value || "")).replace(/%20/g, "+");
  }

  function isPlainObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function normalizeEmergencySettings(value) {
    if (!isPlainObject(value) || !isPlainObject(value.emergency)) return DEFAULT_EMERGENCY_SETTINGS;

    const emergency = value.emergency;
    const approved = isPlainObject(emergency.approved_page_groups) ? emergency.approved_page_groups : {};
    const banner = isPlainObject(emergency.outage_banner) ? emergency.outage_banner : {};
    const fallback = isPlainObject(emergency.hub_email_fallback) ? emergency.hub_email_fallback : {};

    return {
      version: Number(value.version) || DEFAULT_EMERGENCY_SETTINGS.version,
      updated_at: typeof value.updated_at === "string" ? value.updated_at : "",
      updated_by: typeof value.updated_by === "string" ? value.updated_by : "",
      note: typeof value.note === "string" ? value.note : "",
      emergency: {
        enabled: emergency.enabled === true,
        approved_page_groups: {
          hubs: approved.hubs === true,
          home: approved.home === true,
          course_landers: approved.course_landers === true,
          legacy_pages: approved.legacy_pages === true,
        },
        outage_banner: {
          enabled: banner.enabled === true,
          title: typeof banner.title === "string" ? banner.title : DEFAULT_EMERGENCY_SETTINGS.emergency.outage_banner.title,
          lines: Array.isArray(banner.lines) ? banner.lines.filter((line) => typeof line === "string") : [],
        },
        hub_email_fallback: {
          enabled: fallback.enabled === true,
          email: typeof fallback.email === "string" && fallback.email.trim()
            ? fallback.email.trim()
            : DEFAULT_EMERGENCY_SETTINGS.emergency.hub_email_fallback.email,
          button_label: typeof fallback.button_label === "string" && fallback.button_label.trim()
            ? fallback.button_label.trim()
            : DEFAULT_EMERGENCY_SETTINGS.emergency.hub_email_fallback.button_label,
        },
      },
    };
  }

  function emergencyAppliesToHubs(settings) {
    const emergency = (settings || DEFAULT_EMERGENCY_SETTINGS).emergency || {};
    const approved = emergency.approved_page_groups || {};
    return emergency.enabled === true && approved.hubs === true;
  }

  function outageBannerEnabled(settings) {
    const emergency = (settings || DEFAULT_EMERGENCY_SETTINGS).emergency || {};
    return emergencyAppliesToHubs(settings) && emergency.outage_banner && emergency.outage_banner.enabled === true;
  }

  function hubEmailFallbackEnabled(settings) {
    const emergency = (settings || DEFAULT_EMERGENCY_SETTINGS).emergency || {};
    return emergencyAppliesToHubs(settings) && emergency.hub_email_fallback && emergency.hub_email_fallback.enabled === true;
  }

  function isEmergencyFallbackLabel(value) {
    return String(value || "").trim().toLowerCase() === "email us to register";
  }

  function normalButtonLabel(button) {
    const existing = button.getAttribute("data-normal-label");
    if (existing && !isEmergencyFallbackLabel(existing)) return existing;
    const current = button.textContent.trim();
    if (isEmergencyFallbackLabel(current)) return sessionIdForButton(button) ? "Book Seat" : current;
    return current || (sessionIdForButton(button) ? "Book Seat" : "Register");
  }

  function loadEmergencySettings() {
    return fetch(EMERGENCY_SETTINGS_URL, { cache: "no-store" })
      .then((response) => {
        if (!response.ok) throw new Error("Emergency settings unavailable");
        return response.json();
      })
      .then(normalizeEmergencySettings)
      .catch(() => DEFAULT_EMERGENCY_SETTINGS);
  }

  function visibleText(node) {
    return node ? node.textContent.replace(/\s+/g, " ").trim() : "";
  }

  function firstTimeChip(scope) {
    if (!scope) return "";
    return visibleText(Array.from(scope.querySelectorAll(".slug-pill-chip")).find((chip) => {
      return !chip.classList.contains("slug-pill-chip-location")
        && !chip.classList.contains("slug-pill-chip-format")
        && !chip.classList.contains("slug-pill-chip-family")
        && !chip.classList.contains("slug-pill-chip-momentum");
    }));
  }

  function formatClock(date) {
    if (!(date instanceof Date) || Number.isNaN(date.getTime())) return "";
    return date.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  }

  function parseOptionalDate(value) {
    if (!value) return null;
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  function sessionElementForButton(button) {
    return button.closest(".slug-time-row") || button.closest(".slug-pill");
  }

  function courseNameForButton(button) {
    const row = button.closest(".slug-time-row");
    const pill = button.closest(".slug-pill");
    const panel = button.closest(".tab-panel");
    return (
      visibleText(row && row.querySelector(".slug-time-subtitle")) ||
      visibleText(pill && pill.querySelector(".slug-pill-subtitle")) ||
      visibleText(panel && panel.querySelector("h2")) ||
      document.title.replace(/\s*\|\s*910CPR\s*$/i, "").trim() ||
      "910CPR Class"
    );
  }

  function dateForButton(button) {
    const dayCard = button.closest(".slug-day-card");
    const pill = button.closest(".slug-pill");
    return (
      visibleText(dayCard && dayCard.querySelector(".slug-day-title")) ||
      visibleText(pill && pill.querySelector(".slug-pill-title")) ||
      button.getAttribute("data-session-date") ||
      ""
    );
  }

  function timeForButton(button) {
    const row = button.closest(".slug-time-row");
    const pill = button.closest(".slug-pill");
    const sessionElement = sessionElementForButton(button);
    const visibleTime = firstTimeChip(row || pill);
    if (visibleTime && /\bto\b/i.test(visibleTime)) return visibleTime;

    const start = parseOptionalDate(
      button.getAttribute("data-session-start") ||
      (sessionElement && sessionElement.getAttribute("data-session-start")) ||
      (sessionElement && sessionElement.getAttribute("data-start"))
    );
    const end = parseOptionalDate(
      button.getAttribute("data-session-end") ||
      (sessionElement && sessionElement.getAttribute("data-session-end")) ||
      (sessionElement && sessionElement.getAttribute("data-end"))
    );
    if (start && end) return `${formatClock(start)} to ${formatClock(end)}`;
    return visibleTime || (start ? formatClock(start) : "");
  }

  function locationForButton(button) {
    const row = button.closest(".slug-time-row");
    const pill = button.closest(".slug-pill");
    return (
      visibleText(row && row.querySelector(".slug-pill-chip-location")) ||
      visibleText(pill && pill.querySelector(".slug-pill-chip-location")) ||
      ""
    );
  }

  function sessionIdForButton(button) {
    const row = button.closest(".slug-time-row");
    const pill = button.closest(".slug-pill");
    return (
      button.getAttribute("data-session-id") ||
      (row && row.getAttribute("data-session-id")) ||
      (pill && pill.getAttribute("data-session-id")) ||
      ""
    );
  }

  function setCuratedOfferState(card, open) {
    if (!card) return;
    const button = card.querySelector("[data-curated-offer-toggle]");
    const body = card.querySelector("[data-curated-offer-body]");
    if (!button || !body) return;

    card.classList.toggle("is-open", open);
    button.setAttribute("aria-expanded", open ? "true" : "false");

    if (open) {
      body.hidden = false;
      body.style.maxHeight = `${body.scrollHeight}px`;
      body.setAttribute("data-open", "true");
      return;
    }

    body.style.maxHeight = `${body.scrollHeight}px`;
    window.requestAnimationFrame(() => {
      body.style.maxHeight = "0px";
      body.removeAttribute("data-open");
    });
  }

  function closeCuratedOfferBody(body) {
    if (!body || body.getAttribute("data-open") === "true") return;
    body.hidden = true;
  }

  function bindCuratedOffers() {
    document.querySelectorAll("[data-curated-offers]").forEach((section) => {
      const cards = Array.from(section.querySelectorAll(".curated-offer-card"));
      cards.forEach((card, index) => {
        const button = card.querySelector("[data-curated-offer-toggle]");
        const body = card.querySelector("[data-curated-offer-body]");
        if (!button || !body || button.dataset.curatedOfferBound === "true") return;

        button.dataset.curatedOfferBound = "true";
        body.addEventListener("transitionend", () => closeCuratedOfferBody(body));
        setCuratedOfferState(card, index === 0);

        button.addEventListener("click", () => {
          const shouldOpen = button.getAttribute("aria-expanded") !== "true";
          cards.forEach((item) => setCuratedOfferState(item, item === card && shouldOpen));
        });
      });
    });
  }

  function refreshCuratedOfferHeights(root) {
    const scope = root && root.querySelectorAll ? root : document;
    scope.querySelectorAll(".curated-offer-card.is-open [data-curated-offer-body]").forEach((body) => {
      body.style.maxHeight = `${body.scrollHeight}px`;
    });
  }

  function buildEmergencyMailto(button, settings) {
    const course = courseNameForButton(button);
    const date = dateForButton(button);
    const time = timeForButton(button);
    const location = locationForButton(button);
    const sessionId = sessionIdForButton(button);
    const pageUrl = window.location.href;
    const dateTime = [date, time].filter(Boolean).join(" ");
    const subject = `910CPR Registration Help - ${course} - ${dateTime}`.trim();
    const body = [
      "Hi 910CPR,",
      "",
      "I would like help registering for this class:",
      "",
      `Class: ${course}`,
      `Date: ${date}`,
      `Time: ${time}`,
      `Location: ${location}`,
      `Session ID: ${sessionId}`,
      `Page: ${pageUrl}`,
      "",
      "My name:",
      "My phone number:",
      "",
      "Thank you.",
    ].join("\n");

    const email = settings.emergency.hub_email_fallback.email;
    return `mailto:${email}?subject=${encodeMailto(subject)}&body=${encodeMailto(body)}`;
  }

  function applyEmergencyEmailFallback(root, settings) {
    const scope = root && root.querySelectorAll ? root : document;
    scope.querySelectorAll(".slug-hub-shell .slug-pill-actions a.button, .slug-hub-shell .slug-time-actions a.button").forEach((button) => {
      const href = button.getAttribute("href") || "";
      const originalHref = button.getAttribute("data-original-href") || "";
      if (!button.getAttribute("data-normal-label")) {
        button.setAttribute("data-normal-label", normalButtonLabel(button));
      }
      if (!hubEmailFallbackEnabled(settings)) {
        if (originalHref && href.startsWith("mailto:")) {
          button.setAttribute("href", originalHref);
        }
        button.textContent = normalButtonLabel(button);
        button.removeAttribute("data-emergency-email-fallback");
        return;
      }
      if (!sessionIdForButton(button)) return;
      if (!button.getAttribute("data-original-href") && href && !href.startsWith("mailto:")) {
        button.setAttribute("data-original-href", href);
      }
      button.textContent = settings.emergency.hub_email_fallback.button_label;
      button.setAttribute("href", buildEmergencyMailto(button, settings));
      button.setAttribute("data-emergency-email-fallback", "true");
    });
  }

  function syncEmergencyOutageBanner(settings) {
    const existing = document.querySelector("[data-emergency-outage-banner], .slug-hub-shell .slug-emergency-alert");
    if (!outageBannerEnabled(settings)) {
      if (existing) existing.remove();
      return;
    }

    const bannerSettings = settings.emergency.outage_banner;
    const banner = existing || document.createElement("section");
    banner.className = "slug-emergency-alert";
    banner.setAttribute("role", "status");
    banner.setAttribute("aria-live", "polite");
    banner.setAttribute("data-emergency-outage-banner", "true");
    banner.innerHTML = `<h2>${escapeHtml(bannerSettings.title)}</h2>${bannerSettings.lines.map((line) => `<p>${escapeHtml(line)}</p>`).join("")}`;

    if (existing) return;
    const hero = document.querySelector(".slug-hub-shell .slug-hero");
    const shell = document.querySelector(".slug-hub-shell");
    if (hero && hero.parentNode) {
      hero.insertAdjacentElement("afterend", banner);
    } else if (shell) {
      shell.prepend(banner);
    }
  }

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
      fallback.innerHTML = `<strong>${EMPTY_FALLBACK_TITLE}</strong><p>${EMPTY_FALLBACK_BODY}</p><div class="slug-empty-actions"><a class="button primary" href="/index.html">View Full Schedule</a><a class="button secondary" href="/request_group_session.html">Request On-Site Training</a></div>`;
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
      const banner = panel.getAttribute("data-banner");
      let fullScheduleUrl = "/index.html";
      try {
        const parsed = JSON.parse(banner || "{}");
        fullScheduleUrl = parsed.url || fullScheduleUrl;
      } catch (error) {}
      list.innerHTML = (
        "<div class='slug-empty'>"
        + `<strong>${EMPTY_FALLBACK_TITLE}</strong>`
        + `<p>${EMPTY_FALLBACK_BODY}</p>`
        + "<div class='slug-empty-actions'>"
        + `<a class='button primary' href='${escapeHtml(fullScheduleUrl)}'>View Full Schedule</a>`
        + "<a class='button secondary' href='/request_group_session.html'>Request On-Site Training</a>"
        + "</div>"
        + "</div>"
      );
    }
  }

  function syncPanelInventory(panel) {
    const kicker = panel ? panel.querySelector(".slug-panel-kicker") : null;
    if (!kicker) return;
    kicker.textContent = "Start here, more dates available";
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
    scope.classList.add("slug-tabs-ready");

    const panels = Array.from(scope.querySelectorAll(".tab-panel"));
    const visibleTargets = [];

    panels.forEach((panel) => {
      ensurePanelEmptyState(panel);
      syncPanelInventory(panel);

      const targetSelector = `#${panel.id}`;
      const count = countVisibleSessions(panel);
      const hasSessions = panelHasSessions(panel);
      const keepEmptyTab = panel.getAttribute("data-keep-empty-tab") === "true";
      const shouldShowPanel = hasSessions || keepEmptyTab;
      panel.hidden = !shouldShowPanel;
      panel.classList.toggle("is-empty-panel", !hasSessions);
      syncTriggerInventory(targetSelector, count);

      getTriggersForTarget(targetSelector).forEach((trigger) => {
        trigger.hidden = !shouldShowPanel;
        trigger.classList.toggle("is-hidden", !shouldShowPanel);
      });

      if (shouldShowPanel) visibleTargets.push(targetSelector);
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
      originalHref: buttonNode ? (buttonNode.getAttribute("data-original-href") || buttonNode.getAttribute("href") || "") : "",
      buttonText: buttonNode ? buttonNode.textContent.trim() : "Register",
      hint: hintNode ? hintNode.textContent.trim() : "Reserve this class time",
      sessionId: pill.getAttribute("data-session-id") || "",
      sessionStart: start ? start.toISOString() : "",
      sessionEnd: pill.getAttribute("data-end") || pill.getAttribute("data-session-end") || "",
      sessionDate: start ? formatSessionDateKey(start) : "",
      certifyingBody: pill.getAttribute("data-certifying-body") || "",
      certifyingLogo: pill.getAttribute("data-certifying-logo") || "",
    };
  }

  function groupCertifyingLogos(rows) {
    const byBody = new Map();
    rows.forEach((row) => {
      if (!row.certifyingBody || !row.certifyingLogo || byBody.has(row.certifyingBody)) return;
      byBody.set(row.certifyingBody, row.certifyingLogo);
    });
    return Array.from(byBody, ([body, logo]) => ({ body, logo }));
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
          <div class="slug-time-row" data-session-id="${escapeHtml(row.sessionId)}" data-session-start="${escapeHtml(row.sessionStart)}" data-session-end="${escapeHtml(row.sessionEnd)}">
            <div class="slug-time-copy">
              <div class="slug-pill-meta-row slug-time-meta">
                ${row.time ? `<span class="slug-pill-chip">${escapeHtml(row.time)}</span>` : ""}
                ${row.location ? `<span class="slug-pill-chip slug-pill-chip-location">${escapeHtml(row.location)}</span>` : ""}
              </div>
              ${row.subtitle ? `<div class="slug-time-subtitle">${escapeHtml(row.subtitle)}</div>` : ""}
            </div>
            <div class="slug-time-actions">
              <div class="slug-pill-hint">${escapeHtml(row.hint)}</div>
              ${row.href ? `<a class="button small primary" href="${escapeHtml(row.href)}" data-original-href="${escapeHtml(row.originalHref || row.href)}" data-session-id="${escapeHtml(row.sessionId)}" data-session-start="${escapeHtml(row.sessionStart)}" data-session-end="${escapeHtml(row.sessionEnd)}">${escapeHtml(row.buttonText)}</a>` : ""}
            </div>
          </div>
        `).join("");
        const certLogos = groupCertifyingLogos(group.rows);
        const certMarkup = certLogos.length ? `
          <div class="slug-day-cert-logos" aria-label="Certifying body">
            ${certLogos.map((item) => `<img class="slug-day-cert-logo" src="${escapeHtml(item.logo)}" alt="" loading="lazy" data-certifying-body="${escapeHtml(item.body)}">`).join("")}
          </div>
        ` : "";
        const certAttr = certLogos.length === 1 ? ` data-certifying-body="${escapeHtml(certLogos[0].body)}"` : "";

        return `
          <article class="slug-day-card"${group.sessionDate ? ` data-session-date="${group.sessionDate}"` : ""}${certAttr}>
            ${certMarkup}
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

  function boot(settings) {
    pruneExpiredSessions(document);
    bindCuratedOffers();
    initializeScopes();
    activateProgramFromQuery();
    syncEmergencyOutageBanner(settings);
    applyEmergencyEmailFallback(document, settings);
    refreshCuratedOfferHeights(document);
  }

  window.pruneExpiredSessions = window.pruneExpiredSessions || pruneExpiredSessions;
  window.applyEmergencyEmailFallback = function (root, settings) {
    applyEmergencyEmailFallback(root || document, normalizeEmergencySettings(settings || DEFAULT_EMERGENCY_SETTINGS));
  };

  bindTriggers();
  window.addEventListener("resize", () => refreshCuratedOfferHeights(document));
  if (document.readyState === "loading") {
    window.addEventListener("DOMContentLoaded", () => {
      loadEmergencySettings().then(boot);
    });
  } else {
    loadEmergencySettings().then(boot);
  }
})();
