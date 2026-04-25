(function () {
  const sectionsRoot = document.querySelector("[data-home-sections]");
  if (!sectionsRoot) return;

  const MAX_SESSIONS = 6;
  const SECTION_CONFIG = [
    {
      id: "bls",
      title: "BLS",
      audience: "For healthcare workers, dental teams, nursing students, and clinical staff who need professional-level CPR certification.",
      fullScheduleUrl: "/bls.html",
      fullScheduleLabel: "See full schedule",
      emptyLabel: "No upcoming public BLS dates are listed right now.",
    },
    {
      id: "acls",
      title: "ACLS",
      audience: "For nurses, paramedics, respiratory therapists, and other clinicians who need advanced cardiac life support training.",
      fullScheduleUrl: "/acls.html",
      fullScheduleLabel: "See full schedule",
      emptyLabel: "No upcoming public ACLS dates are listed right now.",
    },
    {
      id: "pals",
      title: "PALS",
      audience: "For providers who care for infants and children and need pediatric advanced life support training.",
      fullScheduleUrl: "/pals.html",
      fullScheduleLabel: "See full schedule",
      emptyLabel: "No upcoming public PALS dates are listed right now.",
    },
    {
      id: "heartsaver",
      title: "Heartsaver",
      audience: "For workplaces, schools, childcare teams, fitness staff, and general responders who need CPR, AED, and first aid training.",
      fullScheduleUrl: "/heartsaver.html",
      fullScheduleLabel: "See full schedule",
      emptyLabel: "No upcoming public Heartsaver dates are listed right now.",
    },
    {
      id: "uscg",
      title: "USCG Elementary First Aid",
      audience: "For mariners, crews, and maritime employers who need the USCG-aligned first aid and CPR option.",
      fullScheduleUrl: "/uscg-elementary-first-aid-cpr.html",
      fullScheduleLabel: "See full schedule",
      emptyLabel: "No upcoming public USCG dates are listed right now.",
    },
    {
      id: "group",
      title: "Group / Onsite Training",
      audience: "For offices, clinics, schools, churches, and employers who want private training coordinated for a team.",
      fullScheduleUrl: "/group-training.html",
      fullScheduleLabel: "See full schedule",
      emptyLabel: "No current public preview dates are available for group-training matches.",
    },
  ];

  const EASTERN_TIMEZONE = "America/New_York";
  const dtfMonth = new Intl.DateTimeFormat("en-US", { month: "short", timeZone: EASTERN_TIMEZONE });
  const dtfDay = new Intl.DateTimeFormat("en-US", { day: "numeric", timeZone: EASTERN_TIMEZONE });
  const dtfWeekday = new Intl.DateTimeFormat("en-US", { weekday: "short", timeZone: EASTERN_TIMEZONE });
  const dtfDateLine = new Intl.DateTimeFormat("en-US", { weekday: "long", month: "long", day: "numeric", timeZone: EASTERN_TIMEZONE });
  const dtfTime = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit", hour12: true, timeZone: EASTERN_TIMEZONE });

  function stripHtml(value) {
    return String(value || "")
      .replace(/<br\s*\/?>/gi, " ")
      .replace(/<[^>]+>/g, " ")
      .replace(/&nbsp;/gi, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function normalizeSpace(value) {
    return stripHtml(value).replace(/\s+/g, " ").trim();
  }

  function parseDate(value) {
    if (!value) return null;
    const raw = String(value).trim();
    const hasOffset = /(?:Z|[+-]\d{2}:\d{2})$/.test(raw);
    const naiveIso = raw.includes("T") ? raw : raw.replace(" ", "T");
    const isoCandidate = hasOffset ? naiveIso : `${naiveIso}-04:00`;
    const parsed = new Date(isoCandidate);
    if (!Number.isNaN(parsed.getTime())) return parsed;
    const fallback = new Date(raw);
    return Number.isNaN(fallback.getTime()) ? null : fallback;
  }

  function cleanLocation(raw) {
    const text = normalizeSpace(raw);
    if (!text) return "";
    const withoutPrefix = text.startsWith("::") ? text.slice(2).trim() : text;
    const doubleColonIndex = withoutPrefix.lastIndexOf("::");
    return (doubleColonIndex >= 0 ? withoutPrefix.slice(doubleColonIndex + 2) : withoutPrefix).trim();
  }

  function isApprovedRawLocation(raw) {
    return normalizeSpace(raw).startsWith("::");
  }

  function keyPart(value) {
    return normalizeSpace(value).toLowerCase();
  }

  function inferSectionAndSubtype(name, familyHint) {
    const text = `${normalizeSpace(name)} ${normalizeSpace(familyHint)}`.toUpperCase();
    if (!text) return null;
    if (text.includes("INSTRUCTOR")) return null;
    if (text.includes("USCG") || text.includes("ELEMENTARY FIRST AID")) {
      return { sectionId: "uscg", subtype: "USCG" };
    }
    if (text.includes("PALS")) {
      return { sectionId: "pals", subtype: text.includes("HEARTCODE") ? "HeartCode Skills" : text.includes("RENEW") ? "Renewal" : "Provider" };
    }
    if (text.includes("ACLS")) {
      return { sectionId: "acls", subtype: text.includes("HEARTCODE") ? "HeartCode Skills" : text.includes("RENEW") ? "Renewal" : "Provider" };
    }
    if (text.includes("HEARTSAVER")) {
      if (text.includes("PEDIATRIC")) return { sectionId: "heartsaver", subtype: "Pediatric First Aid" };
      if (text.includes("CPR AED") && !text.includes("FIRST AID")) return { sectionId: "heartsaver", subtype: "CPR + AED" };
      return { sectionId: "heartsaver", subtype: "First Aid + CPR + AED" };
    }
    if (text.includes("BLS")) {
      return { sectionId: "bls", subtype: text.includes("HEARTCODE") ? "HeartCode Skills" : text.includes("RENEW") ? "Renewal" : "Provider" };
    }
    return null;
  }

  function recordKey(start, location, sectionId, subtype) {
    return [startKey(start), keyPart(location), keyPart(sectionId), keyPart(subtype)].join("|");
  }

  function startKey(value) {
    const date = value instanceof Date ? value : parseDate(value);
    if (!date) return "";
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: EASTERN_TIMEZONE,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).formatToParts(date);
    const lookup = Object.fromEntries(parts.filter((part) => part.type !== "literal").map((part) => [part.type, part.value]));
    return `${lookup.year}-${lookup.month}-${lookup.day}T${lookup.hour}:${lookup.minute}`;
  }

  function buildPrimarySessions(publicRows) {
    return publicRows
      .map((row) => {
        const course = row.course || {};
        const title = row.title || {};
        const name = normalizeSpace(course.name || title.name || row.title || row.course);
        const familyHint = normalizeSpace(course.family || title.family || course.card_type || title.card_type || course.discipline || title.discipline);
        const match = inferSectionAndSubtype(name, familyHint);
        if (!match) return null;
        return {
          name,
          sectionId: match.sectionId,
          subtype: match.subtype,
          start: row.start,
          startDate: parseDate(row.start),
          locationRaw: row.location,
          locationClean: cleanLocation(row.location),
          source: "public-primary",
        };
      })
      .filter(Boolean);
  }

  function buildEnrichmentMap(legacyPublic, futureSchedule) {
    const map = new Map();

    function pushRecord(base) {
      const match = inferSectionAndSubtype(base.name, base.familyHint);
      if (!match) return;
      if (!base.locationRaw || !isApprovedRawLocation(base.locationRaw)) return;
      if (!base.registerUrl) return;
      const startDate = parseDate(base.start);
      if (!startDate) return;
      const key = recordKey(base.start, cleanLocation(base.locationRaw), match.sectionId, match.subtype);
      const current = map.get(key);
      const record = {
        registerUrl: base.registerUrl,
        sectionId: match.sectionId,
        subtype: match.subtype,
        start: base.start,
        startDate,
        locationRaw: base.locationRaw,
        locationClean: cleanLocation(base.locationRaw),
        name: base.name,
      };
      if (!current || current.startDate > record.startDate) {
        map.set(key, record);
      }
    }

    (legacyPublic.sessions || []).forEach((row) => {
      pushRecord({
        name: normalizeSpace(row.course || row.title),
        familyHint: "",
        start: row.start,
        locationRaw: row.location,
        registerUrl: row.register_url,
      });
    });

    (futureSchedule.sessions || []).forEach((row) => {
      const seats = Number(row.available_seats || 0);
      if (row.session_status !== "active" || row.is_full || seats <= 0) return;
      pushRecord({
        name: normalizeSpace(`${row.course_name} ${row.course_subtitle || ""}`),
        familyHint: row.course_code || "",
        start: row.start_at,
        locationRaw: row.location_display || row.location_name,
        registerUrl: row.registration_url,
      });
    });

    return map;
  }

  function enrichSessions(primarySessions, enrichmentMap) {
    const now = new Date();
    const seen = new Set();

    return primarySessions
      .map((session) => {
        if (!session.startDate || session.startDate < now) return null;
        const key = recordKey(session.start, session.locationClean, session.sectionId, session.subtype);
        const enrichment = enrichmentMap.get(key);
        if (!enrichment) return null;
        const dedupeKey = `${key}|${enrichment.registerUrl}`;
        if (seen.has(dedupeKey)) return null;
        seen.add(dedupeKey);
        return {
          ...session,
          start: enrichment.start,
          startDate: enrichment.startDate,
          locationRaw: enrichment.locationRaw,
          locationClean: enrichment.locationClean || session.locationClean,
          registerUrl: enrichment.registerUrl,
          name: enrichment.name || session.name,
        };
      })
      .filter(Boolean)
      .sort((a, b) => a.startDate - b.startDate);
  }

  function buildGroupedSessions(enrichedSessions) {
    const groups = new Map(SECTION_CONFIG.map((section) => [section.id, []]));
    enrichedSessions.forEach((session) => {
      const bucket = groups.get(session.sectionId);
      if (bucket) bucket.push(session);
    });

    const groupPreview = [];
    ["bls", "heartsaver", "acls", "pals", "uscg"].forEach((sectionId) => {
      const source = groups.get(sectionId) || [];
      source.slice(0, 2).forEach((item) => {
        groupPreview.push({
          ...item,
          subtype: `${SECTION_CONFIG.find((section) => section.id === sectionId).title} public option`,
        });
      });
    });

    groups.set("group", groupPreview.sort((a, b) => a.startDate - b.startDate));
    return groups;
  }

  function monthLabel(date) {
    return dtfMonth.format(date).toUpperCase();
  }

  function dayLabel(date) {
    return dtfDay.format(date);
  }

  function weekdayLabel(date) {
    return dtfWeekday.format(date);
  }

  function dateLine(date) {
    return dtfDateLine.format(date);
  }

  function timeLine(date) {
    return dtfTime.format(date);
  }

  function pillHref(section, session) {
    if (section.id === "group") {
      const params = new URLSearchParams({ program: section.title === "Group / Onsite Training" ? "BLS On-Site" : section.title });
      if (session.sectionId === "heartsaver") params.set("program", "First Aid / CPR / AED");
      if (session.sectionId === "acls") params.set("program", "ACLS");
      if (session.sectionId === "pals") params.set("program", "PALS");
      if (session.sectionId === "uscg") params.set("program", "USCG Elementary First Aid | CPR");
      if (session.sectionId === "bls") params.set("program", "BLS On-Site");
      return `/request_group_session.html?${params.toString()}`;
    }
    return session.registerUrl || section.fullScheduleUrl;
  }

  function pillCtaLabel(section) {
    return section.id === "group" ? "Request team training" : "Book now";
  }

  function renderPill(section, session) {
    const subtype = session.subtype ? `<div class="finder-pill-subtitle">${escapeHtml(session.subtype)}</div>` : "";
    return `
      <a class="finder-pill-link" href="${escapeAttribute(pillHref(section, session))}">
        <article class="slug-pill finder-pill" data-session-start="${escapeAttribute(session.startDate ? session.startDate.toISOString() : "")}">
          <div class="slug-pill-date">
            <div class="slug-pill-month">${monthLabel(session.startDate)}</div>
            <div class="slug-pill-day">${dayLabel(session.startDate)}</div>
            <div class="slug-pill-weekday">${weekdayLabel(session.startDate)}</div>
          </div>
          <div class="slug-pill-main">
            <div class="slug-pill-title">${escapeHtml(dateLine(session.startDate))}</div>
            <div class="slug-pill-meta">${escapeHtml(timeLine(session.startDate))} · ${escapeHtml(session.locationClean || "Location TBA")}</div>
            ${subtype}
          </div>
          <div class="finder-pill-side">${pillCtaLabel(section)}</div>
        </article>
      </a>
    `;
  }

  function renderSection(section, sessions) {
    const preview = sessions.slice(0, MAX_SESSIONS);
    const content = preview.length
      ? preview.map((session) => renderPill(section, session)).join("")
      : `
        <div class="finder-empty">
          <strong>${escapeHtml(section.emptyLabel)}</strong>
          <p>Use the full schedule page for this category or check back after the next schedule refresh.</p>
        </div>
      `;

    return `
      <section class="finder-card" id="${escapeAttribute(section.id)}">
        <div class="finder-card-head">
          <div>
            <h3>${escapeHtml(section.title)}</h3>
            <p class="finder-card-copy">${escapeHtml(section.audience)}</p>
          </div>
          <a class="button secondary" href="${escapeAttribute(section.fullScheduleUrl)}">${escapeHtml(section.fullScheduleLabel)}</a>
        </div>
        <div class="finder-pills">
          ${content}
        </div>
      </section>
    `;
  }

  function renderError() {
    sectionsRoot.innerHTML = `
      <article class="finder-card">
        <div class="finder-card-head">
          <div>
            <h3>Live schedule unavailable</h3>
            <p class="finder-card-copy">The homepage class finder could not load the current schedule data.</p>
          </div>
        </div>
        <div class="finder-empty">
          <strong>Use the hub pages below while we reload the feed.</strong>
          <p><a href="/bls.html">BLS</a> · <a href="/acls.html">ACLS</a> · <a href="/pals.html">PALS</a> · <a href="/heartsaver.html">Heartsaver</a> · <a href="/uscg-elementary-first-aid-cpr.html">USCG</a> · <a href="/group-training.html">Group Training</a></p>
        </div>
      </article>
    `;
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function escapeAttribute(value) {
    return escapeHtml(value);
  }

  Promise.all([
    fetch("/data/public_schedule.json").then((response) => response.json()),
    fetch("/public_schedule.json").then((response) => response.json()),
    fetch("/data/schedule_future.json").then((response) => response.json()),
  ])
    .then(([primaryFeed, legacyPublic, futureSchedule]) => {
      const primarySessions = buildPrimarySessions(Array.isArray(primaryFeed) ? primaryFeed : []);
      const enrichmentMap = buildEnrichmentMap(legacyPublic || {}, futureSchedule || {});
      const enrichedSessions = enrichSessions(primarySessions, enrichmentMap);
      const groupedSessions = buildGroupedSessions(enrichedSessions);
      sectionsRoot.innerHTML = SECTION_CONFIG.map((section) => renderSection(section, groupedSessions.get(section.id) || [])).join("");
    })
    .catch((error) => {
      console.error(error);
      renderError();
    });
})();
