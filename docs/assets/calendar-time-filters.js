(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.CalendarTimeFilters = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const BUCKETS = [
    { id: "early-am", label: "Early AM", min: 0, max: 360, range: "12:00 AM–6:00 AM" },
    { id: "am", label: "AM", min: 360, max: 720, range: "6:00 AM–12:00 PM" },
    { id: "afternoon", label: "Afternoon", min: 720, max: 1020, range: "12:00 PM–5:00 PM" },
    { id: "evening", label: "Evening", min: 1020, max: 1260, range: "5:00 PM–9:00 PM" },
    { id: "late-pm", label: "Late PM", min: 1260, max: 1440, range: "9:00 PM–12:00 AM" },
  ];
  const DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  // Only named corporate accounts belong in this public picker. General-purpose,
  // promotional, and invoice-only codes stay out of browser-loaded source.
  const CORPORATE_BILLING_CODES = [
    { code: "assistedcare", company: "AssistedCare", aliases: ["assisted care"] },
    { code: "Breakthrough", company: "Breakthrough Autism", aliases: ["breakthrough"] },
    { code: "Maxim", company: "Maxim Homecare", aliases: ["maxim home care", "homecare"] },
    { code: "MaximBH", company: "Maxim Behavioral Health", aliases: ["maxim bh", "behavioral health", "aba"] },
    { code: "MaximDSP", company: "Maxim Direct Support Professionals", aliases: ["maxim dsp", "direct support", "idd"] },
  ];
  const DAY_TOKEN = "(?:sunday|monday|tuesday|wednesday|thursday|friday|saturday)s?";
  const TIME_TOKEN = "(?:noon|midnight|\\d{1,2}(?::\\d{2})?\\s*(?:am|pm)|\\d{1,2}:\\d{2})";
  const HELP = "Try “after 6pm”, “Tuesday or Wednesday evening”, or “can't Saturday morning”. Use AM/PM for times.";

  function dateValue(key) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(key || "")) return null;
    const date = new Date(`${key}T12:00:00Z`);
    return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === key ? date : null;
  }

  function addDays(key, offset) {
    const date = dateValue(key);
    if (!date) return null;
    date.setUTCDate(date.getUTCDate() + offset);
    return date.toISOString().slice(0, 10);
  }

  function clockMinutes(value) {
    const text = String(value).trim().toLowerCase();
    if (text === "noon") return 720;
    if (text === "midnight") return 0;
    const match = text.match(/^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$/);
    if (!match || (!match[3] && match[2] === undefined)) return NaN;
    let hour = Number(match[1]);
    const minute = Number(match[2] || 0);
    if (minute > 59 || (match[3] ? hour < 1 || hour > 12 : hour > 23)) return NaN;
    if (match[3]) hour = (hour % 12) + (match[3] === "pm" ? 12 : 0);
    return hour * 60 + minute;
  }

  function timeLabel(minutes) {
    if (minutes === 1440) return "midnight";
    const hour = Math.floor(minutes / 60);
    return `${hour % 12 || 12}:${String(minutes % 60).padStart(2, "0")} ${hour >= 12 ? "PM" : "AM"}`;
  }

  // Consume the entire supported phrase. Unrecognized words never become ignored constraints.
  function parseClause(input, today) {
    let text = input.trim().replace(/^(?:i am |i'm |i can |available |anything |only |please )+/, "");
    const rule = { daysOfWeek: [], startTimeMin: null, startTimeMax: null, dateMin: null, dateMax: null };
    const labels = [];
    let recognized = false;
    let hasTime = false;
    const dateMatch = text.match(/\b(next week|this week|tomorrow|today|\d{4}-\d{2}-\d{2})\b/);
    if (dateMatch) {
      const token = dateMatch[0];
      if (token.endsWith("week")) {
        const date = dateValue(today);
        if (!date) return null;
        const mondayOffset = -((date.getUTCDay() + 6) % 7) + (token === "next week" ? 7 : 0);
        rule.dateMin = addDays(today, mondayOffset);
        rule.dateMax = addDays(rule.dateMin, 6);
      } else {
        rule.dateMin = token === "today" ? today : token === "tomorrow" ? addDays(today, 1) : token;
        if (!dateValue(rule.dateMin)) return null;
        rule.dateMax = rule.dateMin;
      }
      labels.push(rule.dateMin === rule.dateMax ? rule.dateMin : `${rule.dateMin}–${rule.dateMax}`);
      text = text.replace(dateMatch[0], " ");
      recognized = true;
    }
    const dayMatch = text.match(new RegExp(`\\b(?:weekdays|weekends|weekend|${DAY_TOKEN}(?:\\s*(?:or|and|,|&)\\s*${DAY_TOKEN})*)\\b`));
    if (dayMatch) {
      const token = dayMatch[0];
      rule.daysOfWeek = token === "weekdays" ? [1, 2, 3, 4, 5] : token.startsWith("weekend") ? [0, 6] :
        [...token.matchAll(new RegExp(DAY_TOKEN, "g"))].map(match => DAY_NAMES.findIndex(day => match[0].startsWith(day.toLowerCase())));
      rule.daysOfWeek = [...new Set(rule.daysOfWeek)];
      labels.push(rule.daysOfWeek.map(day => DAY_NAMES[day]).join(" / "));
      text = text.replace(token, " ");
      recognized = true;
    }
    text = text.replace(/\s+/g, " ").trim().replace(/^(?:on |in the |in |at (?!or ))/, "").trim();
    if (text) {
      const periods = {
        "early am": BUCKETS[0], "am": BUCKETS[1], "morning": BUCKETS[1], "mornings": BUCKETS[1],
        "afternoon": BUCKETS[2], "afternoons": BUCKETS[2], "evening": BUCKETS[3], "evenings": BUCKETS[3],
        "late pm": BUCKETS[4],
      };
      if (periods[text]) {
        rule.startTimeMin = periods[text].min;
        rule.startTimeMax = periods[text].max;
        labels.push(`${periods[text].label} (${periods[text].range})`);
      } else if (text === "after work") {
        rule.startTimeMin = 1020;
        rule.minExclusive = true;
        labels.push("after work = after 5:00 PM");
      } else {
        const range = text.match(new RegExp(`^between (${TIME_TOKEN}) and (${TIME_TOKEN})$`));
        const bounds = text.match(new RegExp(`^(after|before|at or after|at or before) (${TIME_TOKEN})(?: and (after|before) (${TIME_TOKEN}))?$`));
        if (range) {
          rule.startTimeMin = clockMinutes(range[1]);
          rule.startTimeMax = clockMinutes(range[2]);
          if (rule.startTimeMax === 0) rule.startTimeMax = 1440;
          labels.push(`${timeLabel(rule.startTimeMin)}–${timeLabel(rule.startTimeMax)} (end excluded)`);
        } else if (bounds) {
          for (const [operator, value] of [[bounds[1], bounds[2]], [bounds[3], bounds[4]]]) {
            if (!operator) continue;
            let minutes = clockMinutes(value);
            if (!Number.isFinite(minutes)) return null;
            if (operator.endsWith("after")) {
              if (rule.startTimeMin !== null) return null;
              rule.startTimeMin = minutes;
              rule.minExclusive = operator === "after";
            } else {
              if (rule.startTimeMax !== null) return null;
              if (minutes === 0) minutes = 1440;
              rule.startTimeMax = minutes;
              rule.maxInclusive = operator === "at or before";
            }
            labels.push(`${operator} ${timeLabel(minutes)}`);
          }
        } else return null;
      }
      if ([rule.startTimeMin, rule.startTimeMax].some(value => value !== null && !Number.isFinite(value))) return null;
      // Overnight requests must be explicit alternatives, rather than a guessed reversed range.
      if (rule.startTimeMin !== null && rule.startTimeMax !== null && rule.startTimeMin >= rule.startTimeMax) return null;
      recognized = true;
      hasTime = true;
    }
    return recognized ? { rule, label: labels.join(" · "), hasTime } : null;
  }

  function parseSmart(text, today) {
    const normalized = String(text || "").toLowerCase().replace(/[’‘]/g, "'").replace(/\s+/g, " ").trim().replace(/[.!]$/, "");
    const result = { valid: true, include: [], exclude: [], summary: "", error: "" };
    if (!normalized) return result;
    if (normalized.length > 240) return { ...result, valid: false, error: HELP };
    const sections = normalized.split(/\s+(?:except|but not)\s+/);
    const labels = [];
    for (let index = 0; index < sections.length; index += 1) {
      let section = sections[index].trim();
      const negative = section.match(/^(?:i\s+)?(?:can't|cant|cannot|am unavailable|am not available|am busy|unavailable|not available|busy|avoid|not)\s+/);
      const exclude = Boolean(negative) || index > 0;
      if (negative) section = section.slice(negative[0].length);
      const clause = parseClause(section, today);
      let clauses = clause ? [clause] : section.split(/\s+or\s+/).map(part => parseClause(part, today));
      if (!clause && (clauses.length < 2 || clauses.some(part => !part?.hasTime))) clauses = [];
      if (!clauses.length || clauses.some(part => !part)) return { ...result, valid: false, error: HELP };
      result[exclude ? "exclude" : "include"].push(...clauses.map(part => part.rule));
      labels.push(`${exclude ? "Exclude: " : ""}${clauses.map(part => part.label).join(" OR ")}`);
    }
    result.summary = labels.join("; ");
    return result;
  }

  function compile(bucketIds = [], text = "", today) {
    const smart = parseSmart(text, today);
    return {
      ...smart,
      timeRanges: BUCKETS.filter(bucket => bucketIds.includes(bucket.id)).map(({ min, max }) => ({ min, max })),
      active: Boolean(bucketIds.length || String(text).trim()),
    };
  }

  function matchesRule(rule, date, minutes) {
    const day = dateValue(date);
    return Boolean(day) &&
      (!rule.daysOfWeek.length || rule.daysOfWeek.includes(day.getUTCDay())) &&
      (!rule.dateMin || date >= rule.dateMin) && (!rule.dateMax || date <= rule.dateMax) &&
      (rule.startTimeMin === null || (rule.minExclusive ? minutes > rule.startTimeMin : minutes >= rule.startTimeMin)) &&
      (rule.startTimeMax === null || (rule.maxInclusive ? minutes <= rule.startTimeMax : minutes < rule.startTimeMax));
  }

  function filterDates(dates, constraints) {
    if (!constraints.active) return dates;
    if (!constraints.valid) return [];
    // Input has already passed the existing course/family filter. Never add dates, slots, or courses.
    return dates.map(day => ({
      ...day,
      startTimes: day.startTimes.filter(slot => {
        const minutes = clockMinutes(slot.startTime);
        return Number.isFinite(minutes) && Boolean(dateValue(day.date)) &&
          (!constraints.timeRanges.length || constraints.timeRanges.some(range => minutes >= range.min && minutes < range.max)) &&
          (!constraints.include.length || constraints.include.some(rule => matchesRule(rule, day.date, minutes))) &&
          !constraints.exclude.some(rule => matchesRule(rule, day.date, minutes));
      }),
    })).filter(day => day.startTimes.length);
  }

  function matchingCorporateBillingCodes(text) {
    const query = String(text || "").trim().toLowerCase();
    if (query.length < 3) return [];
    return CORPORATE_BILLING_CODES.filter(item => [item.code, item.company, ...item.aliases]
      .some(value => value.toLowerCase().includes(query)));
  }

  function mount(host, { today, onChange }) {
    const doc = host.ownerDocument;
    host.className = "calendar-time-filters";
    host.setAttribute("aria-label", "Calendar timing preferences");
    host.dataset.version = "20260929.1";
    const quick = doc.createElement("div");
    quick.className = "calendar-time-quick";
    quick.setAttribute("role", "group");
    quick.setAttribute("aria-label", "Time of Day Preferences");
    const caption = doc.createElement("span");
    caption.textContent = "Time of Day";
    caption.className = "calendar-time-caption";
    quick.append(caption);
    const boxes = BUCKETS.map((bucket, index) => {
      const item = doc.createElement("span");
      item.className = "calendar-time-item";
      if (index) {
        const bullet = doc.createElement("span");
        bullet.className = "calendar-time-bullet";
        bullet.textContent = "•";
        bullet.setAttribute("aria-hidden", "true");
        item.append(bullet);
      }
      const label = doc.createElement("label");
      label.title = `${bucket.range}; end time excluded`;
      const box = doc.createElement("input");
      box.type = "checkbox";
      box.value = bucket.id;
      box.setAttribute("aria-label", `${bucket.label}, ${bucket.range}`);
      label.append(box, doc.createTextNode(bucket.label));
      item.append(label);
      quick.append(item);
      return box;
    });
    const row = doc.createElement("div");
    row.className = "calendar-time-smart";
    const label = doc.createElement("label");
    label.htmlFor = `${host.id}-smart`;
    label.textContent = "Smart filter";
    const input = doc.createElement("input");
    input.id = label.htmlFor;
    input.type = "text";
    input.maxLength = 240;
    input.autocomplete = "off";
    input.placeholder = "Describe when’s good for you…";
    const clear = doc.createElement("button");
    clear.type = "button";
    clear.textContent = "Clear";
    clear.setAttribute("aria-label", "Clear timing filters");
    row.append(label, input, clear);
    const billing = doc.createElement("div");
    billing.className = "calendar-billing-code";
    const billingLabel = doc.createElement("label");
    billingLabel.htmlFor = `${host.id}-billing-code`;
    billingLabel.textContent = "Billing Code";
    const billingInput = doc.createElement("input");
    billingInput.id = billingLabel.htmlFor;
    billingInput.type = "text";
    billingInput.autocomplete = "off";
    billingInput.maxLength = 80;
    billingInput.placeholder = "Company name or billing code";
    billingInput.setAttribute("role", "combobox");
    billingInput.setAttribute("aria-autocomplete", "list");
    billingInput.setAttribute("aria-expanded", "false");
    const suggestions = doc.createElement("div");
    suggestions.id = `${host.id}-billing-suggestions`;
    suggestions.className = "calendar-billing-suggestions";
    suggestions.setAttribute("role", "listbox");
    suggestions.hidden = true;
    billingInput.setAttribute("aria-controls", suggestions.id);
    const billingStatus = doc.createElement("p");
    billingStatus.className = "calendar-billing-status";
    billingStatus.setAttribute("role", "status");
    billingStatus.setAttribute("aria-live", "polite");
    billingStatus.hidden = true;
    billing.append(billingLabel, billingInput, suggestions, billingStatus);
    const hint = doc.createElement("p");
    hint.id = `${host.id}-hint`;
    hint.className = "calendar-time-hint";
    hint.textContent = "Or tell us when you can’t. Matches class start times (Eastern).";
    const status = doc.createElement("p");
    status.id = `${host.id}-status`;
    status.className = "calendar-time-status";
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    input.setAttribute("aria-describedby", `${hint.id} ${status.id}`);
    const pillRow = doc.createElement("div");
    pillRow.className = "calendar-filter-pill-row";
    const timingPill = doc.createElement("section");
    timingPill.className = "calendar-filter-pill calendar-timing-pill";
    timingPill.setAttribute("aria-label", "Scheduling preferences");
    timingPill.append(quick, row, hint, status);
    const billingPill = doc.createElement("section");
    billingPill.className = "calendar-filter-pill calendar-billing-pill";
    billingPill.setAttribute("aria-label", "Corporate billing code");
    billingPill.append(billing);
    pillRow.append(timingPill, billingPill);
    host.append(pillRow);
    let constraints = compile([], "", today());
    let billingCode = "";
    let timer;
    function update() {
      clearTimeout(timer);
      constraints = compile(boxes.filter(box => box.checked).map(box => box.value), input.value, today());
      input.setAttribute("aria-invalid", String(!constraints.valid));
      status.textContent = constraints.valid ? constraints.summary : `No matches shown. ${constraints.error}`;
      status.hidden = !status.textContent;
      clear.disabled = !constraints.active;
      onChange();
    }
    boxes.forEach(box => box.addEventListener("change", update));
    input.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(update, 180); });
    input.addEventListener("keydown", event => {
      if (event.key === "Enter") { event.preventDefault(); update(); }
    });
    clear.addEventListener("click", () => {
      boxes.forEach(box => { box.checked = false; });
      input.value = "";
      update();
      input.focus();
    });
    clear.disabled = true;
    status.hidden = true;
    function closeBillingSuggestions() {
      suggestions.hidden = true;
      suggestions.replaceChildren();
      billingInput.setAttribute("aria-expanded", "false");
    }
    function selectBillingCode(item) {
      billingCode = item.code;
      billingInput.value = item.code;
      billingStatus.textContent = `${item.company} selected. Enter this code in Enrollware registration.`;
      billingStatus.hidden = false;
      closeBillingSuggestions();
    }
    function updateBillingSuggestions() {
      billingCode = "";
      billingStatus.hidden = true;
      const matches = matchingCorporateBillingCodes(billingInput.value);
      if (!matches.length) return closeBillingSuggestions();
      suggestions.replaceChildren(...matches.map(item => {
        const option = doc.createElement("button");
        option.type = "button";
        option.setAttribute("role", "option");
        option.textContent = item.company;
        option.addEventListener("click", () => selectBillingCode(item));
        return option;
      }));
      suggestions.hidden = false;
      billingInput.setAttribute("aria-expanded", "true");
    }
    billingInput.addEventListener("input", updateBillingSuggestions);
    billingInput.addEventListener("keydown", event => {
      if (event.key === "Escape") closeBillingSuggestions();
      if (event.key === "Enter" && !suggestions.hidden && suggestions.firstElementChild) {
        event.preventDefault();
        suggestions.firstElementChild.click();
      }
    });
    billingInput.addEventListener("blur", () => setTimeout(closeBillingSuggestions, 120));
    return {
      get constraints() { return constraints; },
      get billingCode() { return billingCode; },
    };
  }

  return { BUCKETS, CORPORATE_BILLING_CODES, compile, parseSmart, filterDates, matchingCorporateBillingCodes, mount };
});
