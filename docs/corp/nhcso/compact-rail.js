(function () {
  "use strict";

  function install() {
    if (!location.pathname.startsWith("/corp/nhcso")) return;

    const shell = document.querySelector(".shell");
    const layout = document.querySelector(".layout");
    const aside = document.querySelector("aside");
    const toolbar = shell && shell.querySelector(":scope > .toolbar");
    const calendar = shell && shell.querySelector(":scope > .calendar");
    const classList = document.getElementById("classList");
    if (!shell || !layout || !aside || !toolbar || !calendar || !classList) return;

    const style = document.createElement("style");
    style.textContent = `
      .shell{display:block!important;padding:14px 18px!important}
      .layout{grid-template-columns:minmax(0,1fr) 430px!important;gap:16px!important}
      main{min-width:0}
      aside{height:calc(100vh - 92px)!important;max-height:none!important;overflow:hidden!important}
      .nhcso-mini-calendar{flex:0 0 auto;margin-bottom:8px}
      .nhcso-mini-calendar>.toolbar{display:grid!important;grid-template-columns:auto auto auto 1fr auto;gap:5px!important;margin:0 0 5px!important;align-items:center}
      .nhcso-mini-calendar>.toolbar .btn{padding:4px 7px!important;border-radius:7px!important;font-size:10px!important}
      .nhcso-mini-calendar>.toolbar #monthTitle{font-size:13px!important;text-align:center;white-space:nowrap}
      .nhcso-mini-calendar>.toolbar .muted{display:none!important}
      .nhcso-mini-calendar>.toolbar .spacer{display:none!important}
      .nhcso-mini-calendar>.toolbar #newTop{padding:5px 8px!important;font-size:10px!important}
      .nhcso-mini-calendar .calendar{border-radius:9px!important}
      .nhcso-mini-calendar .cal-head div{padding:3px 1px!important;font-size:8px!important}
      .nhcso-mini-calendar .day{min-height:39px!important;padding:2px!important}
      .nhcso-mini-calendar .daynum{font-size:8px!important;margin-bottom:1px!important;line-height:1!important}
      .nhcso-mini-calendar .event{margin-top:1px!important;border-radius:4px!important;padding:2px!important;font-size:0!important;line-height:1.05!important;overflow:hidden}
      .nhcso-mini-calendar .event b{font-size:8px!important;font-weight:650!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      .nhcso-mini-calendar .event .mini-loc{display:block;font-size:7px;color:#9fb0c7;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:1px}
      aside .feature-row{flex:0 0 auto;margin-bottom:7px!important;gap:7px!important}
      aside .feature{padding:7px 8px!important}
      aside .feature b{font-size:13px!important}
      aside .feature span{font-size:9px!important}
      aside .myclasses{margin-bottom:0!important;min-height:0!important;flex:1!important;padding:12px!important}
      aside .myclasses h2{margin-bottom:5px!important}
      aside .myclasses>.muted{margin-bottom:6px!important}
      aside .class-list{min-height:0!important;flex:1!important}
      @media(max-width:1050px){
        .layout{grid-template-columns:1fr!important}
        aside{height:auto!important;overflow:visible!important;position:static!important}
        .nhcso-mini-calendar{max-width:520px}
      }
    `;
    document.head.appendChild(style);

    const wrap = document.createElement("div");
    wrap.className = "nhcso-mini-calendar";
    wrap.appendChild(toolbar);
    wrap.appendChild(calendar);
    aside.insertBefore(wrap, aside.firstChild);

    function maps() {
      const live = new Map();
      const hist = new Map();
      classList.querySelectorAll(".class-card[data-live]").forEach(card => {
        const spans = [...card.querySelectorAll(".meta span")].map(x => x.textContent.trim());
        live.set(card.dataset.live, {
          location: spans[2] || "",
          instructor: spans.length ? spans[spans.length - 1] : ""
        });
      });
      classList.querySelectorAll(".class-card.history[data-hist]").forEach(card => {
        const spans = [...card.querySelectorAll(".meta span")].map(x => x.textContent.trim());
        const combined = spans[2] || "";
        const parts = combined.split(" · ");
        hist.set(card.dataset.hist, {
          location: parts.slice(0, -1).join(" · ") || combined,
          instructor: parts.length > 1 ? parts[parts.length - 1] : ""
        });
      });
      return { live, hist };
    }

    function timeOnly(button) {
      const b = button.querySelector("b");
      if (!b) return "";
      return b.textContent.split(" · ")[0].trim();
    }

    function rewriteCalendar() {
      const { live, hist } = maps();
      document.querySelectorAll("#cal .event[data-live], #cal .event[data-hist]").forEach(button => {
        const time = timeOnly(button);
        const info = button.dataset.live ? live.get(button.dataset.live) : hist.get(button.dataset.hist);
        if (!info) return;
        const instructor = info.instructor || "Instructor TBD";
        const loc = info.location || "Location TBD";
        button.innerHTML = `<b>${escapeHtml(time)} · ${escapeHtml(instructor)}</b><span class="mini-loc">${escapeHtml(loc)}</span>`;
      });
    }

    function escapeHtml(value) {
      return String(value || "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
    }

    let queued = false;
    function queueRewrite() {
      if (queued) return;
      queued = true;
      requestAnimationFrame(() => {
        queued = false;
        rewriteCalendar();
      });
    }

    new MutationObserver(queueRewrite).observe(classList, { childList:true, subtree:true });
    const cal = document.getElementById("cal");
    if (cal) new MutationObserver(queueRewrite).observe(cal, { childList:true, subtree:true });
    queueRewrite();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install, { once:true });
  else install();
})();
