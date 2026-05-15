(function () {
  const DEFAULT_THEME = "TH000";
  const SCOPE_WEIGHT = {
    global: 0,
    page_type: 1,
    city: 2,
    certifying_body: 3,
    course_slug: 4
  };

  function parseDate(value) {
    if (!value) return null;
    const parsed = new Date(`${value}T00:00:00`);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  function normalizeDate(value) {
    if (!value) return new Date();
    if (value instanceof Date) return value;
    const parsed = parseDate(value);
    return parsed || new Date();
  }

  function scopeMatches(scope, context) {
    const safeScope = scope || { type: "global" };
    if (safeScope.type === "global") return true;
    return String(context?.[safeScope.type] || "").toLowerCase() === String(safeScope.value || "").toLowerCase();
  }

  function ruleIsActive(rule, date) {
    if (!rule || rule.enabled === false) return false;
    const start = parseDate(rule.start);
    const end = parseDate(rule.end);
    if (!start || !end || end <= start) return false;
    return date >= start && date < end;
  }

  function resolveActiveTheme(registry, schedule, context = {}, dateValue = new Date()) {
    try {
      const date = normalizeDate(dateValue);
      const defaultTheme = schedule?.default_theme || registry?.default_theme || DEFAULT_THEME;
      const rules = Array.isArray(schedule?.rules) ? schedule.rules : [];
      const matches = rules
        .map((rule, index) => ({ rule, index }))
        .filter(item => ruleIsActive(item.rule, date) && scopeMatches(item.rule.scope, context))
        .sort((a, b) => {
          const aScope = SCOPE_WEIGHT[a.rule.scope?.type || "global"] || 0;
          const bScope = SCOPE_WEIGHT[b.rule.scope?.type || "global"] || 0;
          if (aScope !== bScope) return bScope - aScope;
          const aStart = parseDate(a.rule.start)?.getTime() || 0;
          const bStart = parseDate(b.rule.start)?.getTime() || 0;
          if (aStart !== bStart) return bStart - aStart;
          return b.index - a.index;
        });
      const selected = matches[0]?.rule;
      const theme = selected?.theme && registry?.themes?.[selected.theme] ? selected.theme : defaultTheme;
      return {
        theme,
        default_theme: defaultTheme,
        matched_rule: selected || null,
        reason: selected ? `Matched ${selected.label || selected.id}` : "No enabled schedule rule matched; using default theme."
      };
    } catch (error) {
      return {
        theme: DEFAULT_THEME,
        default_theme: DEFAULT_THEME,
        matched_rule: null,
        reason: `Theme resolver warning: ${error.message}. Falling back to ${DEFAULT_THEME}.`
      };
    }
  }

  window.ThemeResolver = { resolveActiveTheme, scopeMatches, ruleIsActive };
})();
