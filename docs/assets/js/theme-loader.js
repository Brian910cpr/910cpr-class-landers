(function () {
  const DEFAULT_THEME = {
    themeName: "default",
    accent: "#26a9c2",
    contrast: "#1f87af",
    highlight: "rgba(38, 169, 194, 0.12)",
    heroSurface: "linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(247, 250, 252, 0.96) 100%)",
    heroOrb: "radial-gradient(circle, rgba(126, 201, 200, 0.18) 0%, rgba(126, 201, 200, 0) 72%)",
    guidanceSurface: "linear-gradient(135deg, rgba(240, 251, 252, 0.96) 0%, rgba(255, 247, 235, 0.98) 100%)",
    sidebarSurface: "linear-gradient(180deg, #ffffff 0%, #fff9ef 100%)",
    cardSurface: "linear-gradient(180deg, #ffffff 0%, #fffdf8 100%)",
    heroImage: "/docs/images/bls_general.png",
    sidebarImage: "/docs/images/bls_general.png",
  };

  const PRESETS = {
    default: DEFAULT_THEME,
    summer: {
      themeName: "summer",
      accent: "#1fa3ba",
      contrast: "#136f94",
      highlight: "rgba(31, 163, 186, 0.12)",
      heroSurface: "linear-gradient(135deg, rgba(255, 249, 238, 0.96) 0%, rgba(235, 250, 255, 0.96) 100%)",
      heroOrb: "radial-gradient(circle, rgba(245, 189, 99, 0.22) 0%, rgba(245, 189, 99, 0) 72%)",
      guidanceSurface: "linear-gradient(135deg, rgba(237, 251, 255, 0.98) 0%, rgba(255, 244, 226, 0.98) 100%)",
      sidebarSurface: "linear-gradient(180deg, #fffdf7 0%, #eefafc 100%)",
      cardSurface: "linear-gradient(180deg, #ffffff 0%, #fff7ea 100%)",
      heroImage: "/docs/images/bls_general.png",
      sidebarImage: "/docs/images/heartsaver_general.png",
    },
    holiday: {
      themeName: "holiday",
      accent: "#bf4e5f",
      contrast: "#8c2f46",
      highlight: "rgba(191, 78, 95, 0.12)",
      heroSurface: "linear-gradient(135deg, rgba(255, 248, 248, 0.96) 0%, rgba(247, 255, 251, 0.96) 100%)",
      heroOrb: "radial-gradient(circle, rgba(95, 176, 132, 0.2) 0%, rgba(95, 176, 132, 0) 72%)",
      guidanceSurface: "linear-gradient(135deg, rgba(255, 247, 247, 0.98) 0%, rgba(245, 255, 248, 0.98) 100%)",
      sidebarSurface: "linear-gradient(180deg, #fffafb 0%, #f4fbf7 100%)",
      cardSurface: "linear-gradient(180deg, #ffffff 0%, #fff8f8 100%)",
      heroImage: "/docs/images/acls_general.png",
      sidebarImage: "/docs/images/pals_general.png",
    },
  };

  function normalizeTheme(overrides) {
    const input = overrides || {};
    const preset = PRESETS[input.themeName] || PRESETS.default;
    return { ...DEFAULT_THEME, ...preset, ...input };
  }

  function setVar(scope, name, value) {
    if (!scope || !value) return;
    scope.style.setProperty(name, value);
  }

  function applyTheme(scope, overrides, applyTo) {
    if (!scope) return normalizeTheme(overrides);
    const theme = normalizeTheme(overrides);
    const activeScopes = new Set((applyTo || ["hero", "guidance", "card", "sidebar"]).filter(Boolean));

    scope.querySelectorAll("[data-site-theme-scope]").forEach((node) => {
      const area = node.getAttribute("data-site-theme-scope");
      node.toggleAttribute("data-theme-active", activeScopes.has(area));
      if (!activeScopes.has(area)) {
        node.style.removeProperty("--site-hero-surface");
        node.style.removeProperty("--site-hero-orb");
        node.style.removeProperty("--site-guidance-surface");
        node.style.removeProperty("--site-sidebar-surface");
        node.style.removeProperty("--site-card-surface");
        node.style.removeProperty("--site-preview-accent");
        node.style.removeProperty("--site-preview-contrast");
        node.style.removeProperty("--site-preview-highlight");
        return;
      }
      setVar(node, "--site-hero-surface", theme.heroSurface);
      setVar(node, "--site-hero-orb", theme.heroOrb);
      setVar(node, "--site-guidance-surface", theme.guidanceSurface);
      setVar(node, "--site-sidebar-surface", theme.sidebarSurface);
      setVar(node, "--site-card-surface", theme.cardSurface);
      setVar(node, "--site-preview-accent", theme.accent);
      setVar(node, "--site-preview-contrast", theme.contrast);
      setVar(node, "--site-preview-highlight", theme.highlight);
    });

    const heroImage = scope.querySelector("[data-preview-hero-image]");
    if (heroImage) heroImage.setAttribute("src", theme.heroImage);
    const sidebarImage = scope.querySelector("[data-preview-sidebar-image]");
    if (sidebarImage) sidebarImage.setAttribute("src", theme.sidebarImage);

    return theme;
  }

  async function validateAssetPath(path) {
    const result = { path: path || "", exists: false, warning: "" };
    if (!path) {
      result.warning = "Missing path";
      return result;
    }
    try {
      let response = await fetch(path, { method: "HEAD", cache: "no-store" });
      if (!response.ok || response.status === 405) {
        response = await fetch(path, { method: "GET", cache: "no-store" });
      }
      result.exists = response.ok;
      if (!response.ok) result.warning = `Missing file (${response.status})`;
      return result;
    } catch (error) {
      result.warning = "Could not verify asset";
      return result;
    }
  }

  window.SiteThemeLoader = { DEFAULT_THEME, PRESETS, normalizeTheme, applyTheme, validateAssetPath };
})();