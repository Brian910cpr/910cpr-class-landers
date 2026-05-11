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
      fullScheduleLabel: "See all BLS dates",
      emptyLabel: "No BLS dates are posted here right now.",
    },
    {
      id: "acls",
      title: "ACLS",
      audience: "For nurses, paramedics, respiratory therapists, and other clinicians who need advanced cardiac life support training.",
      fullScheduleUrl: "/acls.html",
      fullScheduleLabel: "See all ACLS dates",
      emptyLabel: "No ACLS dates are posted here right now.",
    },
    {
      id: "pals",
      title: "PALS",
      audience: "For providers who care for infants and children and need pediatric advanced life support training.",
      fullScheduleUrl: "/pals.html",
      fullScheduleLabel: "See all PALS dates",
      emptyLabel: "No PALS dates are posted here right now.",
    },
    {
      id: "heartsaver",
      title: "Heartsaver",
      audience: "For workplaces, schools, childcare teams, fitness staff, and general responders who need CPR, AED, and first aid training.",
      fullScheduleUrl: "/heartsaver.html",
      fullScheduleLabel: "See all Heartsaver dates",
      emptyLabel: "No Heartsaver dates are posted here right now.",
    },
    {
      id: "arc",
      title: "American Red Cross",
      audience: "For students whose employer, school, or program specifically requests Red Cross certification.",
      fullScheduleUrl: "/arc.html",
      fullScheduleLabel: "Compare ARC options",
      emptyLabel: "No ARC dates are posted here right now.",
    },
    {
      id: "hsi",
      title: "HSI",
      audience: "For workplaces, schools, and professional requirements that accept or request HSI certification.",
      fullScheduleUrl: "/hsi.html",
      fullScheduleLabel: "Compare HSI options",
      emptyLabel: "No HSI dates are posted here right now.",
    },
    {
      id: "pediatric",
      title: "Pediatric First Aid CPR AED",
      audience: "For childcare providers, teachers, babysitters, foster parents, and caregivers of children.",
      fullScheduleUrl: "/heartsaver.html?program=Pediatric%20First%20Aid%20CPR%20AED%20Blended",
      fullScheduleLabel: "Blended dates",
      secondaryScheduleUrl: "/heartsaver.html?program=Pediatric%20First%20Aid%20CPR%20AED%20In-Person",
      secondaryScheduleLabel: "In-person dates",
      emptyLabel: "No Pediatric First Aid CPR AED dates are posted here right now.",
    },
    {
      id: "uscg",
      title: "USCG Elementary First Aid",
      audience: "For mariners, crews, and maritime employers who need the USCG-aligned first aid and CPR option.",
      fullScheduleUrl: "/uscg-elementary-first-aid-cpr.html",
      fullScheduleLabel: "See all USCG dates",
      emptyLabel: "No USCG dates are posted here right now.",
    },
  ];

  const EASTERN_TIMEZONE = "America/New_York";
  const HEARTSAVER_SUBTYPE_ORDER = ["First Aid + CPR + AED", "CPR + AED"];
  const HEARTSAVER_SUBTYPE_COPY = {
    "First Aid + CPR + AED": "Best for general workplace first aid, CPR, and AED certification.",
    "Pediatric First Aid": "Best for childcare, camps, schools, and caregiver teams.",
    "CPR + AED": "Best when first aid is not required and CPR/AED only is enough.",
  };
  const dtfMonth = new Intl.DateTimeFormat("en-US", { month: "short", timeZone: EASTERN_TIMEZONE });
  const dtfDay = new Intl.DateTimeFormat("en-US", { day: "numeric", timeZone: EASTERN_TIMEZONE });
  const dtfWeekday = new Intl.DateTimeFormat("en-US", { weekday: "short", timeZone: EASTERN_TIMEZONE });
  const dtfDateLine = new Intl.DateTimeFormat("en-US", { weekday: "long", month: "long", day: "numeric", timeZone: EASTERN_TIMEZONE });
  const dtfTime = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit", hour12: true, timeZone: EASTERN_TIMEZONE });
  const COURSE_IMAGE_MAP = {
    bls: "/images/bls_general.png",
    acls: "/images/acls_general.png",
    pals: "/images/pals_general.png",
    heartsaver: "/images/heartsaver_general.png",
    arc: "/images/0arc.png",
    hsi: "/images/0hsi.png",
    pediatric: "/images/heartsaver_general.png",
    uscg: "/images/stripes.png",
    group: "/images/bls_general.png",
  };
  const COURSE_IMAGE_FALLBACK = "/images/bls_general.png";

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

  function isInstructorOnlyCourse(name, familyHint) {
    const text = `${normalizeSpace(name)} ${normalizeSpace(familyHint)}`.toUpperCase();
    if (!text) return false;
    return (
      /\bINSTRUCTOR\s+(?:COURSE|RENEWAL|UPDATE|ESSENTIALS)\b/.test(text) ||
      /\bINSTRUCTOR-LED\b/.test(text) === false && /\bAHA\s*-\s*.*\bINSTRUCTOR\b/.test(text)
    );
  }

  function inferSectionAndSubtype(name, familyHint) {
    const text = `${normalizeSpace(name)} ${normalizeSpace(familyHint)}`.toUpperCase();
    if (!text) return null;
    if (isInstructorOnlyCourse(name, familyHint)) return null;
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
      if (text.includes("PEDIATRIC") || text.includes("AHA_HS_PED_FA_CPR")) return { sectionId: "pediatric", subtype: inferFormatLabel(name, familyHint) || "Pediatric First Aid" };
      if ((text.includes("CPR AED") && !text.includes("FIRST AID")) || text.includes("344085")) return { sectionId: "heartsaver", subtype: "CPR + AED" };
      if (text.includes("329495") || text.includes("209809") || text.includes("AHA_HS_FA_CPR")) return { sectionId: "heartsaver", subtype: "First Aid + CPR + AED" };
      return { sectionId: "heartsaver", subtype: "First Aid + CPR + AED" };
    }
    if (text.includes("AMERICAN RED CROSS") || text.includes("RED CROSS") || text.includes("ARC_") || text.includes("ARC ")) {
      if (text.includes("FIRST AID")) return { sectionId: "arc", subtype: "First Aid + CPR + AED" };
      if (text.includes("CPR") && text.includes("AED")) return { sectionId: "arc", subtype: "CPR + AED" };
      if (text.includes("BLS")) return { sectionId: "arc", subtype: "BLS" };
      return { sectionId: "arc", subtype: "ARC option" };
    }
    if (text.includes("HSI") || text.includes("ASHI")) {
      if (text.includes("BLS") && text.includes("FIRST AID")) return { sectionId: "hsi", subtype: "BLS + First Aid" };
      if (text.includes("BLS") || text.includes("BASIC LIFE SUPPORT")) return { sectionId: "hsi", subtype: "BLS" };
      if (text.includes("FIRST AID")) return { sectionId: "hsi", subtype: "First Aid + CPR + AED" };
      if (text.includes("CPR") && text.includes("AED")) return { sectionId: "hsi", subtype: "CPR + AED" };
      return { sectionId: "hsi", subtype: "HSI option" };
    }
    if (text.includes("BLS")) {
      return { sectionId: "bls", subtype: text.includes("HEARTCODE") ? "HeartCode Skills" : text.includes("RENEW") ? "Renewal" : "Provider" };
    }
    return null;
  }

  function inferFormatLabel(name, familyHint) {
    const text = `${normalizeSpace(name)} ${normalizeSpace(familyHint)}`.toUpperCase();
    if (!text) return "";
    if (text.includes("HEARTCODE") || text.includes("ONLINE + SKILLS") || text.includes("ONLINE COURSE + IN-PERSON SKILLS") || text.includes("SKILLS SESSION") || text.includes("AHA_HS_FA_CPR_BL") || text.includes("AHA_HS_PED_FA_CPR_BL")) {
      return "Online + Skills";
    }
    if (text.includes("IN-PERSON") || text.includes("CLASSROOM") || text.includes("AHA_HS_FA_CPR_IP") || text.includes("AHA_BLS_IP") || text.includes("AHA_ACLS_PROVIDER") || text.includes("AHA_PALS_") || text.includes("ILT")) {
      return "In-Person";
    }
    return "";
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
          formatLabel: inferFormatLabel(name, familyHint),
          start: row.start,
          startDate: parseDate(row.start),
          locationRaw: row.location,
          locationClean: cleanLocation(row.location),
          source: "public-primary",
        };
      })
      .filter(Boolean);
  }

  function buildPrimarySessionsFromFuture(futureSchedule) {
    return (futureSchedule.sessions || [])
      .map((row) => {
        const seats = Number(row.available_seats || 0);
        if (row.session_status !== "active" || row.is_full || seats <= 0) return null;

        const name = normalizeSpace(`${row.course_name || ""} ${row.course_subtitle || ""}`);
        const familyHint = normalizeSpace(row.course_code || "");
        const match = inferSectionAndSubtype(name, familyHint);
        if (!match) return null;

        return {
          name,
          sectionId: match.sectionId,
          subtype: match.subtype,
          formatLabel: inferFormatLabel(name, familyHint),
          enrolledCount: Number(row.enrolled_count || row.registered_count || 0),
          start: row.start_at,
          startDate: parseDate(row.start_at),
          locationRaw: row.location_display || row.location_name,
          locationClean: cleanLocation(row.location_display || row.location_name),
          source: "future-primary",
        };
      })
      .filter(Boolean);
  }

  function dedupePrimarySessions(primarySessions) {
    const seen = new Set();
    return primarySessions.filter((session) => {
      const key = recordKey(session.start, session.locationClean, session.sectionId, session.subtype);
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
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
        formatLabel: inferFormatLabel(base.name, base.familyHint),
        enrolledCount: Number(base.enrolledCount || 0),
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
        enrolledCount: 0,
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
        enrolledCount: Number(row.enrolled_count || row.registered_count || 0),
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
          formatLabel: enrichment.formatLabel || session.formatLabel,
          enrolledCount: Math.max(Number(session.enrolledCount || 0), Number(enrichment.enrolledCount || 0)),
        };
      })
      .filter(Boolean)
      .sort((a, b) => {
        const enrolledDelta = Number(b.enrolledCount || 0) - Number(a.enrolledCount || 0);
        if (enrolledDelta !== 0) return enrolledDelta;
        if (a.sectionId === "heartsaver" && b.sectionId === "heartsaver") {
          const subtypeDelta = HEARTSAVER_SUBTYPE_ORDER.indexOf(a.subtype) - HEARTSAVER_SUBTYPE_ORDER.indexOf(b.subtype);
          if (subtypeDelta !== 0) return subtypeDelta;
          const formatDelta = (a.formatLabel || "").localeCompare(b.formatLabel || "");
          if (formatDelta !== 0) return formatDelta;
        }
        return a.startDate - b.startDate;
      });
  }

  function buildGroupedSessions(enrichedSessions) {
    const groups = new Map(SECTION_CONFIG.map((section) => [section.id, []]));
    enrichedSessions.forEach((session) => {
      const bucket = groups.get(session.sectionId);
      if (bucket) bucket.push(session);
    });

    const groupPreview = [];
    ["bls", "heartsaver", "pediatric", "acls", "pals", "arc", "hsi", "uscg"].forEach((sectionId) => {
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
    return session.registerUrl || section.fullScheduleUrl;
  }

  function pillCtaLabel(section) {
    return "Book now";
  }

  function pillImageSrc(section, session) {
    const sectionKey = (session.sectionId || section.id || "").toLowerCase();
    return COURSE_IMAGE_MAP[sectionKey] || COURSE_IMAGE_MAP[(section.id || "").toLowerCase()] || COURSE_IMAGE_FALLBACK;
  }

  function renderPill(section, session) {
    const chips = [];
    if (session.subtype) chips.push(`<span class="finder-pill-tag">${escapeHtml(session.subtype)}</span>`);
    if (session.formatLabel) chips.push(`<span class="finder-pill-tag finder-pill-tag-format">${escapeHtml(session.formatLabel)}</span>`);
    if (Number(session.enrolledCount || 0) >= 1) {
      chips.push(`<span class="finder-pill-tag finder-pill-tag-popular">${escapeHtml(Number(session.enrolledCount) === 1 ? "1 already enrolled" : `${Number(session.enrolledCount)} already enrolled`)}</span>`);
    }
    const metaTags = chips.length ? `<div class="finder-pill-tags">${chips.join("")}</div>` : "";
    const subtype = session.subtype ? `<div class="finder-pill-subtitle">${escapeHtml(session.name)}</div>` : "";
    return `
      <a class="finder-pill-link" href="${escapeAttribute(pillHref(section, session))}">
        <article class="slug-pill finder-pill" data-session-start="${escapeAttribute(session.startDate ? session.startDate.toISOString() : "")}">
          <div class="slug-pill-main">
            <div class="class-card-top-row">
              <div class="slug-pill-date">
                <div class="slug-pill-month">${monthLabel(session.startDate)}</div>
                <div class="slug-pill-day">${dayLabel(session.startDate)}</div>
                <div class="slug-pill-weekday">${weekdayLabel(session.startDate)}</div>
              </div>
              <img class="class-card-course-image" src="${escapeAttribute(pillImageSrc(section, session))}" alt="${escapeAttribute(section.title)} class" loading="lazy" onerror="this.src='${escapeAttribute(COURSE_IMAGE_FALLBACK)}';this.onerror=null;">
            </div>
            <div class="slug-pill-title">${escapeHtml(dateLine(session.startDate))}</div>
            <div class="slug-pill-meta">${escapeHtml(timeLine(session.startDate))} · ${escapeHtml(session.locationClean || "Location TBA")}</div>
            ${metaTags}
            ${subtype}
          </div>
          <div class="finder-pill-side">
            <div class="finder-pill-side-label">${pillCtaLabel(section)}</div>
          </div>
        </article>
      </a>
    `;
  }

  function renderSection(section, sessions) {
    const preview = sessions.slice(0, MAX_SESSIONS);
    const scheduleActions = section.secondaryScheduleUrl
      ? `<div class="finder-card-actions"><a class="button secondary" href="${escapeAttribute(section.fullScheduleUrl)}">${escapeHtml(section.fullScheduleLabel)}</a><a class="button secondary" href="${escapeAttribute(section.secondaryScheduleUrl)}">${escapeHtml(section.secondaryScheduleLabel)}</a></div>`
      : `<a class="button secondary" href="${escapeAttribute(section.fullScheduleUrl)}">${escapeHtml(section.fullScheduleLabel)}</a>`;
    if (section.id === "heartsaver" && preview.length) {
      const buckets = new Map(HEARTSAVER_SUBTYPE_ORDER.map((label) => [label, []]));
      preview.forEach((session) => {
        const bucket = buckets.get(session.subtype) || buckets.get("First Aid + CPR + AED");
        bucket.push(session);
      });
      const groupedContent = HEARTSAVER_SUBTYPE_ORDER
        .map((subtype) => {
          const items = buckets.get(subtype) || [];
          if (!items.length) return "";
          return `
            <section class="finder-subgroup">
              <div class="finder-subgroup-head">
                <h4>${escapeHtml(subtype)}</h4>
                <p>${escapeHtml(HEARTSAVER_SUBTYPE_COPY[subtype] || "")}</p>
              </div>
              <div class="finder-pills">
                ${items.map((session) => renderPill(section, session)).join("")}
              </div>
            </section>
          `;
        })
        .filter(Boolean)
        .join("");

      return `
        <section class="finder-card" id="${escapeAttribute(section.id)}">
          <div class="finder-card-head">
            <div>
              <h3>${escapeHtml(section.title)}</h3>
              <p class="finder-card-copy">${escapeHtml(section.audience)}</p>
            </div>
            ${scheduleActions}
          </div>
          <div class="finder-subgroups">
            ${groupedContent}
          </div>
        </section>
      `;
    }

    const content = preview.length
      ? preview.map((session) => renderPill(section, session)).join("")
      : `
        <div class="finder-empty">
          <strong>${escapeHtml(section.emptyLabel)}</strong>
          <p>Open the course page for more dates, locations, and registration options.</p>
        </div>
      `;

    return `
      <section class="finder-card" id="${escapeAttribute(section.id)}">
        <div class="finder-card-head">
          <div>
            <h3>${escapeHtml(section.title)}</h3>
            <p class="finder-card-copy">${escapeHtml(section.audience)}</p>
          </div>
          ${scheduleActions}
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
            <h3>Choose your training type</h3>
            <p class="finder-card-copy">Use the links below to find CPR, BLS, ACLS, PALS, First Aid, or group training.</p>
          </div>
        </div>
        <div class="finder-empty">
          <p class="home-status-badges">
            <a class="home-stat" href="/bls.html">BLS</a>
            <a class="home-stat" href="/acls.html">ACLS</a>
            <a class="home-stat" href="/pals.html">PALS</a>
            <a class="home-stat" href="/heartsaver.html">Heartsaver &amp; First Aid</a>
            <a class="home-stat" href="/arc.html">American Red Cross</a>
            <a class="home-stat" href="/hsi.html">HSI</a>
            <a class="home-stat" href="/uscg-elementary-first-aid-cpr.html">USCG First Aid/CPR</a>
            <a class="home-stat" href="/request_group_session.html">Request Group Training</a>
          </p>
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

  function loadJsonOptional(url) {
    return fetch(url)
      .then((response) => {
        if (!response.ok) return null;
        return response.json().catch(() => null);
      })
      .catch(() => null);
  }

  Promise.all([
    loadJsonOptional("/data/public_schedule.json"),
    loadJsonOptional("/public_schedule.json"),
    loadJsonOptional("/data/schedule_future.json"),
  ]).then(([primaryFeed, legacyPublic, futureSchedule]) => {
    const primarySessions = dedupePrimarySessions([
      ...buildPrimarySessions(Array.isArray(primaryFeed) ? primaryFeed : []),
      ...buildPrimarySessions(Array.isArray(legacyPublic) ? legacyPublic : []),
      ...buildPrimarySessionsFromFuture(futureSchedule || {}),
    ]);
    const enrichmentMap = buildEnrichmentMap(legacyPublic || {}, futureSchedule || {});
    const enrichedSessions = enrichSessions(primarySessions, enrichmentMap);
    const groupedSessions = buildGroupedSessions(enrichedSessions);
    const hasAnySessions = SECTION_CONFIG.some((section) => (groupedSessions.get(section.id) || []).length > 0);
    if (!hasAnySessions) {
      renderError();
      return;
    }
    sectionsRoot.innerHTML = SECTION_CONFIG.map((section) => renderSection(section, groupedSessions.get(section.id) || [])).join("");
  });
})();
