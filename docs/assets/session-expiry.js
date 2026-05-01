(function () {
  var EMPTY_MESSAGE = "These listed times have passed. Please view the current schedule for available seats.";

  function parseStart(value) {
    if (!value) return null;
    var dt = new Date(value);
    return Number.isNaN(dt.getTime()) ? null : dt;
  }

  function sessionNodes(root) {
    return Array.from((root || document).querySelectorAll("[data-start], [data-session-start]"));
  }

  function getStart(node) {
    var direct = node.getAttribute("data-start") || node.getAttribute("data-session-start");
    var parsed = parseStart(direct);
    if (parsed) {
      if (!node.getAttribute("data-start")) node.setAttribute("data-start", parsed.toISOString());
      return parsed;
    }
    return null;
  }

  function containerOf(node) {
    return (
      node.closest("[data-session-container]") ||
      node.closest(".upcoming-grid") ||
      node.closest(".slug-pill-list") ||
      node.closest("[data-session-list]") ||
      node.closest("tbody") ||
      node.closest("ul") ||
      node.parentElement
    );
  }

  function itemsIn(container) {
    return Array.from(container.querySelectorAll(":scope > [data-start], :scope > [data-session-start]"));
  }

  function ensureEmptyMessage(container) {
    if (!container || container.querySelector(":scope > .session-expiry-empty")) return;
    var p = document.createElement("p");
    p.className = "session-expiry-empty";
    p.textContent = EMPTY_MESSAGE;
    container.appendChild(p);
  }

  function removeEmptyMessage(container) {
    if (!container) return;
    var msg = container.querySelector(":scope > .session-expiry-empty");
    if (msg) msg.remove();
  }

  function sortVisible(container) {
    if (!container) return;
    var rows = itemsIn(container).filter(function (node) {
      return !node.hidden && node.style.display !== "none";
    });
    rows.sort(function (a, b) {
      var aDt = getStart(a);
      var bDt = getStart(b);
      var aTime = aDt ? aDt.getTime() : Number.MAX_SAFE_INTEGER;
      var bTime = bDt ? bDt.getTime() : Number.MAX_SAFE_INTEGER;
      return aTime - bTime;
    });
    rows.forEach(function (node) {
      container.appendChild(node);
    });
  }

  function firstVisibleUpcoming() {
    var now = new Date();
    var candidates = sessionNodes(document)
      .filter(function (node) {
        return !node.hidden && node.style.display !== "none";
      })
      .map(function (node) {
        return { node: node, start: getStart(node) };
      })
      .filter(function (item) {
        return item.start && item.start >= now;
      })
      .sort(function (a, b) {
        return a.start.getTime() - b.start.getTime();
      });
    return candidates.length ? candidates[0] : null;
  }

  function showDebug(hiddenCount) {
    var params = new URLSearchParams(window.location.search || "");
    if (params.get("debugExpiry") !== "1") return;

    var existing = document.getElementById("session-expiry-debug");
    if (existing) existing.remove();

    var wrap = document.createElement("div");
    wrap.id = "session-expiry-debug";
    wrap.style.cssText = "position:fixed;right:12px;bottom:12px;z-index:99999;background:#111827;color:#fff;padding:10px 12px;border-radius:8px;font:12px/1.4 Arial,sans-serif;max-width:360px;";

    var first = firstVisibleUpcoming();
    var firstLabel = "none";
    if (first) {
      var sid = first.node.getAttribute("data-session-id") || "unknown";
      firstLabel = sid + " @ " + first.start.toISOString();
    }

    wrap.innerHTML =
      "<div><strong>Expiry Debug</strong></div>" +
      "<div>Hidden expired: " + hiddenCount + "</div>" +
      "<div>Browser now: " + new Date().toISOString() + "</div>" +
      "<div>First upcoming: " + firstLabel + "</div>";
    document.body.appendChild(wrap);
  }

  function applySessionExpiry(root) {
    var now = new Date();
    var hiddenCount = 0;
    var touched = new Set();

    sessionNodes(root).forEach(function (node) {
      var start = getStart(node);
      if (!start) return;
      var container = containerOf(node);
      if (container) touched.add(container);
      if (start < now) {
        node.hidden = true;
        node.style.display = "none";
        hiddenCount += 1;
      } else {
        node.hidden = false;
        node.style.display = "";
      }
    });

    touched.forEach(function (container) {
      sortVisible(container);
      var visible = itemsIn(container).some(function (node) {
        return !node.hidden && node.style.display !== "none";
      });
      if (!visible) ensureEmptyMessage(container);
      else removeEmptyMessage(container);
    });

    showDebug(hiddenCount);
    return hiddenCount;
  }

  window.applySessionExpiry = applySessionExpiry;
  window.addEventListener("DOMContentLoaded", function () {
    applySessionExpiry(document);
  });
})();
