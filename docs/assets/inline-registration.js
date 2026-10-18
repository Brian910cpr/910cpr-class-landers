/* Keep registration beside the selected time; share the canonical registration UI. */
(() => {
  'use strict';
  const sessionPattern = /^(?:\d+|lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})$/;
  let current = null;
  function sessionFromLink(value) {
    const url = new URL(value, location.href);
    if (url.origin === location.origin && url.pathname === '/register/') {
      const id = url.searchParams.get('session');
      return sessionPattern.test(id || '') ? id : null;
    }
    if (url.origin === 'https://coastalcprtraining.enrollware.com' && url.pathname === '/enroll') {
      const id = url.searchParams.get('id');
      return /^\d+$/.test(id || '') ? id : null;
    }
    return null;
  }
  function close() {
    if (!current) return;
    current.link.setAttribute('aria-expanded', 'false');
    current.panel.remove();
    current = null;
  }
  document.addEventListener('click', event => {
    const link = event.target.closest?.('#course-list .register-link');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const sessionId = sessionFromLink(link.href);
    if (!sessionId) return; // Dynamic offers retain their existing booking contract.
    event.preventDefault();
    if (current?.link === link) { close(); return; }
    close();
    const panel = document.createElement('section');
    panel.className = 'inline-registration';
    panel.id = 'selected-time-checkout';
    panel.setAttribute('aria-label', 'Registration for your selected class');
    panel.style.cssText = 'grid-column:1/-1;width:100%;margin-top:16px;border:1px solid #d9e0e8;border-radius:12px;overflow:hidden;background:white';
    const cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.textContent = 'Close registration';
    cancel.style.cssText = 'display:block;margin:12px 12px 0 auto;padding:8px 12px';
    cancel.addEventListener('click', () => { close(); link.focus(); });
    const frame = document.createElement('iframe');
    frame.title = 'Class registration and checkout';
    frame.src = `/register/?session=${encodeURIComponent(sessionId)}&embed=1`;
    frame.style.cssText = 'display:block;width:100%;height:820px;border:0';
    panel.append(cancel, frame);
    link.closest('.course').appendChild(panel);
    link.setAttribute('aria-controls', panel.id);
    link.setAttribute('aria-expanded', 'true');
    current = {link, panel, frame, sessionId};
    frame.addEventListener('load', () => { if (current?.frame === frame) frame.focus(); });
    panel.scrollIntoView({behavior: 'smooth', block: 'start'});
  });
  addEventListener('message', event => {
    if (!current || event.origin !== location.origin || event.source !== current.frame.contentWindow) return;
    const data = event.data;
    if (data?.type !== 'landerware:checkout-size' || data.sessionId !== current.sessionId || !Number.isFinite(data.height)) return;
    current.frame.style.height = `${Math.min(16000, Math.max(280, data.height))}px`;
  });
  // Calendar renders remove the old card; never retain its detached frame/state.
  new MutationObserver(() => { if (current && !current.link.isConnected) close(); })
    .observe(document.getElementById('course-list') || document.body, {childList: true, subtree: true});
})();
