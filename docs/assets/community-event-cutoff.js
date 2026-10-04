/* October 4 community pages only. No backend/session changes. */
(function () {
  'use strict';
  const cutoff = Date.parse('2026-10-04T11:30:00-04:00');
  let observer;
  function expired() { return Date.now() >= cutoff; }
  function close() {
    if (!expired()) return false;
    document.documentElement.dataset.communityEvent = 'passed';
    const banner = document.getElementById('event-passed-banner');
    if (banner) banner.hidden = false;
    const follow = document.getElementById('event-followup');
    if (follow) follow.hidden = false;
    document.querySelectorAll('form input,form select,form textarea,form button').forEach(el => {
      if (!el.disabled) el.disabled = true;
    });
    document.querySelectorAll('a[data-switch],a[data-registration-action]').forEach(el => {
      if (el.hasAttribute('href')) { el.dataset.closedHref = el.getAttribute('href'); el.removeAttribute('href'); }
      el.setAttribute('aria-disabled', 'true'); el.setAttribute('tabindex', '-1');
    });
    const button = document.getElementById('submit');
    if (button && button.textContent !== 'Registration closed') button.textContent = 'Registration closed';
    const seat = document.getElementById('seatLabel');
    if (seat && seat.textContent !== 'This community event has passed') seat.textContent = 'This community event has passed';
    if (!observer && document.body) {
      observer = new MutationObserver(close);
      observer.observe(document.body, {childList:true,subtree:true,attributes:true,attributeFilter:['disabled','href']});
    }
    return true;
  }
  window.CommunityEventCutoff = {closed: close, cutoff};
  document.addEventListener('submit', event => { if (close()) { event.preventDefault(); event.stopImmediatePropagation(); } }, true);
  document.addEventListener('click', event => {
    if (event.target.closest('a[data-switch],a[data-registration-action],form button') && close()) {
      event.preventDefault(); event.stopImmediatePropagation();
    }
  }, true);
  document.addEventListener('keydown', event => {
    if ((event.key === 'Enter' || event.key === ' ') && event.target.closest('form,a[data-switch],a[data-registration-action]') && close()) {
      event.preventDefault(); event.stopImmediatePropagation();
    }
  }, true);
  function check() {
    close();
    if (!expired()) setTimeout(check, Math.min(2147483647, Math.max(1, cutoff - Date.now())));
  }
  document.addEventListener('DOMContentLoaded', () => {
    check();
    const copy = document.getElementById('copy-page-details');
    if (copy) copy.addEventListener('click', async () => {
      const lines = ['URL: ' + location.href];
      ['page-id','build-id','release-built-at','asset-version'].forEach(name => lines.push(name + ': ' + document.querySelector('meta[name="' + name + '"]').content));
      try { await navigator.clipboard.writeText(lines.join('\n')); document.getElementById('page-details-status').textContent = ' Copied'; }
      catch { document.getElementById('page-details-status').textContent = ' Copy unavailable'; }
    });
  }, {once:true});
  window.addEventListener('pageshow', close);
  window.addEventListener('focus', close);
  document.addEventListener('visibilitychange', close);
  setInterval(close, 1000); // Recheck clock changes and already-open tabs; no server timer.
})();
