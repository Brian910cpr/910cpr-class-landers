/* Keep registration beside the selected time; share the canonical registration UI. */
(() => {
  'use strict';
  const sessionPattern = /^(?:\d+|lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})$/;
  let current = null;
  let draft = [];
  let draftCourse = '';
  const times = document.getElementById('start-list')?.closest('.panel');
  const choices = document.getElementById('course-list')?.closest('.panel');
  const grid = choices?.parentElement;
  function remember() {
    try {
      const cards = current?.frame.contentDocument.querySelectorAll('.student');
      if (cards?.length) draftCourse = current.frame.contentDocument.querySelector('h1')?.textContent || '';
      if (cards?.length) draft = [...cards].map(card => [...card.querySelectorAll('input')].map(input => ({
        field: input.dataset.field, billing: input.hasAttribute('data-billing-code'), completion: input.hasAttribute('data-online-completion-ack'), name: input.name, addon: input.dataset.addonKey,
        type: input.type, value: input.value, checked: input.checked
      })));
    } catch (_) { /* Never read a frame after it navigates to another origin. */ }
  }
  function restoreDraft() {
    if (!current || current.restored || !draft.length) return;
    try {
      const doc = current.frame.contentDocument;
      if (!doc.querySelector('.student')) return;
      const add = doc.getElementById('add-student');
      while (doc.querySelectorAll('.student').length < draft.length && add && !add.disabled) {
        const before = doc.querySelectorAll('.student').length;
        add.click();
        if (doc.querySelectorAll('.student').length === before) break;
      }
      [...doc.querySelectorAll('.student')].forEach((card, index) => {
        for (const saved of draft[index] || []) {
          const input = [...card.querySelectorAll('input')].find(input => !input.disabled &&
            (saved.field ? input.dataset.field === saved.field : saved.billing ? input.hasAttribute('data-billing-code') :
              draftCourse === (doc.querySelector('h1')?.textContent || '') &&
                (saved.completion ? input.hasAttribute('data-online-completion-ack') :
                 saved.addon ? input.dataset.addonKey === saved.addon && input.value === saved.value :
                 saved.name && input.name === saved.name && input.value === saved.value)));
          if (!input) continue;
          if (saved.type === 'radio' || saved.type === 'checkbox') input.checked = saved.checked;
          else input.value = saved.value;
          input.dispatchEvent(new current.frame.contentWindow.Event('change', {bubbles: true}));
        }
      });
      current.restored = true;
    } catch (_) { /* The native form remains authoritative and must load successfully. */ }
  }
  function showTimes() {
    if (times) times.hidden = false;
    if (choices) choices.hidden = false;
    if (current) current.panel.hidden = true;
  }
  function showIntake() {
    if (times) times.hidden = true;
    if (choices) choices.hidden = true;
    current.panel.hidden = false;
  }
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
    remember();
    showTimes();
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
    if (current?.sessionId === sessionId) {
      current.link = link;
      link.setAttribute('aria-expanded', 'true');
      link.setAttribute('aria-controls', current.panel.id);
      showIntake();
      return;
    }
    close();
    const panel = document.createElement('section');
    panel.className = 'inline-registration';
    panel.id = 'selected-time-checkout';
    panel.setAttribute('aria-label', 'Registration for your selected class');
    panel.style.cssText = 'grid-column:2/-1;min-width:0;width:100%;border:1px solid #d9e0e8;border-radius:12px;overflow:hidden;background:white';
    if (matchMedia('(max-width: 924px)').matches) panel.style.gridColumn = '1/-1';
    const cancel = document.createElement('button');
    cancel.type = 'button';
    const selected = document.querySelector('#start-list button[aria-pressed="true"]');
    cancel.textContent = `${selected?.textContent || 'Selected time'} — Change time ▾`;
    cancel.style.cssText = 'display:block;margin:12px 12px 0 auto;padding:8px 12px';
    cancel.addEventListener('click', () => { remember(); showTimes(); selected?.focus(); });
    const frame = document.createElement('iframe');
    frame.title = 'Class registration and checkout';
    frame.src = `/register/?session=${encodeURIComponent(sessionId)}&embed=1`;
    frame.style.cssText = 'display:block;width:100%;height:820px;border:0';
    panel.append(cancel, frame);
    if (!grid) return;
    grid.appendChild(panel);
    link.setAttribute('aria-controls', panel.id);
    link.setAttribute('aria-expanded', 'true');
    current = {link, panel, frame, sessionId};
    showIntake();
    frame.addEventListener('load', () => { if (current?.frame === frame) frame.focus(); });
    panel.scrollIntoView({behavior: 'smooth', block: 'start'});
  });
  addEventListener('message', event => {
    if (!current || event.origin !== location.origin || event.source !== current.frame.contentWindow) return;
    const data = event.data;
    if (data?.type !== 'landerware:checkout-size' || data.sessionId !== current.sessionId || !Number.isFinite(data.height)) return;
    restoreDraft();
    current.frame.style.height = `${Math.min(16000, Math.max(280, data.height))}px`;
  });
  addEventListener('resize', () => {
    if (current) current.panel.style.gridColumn = matchMedia('(max-width: 924px)').matches ? '1/-1' : '2/-1';
  });
  // Keep the frame outside regenerated cards. A new time requires a fresh
  // native session check, while customer input remains in this page's memory.
  new MutationObserver(() => { if (current && !current.link.isConnected) { remember(); showTimes(); } })
    .observe(document.getElementById('course-list') || document.body, {childList: true, subtree: true});
})();
